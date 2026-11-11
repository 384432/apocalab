/**
 * Loads a shared URL directly (no interaction at all) and reports what the page
 * renders, including whether the hidden rings are really hidden.
 *
 * This is the "分享一下链接能还原状态" test: it must pass on a cold load, not only
 * after clicking.
 *
 * Usage: node scripts/verify_share_url.mjs "http://127.0.0.1:4322/?city=tokyo&yield=15&burst=ground"
 */
const URL_ = process.argv[2];
if (!URL_) throw new Error('pass a url');

const targets = await (await fetch('http://127.0.0.1:9333/json/list')).json();
const page = targets.find((t) => t.type === 'page');
const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();
ws.addEventListener('message', (ev) => {
  const m = JSON.parse(ev.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
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
await send('Page.navigate', { url: URL_ });
await new Promise((r) => setTimeout(r, 1000));

const expr = `(() => {
  const rows = [...document.querySelectorAll('.ro')].map(w => ({
    id: w.getAttribute('data-row'),
    km: w.querySelector('[data-cell="km"]').textContent.trim(),
    absent: w.getAttribute('data-absent'),
    ring_display: (w.querySelector('[data-cell="km"]'), (document.querySelector('[data-ring="'+w.getAttribute('data-row')+'"]')||{}).style?.display || '')
  }));
  return {
    url: location.search,
    head: document.querySelector('[data-bind="city"]').textContent + ' · ' +
          document.querySelector('[data-bind="yield"]').textContent + ' · ' +
          document.querySelector('[data-bind="burst"]').textContent,
    coords: document.querySelector('[data-bind="coords"]').textContent,
    city_select: document.getElementById('city-select') ? document.getElementById('city-select').value : null,
    yield_checked: document.querySelector('input[name="yield"]:checked')?.value ?? null,
    burst_checked: document.querySelector('input[name="burst"]:checked')?.value ?? null,
    fallback_hidden: getComputedStyle(document.querySelector('.fallback')).display === 'none',
    controls_shown: getComputedStyle(document.getElementById('controls')).display,
    scalebar: document.querySelector('[data-bind="sbt"]').textContent,
    rows,
  };
})()`;

const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
console.log(JSON.stringify(r.result.result.value, null, 2));
ws.close();
