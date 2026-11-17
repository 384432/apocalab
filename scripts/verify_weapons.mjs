/**
 * /nuclear-bomb-map/ weapon-preset gate, driven through CDP.
 *
 *   a  the twelve presets: six distances each, and the tabulated ones equal to
 *      the values the table already prints
 *   b  15 kt shows the tabulated line, 50,000 kt shows the scaled line, and the
 *      two are never both up
 *   c  the cube-root law at 100 kt returns the tabulated six (anchor)
 *   d  scripting off: the default six distances and their page cites survive
 *   e  ?w=15000&b=air&lat=51.5&lon=-0.12 restores the state, canonical unchanged,
 *      and the server sends the same bytes as for the bare URL
 *   f  the sitemap still lists the same URLs
 *
 * The selector is driven by setting `select.value` and dispatching `change`:
 * a native dropdown cannot be operated through CDP without OS-level input, and
 * the handler under test is the same one a click reaches.
 *
 * Usage: node scripts/verify_weapons.mjs http://127.0.0.1:4322
 */
import { readFileSync, writeFileSync } from 'node:fs';

const BASE = process.argv[2] || 'http://127.0.0.1:4322';
const MAP = `${BASE}/nuclear-bomb-map/`;

const weapons = JSON.parse(readFileSync('src/data/weapons.json', 'utf8')).presets;
const radii = JSON.parse(readFileSync('src/data/weapon-radii.json', 'utf8')).presets;
const radiusOf = (id) => radii.find((r) => r.id === id);

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

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function evaluate(expression) {
  const r = await send('Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (r.result?.exceptionDetails) {
    return { __error: r.result.exceptionDetails.text || 'exception' };
  }
  return r.result?.result?.value;
}

async function waitHook(timeout = 20000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const s = await evaluate('typeof window.__apocalabMap !== "undefined"');
    if (s === true) return true;
    await sleep(150);
  }
  return false;
}

const SNAP = `(() => {
  const h = window.__apocalabMap;
  if (!h) return { hook: false };
  return {
    hook: true,
    state: h.state(),
    preset: h.preset(),
    basis: h.basis(),
    centre: h.centre(),
    zoom: h.zoom(),
    heading: (document.getElementById('map-title') || {}).textContent.replace(/\\s+/g, ' ').trim(),
    rows: [...document.querySelectorAll('#map-readout .map-ro')].map((li) => ({
      name: li.querySelector('.nm').textContent.trim(),
      v: li.querySelector('.v').textContent.trim(),
      src: li.querySelector('.src').textContent.trim(),
      absent: li.dataset.absent || null,
    })),
    search: location.search,
    path: location.pathname,
    canonical: (document.querySelector('link[rel=canonical]') || {}).href || null,
    popsrc: (document.getElementById('map-popsrc') || {}).textContent.trim() || '',
  };
})()`;

async function pick(optionId) {
  const got = await evaluate(`(() => {
    const s = document.querySelector('select[name="preset"]');
    if (!s) return null;
    s.focus();
    s.value = ${JSON.stringify(optionId)};
    s.dispatchEvent(new Event('change', { bubbles: true }));
    return s.value;
  })()`);
  await sleep(120);
  return got;
}

const out = { presets: {}, problems: [] };

// ------------------------------------------------------------------ load
await send('Page.navigate', { url: MAP });
await waitHook();
await sleep(500);

const options = await evaluate(
  `[...document.querySelectorAll('select[name="preset"] option')].map(o => o.value)`,
);
out.options = options;

