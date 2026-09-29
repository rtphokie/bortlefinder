"""Sanity checks against real, certified International Dark Sky Places
(https://darksky.org/what-we-do/international-dark-sky-places/all-places/).

These need the real light-pollution grid (`bortlefinder-fetch-grid`), which
is a one-time ~684MB download, so they're skipped unless it's already been
fetched -- they won't run in a plain `uv run pytest` on a fresh checkout.

Coordinates are sourced from Wikipedia, not darksky.org itself (which
blocks non-browser requests). Both sites are long-certified, well-known
dark-sky parks, so a bright-city-level reading here would indicate a real
regression rather than an edge-of-scale judgment call -- hence the loose
"<=3" threshold rather than requiring class 1, matching the accuracy
caveat that satellite zenith brightness and the whole-sky Bortle rating
can disagree by a class or more (see grid.py / README "Accuracy").
"""

import pytest

import bortlefinder

pytestmark = pytest.mark.skipif(
    not bortlefinder.grid_available(),
    reason="requires the real light-pollution grid; run `bortlefinder-fetch-grid` first",
)

# (name, lat, lon) -- https://en.wikipedia.org/wiki/Natural_Bridges_National_Monument,
# https://en.wikipedia.org/wiki/Cherry_Springs_State_Park
DARK_SKY_SITES = [
    ("Natural Bridges National Monument, UT (first-ever certified Dark Sky Park, 2007)", 37.6014, -110.0137),
    ("Cherry Springs State Park, PA (Gold-tier certified Dark Sky Park)", 41.6598, -77.8213),
]


@pytest.mark.parametrize("name,lat,lon", DARK_SKY_SITES)
def test_certified_dark_sky_site_reads_as_dark(name, lat, lon):
    estimate = bortlefinder.estimate(lat=lat, lon=lon)
    assert estimate.bortle_class <= 3, f"{name}: expected a dark reading, got Bortle {estimate.bortle_class}"
