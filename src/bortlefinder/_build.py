"""Download and build the light-pollution grid `grid.py` reads at runtime.

Source: Falchi, F. et al. (2016), "The New World Atlas of Artificial Night
Sky Brightness", archived at GFZ Potsdam
(https://doi.org/10.5880/GFZ.1.4.2016.001), **CC BY-NC 4.0** (attribution,
non-commercial). This is a ~684MB zip download containing a native ~30
arcsec (~0.93km) resolution GeoTIFF. Because that license doesn't permit
commercial redistribution, `bortlefinder` never bundles this data or hosts
a mirror of it: this module downloads it directly from GFZ Potsdam, once,
the first time `fetch()` runs, and reduces it locally to a small
(~19MB) grid cached under the platform's user cache directory (see
`grid.CACHE_DIR`). Only this build step needs rasterio; normal package use
(`bortlefinder.estimate(...)`) does not.

The block-mean reduction to ~0.05 degree (~5.6km) cells is justified
because this data already represents post-atmospheric-scattering sky
brightness, which is physically smooth over a few km; it also keeps peak
memory to one row-strip rather than the ~2.9GB full decompressed grid.
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
import zipfile
from pathlib import Path

from .grid import DATA_FILENAME, cache_dir

FALCHI_ZIP_URL = "https://datapub.gfz-potsdam.de/download/10.5880.GFZ.1.4.2016.001/World_Atlas_2015.zip"
TARGET_RES_DEG = 0.05


def _download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"already downloaded: {dest} ({dest.stat().st_size >> 20} MB)")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {url}")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as resp, open(tmp, "wb") as f:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 1 << 20
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                print(f"\r  {downloaded >> 20} / {total >> 20} MB ({pct:.0f}%)", end="", flush=True)
    print()
    tmp.rename(dest)


def _extract_tif(zip_path: Path, dest_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        tif_names = [n for n in zf.namelist() if n.lower().endswith(".tif")]
        if not tif_names:
            raise RuntimeError(f"no .tif found in {zip_path}")
        # Prefer the artificial-brightness band over any ancillary rasters.
        name = sorted(tif_names, key=len)[0]
        out_path = dest_dir / Path(name).name
        if out_path.exists():
            print(f"already extracted: {out_path}")
            return out_path
        print(f"extracting {name}")
        with zf.open(name) as src, open(out_path, "wb") as dst:
            dst.write(src.read())
    return out_path


def _reduce_to_grid(tif_path: Path, out_path: Path, target_res_deg: float) -> None:
    import numpy as np
    import rasterio
    from rasterio.windows import Window

    with rasterio.open(tif_path) as ds:
        transform = ds.transform
        if transform.b != 0 or transform.d != 0:
            raise ValueError("source raster is rotated/sheared; expected a plain north-up grid")
        west, north = float(transform.c), float(transform.f)
        x_res, y_res = float(transform.a), float(-transform.e)
        width, height = ds.width, ds.height

        block = max(1, round(target_res_deg / y_res))
        block_x = max(1, round(target_res_deg / x_res))
        out_rows = height // block
        out_cols = width // block_x
        actual_res_deg = block * y_res

        print(
            f"source: {width}x{height} @ {x_res:.6f} deg/px  ->  "
            f"{out_cols}x{out_rows} @ {actual_res_deg:.4f} deg/px "
            f"(block {block_x}x{block})"
        )

        out = np.zeros((out_rows, out_cols), dtype=np.float32)
        for out_row in range(out_rows):
            row0 = out_row * block
            strip = ds.read(1, window=Window(0, row0, width, block)).astype(np.float32)
            if ds.nodata is not None:
                strip = np.where(strip == ds.nodata, 0.0, strip)
            usable_cols = out_cols * block_x
            strip = strip[:, :usable_cols]
            # block-mean: reshape to (block_rows, out_cols, block_x) and average both axes
            reshaped = strip.reshape(strip.shape[0], out_cols, block_x)
            out[out_row, :] = reshaped.mean(axis=(0, 2))
            if out_row % 100 == 0 or out_row == out_rows - 1:
                print(f"\r  row {out_row + 1}/{out_rows} ({(out_row + 1) / out_rows * 100:.0f}%)", end="", flush=True)
        print()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_path,
        luminance=out,
        lat_north=np.float32(north),
        lon_west=np.float32(west),
        res_deg=np.float32(actual_res_deg),
    )
    print(f"wrote {out_path} ({out_path.stat().st_size >> 20} MB)")


def fetch(force: bool = False) -> Path:
    """Download the Falchi atlas (once) and build the small grid `grid.py`
    reads, caching both under the user cache directory. Returns the path to
    the built grid. Requires the `build` extra (`pip install bortlefinder[build]`).
    """
    out_path = cache_dir() / DATA_FILENAME
    if out_path.is_file() and not force:
        print(f"grid already built: {out_path}")
        return out_path

    scratch = cache_dir() / "build"
    zip_path = scratch / "World_Atlas_2015.zip"
    _download(FALCHI_ZIP_URL, zip_path)
    tif_path = _extract_tif(zip_path, scratch)
    _reduce_to_grid(tif_path, out_path, TARGET_RES_DEG)
    print(
        f"\nDone. Raw download/extract left in {scratch} (delete freely; "
        f"only {out_path} is read at runtime)."
    )
    return out_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="bortlefinder-fetch-grid",
        description=(
            "Download the Falchi et al. (2016) light-pollution atlas (CC BY-NC 4.0, "
            "~684MB, one time) and build the small grid bortlefinder.estimate() reads."
        ),
    )
    parser.add_argument(
        "--force", action="store_true", help="re-download and rebuild even if a cached grid already exists"
    )
    args = parser.parse_args(argv)
    fetch(force=args.force)


if __name__ == "__main__":
    sys.exit(main())
