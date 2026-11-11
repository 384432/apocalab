/**
 * Measures the cost of switching yield on the homepage, in a real browser.
 *
 * The gate in plan §4.1 is "切当量 <300 ms". Rather than assert it by
 * construction, this drives headless Chromium over CDP: it loads the built page,
 * dispatches a real `change` event on a yield radio (the same event the control
 * bar fires), and times (a) the synchronous DOM work and (b) the time until the
 * next frame is committed, which is when the new numbers are on screen.
 *
 * Usage:
 *   node scripts/measure_switch.mjs [url] [runs]
 */
const URL_ = process.argv[2] || 'http://127.0.0.1:4322/';
const RUNS = Number(process.argv[3] || 20);

const res = await fetch('http://127.0.0.1:9333/json/list');
const targets = await res.json();
const page = targets.find((t) => t.type === 'page');
if (!page) throw new Error('no page target');

const ws = new WebSocket(page.webSocketDebuggerUrl);
let id = 0;
const pending = new Map();

ws.addEventListener('message', (ev) => {
  const msg = JSON.parse(ev.data);
  if (msg.id && pending.has(msg.id)) {
    pending.get(msg.id)(msg);
    pending.delete(msg.id);
  }
});

function send(method, params = {}) {
  return new Promise((resolve) => {
    const mid = ++id;
    pending.set(mid, resolve);
    ws.send(JSON.stringify({ id: mid, method, params }));
  });
}

await new Promise((r) => ws.addEventListener('open', r));

await send('Page.enable');
await send('Runtime.enable');
await send('Page.navigate', { url: URL_ });
// wait for load
await new Promise((r) => setTimeout(r, 1200));

const expr = `(async () => {
  const form = document.getElementById('controls');
  if (!form) return { error: 'no controls (script did not run)' };
  const radios = [...form.querySelectorAll('input[name="yield"]')];
  const read = () => [...document.querySelectorAll('[data-cell="km"]')].map(n => n.textContent.trim()).join(',');
  const before = read();
  const sync = [];
  const frame = [];
  for (let i = 0; i < ${RUNS}; i++) {
    const target = radios.find(r => !r.checked);
    const t0 = performance.now();
    target.checked = true;
    form.dispatchEvent(new Event('change', { bubbles: true }));
    const t1 = performance.now();
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
    const t2 = performance.now();
    sync.push(t1 - t0);
    frame.push(t2 - t0);
  }
  const p = (a) => { const s = [...a].sort((x,y)=>x-y); return {
    min: +s[0].toFixed(2), med: +s[(s.length/2)|0].toFixed(2), max: +s[s.length-1].toFixed(2) }; };
  return {
    runs: ${RUNS},
    sync_ms: p(sync),
    to_next_frame_ms: p(frame),
    sample_before: before,
    sample_after: read(),
    url_after: location.search,
    node_count: document.querySelectorAll('[data-cell]').length,
  };
})()`;

const out = await send('Runtime.evaluate', {
  expression: expr,
  awaitPromise: true,
  returnByValue: true,
});

console.log(JSON.stringify(out.result.result.value ?? out.result, null, 2));
ws.close();
