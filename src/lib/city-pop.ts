/**
 * Typed access layer over src/data/city-pop.json.
 *
 * The JSON is produced by scripts/build_city_pop.py from the WorldPop API and
 * cached in the repo. Nothing here computes a population: it looks a radius up
 * and formats it. If a city or a radius is missing, every accessor throws —
 * a city page must fail the build rather than print a hole.
 *
 * Two figures, two different questions, and they are never mixed (D4):
 *
 *   city_pop_10km     people inside a 10 km disc — a fact about the city
 *   ring_population   people inside an effect ring — a fact about a yield
 *
 * The ring figure is never subtracted from the city figure to "explain" what is
 * left over: the manual gives no basis for treating survivors as an arithmetic
 * remainder, and terrain, shelter and time of day are all missing from it.
 */
import raw from '../data/city-pop.json';
import type { City } from './cities';
import { EFFECT_ROWS, get, YIELDS } from './effects';

export interface PopSource {
  name: string;
  api: string;
  year: number;
  radius_km: number;
  catch_radius_km: number;
  retrieved: string;
  license: string;
  note: string;
}

interface CityPop {
  geonameid: number;
  data_year: number;
  catchRadiusKm: number;
  city_pop_10km: number;
  ring_population: Record<string, number>;
}

const data = raw as unknown as {
  source: PopSource;
  radii_km: number[];
  cities: Record<string, CityPop>;
};

export const popSource = data.source;
export const CITY_RADIUS_KM = data.source.radius_km;
export const CATCH_RADIUS_KM = data.source.catch_radius_km;

/**
 * The widest ring any city page draws: 1 Mt 1 psi, 21.40 km.
 *
 * Read from effects.json rather than typed, so a new yield or a re-read contour
 * cannot quietly outgrow the catchment. If it does, this module throws and the
 * build stops — a truncated ring is exactly the number this site must not print.
 */
export const MAX_RING_KM = Math.max(
  ...YIELDS.flatMap((y) => EFFECT_ROWS.map((row) => get(row.id, 'air', y)?.radius_km ?? 0)),
);

function assertCatchWideEnough(slug: string, r: CityPop): void {
  if (!r.catchRadiusKm) {
    throw new Error(
      `city-pop.json entry "${slug}" has no catchRadiusKm — re-run ` +
        `python scripts/build_city_pop.py --refresh`,
    );
  }
  if (r.catchRadiusKm < MAX_RING_KM) {
    throw new Error(
      `city-pop.json catchment for "${slug}" is ${r.catchRadiusKm} km, but the ` +
        `widest ring on the page is ${MAX_RING_KM} km: that ring would be cut off ` +
        `by the catchment and the number printed for it would be the catchment, ` +
        `not the ring.`,
    );
  }
}

function record(slug: string): CityPop {
  const r = data.cities[slug];
  if (!r) {
    throw new Error(
      `city-pop.json has no entry for "${slug}" — run python scripts/build_city_pop.py`,
    );
  }
  assertCatchWideEnough(slug, r);
  return r;
}

export function cityPopulation(city: City): number {
  const r = record(city.slug);
  if (r.geonameid !== city.geonameid) {
    throw new Error(
      `city-pop.json entry for "${city.slug}" belongs to geonameid ${r.geonameid}, ` +
        `but cities.json says ${city.geonameid} — the gazetteer match moved.`,
    );
  }
  return r.city_pop_10km;
}

/** People inside an effect ring. `km` is the radius drawn on the page. */
export function peopleWithin(city: City, km: number): number {
  const r = record(city.slug);
  const key = km.toFixed(3);
  const v = r.ring_population[key];
  if (v === undefined) {
    throw new Error(
      `city-pop.json has no count at ${key} km for "${city.slug}" — ` +
        `either the radius changed or scripts/build_city_pop.py was not re-run.`,
    );
  }
  return v;
}

/** 3743585 -> "3,743,585" */
export function fmtPeople(n: number): string {
  return Math.round(n).toLocaleString('en-US');
}

/**
 * The population convention, in one sentence, printed on every city page.
 *
 * Built here rather than typed into a template: the number, the point, the
 * dataset name and the year all come from the data, so the sentence cannot drift
 * away from the figure it describes.
 */
export function populationSentence(city: City, lat: string, lon: string): string {
  const n = fmtPeople(cityPopulation(city));
  // The API returns "WorldPop Global2 R2025A, 100 m"; in a sentence the comma
  // reads as a list separator, so it becomes one name.
  const dataset = popSource.name.replace(/,\s*/, ' ');
  // Both radii, always: a reader who sees 10,166,583 inside a 21.4 km ring and
  // 3,743,585 "in the city" is owed the fact that one request produced both.
  return (
    `${n} people live within ${CITY_RADIUS_KM} km of ${lat}, ${lon} ` +
    `(rings up to ${MAX_RING_KM.toFixed(2).replace(/0$/, '')} km counted from the same ` +
    `${CATCH_RADIUS_KM} km catchment) — the GeoNames point for ${city.name} — ` +
    `counted on the ${dataset} grid, ${popSource.year} estimates, ` +
    `not inside a city boundary.`
  );
}

/** How many people inside a ring, as a share of the 10 km disc. Never a survivor count. */
export function shareOfCity(city: City, km: number): number {
  return (100 * peopleWithin(city, km)) / cityPopulation(city);
}
