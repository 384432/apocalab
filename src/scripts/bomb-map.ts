/**
 * /nuclear-bomb-map/ client.
 *
 * Layering, bottom to top:
 *   1. <canvas id="map-fallback">  Natural Earth 110m outline, drawn immediately
 *   2. <div id="map">              MapLibre + OpenFreeMap tiles, fades in when ready
 *   3. <canvas id="map-rings">     the five radii, drawn by us, never by the map
 *
 * The rings are ours because a basemap that fails must not take the numbers with
 * it. Both basemap paths project through the same Web Mercator convention
 * (512 px tiles, src/lib/mercator.ts), so the rings do not move when the tiles
 * arrive. Rotation and pitch are off in every path: a self-drawn ground circle
 * is only valid while the map is north-up and flat, and this is a 2D product.
 *
 * Nothing here computes a radius. The island carries the km values from
 * src/data/effects.json exactly as /blast-radius/ prints them.
 */
import type { Burst } from '../lib/effects';
import {
  MAX_LAT,
  clamp,
  geodesicRing,
  metersPerPixel,
  niceStep,
  projectWorld,
  worldSize,
  zoomForRadius,
} from '../lib/mercator';

interface Tags {
  t: string;
  c: string;
}

interface Row {
  id: string;
  name: string;
  sub: string;
  km: string;
  ft: string;
  hob: string;
  src: string;
  tags: Tags[];
  r: number | null;
  color: string;
  absent: string | null;
  checked: boolean;
}

interface CityRec {
  slug: string;
  name: string;
  coords: string;
  lat: number;
  lon: number;
}

interface Island {
  default: { city: string; yield: number; burst: Burst };
  yields: number[];
  cities: CityRec[];
  combos: Record<string, Record<string, Row[]>>;
}

interface View {
  lon: number;
  lat: number;
  zoom: number;
}

const SHORT: Record<string, string> = {
  fireball: 'Fireball',
  overpressure_5psi: '5 psi',
  overpressure_1psi: '1 psi',
  thermal_2nd: '2nd° burn',
  thermal_3rd: '3rd° burn',
};

/** Fraction of the shorter side the outermost ring takes up. */
const FIT = 0.4;

const STYLE_URL = 'https://tiles.openfreemap.org/styles/fiord';

function f(n: number): string {
  return Math.round(n).toLocaleString('en-US');
}

