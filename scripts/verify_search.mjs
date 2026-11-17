/**
 * Any-city search gate: the six acceptance cases in plan §14.5, plus the two
 * things §15 writes down as hard constraints (nothing fetched before typing, and
 * a failed shard leaves the default state alone).
 *
 * Everything is asserted against the live DOM through CDP — no screenshots, no
 * eyeballing. The expected coordinates are read out of the *shipped* shard, so
 * case b cannot pass against a page that invented its own numbers.
 *
 * Usage: node scripts/verify_search.mjs http://127.0.0.1:4322
 */
import { readFileSync, writeFileSync } from 'node:fs';

const BASE = process.argv[2] || 'http://127.0.0.1:4322';
const HOME = `${BASE}/`;
const MAP = `${BASE}/nuclear-bomb-map/`;

const shard = (key) =>
  JSON.parse(readFileSync(new URL(`../dist/data/cities/${key}.json`, import.meta.url), 'utf8'));

const targets = await (await fetch('http://127.0.0.1:9333/json/list')).json();
const page = targets.find((t) => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
let shardRequests = [];

ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.method === 'Network.requestWillBeSent') {
    const u = m.params.request.url;
    if (u.includes('/data/cities/')) shardRequests.push(u.slice(u.indexOf('/data/cities/')));
  }
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
  const r = await send('Runtime.evaluate', {
    expression,
    returnByValue: true,
    awaitPromise: true,
  });
  if (r.result?.exceptionDetails) return { __error: r.result.exceptionDetails.text };
  return r.result?.result?.value;
}

async function waitFor(expression, timeout = 8000) {
  const t0 = Date.now();
  while (Date.now() - t0 < timeout) {
    if ((await evaluate(expression)) === true) return true;
    await sleep(120);
  }
  return false;
}

/** Type into the box the way a person does: set the value, fire `input`. */
const type = (q) => `(() => {
  const el = document.getElementById('city-search-input');
  el.focus();
  el.value = ${JSON.stringify(q)};
  el.dispatchEvent(new Event('input', { bubbles: true }));
  return true;
})()`;

const PROBE = `(() => {
  const t = (s) => { const n = document.querySelector(s); return n ? n.textContent.trim() : null; };
  const s = window.__apocalabSearch;
  return {
    head: t('#result [data-bind="city"]'),
    coords: t('#result [data-bind="coords"]'),
    rows: [...document.querySelectorAll('#result .ro')].map((r) => ({
      id: r.dataset.row,
      km: r.querySelector('[data-cell="km"]').textContent.trim(),
      hob: r.querySelector('[data-cell="hob"]').textContent.trim(),
      src: r.querySelector('[data-cell="src"]').textContent.trim(),
    })),
    rings: [...document.querySelectorAll('#result #rings circle[data-ring]')].map((c) => ({
      id: c.dataset.ring,
      r: c.getAttribute('r'),
      hidden: c.style.display === 'none',
    })),
    svg: !!document.querySelector('#result svg.rings') || !!document.querySelector('#result figure.rings svg'),
    status: s ? s.status() : null,
    state: s ? s.state() : null,
    count: s ? s.count() : null,
    shown: s ? s.shown() : null,
    fetches: s ? s.fetches() : null,
  };
})()`;

const out = { cases: {} };
const bad = [];

// ---------------------------------------------------------------- boot
shardRequests = [];
await send('Network.setBlockedURLs', { urls: [] });
await send('Page.navigate', { url: HOME });
await waitFor('!!window.__apocalabSearch');
await sleep(400);

const base = await evaluate(PROBE);
out.cases.boot = { head: base.head, coords: base.coords, status: base.status };
if (base.head !== 'New York') bad.push(`boot: 默认状态头不是 New York（${base.head}）`);
if (base.rows.length !== 6) bad.push(`boot: 读数列 ${base.rows.length} 行`);
if (shardRequests.length) bad.push(`boot: 首屏就请求了分片 ${JSON.stringify(shardRequests)}`);
if (base.fetches !== 0) bad.push(`boot: 未输入就 fetch 了 ${base.fetches} 次`);

// ---------------------------------------------------------------- a: Denver
await evaluate(type('Denver'));
await waitFor('window.__apocalabSearch && window.__apocalabSearch.count() > 0');
await sleep(250);
const a = await evaluate(PROBE);
out.cases.a = { head: a.head, coords: a.coords, status: a.status, rings: a.rings.length };
if (!/^Denver\b/.test(a.head || '')) bad.push(`a: 状态区没有变成 Denver（${a.head}）`);
if (a.rings.length !== 6) bad.push(`a: 环数 ${a.rings.length}`);
if (a.rings.some((r) => r.hidden)) bad.push('a: 有环被隐藏');
if (a.head === base.head) bad.push('a: 状态区与默认态相同，没有变化');

