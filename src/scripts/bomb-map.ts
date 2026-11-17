/**
 * /nuclear-bomb-map/ client.
 *
 * Layering, bottom to top:
 *   1. <canvas id="map-fallback">  Natural Earth 110m outline, drawn immediately
 *   2. <div id="map">              MapLibre + OpenFreeMap tiles, fades in when ready
 *   3. <canvas id="map-rings">     the six radii, drawn by us, never by the map
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
  ANCHOR_KT,
  PRESETS,
  THERMAL_CONTACT,
  THERMAL_OFF_CHART,
  fmtKt,
  isTabulated,
  ktOf,
  optionForKt,
  presetById,
  radiiOf,
  scaledLine,
  tabulatedLine,
  thermalOf,
} from '../lib/weapons';
import {
  MAX_LAT,
  clamp,
  geodesicRing,
  metersPerPixel,
  niceStep,
  projectWorld,
  unprojectWorld,
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
  reason: string;
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
  pop?: Record<string, Record<string, number>>;
  popGrid?: PopGrid;
}

interface PopGrid {
  cellDeg: number;
  cellsPerTile: number;
  tileDeg: number;
  floor: number;
  ratio: number;
}

/** radius (3 dp) -> people inside it */
type PopVals = Record<string, number>;

/**
 * Where a population column comes from, in four states that are never mixed:
 *
 *   tabulated   the 20 preset cities, from the WorldPop API at 100 m
 *   snapped     a click within 5 km of one of them — same table, so the figure
 *               is the tabulated one to the digit, and the label says so
 *   tiles       a click anywhere else, summed in the browser from 1 km tiles
 *   unavailable tiles did not arrive; say so, never print 0 for "unknown"
 */
type PopState =
  | { kind: 'idle' }
  | { kind: 'loading' }
  | { kind: 'tabulated'; city: string; snapped: boolean; vals: PopVals }
  | { kind: 'tiles'; vals: PopVals }
  | { kind: 'unavailable' }
  /** a named city at a yield the table does not carry: say so, do not guess */
  | { kind: 'untabulated'; kt: number };

