"""Build the default HoloViz application from YAML configuration.

Elements remain standalone in :mod:`echoshader.elements`.
"""

from __future__ import annotations

import os
from pathlib import Path

import xarray as xr

from echoshader.validation import validate_dataset

from .holoviz import AcousticSource, build_acoustic_app
from .registry import EXTENSIONS


def _data_path(value: str, config_dir: str | Path | None) -> Path:
    path = Path(os.path.expandvars(os.path.expanduser(str(value))))
    if not path.is_absolute() and config_dir is not None:
        path = Path(config_dir) / path
    return path.resolve()


def build_app(
    config: dict,
    datasets: dict | None = None,
    context: dict | None = None,
    *,
    config_dir: str | Path | None = None,
):
    """Build the default Echoshader app with optional extensions."""

    app = config.get("app", {})
    name = app.get("source", "survey")
    sources = config.get("data", {})
    if name not in sources and (not datasets or name not in datasets):
        raise ValueError(f"Missing data source {name!r}")

    settings = sources.get(name, {})
    path = _data_path(settings["path"], config_dir) if "path" in settings else None
    if datasets and name in datasets:
        ds = datasets[name]
    else:
        if path is None or not path.exists():
            raise FileNotFoundError(f"Acoustic dataset not found: {path}")
        kind = settings.get("type", "netcdf").lower()
        if kind == "zarr":
            ds = xr.open_zarr(path)
        elif kind in ("netcdf", "nc"):
            ds = xr.open_dataset(path, chunks="auto")
        else:
            raise ValueError(f"Unsupported acoustic source: {kind!r}")

    # validate the input dataset before building the application
    validate_dataset(ds)

    navigation = config.get("navigation", {})
    display = config.get("display", {})
    max_pings = int(navigation.get("max_pings", 500))
    max_range_samples = int(display.get("max_range_samples", 1200))

    extra_tabs = []
    bottom = None
    for extension_name, extension_config in config.get("extensions", {}).items():
        if extension_name not in EXTENSIONS:
            raise ValueError(f"Unknown extension {extension_name!r}")
        factory = EXTENSIONS[extension_name]()
        options = extension_config or {}
        root = _data_path(options.get("root", str(path.parent.parent) if path else "."), config_dir)
        extension_bottom, tabs = factory(
            ds=ds,
            root=root,
            config=options,
            max_pings=max_pings,
            max_range_samples=max_range_samples,
        )
        if extension_bottom is not None:
            bottom = extension_bottom
        extra_tabs.extend(tabs)

    source = AcousticSource(
        data=ds,
        name=str(settings.get("label", name)),
        path=path,
        bottom=bottom,
        max_pings=max_pings,
        max_range_samples=max_range_samples,
        map_width=int(display.get("map_width", 650)),
        map_height=int(display.get("map_height", 400)),
    )
    return build_acoustic_app(source, extra_tabs=extra_tabs, title=app.get("title", "Echoshader"))