// ---------------------------------------------------------------- b: coords
const denverRow = shard('d').find((r) => r[2].toUpperCase().startsWith('DENVER'));
const fmt = (lat, lon) =>
  `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? 'N' : 'S'}, ` +
  `${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? 'E' : 'W'}`;
const wantCoords = fmt(denverRow[3], denverRow[4]);
out.cases.b = { shown: a.coords, expected: wantCoords };
if (a.coords !== wantCoords) bad.push(`b: 坐标 ${a.coords} ≠ 分片值 ${wantCoords}`);

// ---------------------------------------------------------------- c: same six
const same =
  JSON.stringify(a.rows) === JSON.stringify(base.rows) &&
  JSON.stringify(a.rings) === JSON.stringify(base.rings);
out.cases.c = {
  identical_rows: JSON.stringify(a.rows) === JSON.stringify(base.rows),
  identical_rings: JSON.stringify(a.rings) === JSON.stringify(base.rings),
  km: a.rows.map((r) => r.km),
  hob: a.rows.map((r) => r.hob),
};
if (!same) bad.push('c: Denver 的五距离/爆高/出处与 New York 不是逐字相同');
for (const [i, km] of ['9.93', '6.99', '4.02', '3.22', '1.31', '0.21'].entries()) {
  if (!a.rows[i] || !a.rows[i].km.startsWith(km)) {
    bad.push(`c: 第 ${i + 1} 行 km 应为 ${km}，实际 ${a.rows[i]?.km}`);
  }
}
if (!a.rows.every((r) => /p\.\s?\d{2,3}/.test(r.src))) bad.push('c: 有一行缺印刷页码');

// ---------------------------------------------------------------- d: no hit
await evaluate(type('zzzzqqqq'));
await waitFor(`window.__apocalabSearch.state() === 'miss'`);
await sleep(200);
const d = await evaluate(PROBE);
out.cases.d = { status: d.status, head: d.head, coords: d.coords, state: d.state };
if (!/not in the gazetteer/.test(d.status || '')) bad.push(`d: 提示不是 not in the gazetteer（${d.status}）`);
if (d.head !== a.head) bad.push(`d: 零命中把状态区改掉了（${d.head}）`);
if (d.coords !== a.coords) bad.push('d: 零命中把环心改掉了');
if (JSON.stringify(d.rows) !== JSON.stringify(a.rows)) bad.push('d: 零命中把五距离改掉了');

// ---------------------------------------------------------------- e: Springfield
await evaluate(type('Springfield'));
await waitFor(`window.__apocalabSearch.count() > 0`);
await sleep(250);
const e = await evaluate(PROBE);
out.cases.e = {
  count: e.count,
  shown: e.shown,
  head_before_pick: e.head,
  status: e.status,
};
if (e.count !== 10) bad.push(`e: 前缀命中数 ${e.count}，期望 10`);
const want5 = [
  ['Springfield', 'MO'],
  ['Springfield', 'MA'],
  ['Springfield', 'IL'],
  ['Springfield', 'OR'],
  ['Springfield', 'OH'],
];
for (let i = 0; i < 5; i++) {
  const got = (e.shown || [])[i] || [];
  if (got[0] !== want5[i][0] || got[1] !== want5[i][1]) {
    bad.push(`e: 第 ${i + 1} 条 ${JSON.stringify(got)}，期望 ${JSON.stringify(want5[i])}`);
  }
}
// 默认选中人口最大的那条（MO），并且状态区必须带 admin1。
if (e.head !== 'Springfield, MO') bad.push(`e: 默认选中 ${e.head}，期望 Springfield, MO`);

// 点第 3 条 → Springfield, IL
await evaluate(`document.querySelectorAll('#city-search-list button')[2].click()`);
await sleep(200);
const e3 = await evaluate(PROBE);
out.cases.e_pick3 = { head: e3.head, status: e3.status };
if (e3.head !== 'Springfield, IL') bad.push(`e: 点第 3 条后状态区 ${e3.head}，期望 Springfield, IL`);

// ---------------------------------------------------------------- f: Lodz
await evaluate(type('Lodz'));
await waitFor(`window.__apocalabSearch.count() > 0`);
await sleep(250);
const f = await evaluate(PROBE);
const applied = await evaluate('window.__apocalabSearch.applied()');
out.cases.f = { head: f.head, coords: f.coords, status: f.status, applied };
if (!applied || applied.name !== 'Łódź') bad.push(`f: 命中的 name 是 ${applied?.name}，期望 Łódź`);
if (!/^Łódź/.test(f.head || '')) bad.push(`f: 状态区 ${f.head} 不含 Łódź`);
if (!/l\.json$/.test(shardRequests.join(' '))) bad.push(`f: 没有取 l 桶（${shardRequests.join(' ')}）`);
if (f.rows.length !== 6) bad.push('f: 命中 Łódź 后读数列不是 6 行');

