/**
 * The twelve weapon presets, and the two routes a ring radius can take.
 *
 * Split by provenance, not by size:
 *
 *   tabulated  15, 100 and 1,000 kt. The radii are the numbers in
 *              src/data/effects.json — printed readings off Fig. 3.73c (p. 115)
 *              and Fig. 7.42 (p. 291), and the fireball equation (2.127.1).
 *   scaled     everything else. The three overpressure rings come from
 *              R = R(100 kt) × (W/100)^(1/3), §3.61, Eq. (3.61.2), p. 101.
 *
 * Two rows never take the cube root, and the code says so rather than letting
 * the class label speak for them:
 *
 *   the fireball   R = 110·W^0.4 ft (air) / 145·W^0.4 ft (contact), Eq. (2.127.1)
 *                  and (2.127.2), pp. 70-71. A formula in W is exact; scaling it
 *                  from 100 kt would disagree with the printed equation by 11%
 *                  at 21 kt.
 *   the thermal    read off Fig. 7.42 at the preset's own column. The figure's
 *   rings          contours scale at about W^0.38, not W^0.333: cube-rooting
 *                  them would put 50 Mt at 55 km where the printed curve runs to
 *                  about 73 km. Above 10 Mt the figure has no ink at all.
 *
 * Every radius in weapon-radii.json was produced by scripts/build_weapon_radii.py
 * from those two sources; this file only formats and looks things up.
 */
import type { Burst } from './effects';
import weaponsRaw from '../data/weapons.json';
import radiiRaw from '../data/weapon-radii.json';

export interface Preset {
  id: string;
  name: string;
  country: string;
  year: number;
  kt: number;
  /** Present when the cited page prints a range: the radii use `kt` regardless. */
  kt_range?: [number, number];
  /** The sentence that says a range was involved and where inside it `kt` sits. */
  yield_note?: string;
  note: string;
  source: { label: string; url: string };
  quote_yield: string;
  quote_year: string;
}

export const PRESETS: Preset[] = (weaponsRaw as unknown as { presets: Preset[] }).presets;

/** The three yields that are printed in the manual, and their selector ids. */
export const YIELD_OPTIONS = [
  { id: 'y15', kt: 15 },
  { id: 'y100', kt: 100 },
  { id: 'y1000', kt: 1000 },
] as const;

export function isTabulated(kt: number): boolean {
  return YIELD_OPTIONS.some((y) => y.kt === kt);
}

export function presetById(id: string): Preset | undefined {
  return PRESETS.find((p) => p.id === id);
}

/** "y300" is not a preset id; a selector id is either y<kt> or a weapon. */
export function ktOf(id: string): number {
  const fixed = YIELD_OPTIONS.find((y) => y.id === id);
  if (fixed) return fixed.kt;
  return presetById(id)?.kt ?? 100;
}

/**
 * ?w=<kt> names a yield, not a weapon, so a shared link has to find its way
 * back to an option. 15 kt is ambiguous in one direction only: Little Boy is
 * also 15 kt, and it resolves to the plain "15 kt" option, which draws the same
 * six rings from the same table row.
 */
export function optionForKt(kt: number): string | null {
  const fixed = YIELD_OPTIONS.find((y) => y.kt === kt);
  if (fixed) return fixed.id;
  const hits = PRESETS.filter((p) => p.kt === kt);
  return hits.length === 1 ? hits[0].id : null;
}

interface RadiusRec {
  id: string;
  kt: number;
  basis: 'tabulated' | 'scaled';
  thermal: 'tabulated' | 'read' | 'off-chart';
  radii?: Record<Burst, Array<number | null>>;
}

export const RADII: RadiusRec[] = (radiiRaw as unknown as { presets: RadiusRec[] }).presets;

export function radiiOf(kt: number): Record<Burst, Array<number | null>> | null {
  const hit = RADII.find((r) => r.kt === kt);
  return hit?.radii ?? null;
}

export function thermalOf(kt: number): RadiusRec['thermal'] {
  return RADII.find((r) => r.kt === kt)?.thermal ?? 'tabulated';
}

/** The figure the cube-root law is anchored on, from the ledger. */
export const ANCHOR_KT = 100;

export const SCALED_LAW =
  'scaled by the cube-root law, §3.61 (p. 101), anchored on the 100 kt tabulated value';

export const FIGURE_MAX_KT = 10_000;

/**
 * The tabulated line names every printed source the current rows use, so it
 * cannot claim a figure the rows do not show: a contact burst has no thermal
 * rows, and the line drops Fig. 7.42 when they are gone.
 */
export function citedSources(rows: Array<{ src: string }>): string[] {
  const figs: string[] = [];
  const eqs: string[] = [];
  for (const row of rows) {
    const fig = /Fig\. ?([\w.]+) · p\. ?(\d+)/.exec(row.src);
    const eq = /Eq\. ?(\([\d.]+\)) · p\. ?(\d+)/.exec(row.src);
    if (fig) {
      const label = `Fig. ${fig[1]} (p. ${fig[2]})`;
      if (figs.indexOf(label) < 0) figs.push(label);
    } else if (eq) {
      const label = `Eq. ${eq[1]} (p. ${eq[2]})`;
      if (eqs.indexOf(label) < 0) eqs.push(label);
    }
  }
  return [...figs, ...eqs];
}

export function tabulatedLine(rows: Array<{ src: string }>): string {
  return `tabulated from ${citedSources(rows).join(', ')}`;
}

/**
 * The scaled line states the law, its anchor, and then — in the same sentence,
 * because dropping it would let the label speak for rows it does not govern —
 * which rows it does not cover.
 */
export function scaledLine(burst: Burst, kt: number): string {
  const fb = burst === 'air' ? '(2.127.1)' : '(2.127.2)';
  const tail = burst === 'ground'
    ? `the three overpressure rings; the fireball comes from Eq. ${fb} at this yield, and a contact burst draws no thermal ring`
    : kt > FIGURE_MAX_KT
      ? `the three overpressure rings; the fireball comes from Eq. ${fb}, and above 10 Mt Fig. 7.42 has no curve to read`
      : `the three overpressure rings; the fireball comes from Eq. ${fb} at this yield and the thermal rings are read off Fig. 7.42 at this yield`;
  return `${SCALED_LAW} — ${tail}`;
}

export const SOURCE_PREFIX = {
  fireball: (burst: Burst) => `Ch. 2 · Eq. ${burst === 'air' ? '(2.127.1)' : '(2.127.2)'} · p. ${burst === 'air' ? 70 : 71}`,
  blast: 'Ch. 3 · Eq. (3.61.2) · p. 101',
  thermal: 'Ch. 7 · Fig. 7.42 · p. 291',
} as const;

export const THERMAL_OFF_CHART =
  'Fig. 7.42 stops at 10 Mt: no thermal radius is read above it.';

export const THERMAL_CONTACT = 'contact burst: not reported';

/** "15,000" */
export function fmtKt(kt: number): string {
  return kt.toLocaleString('en-US');
}

/** How an option reads in the selector and in the heading. */
export function presetOptionText(p: Preset): string {
  return `${p.name} — ${fmtKt(p.kt)} kt, ${p.year}`;
}
