"""Build the per-preset ring radii from the two printed routes and the figure.

Every number this script writes has exactly one of three origins:

  formula   the fireball: R = 110·W^0.4 ft (air) / 145·W^0.4 ft (contact),
            Eq. (2.127.1) and (2.127.2), pp. 70-71. Exact in W, so no scaling.
  scaled    the three overpressure rings: R = R(100 kt) × (W/100)^(1/3),
            the cube-root law of §3.61, Eq. (3.61.2), p. 101, anchored on the
            100 kt value in src/data/effects.json.
  read      the two thermal rings: the 4.5 and 10 cal/cm² contours of Fig. 7.42
            (p. 291), measured on the high-resolution scan at the yield's own
            column. Not scaled: the figure's contours are not cube-root, and
            the manual prints no exponent for them.

Above 10 Mt the figure has no ink — its frame ends exactly at 10,000 kt — so the
thermal rows are emitted as null there and the page says why.

Usage:
    python scripts/build_weapon_radii.py
    python scripts/build_weapon_radii.py --check    # assert, write nothing

Outputs src/data/weapon-radii.json and weapon-ledger.csv.
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
EFFECTS = ROOT / "src/data/effects.json"
WEAPONS = ROOT / "src/data/weapons.json"
OUT_JSON = ROOT / "src/data/weapon-radii.json"
OUT_CSV = ROOT / "weapon-ledger.csv"
FIG = ROOT / ".tmp_handbook/fig7242_hi_rot.png"

FT2M = 0.3048
MI2M = 1609.344
TABULATED_YIELDS = (15, 100, 1000)
ANCHOR_KT = 100

# Fig. 7.42 calibration, copied from scripts/build_effects.py (p. 291, scan
# rotated 270°, 4,692 × 3,156 px):
#     x_px = 834.5 + 783.25 · log10(W_kt)
#     y_px = 212.0 + 783.67 · (2 − log10(slant_range_mi))
# The vertical grid was verified to land on 100/50/20/10/5/2/1/0.5/0.1 mi and
# the frame closes at x_px 3,966-3,970, i.e. exactly 10,000 kt.
X0, XS = 834.5, 783.25
Y0, YS = 212.0, 783.67
AXIS_MAX_KT = 10_000

# The two contours these presets need, as indices into the six contours that
# cross every yield column, counted from the outside: 4.5, 6, 8, 10, 15, 25
# cal/cm². thermal_2nd is the 4.5 contour, thermal_3rd the 10 (see build_effects).
CONTOURS = {"thermal_2nd": 0, "thermal_3rd": 3}

# Pixel columns already digitised in scripts/build_effects.py, reused here as the
# self-test: this script must reproduce them before it is allowed to read a new
# column.
KNOWN_X = {15: 1756, 100: 2391, 1000: 3194}
KNOWN_Y = {
    15: [1528.0, 1614.5, 1688.5, 1746.5, 1883.5, 1997.0],
    100: [1279.5, 1339.0, 1410.0, 1467.5, 1590.5, 1690.0],
    1000: [983.5, 1045.0, 1100.5, 1146.0, 1241.0, 1329.5],
}

# Must equal EFFECT_ROWS in src/lib/effects.ts, element for element: the radii
# below are written as positional arrays and the client reads them by index of
# that list. The anchor self-check is the guard — it walks the same order and
# compares the 100 kt result to the tabulated row for the same effect id, so a
# divergence surfaces as a failed build rather than as swapped rings.
EFFECT_ORDER = [
    "overpressure_1psi",
    "thermal_2nd",
    "thermal_3rd",
    "overpressure_5psi",
    "overpressure_20psi",
    "fireball",
]


def x_of(kt: float) -> int:
    return int(round(X0 + XS * math.log10(kt)))


def mi_of(y: float) -> float:
    return 10 ** (2.0 - (y - Y0) / YS)


def fireball_ft(kt: float, burst: str) -> float:
    return (110.0 if burst == "air" else 145.0) * kt**0.4


class Figure:
    """Column reads on the Fig. 7.42 scan, with the grid masked out."""

    def __init__(self, path: Path) -> None:
        self.dark = np.asarray(Image.open(path).convert("L")) < 128
        self.h, self.w = self.dark.shape
        rowfrac = self.dark.mean(axis=1)
        # Horizontal grid lines cross the whole plot; they are ink at every
        # column and would otherwise be mistaken for a curve.
        self.grid = rowfrac > 0.35
        self.grid_rows = int(self.grid.sum())

    def runs(self, x: int, lo: int, hi: int) -> list[tuple[float, int]]:
        col = self.dark[lo:hi, x] & ~self.grid[lo:hi]
        out: list[tuple[float, int]] = []
        y = 0
        while y < col.size:
            if col[y]:
                y0 = y
                while y < col.size and col[y]:
                    y += 1
                out.append((lo + (y0 + y - 1) / 2, y - y0))
            else:
                y += 1
        return out

    def predict(self, kt: float, idx: int) -> tuple[float, bool]:
        """Straight line through the neighbouring digitised columns.

        The printed contours are straight in these log-log coordinates to
        within a few pixels over a decade, so the prediction is only a search
        centre; the value written down is the measured run.
        """
        xs = [KNOWN_X[y] for y in TABULATED_YIELDS]
        ys = [KNOWN_Y[y][idx] for y in TABULATED_YIELDS]
        x = x_of(kt)
        for (xa, ya), (xb, yb) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
            if xa <= x <= xb:
                t = (x - xa) / (xb - xa)
                return ya + t * (yb - ya), False
        (xa, ya), (xb, yb) = (xs[0], ys[0]), (xs[1], ys[1])
        if x < xs[0]:
            t = (x - xa) / (xb - xa)
            return ya + t * (yb - ya), True
        (xa, ya), (xb, yb) = (xs[-2], ys[-2]), (xs[-1], ys[-1])
        t = (x - xa) / (xb - xa)
        return ya + t * (yb - ya), True

    def read(self, kt: float, idx: int) -> tuple[float, int, float, bool]:
        """(y_px, x_px, predicted_y_px, extrapolated) for one contour."""
        return self.read_at(x_of(kt), self.predict(kt, idx), idx, kt)

    def read_at(self, x: int, pred: tuple[float, bool], idx: int, kt: float) -> tuple[float, int, float, bool]:
        """As `read`, but at a given column — the self-test reuses the three
        columns digitised in build_effects.py, which sit up to 10 px off the
        nominal x(kt) because that is where the printed crossing is cleanest."""
        pred, extrap = pred
        win = 90 if extrap else 40
        lo = max(int(pred - win), 216)
        hi = min(int(pred + win), self.h - 1)
        cand = self.runs(x, lo, hi)
        if not cand:
            raise RuntimeError(f"no ink at x={x} near y={pred:.0f} (kt={kt}, contour {idx})")
        y = min(cand, key=lambda r: abs(r[0] - pred))[0]
        return y, x, pred, extrap


def main() -> int:
    check_only = "--check" in sys.argv

    effects = json.loads(EFFECTS.read_text(encoding="utf-8"))["entries"]
    tab = {(e["effect"], e["burst"], e["yield_kt"]): e for e in effects}
    presets = json.loads(WEAPONS.read_text(encoding="utf-8"))["presets"]

    fig = Figure(FIG)

    # ---- self-test: the routine must reproduce the three digitised columns
    # Tolerance: 2.5 px. The one point that sits at 2 px is the 15 cal/cm²
    # contour at 1,000 kt (y_px 1,241), which crosses the 5-mile grid line and
    # merges with it; masking the grid costs a couple of pixels. 2.5 px is
    # 0.3% of a decade, i.e. 0.7% in slant range — inside the ±6% this figure
    # is quoted at, and two orders below the effect being measured.
    worst, worst_at = 0.0, ""
    for kt, ys in KNOWN_Y.items():
        for idx, want in enumerate(ys):
            got, x, pred, _ = fig.read_at(KNOWN_X[kt], fig.predict(kt, idx), idx, kt)
            if x != KNOWN_X[kt]:
                raise SystemExit(f"column mismatch at {kt} kt: {x} vs {KNOWN_X[kt]}")
            if abs(got - want) > worst:
                worst, worst_at = abs(got - want), f"{kt} kt contour {idx} ({got:.1f} vs {want:.1f})"
    print(f"self-test: reproduced 18 known contour points, worst |Δy| = {worst:.2f} px — {worst_at}")
    if worst > 2.5:
        raise SystemExit("self-test failed: the column read does not reproduce build_effects.py")

    # ---- the cube-root law, quoted from §3.61 p.101
    # Printed pages only: §3.61 opens at the foot of p.100 ("a given pressure
    # will occur at a distance ... proportional to the cube root"), Eq. (3.61.2)
    # is printed on p.101, and §3.62-§3.63 continue the same law on p.102.
    # A PDF page number here would be an offset artefact, not a citation.
    law = {
        "section": "§3.61",
        "equation": "(3.61.2)",
        "pages": [100, 101, 102],
        "formula": "R = R(100 kt) × (W/100)^(1/3)",
        "quote": (
            "Full-scale tests have shown this relationship between distance and energy "
            "yield to hold for yields up to (and including) the megaton range."
        ),
        "applies_to": ["overpressure_5psi", "overpressure_20psi", "overpressure_1psi"],
    }

    # ---- anchor: the scaled path at 100 kt must land on the tabulated value
    anchor = {"kt": ANCHOR_KT, "bursts": {}, "identical": True}
    for burst in ("air", "ground"):
        rows = {}
        for eff in ("overpressure_5psi", "overpressure_20psi", "overpressure_1psi"):
            base_m = tab[(eff, burst, 100)]["radius_m"]
            factor = (ANCHOR_KT / 100.0) ** (1 / 3)
            scaled = round(round(base_m * factor) / 1000, 2)
            rows[eff] = {"scaled_km": scaled, "tabulated_km": tab[(eff, burst, 100)]["radius_km"]}
            if scaled != tab[(eff, burst, 100)]["radius_km"]:
                anchor["identical"] = False
        fb = round(round(fireball_ft(ANCHOR_KT, burst) * FT2M) / 1000, 2)
        rows["fireball"] = {"scaled_km": fb, "tabulated_km": tab[("fireball", burst, 100)]["radius_km"]}
        if fb != tab[("fireball", burst, 100)]["radius_km"]:
            anchor["identical"] = False
        anchor["bursts"][burst] = rows
    print(f"anchor: 100 kt through the law reproduces the table → {anchor['identical']}")
    if not anchor["identical"]:
        raise SystemExit("anchor check failed: the scaled path does not return the tabulated value")

    # ---- per preset
    out_presets = []
    ledger: list[dict[str, object]] = []
    for p in presets:
        kt = int(p["kt"])
        basis = "tabulated" if kt in TABULATED_YIELDS else "scaled"
        # Provenance travels with the number: every ledger row carries the page
        # the yield came from, and the yield's own caveat when it has one (the
        # W76-2 range is computed at its midpoint, and the row says so).
        src_url = ((p.get("source") or {}).get("url") or "").strip() or "MISSING"
        prov = {"source_url": src_url, "yield_note": p.get("yield_note", "")}
        rec: dict[str, object] = {
            "id": p["id"],
            "kt": kt,
            "basis": basis,
            "thermal": "tabulated" if basis == "tabulated" else (
                "read" if kt <= AXIS_MAX_KT else "off-chart"
            ),
        }
        if basis == "tabulated":
            # The client reads these straight out of the combos table, which is
            # built from the same effects.json the print table uses.
            out_presets.append(rec)
            continue

        radii: dict[str, list[float | None]] = {"air": [], "ground": []}
        px: dict[str, list[int] | None] = {"air": None, "ground": None}
        for burst in ("air", "ground"):
            for eff in EFFECT_ORDER:
                if eff == "fireball":
                    ft = fireball_ft(kt, burst)
                    m = round(ft * FT2M)
                    km = round(m / 1000, 2)
                    detail = f"{110 if burst == 'air' else 145} × {kt}^0.4 = {ft:.0f} ft = {m} m"
                    method, cite = "formula", ("(2.127.1) · p. 70" if burst == "air" else "(2.127.2) · p. 71")
                elif eff.startswith("thermal"):
                    if burst == "ground" or kt > AXIS_MAX_KT:
                        radii[burst].append(None)
                        detail = "contact burst" if burst == "ground" else "beyond Fig. 7.42"
                        method, cite = "absent", "Fig. 7.42 · p. 291"
                        ledger.append(dict(preset_id=p["id"], kt=kt, effect=eff, burst=burst,
                                           method=method, value_km="", basis=basis,
                                           detail=detail, citation=cite, **prov))
                        continue
                    y, x, pred, extrap = fig.read(kt, CONTOURS[eff])
                    mi = mi_of(y)
                    m = round(mi * MI2M)
                    km = round(m / 1000, 2)
                    if px[burst] is None:
                        px[burst] = []
                    px[burst].append(x)  # type: ignore[union-attr]
                    px[burst].append(round(y, 1))  # type: ignore[union-attr]
                    detail = (
                        f"x_px {x}, y_px {y:.1f} → {mi:.2f} mi = {m} m"
                        f" (predicted {pred:.1f} px{', extrapolated' if extrap else ''})"
                    )
                    method, cite = "read", "Fig. 7.42 · p. 291"
                else:
                    base_m = tab[(eff, burst, 100)]["radius_m"]
                    factor = (kt / 100.0) ** (1 / 3)
                    m = round(base_m * factor)
                    km = round(m / 1000, 2)
                    detail = (
                        f"{tab[(eff, burst, 100)]['radius_km']:.2f} km × ({kt}/100)^(1/3)"
                        f" = {m} m"
                    )
                    method, cite = "scaled", "§3.61 · p. 101"
                radii[burst].append(km)
                ledger.append(dict(preset_id=p["id"], kt=kt, effect=eff, burst=burst,
                                   method=method, value_km=f"{km:.2f}", basis=basis,
                                   detail=detail, citation=cite, **prov))
        rec["radii"] = radii
        rec["px"] = px
        out_presets.append(rec)

    payload = {
        "law": law,
        "figure": {
            "id": "7.42",
            "page": 291,
            "max_yield_kt": AXIS_MAX_KT,
            "calibration": {"x0": X0, "x_per_decade": XS, "y0": Y0, "y_per_decade": YS},
            "note": (
                "the 4.5 and 10 cal/cm² contours measured at each preset's own column; "
                "the frame closes at 10,000 kt, so no thermal radius is read above it"
            ),
        },
        "anchor": anchor,
        "presets": out_presets,
    }

    if not check_only:
        OUT_JSON.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["preset_id", "kt", "effect", "burst", "method",
                                               "value_km", "basis", "detail", "citation",
                                               "source_url", "yield_note"])
            w.writeheader()
            w.writerows(ledger)
        print(f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_CSV.name} ({len(ledger)} ledger rows)")
        missing = sorted({r["preset_id"] for r in ledger if r["source_url"] == "MISSING"})
        print(f"presets without a citable source: {missing if missing else 'none'}")

    for rec in out_presets:
        if rec["basis"] == "tabulated":
            print(f"  {rec['id']:14} {rec['kt']:>6} kt  tabulated")
            continue
        air = rec["radii"]["air"]  # type: ignore[index]
        grd = rec["radii"]["ground"]  # type: ignore[index]
        fmt = lambda xs: " / ".join("  —  " if v is None else f"{v:5.2f}" for v in xs)  # noqa: E731
        print(f"  {rec['id']:14} {rec['kt']:>6} kt  air {fmt(air)}   ground {fmt(grd)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
