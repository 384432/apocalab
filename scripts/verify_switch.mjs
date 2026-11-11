/**
 * Verifies that a yield change actually changes the rendered numbers (the
 * timing script alone cannot tell a no-op from a fast update), and reports the
 * values before/after so the numbers can be eyeballed against effects.json.
 *
 * Usage: node scripts/verify_switch.mjs [url]
 */
const URL_ = process.argv[2] || 'http://127.0.0.1:4322/';

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

async function evaluate(expression, awaitPromise = false) {
  const r = await send('Runtime.evaluate', { expression, awaitPromise, returnByValue: true });
  return r.result?.result?.value ?? r.result;
}

await send('Page.navigate', { url: URL_ });
await new Promise((r) => setTimeout(r, 1000));

const snapshot = `(() => {
  const rows = [...document.querySelectorAll('.ro')].map(w => ({
    id: w.getAttribute('data-row'),
    km: w.querySelector('[data-cell="km"]').textContent.trim(),
    hob: w.querySelector('[data-cell="hob"]').textContent.trim(),
    src: w.querySelector('[data-cell="src"]').textContent.trim(),
    tags: [...w.querySelectorAll('[data-cell="tags"] .tag')].map(t => t.textContent.trim()),
    absent: w.getAttribute('data-absent'),
  }));
  return {
    head: document.querySelector('[data-bind="city"]').textContent + ' · ' +
          document.querySelector('[data-bind="yield"]').textContent + ' · ' +
          document.querySelector('[data-bind="burst"]').textContent,
    coords: document.querySelector('[data-bind="coords"]').textContent,
    scalebar: document.querySelector('[data-bind="sbt"]').textContent,
    ring_r: [...document.querySelectorAll('[data-ring]')].map(c => c.getAttribute('data-ring') + '=' + c.getAttribute('r')),
    rings_transform: document.getElementById('rings').getAttribute('transform'),
    rows,
  };
})()`;

function setState(slug, y, b) {
  return `(() => {
    const form = document.getElementById('controls');
    const sel = document.getElementById('city-select');
    sel.value = ${JSON.stringify(slug)};
    form.querySelector('input[name="yield"][value="${y}"]').checked = true;
    form.querySelector('input[name="burst"][value="${b}"]').checked = true;
    const t0 = performance.now();
    form.dispatchEvent(new Event('change', { bubbles: true }));
    const t1 = performance.now();
    return { ms: +(t1 - t0).toFixed(2), url: location.search };
  })()`;
}

const out = { default_state: await evaluate(snapshot) };

for (const [slug, y, b] of [
  ['new-york', 1000, 'air'],
  ['tokyo', 15, 'air'],
  ['tokyo', 1000, 'ground'],
  ['new-york', 100, 'air'],
]) {
  const r = await evaluate(setState(slug, y, b));
  const s = await evaluate(snapshot);
  out[`${slug}/${y}/${b}`] = { ms: r.ms, url: r.url, ...s };
}

console.log(JSON.stringify(out, null, 2));
ws.close();
