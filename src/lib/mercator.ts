/**
 * Web Mercator arithmetic, shared by the MapLibre path and the no-basemap path.
 *
 * Both paths must place a ring in exactly the same pixels, otherwise the rings
 * jump when the basemap finishes loading. That only holds if both use the same
 * world size convention: MapLibre draws a 512 px tile, so the world square at
 * zoom z is 512·2^z pixels across. Everything here uses that, and the MapLibre
 * branch just calls map.project() — the formulas below are the fallback.
 *
 * Nothing here touches the DOM.
 */

/** Mean Earth circumference, metres (WGS 84). */
export const EARTH_CIRCUMFERENCE_M = 40075016.686;

/** MapLibre's default tile size. Fixed: changing it shifts every projected pixel. */
export const TILE_SIZE = 512;

/** Mercator's latitude limit; beyond it y runs to infinity. */
export const MAX_LAT = 85.05112878;

export function clamp(v: number, lo: number, hi: number): number {
  return v < lo ? lo : v > hi ? hi : v;
}

/** Width of the world square in CSS pixels at this zoom. */
export function worldSize(zoom: number): number {
  return TILE_SIZE * Math.pow(2, zoom);
}

/** Ground metres per CSS pixel at this latitude and zoom. */
export function metersPerPixel(lat: number, zoom: number): number {
  return (EARTH_CIRCUMFERENCE_M * Math.cos((clamp(lat, -MAX_LAT, MAX_LAT) * Math.PI) / 180)) /
    worldSize(zoom);
}

/** Lon/lat -> pixel position inside the world square. */
export function projectWorld(lon: number, lat: number, zoom: number): { x: number; y: number } {
  const size = worldSize(zoom);
  const phi = (clamp(lat, -MAX_LAT, MAX_LAT) * Math.PI) / 180;
  const s = Math.sin(phi);
  return {
    x: ((lon + 180) / 360) * size,
    y: (0.5 - Math.log((1 + s) / (1 - s)) / (4 * Math.PI)) * size,
  };
}

/**
 * The zoom at which a ground radius of `radiusM` draws `radiusPx` pixels wide
 * at this latitude. Inverts metersPerPixel().
 */
export function zoomForRadius(lat: number, radiusM: number, radiusPx: number): number {
  const mpp = radiusM / radiusPx;
  const size = (EARTH_CIRCUMFERENCE_M * Math.cos((clamp(lat, -MAX_LAT, MAX_LAT) * Math.PI) / 180)) / mpp;
  return clamp(Math.log2(size / TILE_SIZE), 1, 16);
}

/**
 * A true ground circle, as lon/lat pairs. Not a screen-space circle: a ground
 * circle at 60°N is an ellipse in Mercator, and the manual's distances are
 * ground distances, so the shape has to survive the projection.
 */
export function geodesicRing(
  lon: number,
  lat: number,
  radiusM: number,
  steps = 96,
): Array<[number, number]> {
  const R = 6371008.8; // mean Earth radius, metres
  const delta = radiusM / R;
  const phi1 = (lat * Math.PI) / 180;
  const lambda1 = (lon * Math.PI) / 180;
  const cosPhi1 = Math.cos(phi1);
  const sinPhi1 = Math.sin(phi1);
  const cosD = Math.cos(delta);
  const sinD = Math.sin(delta);

  const out: Array<[number, number]> = [];
  for (let i = 0; i <= steps; i += 1) {
    const theta = (i / steps) * Math.PI * 2;
    const phi2 = Math.asin(clamp(sinPhi1 * cosD + cosPhi1 * sinD * Math.cos(theta), -1, 1));
    const lambda2 =
      lambda1 +
      Math.atan2(Math.sin(theta) * sinD * cosPhi1, cosD - sinPhi1 * Math.sin(phi2));
    // Wrap into -180..180 so a circle that touches the antimeridian does not
    // draw a line all the way across the world.
    let lon2 = ((lambda2 * 180) / Math.PI + 540) % 360 - 180;
    out.push([lon2, (phi2 * 180) / Math.PI]);
  }
  return out;
}

/** "1, 2, 5 × 10^n" ticks that put 3–7 divisions across a given span. */
export function niceStep(span: number, target = 5): number {
  const raw = span / target;
  const exp = Math.floor(Math.log10(raw));
  const base = Math.pow(10, exp);
  const f = raw / base;
  const mult = f < 1.5 ? 1 : f < 3.5 ? 2 : f < 7.5 ? 5 : 10;
  return mult * base;
}
