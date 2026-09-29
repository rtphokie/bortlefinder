# bortlefinder

Estimate an observer's [Bortle dark-sky class](https://en.wikipedia.org/wiki/Bortle_scale)
from their latitude and longitude.

## Install

```
pip install bortlefinder
```

The light-pollution data behind the estimate is licensed CC BY-NC 4.0 (non-commercial) by its original authors, so it isn't bundled with this package (see licensing setion below for details). Fetch it once, directly from the source, before first use:

```
pip install bortlefinder[build]
bortlefinder-fetch-grid
```

This downloads the source atlas (~684MB) which is immediately reduced down to a small (~19MB) grid sufficient for purposes here under your platform's user cache directory (`bortlefinder.cache_dir()`). The `build` extra is only needed for this one-time step, not for normal use.

## Usage

```python
import bortlefinder

estimate = bortlefinder.estimate(lat=35.0, lon=-78.6)
print(estimate.bortle_class, estimate.bortle_desc, estimate.sqm)
# 8 City sky 17.75

# Bortle <-> SQM (sky quality meter, mag/arcsec^2) conversions are also
# available directly, no grid needed:
bortlefinder.bortle_to_sqm(4)      # 21.05
bortlefinder.sqm_to_bortle(21.2)   # (3, 'Rural sky')
```

`estimate()` raises `FileNotFoundError` with fetch instructions if the grid
hasn't been fetched yet.

## Accuracy

The Bortle class is estimated from a satellite measurement of *artificial zenith sky brightness* -- how bright the sky glows when you look straight up, from light scattered back down by the atmosphere (Falchi et al. 2016, *New World Atlas of Artificial Night Sky Brightness*). The Bortle scale itself, though, is a subjective rating of the *whole* sky, and is dominated by light domes sitting low on the horizon rather than by zenith glow. A site can have a dark zenith while still ringed by nearby city lights, or vice versa, so the two don't always agree.

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
