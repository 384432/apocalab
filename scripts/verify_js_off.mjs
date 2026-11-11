/**
 * The JS-off gate (plan §4.1): with scripting disabled, the default state's
 * numbers must still be in the HTML, the control bar must be gone, and the
 * pointer to the static table must be visible.
 *
 * Usage: node scripts/verify_js_off.mjs "http://127.0.0.1:4322/?city=new-york&yield=100"
 */
const URL_ = process.argv[2] || 'http://127.0.0.1:4322/?city=new-york&yield=100';

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
await send('Emulation.setScriptExecutionDisabled', { value: true });
await send('Page.navigate', { url: URL_ });
await new Promise((r) => setTimeout(r, 900));

const expr = `(() => {
  const g = (s) => { const n = document.querySelector(s); return n ? getComputedStyle(n).display : 'MISSING'; };
  return {
    js_off: true,
    panel_class: document.getElementById('result').className,
    head: document.querySelector('[data-bind="city"]').textContent + ' · ' +
          document.querySelector('[data-bind="yield"]').textContent + ' · ' +
          document.querySelector('[data-bind="burst"]').textContent,
    coords: document.querySelector('[data-bind="coords"]').textContent,
    values: [...document.querySelectorAll('[data-cell="km"]')].map(n => n.textContent.trim()),
    srcs: [...document.querySelectorAll('[data-cell="src"]')].map(n => n.textContent.trim()),
    controls_display: g('#controls'),
    fallback_display: g('.fallback'),
    fallback_text: document.querySelector('.fallback').textContent.replace(/\\s+/g, ' ').trim(),
  };
})()`;

const r = await send('Runtime.evaluate', { expression: expr, returnByValue: true });
console.log(JSON.stringify(r.result.result.value, null, 2));
await send('Emulation.setScriptExecutionDisabled', { value: false });
ws.close();
