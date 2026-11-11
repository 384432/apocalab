/**
 * /nuclear-bomb-map/ gate, driven through CDP.
 *
 * Four states are asserted, because "the map works" is not one thing:
 *   A  tiles reachable   -> basemap live, rings drawn on top of it
 *   B  tiles blocked     -> fallback outline drawn, rings still drawn, one-line note shown
 *   C  shared URL        -> city/yield/burst restored, contact burst has no thermal rows
 *   D  scripting off     -> no empty frame, the numbers are still on the page
 *
 * Usage: node scripts/verify_map.mjs http://127.0.0.1:4322
 */
import { writeFileSync } from 'node:fs';

const BASE = process.argv[2] || 'http://127.0.0.1:4322';
const MAP = `${BASE}/nuclear-bomb-map/`;

const targets = await (await fetch('http://127.0.0.1:9333/json/list')).json();
const page = targets.find((t) => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    pending.get(m.id)(m);
    pending.delete(m.id);
  }
});
const send = (method, params = {}) =>
  new Promise((resolve) => {
    const mid = ++id;
    pending.set(mid, resolve);
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
await new Promise((r) => ws.addEventListener('open', r));
await send('Page.enable');
await send('Runtime.enable');
await send('Network.enable');

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function evaluate(expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.result?.exceptionDetails) {
    return { __error: r.result.exceptionDetails.text || 'exception' };
  }
  return r.result?.result?.value;
}

async function waitSettled(timeout = 25000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const s = await evaluate('window.__apocalabMap ? window.__apocalabMap.settled() : false');
    if (s === true) return true;
    await sleep(250);
  }
  return false;
}

const PROBE = `(() => {
  const g = (s) => { const n = document.querySelector(s); return n ? getComputedStyle(n).display : 'MISSING'; };
  const h = window.__apocalabMap;
  if (!h) return { hook: false };
  const p = h.pixels();
  const note = document.getElementById('map-note');
  return {
    hook: true,
    mode: h.mode(),
    rings: h.rings(),
    zoom: h.zoom(),
    state: h.state(),
    pixels: p,
    canvas: h.canvas(),
    note_hidden: note ? note.hidden : null,
    note_text: note ? note.textContent.trim().slice(0, 90) : null,
    readout: [...document.querySelectorAll('#map-readout .map-ro')].map((li) => ({
      name: li.querySelector('.nm').textContent,
      v: li.querySelector('.v').textContent.trim(),
      absent: li.dataset.absent || null,
    })),
    scroll_w: document.documentElement.scrollWidth,
    client_w: document.documentElement.clientWidth,
  };
})()`;

const out = {};

// ---------------------------------------------------------------- A: tiles
await send('Network.setBlockedURLs', { urls: [] });
await send('Page.navigate', { url: MAP });
await waitSettled();
await sleep(700);
out.tiles = await evaluate(PROBE);

// ---------------------------------------------------------------- B: blocked
await send('Network.setBlockedURLs', {
  urls: ['*openfreemap.org*', '*tiles.openfreemap*', '*openmaptiles*'],
});
await send('Page.navigate', { url: MAP });
await waitSettled();
await sleep(700);
out.blocked = await evaluate(PROBE);

// ---------------------------------------------------------------- C: maybe URL
await send('Network.setBlockedURLs', { urls: [] });
await send('Page.navigate', { url: `${MAP}?city=tokyo&yield=15&burst=ground` });
await waitSettled();
await sleep(500);
out.shared = await evaluate(PROBE);

// ---------------------------------------------------------------- D: no JS
await send('Emulation.setScriptExecutionDisabled', { value: true });
await send('Page.navigate', { url: MAP });
await sleep(900);
out.nojs = await evaluate(`(() => {
  const g = (s) => { const n = document.querySelector(s); return n ? getComputedStyle(n).display : 'MISSING'; };
  return {
    js_off: true,
    figure: g('.map-figure'),
    controls: g('.map-controls'),
    nojs_note: g('.map-nojs'),
    readout_rows: document.querySelectorAll('#map-readout .map-ro').length,
    values: [...document.querySelectorAll('#map-readout .v')].map((n) => n.textContent.trim()),
    srcs: [...document.querySelectorAll('#map-readout .src')].map((n) => n.textContent.trim()),
    h1: document.querySelector('h1') ? document.querySelector('h1').textContent.trim() : null,
  };
})()`);
await send('Emulation.setScriptExecutionDisabled', { value: false });