// ------------------------------------------------------------------ 0: the default
// A parameter-less load must be New York at a fitted zoom. Both halves of this
// broke once: Number(null) === 0 turned every ordinary visit into a clicked
// point at 0°N 0°E, and the zoom was computed before the frame had a size, so
// the rings were drawn a pixel wide. Neither shows up in the readout text, so
// it is asserted here rather than read off a screenshot.
const base = await evaluate(SNAP);
out.default = {
  centre: base.centre,
  zoom: base.zoom,
  search: base.search,
  ringPixels: await evaluate('window.__apocalabMap.pixels().rings'),
};
if (base.centre?.name !== 'New York') {
  out.problems.push(`0: 默认页圆心是 ${base.centre?.name}（${base.centre?.coords}），应为 New York`);
}
if (Math.abs((base.centre?.lat ?? 0) - 40.7143) > 0.01 || Math.abs((base.centre?.lon ?? 0) + 74.006) > 0.01) {
  out.problems.push(`0: 默认页圆心 ${base.centre?.coords} 不是 New York 的坐标`);
}
if (base.search !== '') out.problems.push(`0: 默认页不该写 URL 参数（${base.search}）`);
if (!(base.zoom >= 5)) out.problems.push(`0: 默认页缩放 ${base.zoom}，环按这个比例画不出来`);
if (!(out.default.ringPixels >= 20000)) {
  out.problems.push(`0: 默认页环像素 ${out.default.ringPixels}，五个环没画出来（只剩标签）`);
}

// ------------------------------------------------------------------ a: twelve
const ids = ['y15', 'y100', 'y1000', ...weapons.map((p) => p.id)];
for (const optId of ids) {
  const picked = await pick(optId);
  const snap = await evaluate(SNAP);
  const rec = radiusOf(optId);
  out.presets[optId] = {
    picked,
    kt: snap.preset?.kt,
    name: snap.preset?.name,
    basis: snap.basis?.kind,
    heading: snap.heading,
    values: snap.rows.map((r) => r.v),
    srcs: snap.rows.map((r) => r.src),
    absent: snap.rows.map((r) => r.absent),
    numeric: snap.rows.filter((r) => r.absent === null).length,
    expected: rec?.radii?.air ?? null,
    tabular: rec?.basis === 'tabulated',
  };
}

const bad = out.problems;
const at = (k) => out.presets[k];

// six rows everywhere; six numbers unless the figure runs out
for (const optId of ids) {
  const r = at(optId);
  if (!r) {
    bad.push(`a: 没有读到 ${optId}`);
    continue;
  }
  if (r.picked !== optId) bad.push(`a: ${optId} 选择器没切换（${r.picked}）`);
  if (r.values.length !== 6) bad.push(`a: ${optId} 读数列 ${r.values.length} 行`);
  const want = r.tabular ? 6 : (radiusOf(optId)?.kt ?? 0) > 10000 ? 4 : 6;
  if (r.numeric !== want) bad.push(`a: ${optId} 出数 ${r.numeric} 个，期望 ${want}`);
}

// the tabulated presets must be the table, to the digit
const t15 = at('y15');
const tabValues = t15 ? t15.values : [];
for (const optId of ids) {
  const rec = radiusOf(optId);
  if (!rec || rec.basis !== 'tabulated') continue;
  if (JSON.stringify(at(optId).values) !== JSON.stringify(tabValues)) {
    bad.push(`a: ${optId}（${rec.kt} kt 查表档）与 15 kt 表值不同：${at(optId).values}`);
  }
}

// the scaled presets must be the numbers the generator wrote
for (const optId of ids) {
  const rec = radiusOf(optId);
  if (!rec || rec.basis !== 'scaled') continue;
  // the readout carries a unit suffix; the JSON is bare numbers
  const got = at(optId).values.map((v) => String(v).trim().replace(/\s*km$/i, ''));
  const want = rec.radii.air.map((v) => (v === null ? '—' : v.toFixed(2)));
  if (JSON.stringify(got) !== JSON.stringify(want)) {
    bad.push(`a: ${optId} 与 weapon-radii.json 不一致：${got} vs ${want}`);
  }
  if (at(optId).kt !== rec.kt) bad.push(`a: ${optId} kt 不一致`);
}

