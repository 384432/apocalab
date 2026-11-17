/**
 * Click-to-measure gate for /nuclear-bomb-map/.
 *
 * Every step lands a real pointer on the map through CDP Input.*, because "a
 * click works" has to mean a pointer event arrived, not that a helper function
 * was called. The camera is positioned with the page's `goto` test hook — a gate
 * needs a viewport over the Atlantic before it can click the Atlantic — and the
 * state afterwards is read back through the same hook.
 *
 * Acceptance items, one section each:
 *   a  any point -> six rings, and the six distances are the preset distances
 *   b  a click on a tabulated city -> the tabulated figures, digit for digit
 *   c  open ocean / desert -> 0 or "unavailable", no exception, no blank page
 *   d  the URL and the canonical do not move
 *   e  one click -> at most four tile requests, and nothing else of ours
 *   f  tiles forced to 404 -> rings stay, population says unavailable
 *   g  a tap on a phone behaves like a click on a desktop
 *
 * Usage: node scripts/verify_click.mjs http://127.0.0.1:4322
 */
import { writeFileSync } from 'node:fs';

const BASE = process.argv[2] || 'http://127.0.0.1:4322';
const MAP = `${BASE}/nuclear-bomb-map/`;

const targets = await (await fetch('http://127.0.0.1:9333/json/list')).json();
const page = targets.find((t) => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
const exceptions = [];
const requests = [];
let recording = false;

ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) {
    pending.get(m.id)(m);
    pending.delete(m.id);
    return;
  }
  if (m.method === 'Runtime.exceptionThrown') {
    exceptions.push(
      m.params.exceptionDetails.exception?.description ||
        m.params.exceptionDetails.text ||
        'exception',
    );
  }
  if (m.method === 'Network.requestWillBeSent' && recording) {
    requests.push(m.params.request.url);
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
await send('Network.setBlockedURLs', { urls: [] });

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function evaluate(expression) {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.result?.exceptionDetails) return { __error: r.result.exceptionDetails.text || 'exception' };
  return r.result?.result?.value;
}

async function settled(timeout = 25000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    if (await evaluate('window.__apocalabMap && window.__apocalabMap.settled()')) return true;
    await sleep(200);
  }
  return false;
}

const READ = `(() => {
  const h = window.__apocalabMap;
  if (!h) return { hook: false };
  const canon = document.querySelector('link[rel=canonical]');
  const title = document.getElementById('map-title');
  const point = document.getElementById('map-point');
  const popsrc = document.getElementById('map-popsrc');
  const txt = (n) => (n ? n.textContent.replace(/\\s+/g, ' ').trim() : null);
  return {
    hook: true,
    mode: h.mode(),
    rings: h.rings(),
    centre: h.centre(),
    pop: h.pop(),
    tiles: h.tileNames(),
    tile_requests: h.tileRequests(),
    ring_pixels: h.pixels().rings,
    href: location.href,
    canonical: canon ? canon.href : null,
    heading: txt(title),
    point_line: point && !point.hidden ? txt(point) : null,
    popsrc: popsrc && !popsrc.hidden ? txt(popsrc) : null,
    rows: [...document.querySelectorAll('#map-readout .map-ro')].map((li) => ({
      name: li.querySelector('.nm').textContent,
      v: li.querySelector('.v').textContent.trim(),
      pop: li.querySelector('.pop') ? li.querySelector('.pop').textContent.trim() : null,
      src: li.querySelector('.src').textContent.trim(),
    })),
  };
})()`;

const read = () => evaluate(READ);

async function waitPop(timeout = 12000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    const p = await evaluate('window.__apocalabMap ? window.__apocalabMap.pop().kind : "none"');
    if (p !== 'loading') return p;
    await sleep(150);
  }
  return 'timeout';
}

/** The frame has to be on screen before a pointer can land on it. */
async function scrollFrame() {
  await evaluate(
    `document.getElementById('map-frame').scrollIntoView({block: 'center', behavior: 'instant'})`,
  );
  await sleep(300);
}

/** Frame-relative pixel of a lon/lat, plus the frame's screen offset. */
async function pixelOf(lon, lat) {
  const pt = await evaluate(`window.__apocalabMap.screen(${lon}, ${lat})`);
  const rect = await evaluate(
    `(() => { const r = document.getElementById('map-frame').getBoundingClientRect();
       return { x: r.left, y: r.top, w: r.width, h: r.height }; })()`,
  );
  return { x: Math.round(rect.x + pt.x), y: Math.round(rect.y + pt.y), rect, local: pt };
}

