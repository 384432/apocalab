/**
 * The client payload: one JSON island, built from the same functions that
 * server-render the visible markup.
 *
 * Both the homepage panel and the map page read this, so the two can never show
 * different numbers for the same city/yield/burst combination.
 *
 * Nothing here computes a population. The map page also carries the tabulated
 * ring counts (scripts/build_city_pop.py, WorldPop API at 100 m) and the
 * encoding table of the 1 km tiles (scripts/build_pop_tiles.py), because a click
 * must not fetch a second file to learn how to read the first one.
 */
import type { Burst, YieldKt } from './effects';
import { YIELDS } from './effects';
import type { City } from './cities';
import { coordText } from './cities';
import { BURST_LABEL, panelRows, ringScale, scaleBar } from './panel';
import popRaw from '../data/city-pop.json';
import popMeta from '../data/pop-meta.json';

/** How one byte becomes people per cell. Mirrors scripts/build_pop_tiles.py. */
export interface PopGrid {
  /** cell size in degrees (1/24 deg = 5 source pixels of 30 arc-seconds) */
  cellDeg: number;
  /** cells per tile edge; a tile is tileDeg x tileDeg degrees */
  cellsPerTile: number;
  tileDeg: number;
  /** level 0 means no people; level i>0 means floor * ratio^(i-0.5) */
  floor: number;
  ratio: number;
}

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
  /** slug -> radius (3 dp) -> people inside it. Air-burst radii only. */
  pop?: Record<string, Record<string, number>>;
  popGrid?: PopGrid;
}

const TABULATED = (popRaw as unknown as {
  cities: Record<string, { ring_population: Record<string, number> }>;
}).cities;

/**
 * Every radius the map can draw for an air burst must have a tabulated count, or
 * a snapped click would answer some rows from the table and others from the
 * tiles — two sources inside one column, which is exactly the sort of quiet
 * mixture a reader cannot audit. Checked at build time, not at click time.
 */
function assertTabulatedCoverage(pop: Record<string, Record<string, number>>, cities: City[]): void {
  for (const y of YIELDS) {
    for (const row of panelRows('air', y)) {
      if (row.r === null) continue;
      const key = row.r.toFixed(3);
      for (const c of cities) {
        if (pop[c.slug]?.[key] === undefined) {
          throw new Error(
            `city-pop.json has no count at ${key} km for "${c.slug}": the ${y} kt air ` +
              'burst draws that ring, so a snapped click could not fill it from the table. ' +
              'Re-run python scripts/build_city_pop.py.',
          );
        }
      }
    }
  }
}

export function buildIsland(
  city: City,
  y: YieldKt,
  burst: Burst,
  cities: City[],
  withPopulation = false,
): Island {
  const island: Island = {
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

  if (!withPopulation) return island;

  const pop: Record<string, Record<string, number>> = {};
  for (const c of cities) {
    const rec = TABULATED[c.slug];
    if (!rec) {
      throw new Error(
        `city-pop.json has no entry for "${c.slug}" — run python scripts/build_city_pop.py`,
      );
    }
    pop[c.slug] = rec.ring_population;
  }
  assertTabulatedCoverage(pop, cities);

  island.pop = pop;
  island.popGrid = {
    cellDeg: popMeta.grid.cell_deg,
    cellsPerTile: popMeta.grid.cells_per_tile,
    tileDeg: popMeta.grid.tile_deg,
    floor: popMeta.bins.floor,
    ratio: popMeta.bins.ratio,
  };
  return island;
}
