"""Coordinate -> approximate Bortle class, from a locally-built light-pollution grid.

Data source: Falchi, F. et al. (2016), "The New World Atlas of Artificial
Night Sky Brightness", archived at GFZ Potsdam
(https://doi.org/10.5880/GFZ.1.4.2016.001), **CC BY-NC 4.0** (attribution,
non-commercial). Because that license doesn't permit commercial
redistribution, this package never bundles or hosts a mirror of the data:
`bortlefinder._build.fetch()` downloads it directly from GFZ Potsdam the
first time it's needed and reduces it to the small grid this module reads,
cached under the platform's user cache directory (see `cache_dir()`). Only
that one-time fetch needs rasterio; normal package use does not -- see
`_build.py` for how the ~684MB native-resolution GeoTIFF is downloaded once
and reduced.

DarkHours (mbeher2200/DarkHours) uses this same atlas as its fallback
light-pollution source, and avoids any raster-reading dependency
(rasterio/GDAL) at runtime by pre-tiling its source rasters into a
raw-binary format read with plain numpy (see its gridbuild.py/gridraster.py);
this module follows the same split.

CAVEAT: what a satellite measures is *zenith* artificial sky brightness.
The Bortle scale is a subjective whole-sky rating dominated by horizon
light domes, which zenith brightness alone does not capture. David Lorenz's
validation against 397 nights of paired NPS Night Sky Team observations
found real disagreement -- commonly a full class, worse in the Bortle 5-7
range (https://djlorenz.github.io/astronomy/lp/bortle.html). Treat the
class returned here as a reasonable starting estimate, not a substitute for
a local dark-sky reading or a real SQM meter.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .scale import falchi_luminance_to_sqm, nelm_from_sqm, sqm_to_bortle

DATA_FILENAME = "light_pollution_grid.npz"
ACCURACY_CAVEAT = (
    "Bortle class estimated from satellite zenith brightness (Falchi et al. 2016); "
    "can differ from the subjective whole-sky Bortle class by a class or more, "
    "especially near cities -- see grid.py."
)


@dataclass
class GridEstimate:
    """Result of a coordinate lookup, as returned by `estimate_at()`.

    Attributes:
        sqm: Sky surface brightness in mag/arcsec^2 (higher = darker), as
            read from the light-pollution grid and converted from the
            Falchi et al. (2016) zenith luminance reading.
        bortle_class: Approximate Bortle dark-sky class, 1 (darkest) to 9
            (inner-city), derived from `sqm` -- see the module-level CAVEAT
            above and README "Accuracy" for how this can differ from a
            true whole-sky Bortle rating.
        bortle_desc: Short human-readable label for `bortle_class` (e.g.
            "Rural sky"), from the same table as `bortle_to_sqm`/
            `sqm_to_bortle` in `scale.py`.
        nelm: Naked-eye limiting magnitude -- the faintest star magnitude
            visible overhead to an average observer under this sky
            brightness, at the zenith, with no moon up. Higher is fainter
            (better); roughly 6.5-7.0 at Bortle 1, 4-5 at Bortle 7-8. See
            `scale.nelm_from_sqm` for the conversion and its caveats.
    """

    sqm: float
    bortle_class: int
    bortle_desc: str
    nelm: float


def cache_dir() -> Path:
    from platformdirs import user_cache_dir

    return Path(user_cache_dir("bortlefinder"))


def _grid_path() -> Path:
    return cache_dir() / DATA_FILENAME


def grid_available() -> bool:
    return _grid_path().is_file()


@lru_cache(maxsize=1)
def _load_grid():
    import numpy as np

    path = _grid_path()
    if not path.is_file():
        raise FileNotFoundError(
            f"No light-pollution grid found at {path}.\n"
            "This data is CC BY-NC 4.0 (Falchi et al. 2016) and isn't bundled "
            "with bortlefinder -- fetch it once with:\n"
            "  pip install bortlefinder[build]\n"
            "  bortlefinder-fetch-grid\n"
            "(or call bortlefinder.fetch_grid() from Python). One-time ~684MB download."
        )
    with np.load(path) as npz:
        return {
            "luminance": npz["luminance"],
            "lat_north": float(npz["lat_north"]),
            "lon_west": float(npz["lon_west"]),
            "res_deg": float(npz["res_deg"]),
        }


def estimate_at(lat: float, lon: float) -> GridEstimate:
    """Nearest-cell lookup of artificial sky brightness at (lat, lon), converted
    to SQM and an approximate Bortle class. Raises FileNotFoundError if the
    grid hasn't been fetched yet (see module docstring).
    """
    grid = _load_grid()
    luminance = grid["luminance"]
    rows, cols = luminance.shape
    res = grid["res_deg"]

    row = int(round((grid["lat_north"] - lat) / res))
    col = int(round((lon - grid["lon_west"]) / res)) % cols
    row = max(0, min(rows - 1, row))

    la = float(luminance[row, col])
    sqm = falchi_luminance_to_sqm(la)
    bortle_class, bortle_desc = sqm_to_bortle(sqm)
    nelm = nelm_from_sqm(sqm)
    return GridEstimate(sqm=sqm, bortle_class=bortle_class, bortle_desc=bortle_desc, nelm=nelm)
