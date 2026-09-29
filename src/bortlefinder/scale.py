"""Bortle scale <-> sky surface brightness (SQM) conversions.

Ported from the DarkHours project (mbeher2200/DarkHours, darkhours/darksky.py),
MIT licensed:

    Copyright (c) 2026 DarkHours contributors

The Bortle class can be supplied directly (BORTLE_SQM maps it to a
representative sky surface brightness using the midpoints of DarkHours' own
classification bands), or derived from a satellite-measured zenith
luminance reading via `falchi_luminance_to_sqm` (see `grid.py` for the
coordinate -> luminance lookup that feeds it).
"""

from __future__ import annotations

import math

# (min_sqm, class_number, description) -- darkest first, ported from
# DarkHours darksky.py's `_BORTLE` table.
_BORTLE_BANDS = [
    (22.0, 1, "Excellent dark-sky site"),
    (21.7, 2, "Typical dark-sky site"),
    (21.3, 3, "Rural sky"),
    (20.8, 4, "Rural/suburban transition"),
    (20.0, 5, "Suburban sky"),
    (19.1, 6, "Bright suburban sky"),
    (18.0, 7, "Suburban/urban transition"),
    (17.0, 8, "City sky"),
    (0.0, 9, "Inner-city sky"),
]

# Representative SQM (mag/arcsec^2) per Bortle class: the midpoint of each
# band above (class 1 is open-ended upward, capped at a typical excellent
# reading; class 9 is open-ended downward, floored at a typical inner-city
# reading).
BORTLE_SQM: dict[int, float] = {
    1: 22.15,
    2: 21.85,
    3: 21.50,
    4: 21.05,
    5: 20.40,
    6: 19.55,
    7: 18.55,
    8: 17.50,
    9: 16.50,
}


def bortle_to_sqm(bortle: int) -> float:
    if bortle not in BORTLE_SQM:
        raise ValueError(f"Bortle class must be 1-9, got {bortle!r}")
    return BORTLE_SQM[bortle]


def sqm_to_bortle(sqm: float) -> tuple[int, str]:
    for min_sqm, cls, desc in _BORTLE_BANDS:
        if sqm >= min_sqm:
            return cls, desc
    return 9, _BORTLE_BANDS[-1][2]


# Falchi 2016 atlas calibration, ported verbatim from DarkHours darksky.py.
# _FALCHI_L_NATURAL is DarkHours' own calibrated natural-sky reference
# luminance (not the raw 0.174 mcd/m^2 quoted by the Falchi paper itself);
# _FALCHI_SCALE corrects for the Falchi atlas's DMSP-OLS-era (~2014)
# underestimate relative to VIIRS (Kyba et al. 2017), calibrated by
# DarkHours against reported observer SQM measurements and IDA dark-sky
# park classifications.
_FALCHI_L_NATURAL = 0.252  # mcd/m^2
_FALCHI_SQM_NATURAL = 22.08  # mag/arcsec^2
_FALCHI_SCALE = 3.0


def falchi_luminance_to_sqm(la_mcd_m2: float) -> float:
    """Convert a Falchi 2016 atlas artificial zenith luminance reading
    (mcd/m^2) to total sky surface brightness (mag/arcsec^2).
    """
    if la_mcd_m2 <= 0:
        return _FALCHI_SQM_NATURAL
    scaled = la_mcd_m2 * _FALCHI_SCALE
    return _FALCHI_SQM_NATURAL - 2.5 * math.log10((scaled + _FALCHI_L_NATURAL) / _FALCHI_L_NATURAL)


def nelm_from_sqm(sqm: float) -> float:
    """Naked-eye limiting magnitude for a sky of surface brightness `sqm`
    (mag/arcsec^2), via the standard Schaefer-derived (Unihedron) conversion.
    Ported from DarkHours darkhours/moonlight.py (MIT licensed). This is a
    dark-sky, zenith-pointing estimate only -- it doesn't account for moon
    phase, target altitude, or local obstructions.
    """
    return 7.93 - 5.0 * math.log10(10 ** (4.316 - sqm / 5.0) + 1.0)