/** A click this close to a tabulated city is the city: same figure, no drift. */
const SNAP_KM = 5;

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

  /**
   * ?w=<kt> is the share parameter. ?yield= and ?y= are the spellings this page
   * minted before the presets existed and are still read, so an old link keeps
   * working. The centre is either ?city=<slug> or ?lat=&lon= — a point, which is
   * the only way to rebuild a clicked state.
   */
  function readUrl(): {
    city: string;
    preset: string;
    b: Burst;
    point: { lat: number; lon: number } | null;
  } {
    const p = new URLSearchParams(location.search);
    const rawCity = p.get('city') || D.default.city;
    const rawB = p.get('b') || p.get('burst') || D.default.burst;
    const rawW = p.get('w') || p.get('yield') || p.get('y');
    const kt = rawW === null ? D.default.yield : Number(rawW);
    const byKt = Number.isFinite(kt) ? optionForKt(kt) : null;
    const preset =
      byKt ?? (valid.yield.indexOf(String(kt)) >= 0 ? `y${kt}` : null) ?? `y${D.default.yield}`;
    // A missing parameter is not zero: Number(null) and Number('') both return
    // 0, which would turn every ordinary page load into a point at 0°N 0°E and
    // send the rings into the Gulf of Guinea. Presence is tested first, and a
    // genuine ?lat=0&lon=0 is still a point.
    const num = (raw: string | null): number => {
      if (raw === null || raw.trim() === '') return NaN;
      const n = Number(raw);
      return Number.isFinite(n) ? n : NaN;
    };
    const lat = num(p.get('lat'));
    const lon = num(p.get('lon'));
    const point =
      !Number.isNaN(lat) && !Number.isNaN(lon) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180
        ? { lat, lon }
        : null;
    return {
      city: valid.city.indexOf(rawCity) >= 0 ? rawCity : D.default.city,
      preset,
      b: (valid.burst.indexOf(rawB) >= 0 ? rawB : D.default.burst) as Burst,
      point,
    };
  }

  const open = readUrl();
  let state = { city: open.city, preset: open.preset, b: open.b };

  /** The yield behind the current selection: a preset id or y<kt>. */
  function ktNow(): number {
    return ktOf(state.preset);
  }

  /**
   * A place picked from the gazetteer. It has no slug and no page, so it is not
   * part of `state`: it only moves the ring centre and the labels. Dropped the
   * moment the city picker is used, which is the only way back to the presets.
   */
  let gz: (CityRec & { head: string }) | null = null;

  /**
   * A point picked by clicking the map, or restored from ?lat=&lon=. It is not
   * in `state`: a click does not touch the URL. Dropped the moment the city
   * picker or the search box is used, which is the only way back to the presets.
   */
  let clicked: { lat: number; lon: number } | null = open.point;

  let pop: PopState = { kind: 'idle' };
  let popToken = 0;

  function cityOf(slug: string): CityRec {
    return D.cities.find((c) => c.slug === slug) ?? D.cities[0];
  }

  /** "40.7143° N, 74.0060° W" — the same shape the server prints for a city. */
  function latLonText(lat: number, lon: number): string {
    const ns = `${Math.abs(lat).toFixed(4)}° ${lat >= 0 ? 'N' : 'S'}`;
    const ew = `${Math.abs(lon).toFixed(4)}° ${lon >= 0 ? 'E' : 'W'}`;
    return `${ns}, ${ew}`;
  }

  interface Centre {
    lat: number;
    lon: number;
    name: string;
    coords: string;
  }

  /** Where the rings are drawn from: a click wins, then the search pick, then the picker. */
  function centre(): Centre {
    if (clicked) {
      return {
        lat: clicked.lat,
        lon: clicked.lon,
        name: 'Clicked point',
        coords: latLonText(clicked.lat, clicked.lon),
      };
    }
    const c = place();
    return { lat: c.lat, lon: c.lon, name: c.name, coords: c.coords };
  }

  /** Where the rings are drawn from: the gazetteer pick wins over the picker. */
  function place(): CityRec {
    return gz ?? cityOf(state.city);
  }

  /**
   * A yield that is printed in the manual reads its rows straight out of the
   * island's combos table. Every other yield is assembled here from the same
   * six-effect order, with the provenance that belongs to each row: the
   * fireball keeps its printed equation, the three overpressure rings say they
   * are cube-root scaled, and the thermal rings say which column of Fig. 7.42
   * they came from.
   *
   * The order comes from the template rows, which the island built from
   * EFFECT_ROWS. It is deliberately not typed a second time here: the weapon
   * radii are positional arrays, so a hand-kept copy of this list is a silent
   * misalignment waiting to happen. (Importing EFFECT_ROWS would drag all of
   * effects.json into the client bundle for a six-element list.)
   */
  function scaledRows(burst: Burst, kt: number): Row[] {
    const tpl =
      (D.combos[burst] && D.combos[burst][String(ANCHOR_KT)]) ||
      D.combos.air[String(ANCHOR_KT)] ||
      [];
    const radii = radiiOf(kt);
    if (!radii) return tpl;
    const order = tpl.map((r) => r.id);
    return tpl.map((row) => {
      const i = order.indexOf(row.id);
      const r = i >= 0 ? radii[burst][i] : null;
      const out: Row = { ...row, tags: [], ft: '', hob: '' };
      if (r === null || r === undefined) {
        out.r = null;
        out.km = '—';
        out.absent = 'no thermal radius';
        out.reason = burst === 'ground' ? THERMAL_CONTACT : THERMAL_OFF_CHART;
        out.src = '';
        return out;
      }
      out.r = r;
      out.km = r.toFixed(2);
      out.absent = null;
      out.reason = '';
      out.src =
        row.id === 'fireball'
          ? `Ch. 2 · Eq. ${burst === 'air' ? '(2.127.1)' : '(2.127.2)'} · p. ${burst === 'air' ? 70 : 71}`
          : row.id.indexOf('thermal') === 0
            ? 'Ch. 7 · Fig. 7.42 · p. 291'
            : 'Ch. 3 · Eq. (3.61.2) · p. 101';
      return out;
    });
  }

  function rowsNow(): Row[] {
    const kt = ktNow();
    const combo = D.combos[state.b] && D.combos[state.b][String(kt)];
    return combo || scaledRows(state.b, kt);
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
  function viewFor(at: { lat: number; lon: number }, rows: Row[]): View {
    const maxR = rows.reduce((m, r) => (r.r !== null && r.r > m ? r.r : m), 0) || 1;
    const target = Math.min(w, h) * FIT;
    const lat = clamp(at.lat, -70, 70);
    return {
      lon: at.lon,
      lat: at.lat,
      zoom: Math.round(zoomForRadius(lat, maxR * 1000, target) * 100) / 100,
    };
  }

  // A restored ?lat=&lon= must open on its own point, or the rings land outside
  // the frame while the camera sits on the default city.
  let view: View = viewFor(centre(), rowsNow());

  /**
   * The zoom is a function of the frame size, so it has to be re-derived
   * whenever the frame changes — including the first time it has any size at
   * all. At module scope the frame is not laid out yet, which yields a zoom of
   * 1 and rings a pixel wide. The centre is left alone: panning and a picked
   * point both survive a resize, only the scale is fitted again.
   */
  function refit(): void {
    view = viewFor({ lat: view.lat, lon: view.lon }, rowsNow());
    if (map && tilesLive) map.jumpTo({ zoom: view.zoom });
  }

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
    unproject(p: [number, number]): { lat: number; lng: number };
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

    const city = centre();
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
  function renderPopSource(): void {
    const el = root!.querySelector<HTMLElement>('#map-popsrc');
    if (!el) return;
    let text = '';
    if (pop.kind === 'loading') {
      text = 'Population inside each ring · summing tiles…';
    } else if (pop.kind === 'tabulated') {
      text = pop.snapped
        ? `Population inside each ring · snapped to ${pop.city} — tabulated city`
        : 'Population inside each ring · tabulated city';
    } else if (pop.kind === 'tiles') {
      text = 'Population inside each ring · 4.6 km cells, WorldPop 2020';
    } else if (pop.kind === 'unavailable') {
      text = 'circle population unavailable at this point';
    } else if (pop.kind === 'untabulated') {
      text =
        'Population inside each ring · tabulated at 15, 100 and 1,000 kt only, ' +
        `not at ${fmtKt(pop.kt)} kt`;
    }
    el.textContent = text;
    el.hidden = text === '';
  }

  /**
   * The two class lines, one of which is always showing. They are mutually
   * exclusive because they are claims about where the numbers came from, and a
   * yield is either printed in the manual or derived from it.
   */
  function renderBasis(): void {
    const kt = ktNow();
    const printed = !!(D.combos[state.b] && D.combos[state.b][String(kt)]);
    const tab = root!.querySelector<HTMLElement>('#map-basis-tab');
    const scl = root!.querySelector<HTMLElement>('#map-basis-scale');
    if (tab) {
      tab.hidden = !printed;
      if (printed) tab.textContent = tabulatedLine(rowsNow());
    }
    if (scl) {
      scl.hidden = printed;
      if (!printed) scl.textContent = scaledLine(state.b, kt);
    }
  }

  function renderReadout(): void {
    if (!readout) return;
    const vals = pop.kind === 'tabulated' || pop.kind === 'tiles' ? pop.vals : null;
    // The column appears only when it has figures in it: an empty cell reads as
    // "zero people", which is a claim this page is not making.
    if (vals) readout.dataset.pop = '1';
    else delete readout.dataset.pop;
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

      if (vals) {
        const cell = document.createElement('span');
        cell.className = 'pop';
        const key = row.r === null ? null : row.r.toFixed(3);
        const v = key ? vals[key] : undefined;
        cell.textContent = v === undefined ? '—' : f(v);
        li.appendChild(cell);
      }

      const src = document.createElement('span');
      src.className = 'src';
      src.textContent = row.absent ? row.reason : row.src;
      li.appendChild(src);

      readout.appendChild(li);
    }
    renderPopSource();
  }

  // ---------------------------------------------------------------- population
  /*
   * A click turns into people in three steps, and every one of them is a
   * look-up — no service is asked where the point is, and no number is computed
   * from anything but the tiles:
   *
   *   1. within 5 km of a tabulated city? then the city's own figures, to the
   *      digit (SNAP_KM). A ring drawn 4 km from New York that reported a
   *      different population from New York's page would be indefensible.
   *   2. otherwise fetch the 1-4 tiles covering the clicked point, once each,
   *      and keep them for the session.
   *   3. sum the cells inside each ring, weighting a rim cell by the fraction of
   *      it the circle actually covers, so a 0.1 km ring on a 4.6 km cell is a
   *      fraction of that cell and not the whole of it.
   */
  const tileCache = new Map<string, Promise<Uint8Array | null>>();
  let tileRequests = 0;

  function wrapLon(lon: number): number {
    let l = lon;
    while (l < -180) l += 360;
    while (l >= 180) l -= 360;
    return l;
  }

  function tileName(lon: number, lat: number): string {
    const g = D.popGrid!;
    const tx = Math.floor((wrapLon(lon) + 180) / g.tileDeg);
    const ty = Math.floor((90 - clamp(lat, -90, 89.999)) / g.tileDeg);
    return `x${String(tx).padStart(2, '0')}y${String(Math.max(0, ty)).padStart(2, '0')}`;
  }

  function loadTile(name: string): Promise<Uint8Array | null> {
    const hit = tileCache.get(name);
    if (hit) return hit;
    tileRequests += 1;
    const p = (async (): Promise<Uint8Array | null> => {
      const ctrl = new AbortController();
      const timer = window.setTimeout(() => ctrl.abort(), 6000);
      try {
        const res = await fetch(`/data/pop/${name}.bin`, {
          signal: ctrl.signal,
          credentials: 'omit',
        });
        if (!res.ok) return null;
        const buf = await res.arrayBuffer();
        // A truncated file is a failed load, not a small population.
        if (buf.byteLength !== D.popGrid!.cellsPerTile * D.popGrid!.cellsPerTile) return null;
        return new Uint8Array(buf);
      } catch {
        return null;
      } finally {
        window.clearTimeout(timer);
      }
    })();
    // The promise is cached rather than the result: a tile that 404'd is not
    // asked for again in this session, and neither is a good one.
    tileCache.set(name, p);
    return p;
  }

  function distanceKm(aLat: number, aLon: number, bLat: number, bLon: number): number {
    const R = 6371.0088;
    const p1 = (aLat * Math.PI) / 180;
    const p2 = (bLat * Math.PI) / 180;
    const dp = p2 - p1;
    const dl = ((bLon - aLon) * Math.PI) / 180;
    const h = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
  }

  async function tilesFor(
    lat: number,
    lon: number,
    radiusKm: number,
  ): Promise<Map<string, Uint8Array> | null> {
    const g = D.popGrid;
    if (!g) return null;
    const dLat = radiusKm / 110.574 + g.cellDeg;
    const cos = Math.max(0.02, Math.cos((clamp(lat, -89, 89) * Math.PI) / 180));
    const dLon = radiusKm / (111.32 * cos) + g.cellDeg;
    const names: string[] = [];
    for (const la of [lat - dLat, lat + dLat]) {
      for (const lo of [lon - dLon, lon + dLon]) {
        const n = tileName(lo, la);
        if (names.indexOf(n) < 0) names.push(n);
      }
    }
    const here = tileName(lon, lat);
    if (names.indexOf(here) < 0) names.push(here);
    const got = await Promise.all(names.map(loadTile));
    if (got.some((b) => b === null)) return null;
    const out = new Map<string, Uint8Array>();
    names.forEach((n, i) => out.set(n, got[i] as Uint8Array));
    return out;
  }

  function codeAt(tiles: Map<string, Uint8Array>, g: PopGrid, ci: number, cj: number): number {
    const tx = Math.floor(ci / g.cellsPerTile);
    const ty = Math.floor(cj / g.cellsPerTile);
    const t = tiles.get(
      `x${String(tx).padStart(2, '0')}y${String(ty).padStart(2, '0')}`,
    );
    if (!t) return -1;
    const col = ci - tx * g.cellsPerTile;
    const row = cj - ty * g.cellsPerTile;
    if (col < 0 || col >= g.cellsPerTile || row < 0 || row >= g.cellsPerTile) return -1;
    const v = t[row * g.cellsPerTile + col];
    return v === undefined ? -1 : v;
  }

  /**
   * Fraction of an axis-aligned cell the circle covers, by integrating exact
   * chords along y. 48 slices across the cell gives well under 0.5% on a rim
   * cell; anything cheaper mis-measures the small rings, where one cell is
   * larger than the whole circle.
   */
  function overlapFraction(
    x0: number,
    x1: number,
    y0: number,
    y1: number,
    radiusKm: number,
    cellArea: number,
  ): number {
    const lo = Math.max(x0, -radiusKm);
    const hi = Math.min(x1, radiusKm);
    const bot = Math.max(y0, -radiusKm);
    const top = Math.min(y1, radiusKm);
    if (hi <= lo || top <= bot || cellArea <= 0) return 0;
    const n = 48;
    const dy = (top - bot) / n;
    let area = 0;
    for (let i = 0; i < n; i += 1) {
      const y = bot + (i + 0.5) * dy;
      const half = Math.sqrt(Math.max(0, radiusKm * radiusKm - y * y));
      const l = Math.max(lo, -half);
      const r = Math.min(hi, half);
      if (r > l) area += (r - l) * dy;
    }
    return Math.min(1, area / cellArea);
  }

  function sumInside(
    tiles: Map<string, Uint8Array>,
    lat: number,
    lon: number,
    radiusKm: number,
  ): number {
    const g = D.popGrid!;
    const kmLat = 110.574;
    const kmLon = 111.32 * Math.max(0.02, Math.cos((clamp(lat, -89, 89) * Math.PI) / 180));
    const dLat = radiusKm / kmLat;
    const dLon = radiusKm / kmLon;
    const ci0 = Math.floor((lon - dLon + 180) / g.cellDeg);
    const ci1 = Math.floor((lon + dLon + 180) / g.cellDeg);
    const cj0 = Math.floor((90 - (lat + dLat)) / g.cellDeg);
    const cj1 = Math.floor((90 - (lat - dLat)) / g.cellDeg);
    const cellW = g.cellDeg * kmLon;
    const cellH = g.cellDeg * kmLat;
    const cellArea = cellW * cellH;
    let total = 0;
    for (let cj = cj0; cj <= cj1; cj += 1) {
      const y1 = (90 - cj * g.cellDeg - lat) * kmLat;
      const y0 = y1 - cellH;
      for (let ci = ci0; ci <= ci1; ci += 1) {
        const code = codeAt(tiles, g, ci, cj);
        if (code <= 0) continue;
        const x0 = (ci * g.cellDeg - 180 - lon) * kmLon;
        const value = g.floor * Math.pow(g.ratio, code - 0.5);
        total += value * overlapFraction(x0, x0 + cellW, y0, y1, radiusKm, cellArea);
      }
    }
    return total;
  }

  /** Every row's radius must be in the table, or the column would mix sources. */
  function tabulatedFor(slug: string, rows: Row[]): PopVals | null {
    const table = D.pop && D.pop[slug];
    if (!table) return null;
    const out: PopVals = {};
    for (const row of rows) {
      if (row.r === null) continue;
      const key = row.r.toFixed(3);
      const v = table[key];
      if (v === undefined) return null;
      out[key] = v;
    }
    return out;
  }

  function snappedCity(lat: number, lon: number): CityRec | null {
    let best: CityRec | null = null;
    let bestKm = Infinity;
    for (const c of D.cities) {
      const d = distanceKm(lat, lon, c.lat, c.lon);
      if (d < bestKm) {
        bestKm = d;
        best = c;
      }
    }
    return best && bestKm < SNAP_KM ? best : null;
  }

  function renderPoint(): void {
    const sub = root!.querySelector<HTMLElement>('#map-sub');
    const line = root!.querySelector<HTMLElement>('#map-point');
    const hint = root!.querySelector<HTMLElement>('#map-hint');
    const label = root!.querySelector<HTMLElement>('[data-bind="place"]');
    if (!sub || !line) return;
    if (!clicked) {
      sub.hidden = false;
      line.hidden = true;
      if (hint) hint.hidden = false;
      return;
    }
    sub.hidden = true;
    line.hidden = false;
    if (hint) hint.hidden = true;
    if (label) label.textContent = 'Clicked point';
    const c = root!.querySelector<HTMLElement>('[data-bind="point-coords"]');
    if (c) c.textContent = latLonText(clicked.lat, clicked.lon);
    // Nearest named place is a placeholder: a reverse gazetteer lookup would be
    // a third data source on this page, and this release does not carry one.
    const near = root!.querySelector<HTMLElement>('[data-bind="near"]');
    if (near) near.textContent = 'near —';
  }

  function resolvePop(): void {
    const rows = rowsNow();
    const token = ++popToken;

    if (!clicked) {
      // The picker's own city is tabulated; a searched place is not, and §14.6
      // says so in words rather than borrowing a number from somewhere else.
      // A preset yield is a third case: the table has six radii for 15, 100 and
      // 1,000 kt, and a 300 kt ring is not one of them, so the column stays
      // empty and the line above it says why instead of paying the ring out of
      // the tile surface while the same city's other yields come from the API.
      const tab = gz ? null : tabulatedFor(state.city, rows);
      if (tab) {
        pop = { kind: 'tabulated', city: cityOf(state.city).name, snapped: false, vals: tab };
      } else if (!gz && !isTabulated(ktNow())) {
        pop = { kind: 'untabulated', kt: ktNow() };
      } else {
        pop = { kind: 'idle' };
      }
      renderReadout();
      return;
    }

    const near = snappedCity(clicked.lat, clicked.lon);
    const tab = near ? tabulatedFor(near.slug, rows) : null;
    if (tab && near) {
      pop = { kind: 'tabulated', city: near.name, snapped: true, vals: tab };
      renderReadout();
      return;
    }

    pop = { kind: 'loading' };
    renderReadout();
    const lat = clicked.lat;
    const lon = clicked.lon;
    void (async () => {
      const g = D.popGrid;
      const radii = rows.filter((r) => r.r !== null).map((r) => r.r as number);
      let vals: PopVals | null = null;
      if (g && radii.length) {
        const tiles = await tilesFor(lat, lon, Math.max(...radii));
        if (tiles) {
          vals = {};
          for (const r of radii) {
            const key = r.toFixed(3);
            if (vals[key] === undefined) {
              vals[key] = Math.round(sumInside(tiles, lat, lon, r));
            }
          }
        }
      }
      if (token !== popToken) return;
      pop = vals ? { kind: 'tiles', vals } : { kind: 'unavailable' };
      renderReadout();
    })();
  }

  function unprojectFallback(x: number, y: number): { lat: number; lon: number } | null {
    const c = projectWorld(view.lon, clamp(view.lat, -MAX_LAT, MAX_LAT), view.zoom);
    const p = unprojectWorld(x + (c.x - w / 2), y + (c.y - h / 2), view.zoom);
    if (!Number.isFinite(p.lat) || !Number.isFinite(p.lon)) return null;
    return { lat: clamp(p.lat, -MAX_LAT, MAX_LAT), lon: wrapLon(p.lon) };
  }

  function onPoint(lat: number, lon: number): void {
    clicked = { lat, lon };
    renderPoint();
    redraw();
    resolvePop();
  }

  // One listener for both basemap paths, and it is a real pointer gesture: a
  // drag is not a click, and a tap is, on a phone and on a desktop alike.
  let down: { x: number; y: number; id: number } | null = null;
  frame.addEventListener('pointerdown', (ev) => {
    down = { x: ev.clientX, y: ev.clientY, id: ev.pointerId };
  });
  frame.addEventListener('pointercancel', () => {
    down = null;
  });
  frame.addEventListener('pointerup', (ev) => {
    const start = down;
    down = null;
    if (!start || start.id !== ev.pointerId) return;
    const limit = ev.pointerType === 'touch' ? 12 : 6;
    if (Math.abs(ev.clientX - start.x) > limit || Math.abs(ev.clientY - start.y) > limit) return;
    if (ev.pointerType === 'mouse' && ev.button !== 0) return;
    const rect = frame.getBoundingClientRect();
    const x = ev.clientX - rect.left;
    const y = ev.clientY - rect.top;
    if (tilesLive && map) {
      const ll = map.unproject([x, y]);
      onPoint(ll.lat, ll.lng);
      return;
    }
    const ll = unprojectFallback(x, y);
    if (ll) onPoint(ll.lat, ll.lon);
  });

  // ---------------------------------------------------------------- controls
  function syncControls(): void {
    const sel = form!.querySelector<HTMLSelectElement>('select[name="city"]');
    if (sel) {
      if (gz) {
        let opt = sel.querySelector<HTMLOptionElement>('option[value="__gz"]');
        if (!opt) {
          opt = document.createElement('option');
          opt.value = '__gz';
          sel.appendChild(opt);
        }
        opt.textContent = `${gz.name} (gazetteer)`;
        sel.value = '__gz';
      } else {
        sel.value = state.city;
      }
    }
    const preset = form!.querySelector<HTMLSelectElement>('select[name="preset"]');
    if (preset) preset.value = state.preset;
    for (const input of Array.from(
      form!.querySelectorAll<HTMLInputElement>('input[name="burst"]'),
    )) {
      input.checked = input.value === state.b;
    }
  }

  /** "Little Boy · 15 kt · air burst" — the default reads "100 kt · air burst". */
  function settingText(): string {
    const p = presetById(state.preset);
    return `${p ? `${p.name} · ` : ''}${fmtKt(ktNow())} kt · ${
      state.b === 'air' ? 'air burst' : 'contact burst'
    }`;
  }

  function apply(next: { city?: string; preset?: string; b?: Burst }, pushUrl = true): void {
    state = {
      city: next.city ?? state.city,
      preset: next.preset ?? state.preset,
      b: next.b ?? state.b,
    };
    const city = place();
    // A clicked point keeps the camera where the reader put it: moving the map
    // would load basemap tiles and take the ground out from under the rings.
    if (!clicked) {
      view = viewFor(city, rowsNow());
      if (map && tilesLive) {
        map.jumpTo({ center: [city.lon, city.lat], zoom: view.zoom });
      }
    }
    refreshBase();
    redraw();
    syncControls();

    if (!clicked) {
      const label = root!.querySelector<HTMLElement>('[data-bind="place"]');
      if (label) label.textContent = gz ? gz.head : city.name;
      const coordsEl = root!.querySelector<HTMLElement>('[data-bind="coords"]');
      if (coordsEl) coordsEl.textContent = city.coords;
    }
    const sub = root!.querySelector<HTMLElement>('[data-bind="setting"]');
    if (sub) sub.textContent = settingText();
    renderPoint();
    renderBasis();
    // Ring radii may have changed, so any tile sum has to be redone. The tiles
    // themselves are already in memory: a yield change makes no request.
    resolvePop();

    if (pushUrl) {
      const q = new URLSearchParams();
      q.set('w', String(ktNow()));
      q.set('b', state.b);
      // A gazetteer place has no slug to restore, so it travels as its point:
      // the page rebuilds it as a clicked point, which draws the same rings.
      const at = clicked ?? gz;
      if (at) {
        q.set('lat', at.lat.toFixed(5));
        q.set('lon', at.lon.toFixed(5));
      } else {
        q.set('city', state.city);
      }
      history.replaceState(null, '', `${location.pathname}?${q.toString()}`);
    }
  }

  form.addEventListener('change', () => {
    const sel = form.querySelector<HTMLSelectElement>('select[name="city"]');
    const preset = form.querySelector<HTMLSelectElement>('select[name="preset"]');
    const b = form.querySelector<HTMLInputElement>('input[name="burst"]:checked');
    // Using the picker is how you leave a gazetteer place.
    if (sel && sel.value !== '__gz') gz = null;
    // …and how you leave a clicked point: the picker is the way back to the
    // presets, so choosing a city from it must actually move the rings.
    if (sel && sel.value !== '__gz' && sel.value !== state.city) clicked = null;
    apply({
      city: sel ? sel.value : undefined,
      preset: preset ? preset.value : undefined,
      b: b ? (b.value as Burst) : undefined,
    });
  });

  document.addEventListener('apoca:city', (ev) => {
    const d = (ev as CustomEvent).detail as {
      name: string;
      head: string;
      coords: string;
      lat: number;
      lon: number;
    };
    gz = { slug: '__gz', name: d.name, head: d.head, coords: d.coords, lat: d.lat, lon: d.lon };
    clicked = null;
    apply({});
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

    const city = place();
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
  refit();
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
        refit();
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
    state: (): { city: string; y: number; b: string } => ({
      city: state.city,
      y: ktNow(),
      b: state.b,
    }),
    /** The selector, the yield behind it, and which of the two class lines is up. */
    preset: (): { id: string; kt: number; name: string | null; presets: number } => ({
      id: state.preset,
      kt: ktNow(),
      name: presetById(state.preset)?.name ?? null,
      presets: PRESETS.length,
    }),
    basis: (): {
      kind: string;
      tab: string;
      scale: string;
      tabHidden: boolean;
      scaleHidden: boolean;
    } => {
      const tab = root!.querySelector<HTMLElement>('#map-basis-tab');
      const scl = root!.querySelector<HTMLElement>('#map-basis-scale');
      return {
        kind: !!(D.combos[state.b] && D.combos[state.b][String(ktNow())]) ? 'tabulated' : 'scaled',
        tab: tab ? tab.textContent || '' : '',
        scale: scl ? scl.textContent || '' : '',
        tabHidden: tab ? tab.hidden : true,
        scaleHidden: scl ? scl.hidden : true,
      };
    },
    /** The cube-root law applied to the 100 kt table at run time — the anchor test. */
    scaledAt: (kt: number): Array<number | null> => {
      const base = (D.combos.air[String(ANCHOR_KT)] || []).map((r) => r.r);
      const f = Math.pow(kt / ANCHOR_KT, 1 / 3);
      return base.map((b) => (b === null ? null : Math.round(b * f * 100) / 100));
    },
    rows: (): Array<{ id: string; km: string; r: number | null; src: string; absent: boolean }> =>
      rowsNow().map((r) => ({ id: r.id, km: r.km, r: r.r, src: r.src, absent: r.absent !== null })),
    place: (): { name: string; lat: number; lon: number; gazetteer: boolean } => ({
      name: place().name,
      lat: place().lat,
      lon: place().lon,
      gazetteer: gz !== null,
    }),
    zoom: (): number => view.zoom,
    /** Non-transparent pixels, so "the rings were drawn" is measurable. */
    pixels: (): { rings: number; base: number } => ({
      rings: opaquePixels(cvRings!),
      base: opaquePixels(cvBase!),
    }),
    canvas: (): { w: number; h: number; dpr: number } => ({ w, h, dpr }),
    // ---- click-to-measure surface, read by scripts/verify_click.mjs
    centre: (): { lat: number; lon: number; name: string; coords: string } => centre(),
    /** Moves the camera without pretending to be a user action: a gate needs a
     *  viewport over the ocean before it can click the ocean. */
    goto: (lon: number, lat: number, z?: number): void => {
      view = { lon, lat, zoom: z ?? view.zoom };
      if (map && tilesLive) map.jumpTo({ center: [lon, lat], zoom: view.zoom });
      refreshBase();
      redraw();
    },
    /** Where a lon/lat lands in frame-relative pixels, so a gate can click it. */
    screen: (lon: number, lat: number): { x: number; y: number } => project()(lon, lat),
    pop: (): {
      kind: string;
      city: string | null;
      snapped: boolean | null;
      vals: PopVals | null;
    } => ({
      kind: pop.kind,
      city: pop.kind === 'tabulated' ? pop.city : null,
      snapped: pop.kind === 'tabulated' ? pop.snapped : null,
      vals: pop.kind === 'tabulated' || pop.kind === 'tiles' ? pop.vals : null,
    }),
    tileNames: (): string[] => Array.from(tileCache.keys()),
    tileRequests: (): number => tileRequests,
  };
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', boot, { once: true });
} else {
  boot();
}
