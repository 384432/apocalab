/**
 * Typed access layer over src/data/effects.json.
 *
 * The JSON is generated at build time by scripts/build_effects.py and checked by
 * scripts/verify_data.py. Nothing here computes a radius: every number is a
 * transcription or a manual-stated scaling that was applied before the JSON was
 * written. This file only formats and looks things up.
 */
import raw from '../data/effects.json';

export const YIELDS = [15, 100, 1000] as const;
export type YieldKt = (typeof YIELDS)[number];

export type Burst = 'air' | 'ground';
export type EffectId =
  | 'fireball'
  | 'overpressure_5psi'
  | 'overpressure_1psi'
  | 'thermal_2nd'
  | 'thermal_3rd';

export interface Citation {
  chapter: number;
  section: string;
  figure?: string | null;
  equation?: string | null;
  page: number;
}

export interface Entry {
  id: string;
  effect: EffectId;
  label: string;
  burst: Burst;
  yield_kt: number;
  radius_m: number;
  radius_km: number;
  radius_ft: number | null;
  hob_ft: number | null;
  hob_m: number | null;
  value_type: 'formula' | 'curve_read' | 'scaled_curve_read';
  citation: Citation;
  readout: string;
  conversion: string;
  raw_reading_cn: string;
  read_error: string;
  read_by: string;
  checked_by: string | null;
  note: string | null;
  hob_note: string | null;
  scaled?: boolean;
  scaled_label?: string;
  scaling?: { law: string; formula: string; section: string; pages: number[] };
  base?: Record<string, unknown>;
  q_cal_cm2?: number;
  slant_range_mi?: number;
  skin?: string;
  burst_height_note?: string;
}

export interface CrossCheck {
  id: string;
  claim: string;
  manual: string;
  manual_mi?: number;
  manual_ft?: number;
  ours_mi?: number;
  ours_ft?: number;
  delta_pct: number;
}

export interface EffectsData {
  manual: {
    title: string;
    editors: string[];
    edition: string;
    year: number;
    publisher: string[];
    doi: string;
    public_domain: boolean;
    page_convention: string;
  };
  method: Record<string, string>;
  caveats: string[];
  cross_checks: CrossCheck[];
  entries: Entry[];
}

export const data = raw as unknown as EffectsData;
export const entries = data.entries;
export const manual = data.manual;
export const crossChecks = data.cross_checks;

/** The burst heights at which a cell was read, as a single lookup. */
export function get(effect: EffectId, burst: Burst, y: YieldKt): Entry | undefined {
  return entries.find(
    (e) => e.effect === effect && e.burst === burst && e.yield_kt === y,
  );
}

/** "Ch. 3 · Fig. 3.73c · p. 115"  or  "Eq. (2.127.1) · p. 70" */
export function citationLine(e: Entry): string {
  const c = e.citation;
  if (c.figure) return `Ch. ${c.chapter} · Fig. ${c.figure} · p. ${c.page}`;
  const eq = c.equation ?? '';
  const label = eq.startsWith('(') ? `Eq. ${eq}` : eq || 'Eq.';
  return `${label} · p. ${c.page}`;
}

/** 2275.3 -> "2,275" */
export function fmtFt(n: number): string {
  return Math.round(n).toLocaleString('en-US');
}

/** "1.71" — always two decimals so the columns line up. */
export function fmtKm(km: number): string {
  return km.toFixed(2);
}

/**
 * For the 5 psi rows: the 1 kt distance at which the 4 and 6 psi contours were
 * interpolated. Pulled out of `readout` so the page cannot drift from the data.
 */
export function interpFt(e: Entry): string | null {
  const m = /interpolated between 4 and 6 psi contours, at ([\d.,]+) ft/.exec(e.readout);
  return m ? m[1].replace(/,/g, '') : null;
}

export const EFFECT_ROWS: { id: EffectId; name: string; anchor: string }[] = [
  { id: 'fireball', name: 'Fireball', anchor: 'fireball' },
  { id: 'overpressure_5psi', name: '5 psi overpressure', anchor: 'psi5' },
  { id: 'overpressure_1psi', name: '1 psi overpressure', anchor: 'psi1' },
  { id: 'thermal_2nd', name: 'Thermal · 2nd-degree', anchor: 'thermal2' },
  { id: 'thermal_3rd', name: 'Thermal · 3rd-degree', anchor: 'thermal3' },
];
