/**
 * The 20 preset metros.
 *
 * Coordinates come from GeoNames cities15000 (CC BY 4.0), written by
 * scripts/build_cities.py. They are gazetteer points, not administrative
 * centroids and not population-weighted centroids — the 10 km population radius
 * defined in D4 is measured from this exact point, so the point has to be
 * citable rather than chosen by hand.
 *
 * `reference_population` is GeoNames' city-proper population. It exists only to
 * order the list and to catch a bad gazetteer match. It is NOT the "population
 * within 10 km" figure and is never printed as one.
 */
import raw from '../data/cities.json';

export interface City {
  slug: string;
  name: string;
  country: string;
  country_name: string;
  lat: number;
  lon: number;
  geonameid: number;
  gazetteer_name: string;
  reference_population: number;
  reference_population_note: string;
}

export interface CitySource {
  name: string;
  url: string;
  license: string;
  retrieved: string;
  note: string;
}

export const cities = raw.cities as City[];
export const citySource = raw.source as CitySource;
export const DEFAULT_CITY = 'new-york';

const bySlug = new Map(cities.map((c) => [c.slug, c]));

export function getCity(slug: string | null | undefined): City | undefined {
  return slug ? bySlug.get(slug) : undefined;
}

/** "40.7143, −74.0060" — the actual point the rings are measured from. */
export function coordText(c: City): string {
  const lat = `${Math.abs(c.lat).toFixed(4)}° ${c.lat >= 0 ? 'N' : 'S'}`;
  const lon = `${Math.abs(c.lon).toFixed(4)}° ${c.lon >= 0 ? 'E' : 'W'}`;
  return `${lat}, ${lon}`;
}