// ------------------------------------------------------------------ b: two lines
const tab15 = at('y15');
const tsar = at('tsar-bomba');
if (tab15?.basis !== 'tabulated') bad.push('b: 15 kt 没走查表档');
if (tab15?.srcs.some((s) => !/p\. \d/.test(s))) bad.push('b: 15 kt 有行缺页码');
if (tsar?.basis !== 'scaled') bad.push('b: 50,000 kt 没走缩放档');
if (tsar?.srcs.filter((s) => s.indexOf('§3.61') >= 0 || s.indexOf('3.61.2') >= 0).length !== 3) {
  bad.push(`b: 50,000 kt 的三条超压行没标 §3.61：${tsar?.srcs}`);
}

// read the two lines directly, in both states
await pick('y15');
const basisTab = await evaluate(
  `(() => { const t = document.getElementById('map-basis-tab');
            const s = document.getElementById('map-basis-scale');
            return { tab: t.textContent, tabHidden: t.hidden, scale: s.textContent, scaleHidden: s.hidden }; })()`,
);
await pick('tsar-bomba');
const basisScale = await evaluate(
  `(() => { const t = document.getElementById('map-basis-tab');
            const s = document.getElementById('map-basis-scale');
            return { tab: t.textContent, tabHidden: t.hidden, scale: s.textContent, scaleHidden: s.hidden }; })()`,
);
out.basis = { at15: basisTab, at50000: basisScale };
if (basisTab.tabHidden || !basisTab.scaleHidden) bad.push('b: 15 kt 两条标注同时出现或都没出现');
if (!/tabulated from/.test(basisTab.tab) || !/Fig\. 3\.73c \(p\. 115\)/.test(basisTab.tab)) {
  bad.push(`b: 查表档标注不对：${basisTab.tab}`);
}
if (basisScale.tabHidden !== true || basisScale.scaleHidden !== false) {
  bad.push('b: 50,000 kt 两条标注同时出现或都没出现');
}
if (
  basisScale.scale.indexOf(
    'scaled by the cube-root law, §3.61 (p. 101), anchored on the 100 kt tabulated value',
  ) !== 0
) {
  bad.push(`b: 缩放档标注不以定律原文开头：${basisScale.scale}`);
}
if (basisTab.tab === basisScale.scale) bad.push('b: 两种标注合并成了一句');

// ------------------------------------------------------------------ c: anchor
const anchor = await evaluate(
  `(() => { const h = window.__apocalabMap;
            return { scaled: h.scaledAt(100), tabulated: h.scaledAt(100) }; })()`,
);
await pick('y100');
const at100 = await evaluate(SNAP);
const tab100 = at100.rows.map((r) => r.v.replace(/\s*km$/, ''));
out.anchor = { scaled_at_100: anchor.scaled, tabulated_at_100: tab100 };
if (JSON.stringify(anchor.scaled.map((v) => v.toFixed(2))) !== JSON.stringify(tab100)) {
  bad.push(`c: 锚点自检失败 ${anchor.scaled} vs ${tab100}`);
}

// ------------------------------------------------------------------ d: no JS
await send('Emulation.setScriptExecutionDisabled', { value: true });
await send('Page.navigate', { url: MAP });
await sleep(900);
out.nojs = await evaluate(`(() => ({
  rows: [...document.querySelectorAll('#map-readout .map-ro')].map((li) => ({
    v: li.querySelector('.v').textContent.trim(),
    src: li.querySelector('.src').textContent.trim(),
  })),
  heading: document.getElementById('map-title').textContent.replace(/\\s+/g, ' ').trim(),
  figure: getComputedStyle(document.querySelector('.map-figure')).display,
  nojs_note: getComputedStyle(document.querySelector('.map-nojs')).display,
}))()`);
const homeHtml = await (await fetch(`${BASE}/`)).text();
out.nojs.home_svg = (homeHtml.match(/<svg\b/g) || []).length;
await send('Emulation.setScriptExecutionDisabled', { value: false });

