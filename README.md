# bortlefinder

Estimate an observer's [Bortle dark-sky class](https://en.wikipedia.org/wiki/Bortle_scale)
from their latitude and longitude.

## Install

```
pip install bortlefinder
```

The light-pollution data behind the estimate is licensed CC BY-NC 4.0 (non-commercial) by its original authors, so it isn't bundled with this package (see the Licensing section below for details). Fetch it once, directly from the source, before first use:

```
pip install bortlefinder[build]
bortlefinder-fetch-grid
```

This downloads the source atlas (~684MB) which is immediately reduced down to a small (~19MB) grid sufficient for purposes here under your platform's user cache directory (`bortlefinder.cache_dir()`). The `build` extra is only needed for this one-time step, not for normal use.

## Usage

```python
import bortlefinder

# Nicholas R. Anderson Observatory, Blacksburg, VA
estimate = bortlefinder.estimate(lat=37.2221, lon=-80.5401)
print(estimate.bortle_class, estimate.bortle_desc, estimate.sqm, estimate.nelm)
# 5 Suburban sky 20.14 5.59

# Bortle <-> SQM (sky quality meter, mag/arcsec^2) conversions are also
# available directly, no grid needed:
bortlefinder.bortle_to_sqm(4)      # 21.05
bortlefinder.sqm_to_bortle(21.2)   # (3, 'Rural sky')
bortlefinder.nelm_from_sqm(21.2)   # 6.23
```

`estimate()` raises `FileNotFoundError` with fetch instructions if the grid
hasn't been fetched yet.

### Return value

`estimate()` returns a `GridEstimate`, a small dataclass with four fields:

| Field          | Type    | Meaning                                                                                                   |
|----------------|---------|-------------------------------------------------------------------------------------------------------------|
| `sqm`          | `float` | Sky surface brightness in mag/arcsec², higher is darker. Read from the light-pollution grid and converted from the Falchi et al. (2016) zenith luminance reading. |
| `bortle_class` | `int`   | Approximate Bortle dark-sky class, 1 (darkest) to 9 (inner-city), derived from `sqm` -- see "Accuracy" below. |
| `bortle_desc`  | `str`   | Short label for `bortle_class`, e.g. `"Rural sky"`.                                                       |
| `nelm`         | `float` | Naked-eye limiting magnitude: the faintest star an average observer could see overhead, at the zenith, with no moon up. Higher means fainter stars are visible (a better sky) -- roughly 6.5-7.0 at Bortle 1, 3-4 at Bortle 8-9. |

## Accuracy

The Bortle class is estimated from a satellite measurement of *artificial zenith sky brightness* -- how bright the sky glows when you look straight up, from light scattered back down by the atmosphere (Falchi et al. 2016, [*New World Atlas of Artificial Night Sky Brightness*](https://doi.org/10.1126/sciadv.1600377)). The Bortle scale itself, though, is a subjective rating of the *whole* sky, and is dominated by light domes sitting low on the horizon rather than by zenith glow. A site can have a dark zenith while still ringed by nearby city lights, or vice versa, so the two don't always agree.

David Lorenz validated this kind of satellite-derived estimate against 397 nights of paired NPS Night Sky Team observations and found real disagreement -- commonly a full class, worse in the Bortle 5-7 range (https://djlorenz.github.io/astronomy/lp/bortle.html). Treat the class returned here as a reasonable starting estimate, not a substitute for a local dark-sky reading or a real SQM meter. 

## Licensing

- **Code**: MIT (see `LICENSE`).
- **Data**: the light-pollution grid, once fetched, comes from Falchi, F. et al. (2016), "The New World Atlas of Artificial Night Sky Brightness", archived at GFZ Potsdam (https://doi.org/10.5880/GFZ.1.4.2016.001), licensed **CC BY-NC 4.0**. Grid data is fetched from the original source to take advantage of any updates there and to respect its license rather than redistribute here. Review that license before fetching the grid if you plan to use `bortlefinder` commercially.

The Bortle<->SQM table and the Falchi-luminance-to-SQM calibration are
adapted from the [DarkHours](https://github.com/mbeher2200/DarkHours)
project (MIT licensed).

## Development

```
uv sync
uv run pytest
```

Tests use a small synthetic grid fixture and don't require fetching the
real atlas.
