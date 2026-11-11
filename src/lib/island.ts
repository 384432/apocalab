/**
 * The client payload: one JSON island, built from the same functions that
 * server-render the visible markup.
 *
 * Both the homepage panel and the map page read this, so the two can never show
 * different numbers for the same city/yield/burst combination.
 */
import type { Burst, YieldKt } from './effects';
import { YIELDS } from './effects';
import type { City } from './cities';
import { coordText } from './cities';
import { BURST_LABEL, panelRows, ringScale, scaleBar } from './panel';

export interface Island {
  default: { city: string; yield: number; burst: Burst };
  yields: readonly number[];
  burstLabels: Record<Burst, string>;
  cities: Array<{
    slug: string;
    name: string;
    coords: string;
    lat: number;
    lon: number;
  }>;
  combos: Record<Burst, Record<string, ReturnType<typeof panelRows>>>;
  bars: Record<string, { km: number; units: number }>;
  scales: Record<string, number>;
}

export function buildIsland(city: City, y: YieldKt, burst: Burst, cities: City[]): Island {
  return {
    default: { city: city.slug, yield: y, burst },
    yields: YIELDS,
    burstLabels: BURST_LABEL,
    cities: cities.map((c) => ({
      slug: c.slug,
      name: c.name,
      coords: coordText(c),
      lat: c.lat,
      lon: c.lon,
    })),
    combos: {
      air: Object.fromEntries(YIELDS.map((yy) => [String(yy), panelRows('air', yy)])),
      ground: Object.fromEntries(YIELDS.map((yy) => [String(yy), panelRows('ground', yy)])),
    },
    bars: Object.fromEntries(
      (['air', 'ground'] as Burst[]).flatMap((b) =>
        YIELDS.map((yy) => [`${b}.${yy}`, scaleBar(panelRows(b, yy))]),
      ),
    ),
    scales: Object.fromEntries(
      (['air', 'ground'] as Burst[]).flatMap((b) =>
        YIELDS.map((yy) => [`${b}.${yy}`, Math.round(ringScale(panelRows(b, yy)) * 1e4) / 1e4]),
      ),
    ),
  };
}
