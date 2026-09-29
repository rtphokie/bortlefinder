# bortlefinder

Approximate an observer's [Bortle dark-sky class](https://en.wikipedia.org/wiki/Bortle_scale)
from their latitude/longitude, using a locally-built grid derived from the
Falchi et al. (2016) *New World Atlas of Artificial Night Sky Brightness*.

## Usage

```python
import bortlefinder

estimate = bortlefinder.estimate(lat=35.0, lon=-78.6)
print(estimate.bortle_class, estimate.bortle_desc, estimate.sqm)
# 8 City sky 17.75

# Bortle <-> SQM conversions are also available directly:
bortlefinder.bortle_to_sqm(4)      # 21.05
bortlefinder.sqm_to_bortle(21.2)   # (3, 'Rural sky')
```

`estimate()` raises `FileNotFoundError` if the light-pollution grid hasn't
been built yet -- see below.

## Accuracy
This is an estimate of 


What a satellite measures is *zenith* artificial sky brightness. The Bortle
scale is a subjective whole-sky rating dominated by horizon light domes,
which zenith brightness alone doesn't capture. David Lorenz's validation
against 397 nights of paired NPS Night Sky Team observations found real
disagreement -- commonly a full class, worse in the Bortle 5-7 range
(https://djlorenz.github.io/astronomy/lp/bortle.html). Treat the class
returned here as a reasonable starting estimate, not a substitute for a
local dark-sky reading or a real SQM meter. This message is also available
at runtime as `bortlefinder.ACCURACY_CAVEAT`.

## Building the light-pollution grid

The package reads a small (~19MB) `.npz` grid checked in under
`src/bortlefinder/data/`, built once from the ~684MB native-resolution
Falchi atlas GeoTIFF:

```
pip install rasterio numpy
python scripts/build_light_pollution_grid.py
```

Data source: Falchi, F. et al. (2016), "The New World Atlas of Artificial
Night Sky Brightness", archived at GFZ Potsdam
(https://doi.org/10.5880/GFZ.1.4.2016.001), CC BY-NC 4.0.

The Bortle<->SQM table and the Falchi-luminance-to-SQM calibration are
adapted from the [DarkHours](https://github.com/mbeher2200/DarkHours)
project (MIT licensed).

## Development

```
uv sync
uv run python -c "import bortlefinder; print(bortlefinder.estimate(35.0, -78.6))"
```