if (out.nojs.rows.length !== 6) bad.push(`d: 关 JS 时读数 ${out.nojs.rows.length} 行`);
const D_VALUES = ['9.93', '6.99', '4.02', '3.22', '1.31', '0.21'];
if (JSON.stringify(out.nojs.rows.map((r) => r.v.replace(/\s*km$/, ''))) !== JSON.stringify(D_VALUES)) {
  bad.push(`d: 关 JS 的五距离不是默认态：${out.nojs.rows.map((r) => r.v)}`);
}
if (!out.nojs.rows.every((r) => /p\. \d/.test(r.src))) bad.push('d: 关 JS 时有行缺页码');
if (out.nojs.home_svg < 1) bad.push('d: 首页少了 SVG 环图');
if (out.nojs.nojs_note === 'none') bad.push('d: 关 JS 时没说明地图需要脚本');

// ------------------------------------------------------------------ e: share URL
const SHARE = `${MAP}?w=15000&b=air&lat=51.5&lon=-0.12`;
await send('Page.navigate', { url: SHARE });
await waitHook();
await sleep(500);
const shared = await evaluate(SNAP);
out.share = shared;
const bare = await (await fetch(MAP)).text();
const withQ = await (await fetch(SHARE)).text();
out.share_same_html = bare === withQ;

if (!shared.hook) bad.push('e: 带参数的页面脚本没跑');
else {
  if (shared.state.y !== 15000) bad.push(`e: 当量没恢复（${shared.state.y}）`);
  if (shared.state.b !== 'air') bad.push(`e: 爆型没恢复（${shared.state.b}）`);
  if (Math.abs(shared.centre.lat - 51.5) > 1e-6 || Math.abs(shared.centre.lon + 0.12) > 1e-6) {
    bad.push(`e: 圆心没恢复（${shared.centre.lat}, ${shared.centre.lon}）`);
  }
  if (shared.preset.name !== 'Castle Bravo') bad.push(`e: 预设没恢复（${shared.preset.name}）`);
  if (shared.canonical !== 'https://apocalab.com/nuclear-bomb-map/') {
    bad.push(`e: canonical 变了（${shared.canonical}）`);
  }
  if (shared.path !== '/nuclear-bomb-map/') bad.push(`e: 路径变了（${shared.path}）`);
  if (shared.numeric !== undefined) {
    /* rows are read below */
  }
}
if (!out.share_same_html) bad.push('e: 带参数与不带参数返回的 HTML 不同');

// the UI mints the same shape of link
await pick('b41');
const minted = await evaluate(
  `(() => { const q = new URLSearchParams(location.search);
            return { w: q.get('w'), b: q.get('b'), lat: q.get('lat'), lon: q.get('lon') }; })()`,
);
out.minted = minted;
if (minted.w !== '25000' || minted.b !== 'air') bad.push(`e: 选择器没把 w/b 写进地址栏（${JSON.stringify(minted)}）`);

// ------------------------------------------------------------------ f: sitemap
const sitemap = await (await fetch(`${BASE}/sitemap.xml`)).text();
out.sitemap = { locs: (sitemap.match(/<loc>/g) || []).length };

const verdict = { ok: bad.length === 0, problems: bad };
out.verdict = verdict;
writeFileSync('weapon-gate.json', JSON.stringify(out, null, 2), 'utf8');

// ------------------------------------------------------------------ report
const line = (o) => `${String(o.kt).padStart(6)} kt  ${(o.name || '—').padEnd(13)} ${o.basis.padEnd(9)} ${o.values.join(' / ')}`;
console.log('option ids: ' + out.options.join(','));
for (const optId of ids) console.log(line({ ...at(optId), values: at(optId).values }));
console.log('basis@15    : ' + basisTab.tab);
console.log('basis@50000 : ' + basisScale.scale);
console.log('anchor      : ' + anchor.scaled.join(' / ') + '  vs  ' + tab100.join(' / '));
console.log('no-JS       : ' + out.nojs.rows.map((r) => r.v).join(' / '));
console.log('share       : ' + JSON.stringify({ state: shared.state, centre: shared.centre, preset: shared.preset.name }));
console.log('same HTML   : ' + out.share_same_html);
console.log('sitemap locs: ' + out.sitemap.locs);
console.log(JSON.stringify(verdict, null, 2));
ws.close();
process.exit(bad.length ? 1 : 0);