/** Centre pixel of the frame: after goto(), that is the point that was asked for. */
async function centrePixel() {
  const rect = await evaluate(
    `(() => { const r = document.getElementById('map-frame').getBoundingClientRect();
       return { x: r.left, y: r.top, w: r.width, h: r.height }; })()`,
  );
  return { x: Math.round(rect.x + rect.w / 2), y: Math.round(rect.y + rect.h / 2), rect };
}

async function clickPx(x, y) {
  await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y, button: 'none' });
  await send('Input.dispatchMouseEvent', { type: 'mousePressed', x, y, button: 'left', clickCount: 1 });
  await send('Input.dispatchMouseEvent', { type: 'mouseReleased', x, y, button: 'left', clickCount: 1 });
}

async function tapPx(x, y) {
  await send('Input.dispatchTouchEvent', {
    type: 'touchStart',
    touchPoints: [{ x, y, radiusX: 6, radiusY: 6, force: 1, id: 1 }],
  });
  await sleep(40);
  await send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
}

const isBase = (u) => /openfreemap|openmaptiles|maplibre/i.test(u);
async function counted(fn) {
  requests.length = 0;
  recording = true;
  const out = await fn();
  await sleep(500);
  recording = false;
  const pop = requests.filter((u) => u.includes('/data/pop/'));
  const base = requests.filter((u) => isBase(u));
  const other = requests.filter((u) => !u.includes('/data/pop/') && !isBase(u));
  return { out, pop, base, other };
}

async function gotoAndClick(lon, lat) {
  await evaluate(`window.__apocalabMap.goto(${lon}, ${lat})`);
  await sleep(900);
  await scrollFrame();
  const c = await centrePixel();
  const res = await counted(async () => {
    await clickPx(c.x, c.y);
    const kind = await waitPop();
    return { kind, after: await read(), px: { x: c.x, y: c.y } };
  });
  return res;
}

const out = { base: BASE };

// ---------------------------------------------------------------- reference
await send('Page.navigate', { url: MAP });
await settled();
await sleep(900);
out.reference = await read();
const preset = out.reference.rows.map((r) => `${r.name}|${r.v}`);

// ---------------------------------------------------------------- a + e
out.a = await gotoAndClick(8.0, 47.0);
out.a.same_distances =
  JSON.stringify(out.a.out.after.rows.map((r) => `${r.name}|${r.v}`)) ===
  JSON.stringify(preset);
out.a.distances = out.a.out.after.rows.map((r) => r.v).join(' | ');

// second click in the same tile: the cache must answer, so zero requests
out.e_cached = await gotoAndClick(8.1, 47.1);

// ---------------------------------------------------------------- b: snap
out.b = await gotoAndClick(-74.006, 40.7143);
const table = await evaluate(
  `(() => { const d = JSON.parse(document.getElementById('apoca-map-island').textContent);
     return d.pop ? d.pop['new-york'] : null; })()`,
);
const rowKeys = ['9.930', '6.990', '4.020', '3.220', '1.310', '0.210'];
out.b.table = rowKeys.map((k) => table[k]);
out.b.table_text = out.b.table.map((v) => Number(v).toLocaleString('en-US')).join(',');
out.b.rows_text = out.b.out.after.rows.map((r) => r.pop).join(',');
out.b.identical = out.b.table_text === out.b.rows_text;

// b2: the 5 km radius is a boundary, not a decoration, and it is not New York
// only. At Paris, +3 km east is tabulated, +8 km east is the tile surface.
// 3 km / (111.32 * cos 48.85) = 0.0409°, 8 km = 0.109°.
out.b2 = {};
out.b2.near = await gotoAndClick(2.3488 + 0.041, 48.8534);
out.b2.far = await gotoAndClick(2.3488 + 0.109, 48.8534);

const parisTable = await evaluate(
  `(() => { const d = JSON.parse(document.getElementById('apoca-map-island').textContent);
     return d.pop ? d.pop['paris'] : null; })()`,
);
out.b2.near_table = rowKeys.map((k) => parisTable[k]);
out.b2.near_identical =
  out.b2.near_table.map((v) => Number(v).toLocaleString('en-US')).join(',') ===
  out.b2.near.out.after.rows.map((r) => r.pop).join(',');

// ---------------------------------------------------------------- c: ocean, desert
out.c = {};
out.c.ocean = await gotoAndClick(-30.0, 0.0);
out.c.desert = await gotoAndClick(12.0, 23.0);

// ---------------------------------------------------------------- d: url
out.d = {
  href_before: out.reference.href,
  href_after: out.c.desert.out.after.href,
  canonical_before: out.reference.canonical,
  canonical_after: out.c.desert.out.after.canonical,
  heading_after: out.c.desert.out.after.heading,
};

