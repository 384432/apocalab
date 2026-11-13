/**
 * Typed access layer over src/data/city-places.json.
 *
 * These are real, named GeoNames features near each city point — the one part
 * of a city page that cannot be produced by the template. The JSON is written
 * by scripts/fetch_city_places.py from the GeoNames country dumps (CC BY 4.0),
 * and every entry carries the geonameid it came from, so any name on the page
 * can be looked up.
 *
 * A published city with no places throws at build time: a city page without a
 * single local name is a template with a city's numbers in it, and the whole
 * point of these pages is that they are not that.
 */
import raw from '../data/city-places.json';
import type { City } from './cities';
import { EFFECT_ROWS, get } from './effects';

export interface Place {
  geonameid: number;
  name: string;
  kind: string;
  fclass: string;
  fcode: string;
  lat: number;
  lon: number;
  distance_km: number;
  bearing: string;
  curated?: boolean;
}

const data = raw as unknown as { places: Record<string, Place[]> };

export function placesOf(city: City): Place[] {
  const p = data.places[city.slug];
  if (!p || p.length < 2) {
    throw new Error(
      `city-places.json has ${p ? p.length : 0} places for "${city.slug}" — ` +
        `run python scripts/fetch_city_places.py, or keep the page unpublished.`,
    );
  }
  return p;
}

export interface Ring {
  id: string;
  name: string;
  /** Short form for a sentence: "5 psi", "2nd-degree burn". */
  label: string;
  km: number;
}

const LABEL: Record<string, string> = {
  fireball: 'fireball',
  overpressure_5psi: '5 psi',
  overpressure_1psi: '1 psi',
  thermal_2nd: '2nd-degree burn',
  thermal_3rd: '3rd-degree burn',
};

/**
 * Which contour a point at `distanceKm` falls inside, at one yield.
 *
 * `inside` is the smallest contour that still contains the point (the ring it
 * is actually within); `outer` is the largest contour it has left behind. Both
 * come from effects.json, so the sentence follows the table instead of being
 * typed beside it.
 */
export function ringAt(distanceKm: number, yieldKt: number): { inside?: Ring; outer?: Ring } {
  const rings = EFFECT_ROWS
    .map((row) => ({
      id: row.id,
      name: row.name,
      label: LABEL[row.id] ?? row.name.toLowerCase(),
      km: get(row.id, 'air', yieldKt)?.radius_km ?? 0,
    }))
    .filter((r) => r.km > 0)
    .sort((a, b) => a.km - b.km);
  const inside = rings.find((r) => r.km >= distanceKm);
  const outer = [...rings].reverse().find((r) => r.km < distanceKm);
  return { inside, outer };
}
