import numpy as np
import pytest

import bortlefinder
from bortlefinder import grid as grid_module


def test_bortle_sqm_roundtrip_midpoints():
    for bortle, sqm in bortlefinder.BORTLE_SQM.items():
        cls, _desc = bortlefinder.sqm_to_bortle(sqm)
        assert cls == bortle


def test_bortle_to_sqm_rejects_out_of_range():
    with pytest.raises(ValueError):
        bortlefinder.bortle_to_sqm(0)
    with pytest.raises(ValueError):
        bortlefinder.bortle_to_sqm(10)


def test_estimate_at_raises_without_a_fetched_grid(tmp_path, monkeypatch):
    monkeypatch.setattr(grid_module, "cache_dir", lambda: tmp_path)
    grid_module._load_grid.cache_clear()

    assert not bortlefinder.grid_available()
    with pytest.raises(FileNotFoundError):
        bortlefinder.estimate(lat=0.0, lon=0.0)


@pytest.fixture
def synthetic_grid(tmp_path, monkeypatch):
    """A tiny 4x4 grid standing in for the real (fetched) Falchi grid: bright
    in one corner (simulating a city), dark everywhere else.
    """
    monkeypatch.setattr(grid_module, "cache_dir", lambda: tmp_path)
    grid_module._load_grid.cache_clear()

    luminance = np.zeros((4, 4), dtype=np.float32)
    luminance[0, 0] = 50.0  # bright corner -> lat_north=10, lon_west=-10
    np.savez_compressed(
        tmp_path / grid_module.DATA_FILENAME,
        luminance=luminance,
        lat_north=np.float32(10.0),
        lon_west=np.float32(-10.0),
        res_deg=np.float32(5.0),
    )
    yield
    grid_module._load_grid.cache_clear()


def test_estimate_at_bright_cell_is_low_bortle_class(synthetic_grid):
    assert bortlefinder.grid_available()
    estimate = bortlefinder.estimate(lat=9.0, lon=-9.0)  # nearest cell: row 0, col 0
    assert estimate.bortle_class >= 8
    assert estimate.nelm == bortlefinder.nelm_from_sqm(estimate.sqm)


def test_estimate_at_dark_cell_is_pristine(synthetic_grid):
    estimate = bortlefinder.estimate(lat=-9.0, lon=9.0)  # nearest cell: row 3, col 3
    assert estimate.bortle_class == 1
    assert estimate.nelm == bortlefinder.nelm_from_sqm(estimate.sqm)


def test_nelm_from_sqm_darker_sky_means_fainter_limiting_magnitude():
    dark_nelm = bortlefinder.nelm_from_sqm(bortlefinder.bortle_to_sqm(1))
    bright_nelm = bortlefinder.nelm_from_sqm(bortlefinder.bortle_to_sqm(9))
    assert dark_nelm > bright_nelm