// ---------------------------------------------------------------- f: 404 tiles
await evaluate('window.__apocalabMap.goto(140.0, 36.5)');
await sleep(900);
await scrollFrame();
await send('Network.setBlockedURLs', { urls: ['*/data/pop/*'] });
{
  const c = await centrePixel();
  const blocked = await counted(async () => {
    await clickPx(c.x, c.y);
    await waitPop();
    return null;
  });
  out.f = await read();
  // The requests are counted even though they were blocked: the point of the case
  // is that an attempted fetch exists and the UI degrades instead of showing 0.
  out.f.attempted = blocked.pop;
  // A second click on the same point must not ask again: a failure is cached too,
  // otherwise every click in a dead tile would retry the same 404.
  const again = await counted(async () => {
    await clickPx(c.x, c.y);
    await sleep(700);
    return null;
  });
  out.f.repeated = again.pop;
  out.f.still_unavailable = (await read()).pop.kind === 'unavailable';
}
await send('Network.setBlockedURLs', { urls: [] });

// ---------------------------------------------------------------- h: no basemap
// With the basemap blocked the page still draws rings from the bundled outline,
// and a click still lands: the click path must not depend on MapLibre.
await send('Network.setBlockedURLs', {
  urls: ['*openfreemap.org*', '*tiles.openfreemap*', '*openmaptiles*'],
});
await send('Page.navigate', { url: MAP });
await settled();
await sleep(1500);
out.h = await gotoAndClick(8.4, 47.1);
await send('Network.setBlockedURLs', { urls: [] });

// ---------------------------------------------------------------- g: tap
await send('Emulation.setDeviceMetricsOverride', {
  width: 390,
  height: 844,
  deviceScaleFactor: 2,
  mobile: true,
});
await send('Emulation.setTouchEmulationEnabled', { enabled: true, maxTouchPoints: 5 });
await send('Page.navigate', { url: MAP });
await settled();
await sleep(900);
out.phone_reference = await read();
// Desktop parity: click the same point on the phone viewport, then tap the very
// same pixel. Same pixel, same camera, so the two figures have to be identical —
// that is what "a tap behaves like a click" means.
out.g = await gotoAndClick(8.0, 47.0);
{
  const c = await centrePixel();
  out.g.touch = await counted(async () => {
    await tapPx(c.x, c.y);
    const kind = await waitPop();
    return { kind, after: await read(), px: { x: c.x, y: c.y } };
  });
}
await send('Emulation.setTouchEmulationEnabled', { enabled: false });
await send('Emulation.clearDeviceMetricsOverride');

// ---------------------------------------------------------------- verdict
const bad = [];
const A = out.a.out.after;
if (A.rings !== 6) bad.push(`a: 环 ${A.rings} 条，期望 6`);
if (!out.a.same_distances) bad.push('a: 五个距离与预设不同');
if (A.pop.kind !== 'tiles') bad.push(`a: 人口来源 ${A.pop.kind}，期望 tiles`);
if (!A.pop.vals) bad.push('a: 没有环内人口');
if (!A.popsrc) bad.push('a: 人口来源一行缺失');

const B = out.b.out.after;
if (B.pop.kind !== 'tabulated') bad.push(`b: 状态 ${B.pop.kind}，期望 tabulated`);
if (B.pop.city !== 'New York') bad.push(`b: 吸附到 ${B.pop.city}`);
if (B.pop.snapped !== true) bad.push('b: 没有标记 snapped');
if (!out.b.identical) bad.push(`b: 行内数字 ${out.b.rows_text} ≠ 表 ${out.b.table_text}`);
if (!/snapped to New York — tabulated city/.test(B.popsrc || ''))
  bad.push(`b: 说明文字缺失（${B.popsrc}）`);
if (out.b.pop.length > 0) bad.push(`b: 吸附时不该请求瓦片，实际 ${out.b.pop.length}`);

// b2: 3 km from Paris snaps to the table, 8 km does not.
const B2N = out.b2.near.out.after;
const B2F = out.b2.far.out.after;
if (B2N.pop.kind !== 'tabulated' || B2N.pop.city !== 'Paris')
  bad.push(`b2: 3 km 外应为 Paris 表值，实际 ${B2N.pop.kind}/${B2N.pop.city}`);
if (!out.b2.near_identical)
  bad.push(`b2: 吸附值与 paris 表不同（${out.b2.near.out.after.rows.map((r) => r.pop).join(',')} vs ${out.b2.near_table.join(',')}）`);
if (B2F.pop.kind !== 'tiles')
  bad.push(`b2: 8 km 外应走瓦片，实际 ${B2F.pop.kind}/${B2F.pop.city}`);
if (out.b2.near.pop.length > 0) bad.push(`b2: 吸附时请求了 ${out.b2.near.pop.length} 个瓦片`);

const ocean = out.c.ocean.out.after;
const oasis = ocean.pop.vals || {};
if (ocean.pop.kind === 'tiles' && Object.values(oasis).some((v) => v !== 0))
  bad.push(`c: 大洋应全 0（${JSON.stringify(oasis)}）`);