// ---------------------------------------------------------------- E: phone
await send('Emulation.setDeviceMetricsOverride', {
  width: 390,
  height: 844,
  deviceScaleFactor: 2,
  mobile: true,
});
await send('Page.navigate', { url: MAP });
await waitSettled();
await sleep(600);
out.phone = await evaluate(PROBE);
await send('Emulation.clearDeviceMetricsOverride');

// ---------------------------------------------------------------- verdict
const bad = [];
const A = out.tiles;
if (!A || !A.hook) bad.push('A: __apocalabMap 不存在（脚本没跑）');
else {
  if (A.mode !== 'tiles') bad.push(`A: mode=${A.mode}，期望 tiles`);
  if (A.rings !== 5) bad.push(`A: rings=${A.rings}，期望 5`);
  if (A.pixels.rings < 20000) bad.push(`A: 半径圈像素 ${A.pixels.rings}，太少`);
  if (A.note_hidden !== true) bad.push('A: 底图正常时不应显示降级说明');
  if (A.canvas.w < 300) bad.push(`A: 画布宽 ${A.canvas.w}`);
  if (A.scroll_w > A.client_w + 1) bad.push(`A: 横向溢出 ${A.scroll_w} > ${A.client_w}`);
}
const B = out.blocked;
if (!B || !B.hook) bad.push('B: __apocalabMap 不存在');
else {
  if (B.mode !== 'outline') bad.push(`B: mode=${B.mode}，期望 outline`);
  if (B.rings !== 5) bad.push(`B: rings=${B.rings}，期望 5`);
  if (B.pixels.base < 20000) bad.push(`B: 备用轮廓像素 ${B.pixels.base}，太少`);
  if (B.pixels.rings < 20000) bad.push(`B: 降级时半径圈像素 ${B.pixels.rings}，太少`);
  if (B.note_hidden !== false) bad.push('B: 降级时应显示一行说明');
}
const C = out.shared;
if (!C || !C.hook) bad.push('C: __apocalabMap 不存在');
else {
  if (JSON.stringify(C.state) !== JSON.stringify({ city: 'tokyo', y: 15, b: 'ground' }))
    bad.push(`C: URL 状态没还原（${JSON.stringify(C.state)}）`);
  const absent = C.readout.filter((r) => r.absent === '1').length;
  if (absent !== 2) bad.push(`C: 地爆应有 2 行无热辐射（实际 ${absent}）`);
  if (C.readout.length !== 5) bad.push(`C: 读数列 ${C.readout.length} 行`);
}
const D = out.nojs;
if (!D) bad.push('D: 关 JS 探针失败');
else {
  if (D.figure !== 'none') bad.push(`D: 关 JS 时地图 frame 应隐藏（display=${D.figure}）`);
  if (D.readout_rows !== 5) bad.push(`D: 关 JS 时读数 ${D.readout_rows} 行`);
  if (D.nojs_note === 'none') bad.push('D: 关 JS 时应说明地图需要脚本');
  if (!D.srcs.every((s) => /p\. \d+/.test(s))) bad.push('D: 关 JS 时每行仍要带页码');
}

const E = out.phone;
if (!E || !E.hook) bad.push('E: 手机宽度探针失败');
else {
  if (E.scroll_w > E.client_w + 1) bad.push(`E: 390 px 下横向溢出 ${E.scroll_w} > ${E.client_w}`);
  if (E.canvas.w > 390) bad.push(`E: 画布宽 ${E.canvas.w} 超出视口`);
  if (E.canvas.w < 300) bad.push(`E: 手机画布宽 ${E.canvas.w} 太窄`);
}

out.verdict = { ok: bad.length === 0, problems: bad };
writeFileSync('map-gate.json', JSON.stringify(out, null, 2), 'utf8');
console.log(JSON.stringify(out.verdict, null, 2));
ws.close();
process.exit(bad.length ? 1 : 0);
