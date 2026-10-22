"""Tests for the YAML application builder and launcher."""

import numpy as np
import panel as pn
import pytest
import xarray as xr
import yaml

from echoshader.app.builder import build_app
from echoshader.app.config import load_config
from echoshader.app.launcher import launch


def make_dataset():
    return xr.Dataset(
        {"Sv": (("channel", "ping_time", "echo_range"), np.ones((3, 5, 10)))},
        coords={
            "channel": ["18", "38", "120"],
            "ping_time": np.array(
                [
                    "2026-01-01T00:00:00",
                    "2026-01-01T00:00:01",
                    "2026-01-01T00:00:02",
                    "2026-01-01T00:00:03",
                    "2026-01-01T00:00:04",
                ],
                dtype="datetime64[ns]",
            ),
            "echo_range": np.arange(10),
        },
    )


def test_load_config(tmp_path):
    path = tmp_path / "app_config.yaml"
    path.write_text(yaml.safe_dump({"app": {"title": "Test app"}}), encoding="utf-8")
    assert load_config(path)["app"]["title"] == "Test app"


def test_load_config_requires_mapping(tmp_path):
    path = tmp_path / "app_config.yaml"
    path.write_text("- one\n- two\n", encoding="utf-8")
    with pytest.raises(TypeError, match="Application configuration must be a YAML mapping"):
        load_config(path)


def test_build_app():
    config = {
        "app": {"title": "Test app", "source": "survey"},
        "data": {"survey": {"label": "Test survey"}},
        "navigation": {"max_pings": 3},
    }
    app = build_app(config, datasets={"survey": make_dataset()})
    assert isinstance(app, pn.template.FastListTemplate)


def test_launch(monkeypatch, tmp_path):
    dataset_path = tmp_path / "survey.nc"
    make_dataset().to_netcdf(dataset_path)
    config_path = tmp_path / "app_config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "app": {"title": "Test app", "source": "survey", "route": "basic"},
                "data": {"survey": {"type": "netcdf", "path": "survey.nc"}},
            }
        ),
        encoding="utf-8",
    )
    called = {}

    def fake_serve(apps, **kwargs):
        called["apps"] = apps
        called["kwargs"] = kwargs
        return "server"

    monkeypatch.setattr(pn, "serve", fake_serve)
    result = launch(config_path, port=5007, address="127.0.0.1", show=False)

    assert result == "server"
    assert "basic" in called["apps"]
    assert callable(called["apps"]["basic"])
    assert isinstance(called["apps"]["basic"](), pn.template.FastListTemplate)
    assert called["kwargs"]["port"] == 5007
    assert called["kwargs"]["address"] == "127.0.0.1"
    assert called["kwargs"]["show"] is False


def test_build_app_from_zarr(tmp_path):
    dataset_path = tmp_path / "survey.zarr"
    make_dataset().to_zarr(dataset_path, mode="w")

    config = {
        "app": {"title": "Test Zarr app", "source": "survey"},
        "data": {
            "survey": {
                "type": "zarr",
                "path": str(dataset_path),
            }
        },
    }

    app = build_app(config)

    assert isinstance(app, pn.template.FastListTemplate)


def test_build_app_invalid_dataset():
    ds = make_dataset().drop_vars("Sv")

    config = {
        "app": {"title": "Test app", "source": "survey"},
        "data": {"survey": {"label": "Invalid survey"}},
    }

    with pytest.raises(ValueError, match="Sv"):
        build_app(config, datasets={"survey": ds})