if (ocean.pop.kind !== 'tiles' && ocean.pop.kind !== 'unavailable')
  bad.push(`c: 大洋状态 ${ocean.pop.kind}`);
if (ocean.rings !== 6) bad.push('c: 大洋没有画环');
const desert = out.c.desert.out.after;
if (desert.pop.kind !== 'tiles' && desert.pop.kind !== 'unavailable')
  bad.push(`c: 沙漠状态 ${desert.pop.kind}`);
if (!desert.heading || !/Clicked point/.test(desert.heading))
  bad.push(`c: 状态区没变（${desert.heading}）`);

if (out.d.href_before !== out.d.href_after) bad.push('d: 点击改了地址栏');
if (out.d.canonical_before !== out.d.canonical_after) bad.push('d: canonical 变了');
if (!/\/nuclear-bomb-map\/$/.test(new URL(out.d.canonical_after).pathname))
  bad.push(`d: canonical 指向 ${out.d.canonical_after}`);

if (out.a.pop.length > 4) bad.push(`e: 一次点击请求 ${out.a.pop.length} 个瓦片`);
if (out.a.pop.length === 0) bad.push('e: 一次点击没有请求瓦片');
if (out.a.other.length > 0) bad.push(`e: 点击另有请求 ${out.a.other.join(' ')}`);
if (out.e_cached.pop.length > 0) bad.push(`e: 同瓦片第二次点击又请求了 ${out.e_cached.pop.length} 个`);

if (out.f.pop.kind !== 'unavailable') bad.push(`f: 404 时状态是 ${out.f.pop.kind}`);
if (!/circle population unavailable at this point/.test(out.f.popsrc || ''))
  bad.push(`f: 提示文字不对（${out.f.popsrc}）`);
if (out.f.rings !== 6) bad.push('f: 404 时环丢了');
if (out.f.ring_pixels < 20000) bad.push('f: 404 时环没画出来');
if ((out.f.repeated || []).length > 0)
  bad.push(`f: 失败瓦片没有缓存，第二次点击又请求了 ${out.f.repeated.length} 个`);
if (!out.f.still_unavailable) bad.push('f: 第二次点击不再是 unavailable');

if (out.h.out.after.mode !== 'outline') bad.push(`h: 无底图时 mode=${out.h.out.after.mode}`);
if (out.h.out.after.rings !== 6) bad.push('h: 无底图时环数不对');
if (out.h.out.after.pop.kind !== 'tiles') bad.push(`h: 无底图时人口状态 ${out.h.out.after.pop.kind}`);
if (out.h.out.after.ring_pixels < 20000) bad.push('h: 无底图时环没画出来');

const gt = out.g.touch.out.after;
const gm = out.g.out.after;
if (gm.pop.kind !== 'tiles') bad.push(`g: 手机视口点击状态 ${gm.pop.kind}`);
if (!gm.pop.vals) bad.push('g: 手机视口点击没出人口');
if (gt.pop.kind !== 'tiles') bad.push(`g: 触摸点击状态 ${gt.pop.kind}`);
if (!gt.pop.vals) bad.push('g: 触摸点击没出人口');
if (gt.rings !== 6) bad.push('g: 手机点击环数不对');
// Chrome's touch adjustment moves a touch by a pixel or two even when both
// events carry the same integer coordinates, so the two figures are compared
// with a 1% band rather than byte equality; the landing difference is recorded.
const rel = (a, b) => Math.abs(a - b) / Math.max(1, b);
out.g.worst_relative_difference = Math.max(
  ...Object.keys(gm.pop.vals || {}).map((k) => rel(gt.pop.vals[k], gm.pop.vals[k])),
);
out.g.centre_delta_deg = {
  lat: Math.abs(gt.centre.lat - gm.centre.lat),
  lon: Math.abs(gt.centre.lon - gm.centre.lon),
};
if (out.g.worst_relative_difference > 0.01)
  bad.push(
    `g: 同一像素 tap 与 click 差 ${(100 * out.g.worst_relative_difference).toFixed(2)}%（${JSON.stringify(gt.pop.vals)} vs ${JSON.stringify(gm.pop.vals)}）`,
  );
if (out.g.pop.length === 0) bad.push('g: 手机视口首次点击没有请求瓦片');

if (exceptions.length) bad.push(`异常: ${exceptions.slice(0, 2).join(' | ')}`);

out.verdict = { ok: bad.length === 0, problems: bad };
writeFileSync('click-gate.json', JSON.stringify(out, null, 2), 'utf8');
console.log(JSON.stringify(out.verdict, null, 2));
ws.close();
process.exit(bad.length ? 1 : 0);