function boot(): void {
  const root = document.getElementById('bomb-map');
  const islandEl = document.getElementById('apoca-map-island');
  if (!root || !islandEl) return;

  const D = JSON.parse(islandEl.textContent || '{}') as Island;
  const frame = root.querySelector<HTMLElement>('#map-frame');
  const mapHost = root.querySelector<HTMLElement>('#map');
  const cvRings = root.querySelector<HTMLCanvasElement>('#map-rings');
  const cvBase = root.querySelector<HTMLCanvasElement>('#map-fallback');
  const note = root.querySelector<HTMLElement>('#map-note');
  const readout = root.querySelector<HTMLElement>('#map-readout');
  const form = root.querySelector<HTMLFormElement>('#map-controls');
  if (!frame || !mapHost || !cvRings || !cvBase || !readout || !form) return;

  root.classList.add('js');

  const ctxRings = cvRings.getContext('2d');
  const ctxBase = cvBase.getContext('2d');
  if (!ctxRings || !ctxBase) return;

  // ---------------------------------------------------------------- state
  const valid = {
    city: D.cities.map((c) => c.slug),
    yield: D.yields.map(String),
    burst: ['air', 'ground'],
  };

  function readUrl(): { city: string; y: number; b: Burst } {
    const p = new URLSearchParams(location.search);
    let city = p.get('city') || D.default.city;
    let y = p.get('yield') || p.get('y') || String(D.default.yield);
    let b = p.get('burst') || D.default.burst;
    if (valid.city.indexOf(city) < 0) city = D.default.city;
    if (valid.yield.indexOf(y) < 0) y = String(D.default.yield);
    if (valid.burst.indexOf(b) < 0) b = D.default.burst;
    return { city, y: Number(y), b: b as Burst };
  }

  let state = readUrl();

  function cityOf(slug: string): CityRec {
    return D.cities.find((c) => c.slug === slug) ?? D.cities[0];
  }

  function rowsNow(): Row[] {
    return (D.combos[state.b] && D.combos[state.b][String(state.y)]) || [];
  }

  // ---------------------------------------------------------------- sizing
  let w = 0;
  let h = 0;
  let dpr = 1;

  function resize(): boolean {
    const rect = frame!.getBoundingClientRect();
    const nw = Math.max(1, Math.round(rect.width));
    const nh = Math.max(1, Math.round(rect.height));
    const nd = Math.min(window.devicePixelRatio || 1, 2);
    if (nw === w && nh === h && nd === dpr) return false;
    w = nw;
    h = nh;
    dpr = nd;
    for (const cv of [cvRings!, cvBase!]) {
      cv.width = Math.round(w * dpr);
      cv.height = Math.round(h * dpr);
      cv.style.width = `${w}px`;
      cv.style.height = `${h}px`;
    }
    return true;
  }

  // ---------------------------------------------------------------- projection
  /**
   * The fallback view. Kept in sync with the MapLibre view so the two paths put
   * a ring on the same pixel when the basemap swaps in.
   */
  function viewFor(city: CityRec, rows: Row[]): View {
    const maxR = rows.reduce((m, r) => (r.r !== null && r.r > m ? r.r : m), 0) || 1;
    const target = Math.min(w, h) * FIT;
    const lat = clamp(city.lat, -70, 70);
    return {
      lon: city.lon,
      lat: city.lat,
      zoom: Math.round(zoomForRadius(lat, maxR * 1000, target) * 100) / 100,
    };
  }

  let view: View = viewFor(cityOf(state.city), rowsNow());

  type P = { x: number; y: number };
  type Project = (lon: number, lat: number) => P;

  const projectFallback = (v: View): Project => {
    const size = worldSize(v.zoom);
    const c = projectWorld(v.lon, clamp(v.lat, -MAX_LAT, MAX_LAT), v.zoom);
    const ox = c.x - w / 2;
    const oy = c.y - h / 2;
    return (lon, lat) => {
      // Unwrap longitude so a ring spanning the antimeridian stays contiguous.
      let dl = lon - v.lon;
      if (dl > 180) dl -= 360;
      if (dl < -180) dl += 360;
      const p = projectWorld(v.lon + dl, lat, v.zoom);
      return { x: p.x - ox, y: p.y - oy };
    };
  };

  // ---------------------------------------------------------------- basemap
  let map: {
    project(p: [number, number]): { x: number; y: number };
    jumpTo(o: { center: [number, number]; zoom: number }): void;
    resize(): void;
    on(e: string, cb: (...a: unknown[]) => void): unknown;
    once(e: string, cb: (...a: unknown[]) => void): unknown;
    touchZoomRotate?: { disableRotation(): void };
    keyboard?: { disableRotation(): void };
    isStyleLoaded(): boolean;
    remove(): void;
  } | null = null;

  let tilesLive = false;
  frame.dataset.mode = 'pending';
  frame.dataset.settled = '0';

  function markSettled(): void {
    frame!.dataset.settled = '1';
  }

  function setMode(mode: 'outline' | 'tiles'): void {
    frame!.dataset.mode = mode;
    if (mode === 'tiles') markSettled();
    if (mode === 'outline') {
      // One line, per the brief: the map says what it is doing, once.
      if (note) {
        note.hidden = false;
        note.textContent =
          'Basemap unavailable, so this is the bundled Natural Earth 110m outline. The rings are unaffected — they are drawn from the same distances as the table.';
      }
    } else if (note) {
      note.hidden = true;
    }
  }

  // ---------------------------------------------------------------- drawing
  function clearBase(): void {
    ctxBase!.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctxBase!.clearRect(0, 0, w, h);
  }

  let outline: Array<Array<[number, number]>> | null = null;

  function drawBase(): void {
    if (tilesLive) return;
    clearBase();
    const ctx = ctxBase!;
    const p = projectFallback(view);

    // graticule
    const spanLon = (360 * w) / worldSize(view.zoom);
    const spanLat = spanLon * (h / w);
    const step = niceStep(spanLon);
    const stepLat = niceStep(spanLat);
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(120,140,165,0.14)';
    ctx.beginPath();
    const lonMin = Math.floor((view.lon - spanLon / 2) / step) * step;
    const lonMax = view.lon + spanLon / 2;
    for (let lon = lonMin; lon <= lonMax; lon += step) {
      const a = p(lon, 80);
      const b = p(lon, -80);
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
    }
    const latMax = Math.min(84, view.lat + spanLat / 2);
    const latMin = Math.max(-84, view.lat - spanLat / 2);
    for (let lat = Math.floor(latMin / stepLat) * stepLat; lat <= latMax; lat += stepLat) {
      const a = p(view.lon - spanLon, lat);
      const b = p(view.lon + spanLon, lat);
      ctx.moveTo(a.x, a.y);
      ctx.lineTo(b.x, b.y);
    }
    ctx.stroke();

    // land
    if (outline) {
      ctx.beginPath();
      for (const ring of outline) {
        for (let i = 0; i < ring.length; i += 1) {
          const q = p(ring[i][0], ring[i][1]);
          if (i === 0) ctx.moveTo(q.x, q.y);
          else ctx.lineTo(q.x, q.y);
        }
        ctx.closePath();
      }
      ctx.fillStyle = 'rgba(38,46,56,0.92)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(122,146,174,0.55)';
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // scale bar, bottom-left
    const mpp = metersPerPixel(view.lat, view.zoom);
    const want = mpp * 96;
    const exp = Math.floor(Math.log10(want));
    const base = Math.pow(10, exp);
    const mul = want / base < 1.5 ? 1 : want / base < 3.5 ? 2 : want / base < 7.5 ? 5 : 10;
    const km = (mul * base) / 1000;
    const barPx = ((mul * base) / mpp) * 1;
    if (barPx > 24 && barPx < w * 0.6) {
      const y = h - 26;
      const x0 = 18;
      ctx.strokeStyle = 'rgba(233,238,244,0.75)';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x0, y);
      ctx.lineTo(x0 + barPx, y);
      ctx.moveTo(x0, y - 4);
      ctx.lineTo(x0, y + 4);
      ctx.moveTo(x0 + barPx, y - 4);
      ctx.lineTo(x0 + barPx, y + 4);
      ctx.stroke();
      ctx.fillStyle = 'rgba(233,238,244,0.85)';
      ctx.font = '500 11px ui-monospace, SFMono-Regular, Menlo, monospace';
      ctx.textAlign = 'left';
      ctx.textBaseline = 'bottom';
      ctx.fillText(km >= 1 ? `${f(km)} km` : `${f(km * 1000)} m`, x0, y - 6);
    }
  }

  function project(): Project {
    if (tilesLive && map) {
      return (lon, lat) => {
        const q = map!.project([lon, lat]);
        return { x: q.x, y: q.y };
      };
    }
    return projectFallback(view);
  }

  function chip(
    ctx: CanvasRenderingContext2D,
    x: number,
    y: number,
    text: string,
    color: string,
    taken: number[],
  ): void {
    ctx.font = '600 11.5px ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif';
    const tw = ctx.measureText(text).width;
    const pw = tw + 14;
    const ph = 20;
    let py = y - ph / 2;
    // Nudge upward until this chip stops overlapping one already placed.
    let guard = 0;
    while (guard < 12 && taken.some((t) => Math.abs(t - py) < ph + 1)) {
      py -= ph + 2;
      guard += 1;
    }
    taken.push(py);

    const px = clamp(x - pw / 2, 4, w - pw - 4);
    ctx.beginPath();
    const r = 5;
    ctx.moveTo(px + r, py);
    ctx.arcTo(px + pw, py, px + pw, py + ph, r);
    ctx.arcTo(px + pw, py + ph, px, py + ph, r);
    ctx.arcTo(px, py + ph, px, py, r);
    ctx.arcTo(px, py, px + pw, py, r);
    ctx.closePath();
    ctx.fillStyle = 'rgba(9,11,14,0.82)';
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
    ctx.fillStyle = '#e9eef4';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, px + pw / 2, py + ph / 2 + 0.5);
  }

  function drawRings(): void {
    ctxRings!.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctxRings!.clearRect(0, 0, w, h);

    const city = cityOf(state.city);
    const p = project();
    const rows = rowsNow().filter((r) => r.r !== null) as Array<Row & { r: number }>;
    // Outer first so the small rings sit on top.
    rows.sort((a, b) => b.r - a.r);

    const taken: number[] = [];

    for (const row of rows) {
      const pts = geodesicRing(city.lon, city.lat, row.r * 1000, 96);
      ctxRings!.beginPath();
      for (let i = 0; i < pts.length; i += 1) {
        const q = p(pts[i][0], pts[i][1]);
        if (i === 0) ctxRings!.moveTo(q.x, q.y);
        else ctxRings!.lineTo(q.x, q.y);
      }
      ctxRings!.closePath();
      // Two passes: a dark halo so the line survives a light basemap, then the colour.
      ctxRings!.strokeStyle = 'rgba(0,0,0,0.55)';
      ctxRings!.lineWidth = 4.5;
      ctxRings!.stroke();
      ctxRings!.strokeStyle = row.color;
      ctxRings!.lineWidth = 2;
      ctxRings!.stroke();
    }

    // centre
    const c = p(city.lon, city.lat);
    ctxRings!.beginPath();
    ctxRings!.arc(c.x, c.y, 5, 0, Math.PI * 2);
    ctxRings!.fillStyle = '#e9eef4';
    ctxRings!.fill();
    ctxRings!.beginPath();
    ctxRings!.arc(c.x, c.y, 11, 0, Math.PI * 2);
    ctxRings!.strokeStyle = 'rgba(233,238,244,0.35)';
    ctxRings!.lineWidth = 1;
    ctxRings!.stroke();

    // chips at the top of each ring, smallest last so it wins the overlap fight
    for (const row of rows.slice().reverse()) {
      const pts = geodesicRing(city.lon, city.lat, row.r * 1000, 96);
      const topPt = p(pts[0][0], pts[0][1]); // theta = 0 is due north
      if (topPt.y < 26 || topPt.y > h - 8) continue;
      chip(ctxRings!, c.x, topPt.y, `${SHORT[row.id] ?? row.name} · ${row.km} km`, row.color, taken);
    }
  }

  function refreshBase(): void {
    drawBase();
  }

  function redraw(): void {
    drawRings();
  }

  // ---------------------------------------------------------------- readout
  function renderReadout(): void {
    if (!readout) return;
    readout.textContent = '';
    for (const row of rowsNow()) {
      const li = document.createElement('li');
      li.className = 'map-ro';
      if (row.absent) li.dataset.absent = '1';

      const dot = document.createElement('span');
      dot.className = 'dot';
      dot.style.background = row.color;
      li.appendChild(dot);

      const name = document.createElement('span');
      name.className = 'nm';
      name.textContent = row.name;
      li.appendChild(name);

      const val = document.createElement('span');
      val.className = 'v';
      val.textContent = row.absent ? '—' : row.km;
      if (!row.absent) {
        const u = document.createElement('span');
        u.className = 'u';
        u.textContent = 'km';
        val.appendChild(u);
      }
      li.appendChild(val);

      const src = document.createElement('span');
      src.className = 'src';
      src.textContent = row.absent ? 'contact burst: not reported' : row.src;
      li.appendChild(src);

      readout.appendChild(li);
    }
  }

  // ---------------------------------------------------------------- controls
  function syncControls(): void {
    const sel = form!.querySelector<HTMLSelectElement>('select[name="city"]');
    if (sel) sel.value = state.city;
    for (const input of Array.from(form!.querySelectorAll<HTMLInputElement>('input'))) {
      input.checked = input.value === (input.name === 'yield' ? String(state.y) : state.b);
    }
  }

  function apply(next: { city?: string; y?: number; b?: Burst }, pushUrl = true): void {
    state = {
      city: next.city ?? state.city,
      y: next.y ?? state.y,
      b: next.b ?? state.b,
    };
    const city = cityOf(state.city);
    view = viewFor(city, rowsNow());

    if (map && tilesLive) {
      map.jumpTo({ center: [city.lon, city.lat], zoom: view.zoom });
    }
    refreshBase();
    redraw();
    renderReadout();
    syncControls();

    const label = root!.querySelector<HTMLElement>('[data-bind="place"]');
    if (label) label.textContent = city.name;
    const sub = root!.querySelector<HTMLElement>('[data-bind="setting"]');
    if (sub) {
      sub.textContent = `${state.y.toLocaleString('en-US')} kt · ${
        state.b === 'air' ? 'air burst' : 'contact burst'
      }`;
    }

    if (pushUrl) {
      const q = new URLSearchParams();
      q.set('city', state.city);
      q.set('yield', String(state.y));
      q.set('burst', state.b);
      history.replaceState(null, '', `${location.pathname}?${q.toString()}`);
    }
  }

  form.addEventListener('change', () => {
    const sel = form.querySelector<HTMLSelectElement>('select[name="city"]');
    const y = form.querySelector<HTMLInputElement>('input[name="yield"]:checked');
    const b = form.querySelector<HTMLInputElement>('input[name="burst"]:checked');
    apply({
      city: sel ? sel.value : undefined,
      y: y ? Number(y.value) : undefined,
      b: b ? (b.value as Burst) : undefined,
    });
  });

  // ---------------------------------------------------------------- outline
  function loadOutline(): void {
    fetch('/ne_110m_land.geojson', { credentials: 'omit' })
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((geo: { features: Array<{ geometry: { coordinates: number[][][] } }> }) => {
        const rings: Array<Array<[number, number]>> = [];
        for (const feat of geo.features) {
          for (const ring of feat.geometry.coordinates) {
            const pts: Array<[number, number]> = [];
            for (const pair of ring) pts.push([pair[0], pair[1]]);
            rings.push(pts);
          }
        }
        outline = rings;
        if (!tilesLive) drawBase();
      })
      .catch(() => {
        // Rings still draw; only the coastline is missing.
      });
  }

  // ---------------------------------------------------------------- MapLibre
  async function upgrade(): Promise<void> {
    if (navigator.onLine === false) {
      setMode('outline');
      markSettled();
      return;
    }
    let maplibregl: any;
    try {
      const mod: any = await import('maplibre-gl');
      maplibregl = mod.default ?? mod;
      // MapLibre's stylesheet is deliberately not imported: 70 kB of control,
      // popup and attribution chrome this page never renders, and Astro would
      // put it on the critical path. The four rules the canvas needs are
      // mirrored in src/styles/global.css.
    } catch {
      setMode('outline');
      markSettled();
      return;
    }

    const city = cityOf(state.city);
    let settled = false;

    const fail = (): void => {
      if (settled) return;
      settled = true;
      setMode('outline');
      markSettled();
    };

    try {
      map = new maplibregl.Map({
        container: mapHost,
        style: STYLE_URL,
        center: [city.lon, city.lat],
        zoom: view.zoom,
        attributionControl: false,
        // A self-drawn ground circle is only valid north-up and flat.
        dragRotate: false,
        touchPitch: false,
        pitchWithRotate: false,
        maxPitch: 0,
        fadeDuration: 120,
      });
    } catch {
      setMode('outline');
      markSettled();
      return;
    }

    // Belt and braces: these handlers exist in v5 but are not covered by the
    // constructor flags (keyboard rotation, pinch-rotate).
    map.touchZoomRotate?.disableRotation();
    map.keyboard?.disableRotation();

    const watchdog = window.setTimeout(fail, 7000);

    map.on('error', () => {
      // A failed tile or glyph request after the style is in place is noise —
      // MapLibre emits those for single 404s and the map still draws. Only a
      // failure to get the style itself at all is fatal; anything else is left
      // to the watchdog.
      if (settled || tilesLive) return;
      if (!map || !map.isStyleLoaded()) fail();
    });

    map.on('load', () => {
      if (settled) return;
      settled = true;
      window.clearTimeout(watchdog);
      tilesLive = true;
      setMode('tiles');
      mapHost!.style.opacity = '1';
      cvRings!.style.opacity = '1';
      redraw();
    });

    // Panning and zooming keep the rings glued to the ground.
    map.on('move', () => {
      if (tilesLive) redraw();
    });
    map.on('resize', () => {
      if (tilesLive) redraw();
    });
  }

  // ---------------------------------------------------------------- boot
  resize();
  setMode('outline');
  refreshBase();
  redraw();
  renderReadout();
  syncControls();
  apply({}, false);
  loadOutline();
  void upgrade();

  let raf = 0;
  const ro = new ResizeObserver(() => {
    if (raf) return;
    raf = requestAnimationFrame(() => {
      raf = 0;
      if (resize()) {
        if (map) map.resize();
        refreshBase();
        redraw();
      }
    });
  });
  ro.observe(frame);

  // Test hook: the build gate reads these instead of eyeballing a screenshot.
  function opaquePixels(cv: HTMLCanvasElement): number {
    const c = cv.getContext('2d');
    if (!c || !cv.width || !cv.height) return 0;
    const d = c.getImageData(0, 0, cv.width, cv.height).data;
    let n = 0;
    for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n += 1;
    return n;
  }

  (window as unknown as Record<string, unknown>).__apocalabMap = {
    mode: (): string => frame!.dataset.mode || 'pending',
    settled: (): boolean => frame!.dataset.settled === '1',
    rings: (): number => rowsNow().filter((r) => r.r !== null).length,
    state: (): { city: string; y: number; b: string } => state,
    zoom: (): number => view.zoom,
    /** Non-transparent pixels, so "the rings were drawn" is measurable. */
    pixels: (): { rings: number; base: number } => ({
      rings: opaquePixels(cvRings!),
      base: opaquePixels(cvBase!),
    }),
    canvas: (): { w: number; h: number; dpr: number } => ({ w, h, dpr }),
  };
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
  boot();
}
