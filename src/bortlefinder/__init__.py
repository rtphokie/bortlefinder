"""Approximate an observer's Bortle dark-sky class from their coordinates.

    >>> import bortlefinder
    >>> # Nicholas R. Anderson Observatory, Blacksburg, VA
    >>> estimate = bortlefinder.estimate(lat=37.2221, lon=-80.5401)
    >>> estimate.bortle_class, estimate.bortle_desc, estimate.nelm
    (5, 'Suburban sky', 5.59)

`estimate()` returns a `GridEstimate` -- see its docstring (in `grid.py`)
for what each field means, including `nelm`, the naked-eye limiting
magnitude implied by that sky brightness.

The first call needs the light-pollution grid fetched once -- see
`fetch_grid()` and `grid.py` for why it isn't bundled with the package.
"""

from .grid import ACCURACY_CAVEAT, GridEstimate, cache_dir, estimate_at, grid_available
from .scale import BORTLE_SQM, bortle_to_sqm, nelm_from_sqm, sqm_to_bortle

estimate = estimate_at


def fetch_grid(force: bool = False):
    """Download and cache the light-pollution grid `estimate()` needs.
    Requires the `build` extra (`pip install bortlefinder[build]`). One-time
    ~684MB download of CC BY-NC 4.0 data from GFZ Potsdam; see `grid.py`.
    """
    from ._build import fetch

    return fetch(force=force)


__all__ = [
    "estimate",
    "estimate_at",
    "fetch_grid",
    "grid_available",
    "cache_dir",
    "GridEstimate",
    "ACCURACY_CAVEAT",
    "BORTLE_SQM",
    "bortle_to_sqm",
    "sqm_to_bortle",
    "nelm_from_sqm",
]