// ---------------------------------------------------------------- 匹配语义
// §15 item 2：只做前缀，不做子串。「york 搜不到 New York」是写下来的行为，
// 不是 bug —— 所以这里断言它确实如此，防止以后有人「顺手修好」。
await evaluate(type('york'));
await waitFor(`window.__apocalabSearch.count() > 0`);
await sleep(200);
const york = await evaluate(PROBE);
out.cases.semantics = { york_count: york.count, york_shown: york.shown };
if ((york.shown || []).some((r) => r[0] === 'New York')) {
  bad.push('语义: york 命中了 New York，说明变成了子串匹配');
}
await evaluate(type('ork'));
await sleep(700);
const ork = await evaluate(PROBE);
const orkApplied = await evaluate('window.__apocalabSearch.applied()');
out.cases.semantics.ork_state = ork.state;
out.cases.semantics.ork_shown = ork.shown;
out.cases.semantics.ork_applied = orkApplied && orkApplied.name;
if ((ork.shown || []).some((r) => r[0] === 'York') || (orkApplied && /York/.test(orkApplied.name))) {
  bad.push('语义: ork 命中了 York，说明在比较子串而不是前缀');
}

// ---------------------------------------------------------------- 同桶只取一次
const before = shardRequests.length;
await evaluate(type('Denver'));
await sleep(400);
const after = await evaluate(PROBE);
out.one_fetch_per_bucket = {
  requests: shardRequests.slice(),
  refetch_on_retype: shardRequests.length - before,
  fetches_reported: after.fetches,
};
if (shardRequests.length !== before) bad.push('同桶只取一次：重复输入又发了请求');
const counts = {};
for (const u of shardRequests) counts[u] = (counts[u] || 0) + 1;
if (Object.values(counts).some((n) => n > 1)) bad.push(`同桶取了多次：${JSON.stringify(counts)}`);

// ---------------------------------------------------------------- 分片失败
shardRequests = [];
await send('Network.setBlockedURLs', { urls: ['*/data/cities/*'] });
await send('Page.navigate', { url: HOME });
await waitFor('!!window.__apocalabSearch');
await sleep(300);
await evaluate(type('Osaka'));
await waitFor(`window.__apocalabSearch.state() === 'error'`);
await sleep(300);
const g = await evaluate(PROBE);
out.cases.failure = { status: g.status, head: g.head, rows: g.rows.length, rings: g.rings.length, svg: g.svg };
if (g.state !== 'error') bad.push('失败态没有进入 error');
if (g.head !== 'New York') bad.push(`失败后状态区变成了 ${g.head}，必须保持 New York`);
if (g.rows.length !== 6 || g.rings.length !== 6) bad.push('失败后读数或环数变了');
if (!g.svg) bad.push('失败后原 SVG 不在了');
if (g.rows.some((r) => !r.km || r.km === '—')) bad.push('失败后出现空环/空数');
await send('Network.setBlockedURLs', { urls: [] });

// ---------------------------------------------------------------- 地图页
await send('Page.navigate', { url: MAP });
await waitFor('!!window.__apocalabSearch && !!window.__apocalabMap');
await sleep(400);
await send('Page.navigate', { url: MAP });
await waitFor('!!window.__apocalabSearch');
await sleep(300);
await evaluate(type('Denver'));
await waitFor('window.__apocalabSearch && window.__apocalabSearch.count() > 0');
await sleep(600);
const m = await evaluate(`(() => ({
  place: window.__apocalabMap.place(),
  label: document.querySelector('#bomb-map [data-bind="place"]')?.textContent.trim(),
  coords: document.querySelector('#bomb-map [data-bind="coords"]')?.textContent.trim(),
  rings: window.__apocalabMap.rings(),
  readout: document.querySelectorAll('#map-readout .map-ro').length,
}))()`);
out.cases.map = m;
if (!m.place || m.place.gazetteer !== true) bad.push('map: 搜索命中没有落到地图上');
if (m.place && Math.abs(m.place.lat - denverRow[3]) > 1e-9) bad.push('map: 纬度不是分片值');
if (!/^Denver/.test(m.label || '')) bad.push(`map: 标题仍是 ${m.label}`);
if (m.rings !== 6 || m.readout !== 6) bad.push('map: 环或读数不是 6 行');

out.verdict = { ok: bad.length === 0, problems: bad };
writeFileSync('search-gate.json', JSON.stringify(out, null, 2), 'utf8');
console.log(JSON.stringify(out.verdict, null, 2));
ws.close();
process.exit(bad.length ? 1 : 0);
