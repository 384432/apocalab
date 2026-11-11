/**
 * Layout sanity check without eyes on the page.
 *
 * I cannot see screenshots, so this measures what a screenshot would show:
 * horizontal overflow at phone and desktop widths, whether the rings actually
 * occupy space, and whether any panel cell collapsed to zero height.
 *
 * Usage: node scripts/verify_layout.mjs [base-url]
 */
const BASE = process.argv[2] || 'http://127.0.0.1:4322';

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

const probe = `(() => {
  const doc = document.documentElement;
  const over = doc.scrollWidth - doc.clientWidth;
  const svg = document.querySelector('.rings svg');
  const box = svg ? svg.getBoundingClientRect() : null;
  const rows = [...document.querySelectorAll('.ro')].map(w => ({
    id: w.getAttribute('data-row'),
    h: Math.round(w.getBoundingClientRect().height),
  }));
  const cells = [...document.querySelectorAll('[data-cell="km"]')].map(n => ({
    v: n.textContent.trim(),
    w: Math.round(n.getBoundingClientRect().width),
  }));
  const wide = [...document.querySelectorAll('body *')]
    .filter(el => el.getBoundingClientRect().right > doc.clientWidth + 1)
    .slice(0, 5)
    .map(el => el.tagName + '.' + (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className));
  return {
    viewport: doc.clientWidth,
    horizontal_overflow_px: over,
    svg_box: box ? { w: Math.round(box.width), h: Math.round(box.height) } : null,
    row_heights: rows,
    km_cell_widths: cells,
    overflowing_elements: wide,
    body_scroll_height: doc.scrollHeight,
  };
})()`;

const out = {};
for (const [label, w, h, mobile] of [
  ['phone', 390, 844, true],
  ['desktop', 1280, 900, false],
]) {
  await send('Emulation.setDeviceMetricsOverride', {
    width: w, height: h, deviceScaleFactor: mobile ? 3 : 1, mobile,
  });
  await send('Page.navigate', { url: BASE + '/' });
  await new Promise((r) => setTimeout(r, 900));
  const r = await send('Runtime.evaluate', { expression: probe, returnByValue: true });
  out[label] = r.result.result.value;
}
await send('Emulation.clearDeviceMetricsOverride');
console.log(JSON.stringify(out, null, 2));
ws.close();
