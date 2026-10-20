"""Reusable, read-only HoloViz application shell for acoustic datasets.

Uses Panel for layout/reactivity, HoloViews for selections and overlays,
Echoshader for acoustic elements, and xarray for lazily sliced Zarr data.
This module does NOT import Echodataflow, Prefect, or a YAML builder.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path

import geoviews as gv
import holoviews as hv
import numpy as np
import pandas as pd
import panel as pn
import param
import xarray as xr
from bokeh.models import CustomJSTickFormatter

from echoshader.elements.echogram import echogram, tricolor_echogram
from echoshader.elements.track import track as track_element
from echoshader.validation import validate_dataset

hv.extension("bokeh")
pn.extension("tabulator")


@dataclass
class AcousticSource:
    data: xr.Dataset
    name: str = "Acoustic survey"
    path: Path | None = None
    bottom: pd.DataFrame | None = None
    track: pd.DataFrame | None = None
    max_pings: int = 500
    max_range_samples: int = 1200
    map_width: int = 650
    map_height: int = 400


def _channel_for_frequency(ds, freq):
    names = [str(v) for v in ds.channel.values]
    if "frequency_nominal" not in ds:
        return names[0]
    freqs = np.asarray(ds.frequency_nominal.values, dtype=float).reshape(-1)
    finite = np.flatnonzero(np.isfinite(freqs))
    return names[int(finite[np.argmin(abs(freqs[finite] - freq))])] if len(finite) else names[0]


def _parse_track(source: AcousticSource):
    """Return metadata track if time, latitude, longitude are available."""
    if source.track is not None:
        table = source.track.copy()
    elif {"ping_time", "longitude", "latitude"}.issubset(source.data.variables):
        # Track coordinates only; no acoustic array computed.
        table = pd.DataFrame(
            {
                k: np.asarray(source.data[k].values).reshape(-1)
                for k in ("ping_time", "longitude", "latitude")
            }
        )
    else:
        return None
    required = {"ping_time", "longitude", "latitude"}
    if not required.issubset(table):
        return None
    table = table[list(required)].copy()
    table["ping_time"] = pd.to_datetime(
        table["ping_time"], utc=True, errors="coerce"
    ).dt.tz_localize(None)
    for col in ("longitude", "latitude"):
        table[col] = pd.to_numeric(table[col], errors="coerce")
    return table.dropna().sort_values("ping_time").reset_index(drop=True)


def build_acoustic_app(
    source: AcousticSource,
    *,
    extra_tabs: list[tuple[str, object]] | None = None,
    title: str = "Echoshader",
):
    """Build generic interactive app; optional tabs are composed by caller."""

    longitude_formatter = CustomJSTickFormatter(
        code="""
            return (tick / 6378137 * 180 / Math.PI).toFixed(2) + "°";
        """
    )

    latitude_formatter = CustomJSTickFormatter(
        code="""
            const lat = (2 * Math.atan(Math.exp(tick / 6378137)) - Math.PI / 2);
            return (lat * 180 / Math.PI).toFixed(2) + "°";
        """
    )

    ds = source.data
    dataset_validation = validate_dataset(ds)
    n = ds.sizes["ping_time"]
    if not n:
        raise ValueError("No pings available")
    max_pings = min(max(1, int(source.max_pings)), n)
    times = ds.ping_time.values
    initial = (max(0, n - max_pings), n)
    channels = [str(ch) for ch in ds.channel.values]
    freqs = (
        np.asarray(ds.frequency_nominal.values, dtype=float) if "frequency_nominal" in ds else None
    )
    ordered = (
        [_channel_for_frequency(ds, f) for f in (18000, 38000, 70000, 120000, 200000)]
        if freqs is not None
        else channels
    )
    ordered = list(dict.fromkeys(ordered))
    available = (
        {ch: float(freq) / 1000 for ch, freq in zip(channels, freqs)} if freqs is not None else {}
    )

    # native Panel controls: throttled updates avoid re-rendering while dragging
    timeline = pn.widgets.IntRangeSlider(
        label="Ping interval (entire survey)",
        start=0,
        end=n,
        value=initial,
        step=1,
        sizing_mode="stretch_width",
    )
    color = pn.widgets.RangeSlider(
        label="Sv color range (dB)",
        start=-120,
        end=-20,
        value=(-100, -30),
        step=1,
        sizing_mode="stretch_width",
    )
    cmap = pn.widgets.Select(
        label="Colormap",
        options=["viridis", "jet", "plasma", "inferno", "magma", "cividis", "turbo", "Greys"],
        value="viridis",
        width=165,
    )
    rgb_widgets = [
        pn.widgets.Select(
            label=f"{label} channel",
            options=channels,
            value=_channel_for_frequency(ds, freq)
            if freqs is not None
            else channels[min(i, len(channels) - 1)],
        )
        for i, (label, freq) in enumerate(zip(("Red", "Green", "Blue"), (120000, 38000, 18000)))
    ]

    def bounded(window):
        a, b = map(int, window)
        a = min(max(0, a), n - 1)
        b = min(n, max(a + 1, b))
        if b - a > max_pings:
            b = min(n, a + max_pings)
        return a, b

    # single reactive selection shared by all plots, widgets and the map
    # slider updates are throttled; map actions update state immediately
    class WindowState(param.Parameterized):
        window = param.Tuple(default=initial)

    selection = WindowState()

    time_index = pd.DatetimeIndex(times)

    start_input = pn.widgets.DatetimeInput(
        label="Start time (UTC)",
        value=time_index[initial[0]].to_pydatetime(),
        start=time_index[0].to_pydatetime(),
        end=time_index[-1].to_pydatetime(),
        width=240,
    )

    end_input = pn.widgets.DatetimeInput(
        label="End time (UTC)",
        value=time_index[initial[1] - 1].to_pydatetime(),
        start=time_index[0].to_pydatetime(),
        end=time_index[-1].to_pydatetime(),
        width=240,
    )

    # keep the slider value itself within bounds, not just the plotted subset
    updating = False

    def enforce_window(event):
        nonlocal updating
        if updating:
            return
        a, b = map(int, event.new)
        a = min(max(0, a), n - 1)
        b = min(n, max(a + 1, b))
        if b - a > max_pings:
            previous = tuple(map(int, event.old or initial))
            if a != previous[0] and b == previous[1]:
                b = min(n, a + max_pings)
            else:
                a = max(0, b - max_pings)
        value = (a, b)
        if value != tuple(event.new):
            updating = True
            try:
                timeline.value = value
            finally:
                updating = False

    timeline.param.watch(enforce_window, "value")

    def slider_committed(event):
        value = bounded(event.new)
        if tuple(selection.window) != value:
            selection.window = value

    timeline.param.watch(slider_committed, "value_throttled")

    def move_selection(value):
        """Update one common state and reflect map changes in the slider."""
        value = bounded(value)
        if tuple(selection.window) != value:
            selection.window = value
        if tuple(timeline.value) != value:
            timeline.value = value

    syncing_dates = False

    def update_from_dates(event):
        if syncing_dates or start_input.value is None or end_input.value is None:
            return

        start = pd.Timestamp(start_input.value)
        end = pd.Timestamp(end_input.value)

        if start > end:
            return

        a = int(time_index.searchsorted(start, side="left"))
        b = int(time_index.searchsorted(end, side="right"))

        a = min(max(a, 0), n - 1)
        b = min(max(b, a + 1), n)

        move_selection((a, b))

    start_input.param.watch(update_from_dates, "value")
    end_input.param.watch(update_from_dates, "value")

    def sync_date_inputs(event):
        nonlocal syncing_dates
        a, b = bounded(event.new)

        syncing_dates = True
        try:
            start_input.value = time_index[a].to_pydatetime()
            end_input.value = time_index[b - 1].to_pydatetime()
        finally:
            syncing_dates = False

    selection.param.watch(sync_date_inputs, "window")

    # one shared lazily sliced dataset for every currently selected interval
    # the source itself stays lazily opened and is never loaded in full
    @pn.cache(max_items=8)
    def window_dataset(bounds):
        a, b = bounded(bounds)
        window = ds.isel(ping_time=slice(a, b))
        dim = dataset_validation.vertical_dim
        if dim in window.dims and window.sizes[dim] > source.max_range_samples:
            step = int(np.ceil(window.sizes[dim] / source.max_range_samples))
            window = window.isel({dim: slice(None, None, step)})
        return window

    def xrange(bounds):
        a, b = bounded(bounds)
        start, end = (
            pd.Timestamp(times[a]).to_pydatetime(),
            pd.Timestamp(times[b - 1]).to_pydatetime(),
        )
        return (start, end if end > start else start + dt.timedelta(seconds=1))

    def echogram_view(bounds, clim, palette, *, variable, channel, label):
        w = window_dataset(tuple(bounds))
        if variable not in w:
            return pn.pane.Alert(f"{variable} is not available", alert_type="info")
        vert_dim = next(
            (
                name
                for name in (
                    ("depth",)
                    if dataset_validation.vertical_dim == "depth"
                    else ("echo_range", "depth")
                )
                if name in w
            ),
            dataset_validation.vertical_dim,
        )
        # Reuse the standalone element, which handles regular and irregular grids.
        plot = echogram(
            w,
            channel=channel,
            var_name=variable,
            vert_dim=vert_dim,
        ).opts(
            width=1000,
            height=270,
            cmap=palette,
            clim=tuple(clim),
            xlim=xrange(bounds),
            invert_yaxis=True,
            colorbar=False,
            tools=["hover", "pan", "wheel_zoom", "box_zoom", "reset"],
            title=label,
        )
        if source.bottom is not None and {"time", "depth"}.issubset(source.bottom):
            bottom = source.bottom
            x0, x1 = xrange(bounds)
            mask = pd.to_datetime(bottom["time"], utc=True).between(
                pd.to_datetime(x0, utc=True), pd.to_datetime(x1, utc=True)
            )
            subset = bottom.loc[mask]
            if not subset.empty:
                line = hv.Curve(
                    (pd.to_datetime(subset["time"]), subset["depth"]),
                    kdims="ping_time",
                    vdims=vert_dim,
                ).opts(color="black", line_width=2)
                plot = (plot * line).opts(xlim=xrange(bounds), framewise=True)
        return plot

    def multifrequency(bounds, clim, palette):
        return pn.Column(
            *[
                echogram_view(
                    bounds,
                    clim,
                    palette,
                    variable="Sv",
                    channel=ch,
                    label=f"Sv — {available.get(ch, ch)}{' kHz' if ch in available else ''}",
                )
                for ch in ordered
            ],
            sizing_mode="stretch_width",
        )

    def tricolor(bounds, clim, red, green, blue):
        w = window_dataset(tuple(bounds))
        # Keep geometry variables: w[["Sv"]] discards native echo_range/depth.
        dim = next(
            (
                name
                for name in (
                    ("depth",)
                    if dataset_validation.vertical_dim == "depth"
                    else ("echo_range", "depth")
                )
                if name in w
            ),
            dataset_validation.vertical_dim,
        )
        status = validate_dataset(w, tricolor_channels=[red, green, blue], vert_dim=dim)
        if not status.tricolor_ready:
            return pn.pane.Alert(status.tricolor_reason, alert_type="warning")
        return tricolor_echogram(
            w,
            channel=[red, green, blue],
            vmin=float(clim[0]),
            vmax=float(clim[1]),
            var_name="Sv",
            vert_dim=dim,
        ).opts(
            width=1000,
            height=450,
            framewise=True,
            xlim=xrange(bounds),
            tools=["hover", "pan", "wheel_zoom", "reset"],
        )

    def selection_label(bounds):
        a, b = bounded(bounds)
        return f"**Selected:** {a:,}–{b - 1:,} ({b - a:,} pings) · {str(times[a])[:19]} → {str(times[b - 1])[:19]} UTC"

    track_data = _parse_track(source)
    map_widget = pn.pane.Alert(
        "No latitude/longitude coordinates available.",
        alert_type="info",
    )
    if track_data is not None and len(track_data):
        # reuse the standalone Echoshader track element for ping positions
        # render its positions with HoloViews in Web Mercator coordinates:
        # this avoids the GeoViews/Cartopy projection error in tile overlays
        track_ds = ds
        if source.track is not None:
            indexed = track_data.set_index("ping_time").reindex(pd.to_datetime(times))
            track_ds = ds.assign(
                longitude=("ping_time", indexed.longitude.to_numpy()),
                latitude=("ping_time", indexed.latitude.to_numpy()),
            )
        track_plot = track_element(track_ds, tile=None)
        candidates = track_plot.traverse(lambda obj: obj, [gv.Points])
        if not candidates:
            raise ValueError("Track element has no selectable Points layer")
        track_points = candidates[0]
        rows = pd.DataFrame(
            {
                "longitude": track_points.dimension_values("Longitude"),
                "latitude": track_points.dimension_values("Latitude"),
                "ping_index": track_points.dimension_values("Ping Index"),
            }
        )
        latitude = np.clip(rows.latitude.to_numpy(dtype=float), -85.0, 85.0)
        rows["x"] = 6378137.0 * np.deg2rad(rows.longitude.to_numpy(dtype=float))
        rows["y"] = 6378137.0 * np.log(np.tan(np.pi / 4 + np.deg2rad(latitude) / 2))

        points = hv.Points(rows, kdims=["x", "y"], vdims=["ping_index", "longitude", "latitude"])
        selectable = points.opts(
            size=6,
            color="gray",
            alpha=0.7,
            tools=["hover", "box_select", "tap", "pan", "wheel_zoom", "reset"],
        )
        path = hv.Path([rows[["x", "y"]].to_numpy()]).opts(
            color="black",
            line_width=1,
        )
        tiles = hv.Tiles("https://tile.openstreetmap.org/{Z}/{X}/{Y}.png")
        x0, x1 = rows.x.min(), rows.x.max()
        y0, y1 = rows.y.min(), rows.y.max()
        xpad = max((x1 - x0) * 0.1, 200)
        ypad = max((y1 - y0) * 0.1, 200)
        base = (tiles * path * selectable).opts(
            responsive=True,
            min_height=500,
            data_aspect=None,
            xlim=(x0 - xpad, x1 + xpad),
            ylim=(y0 - ypad, y1 + ypad),
            show_grid=False,
            xlabel="Longitude",
            ylabel="Latitude",
            xaxis="bottom",
            yaxis="left",
            xformatter=longitude_formatter,
            yformatter=latitude_formatter,
        )
        selected_stream = hv.streams.Selection1D(source=points)

        def select_indices(event):
            indices = np.asarray(event.new if event.new is not None else [], dtype=int)
            if not len(indices):
                return
            ping_indices = rows.iloc[indices].ping_index.to_numpy(dtype=int)
            a, b = int(ping_indices.min()), int(ping_indices.max()) + 1
            if b - a > max_pings:
                midpoint = (a + b) // 2
                a = max(0, min(n - max_pings, midpoint - max_pings // 2))
                b = a + max_pings
            move_selection((a, b))

        selected_stream.param.watch(select_indices, "index")

        def highlighted_map(bounds):
            a, b = bounded(bounds)
            selected = rows.loc[rows.ping_index.between(a, b - 1)]

            highlight = hv.Points(selected, kdims=["x", "y"]).opts(color="dodgerblue", size=6)

            return (base * highlight).opts(
                xlabel="Longitude (°)",
                ylabel="Latitude (°)",
                xformatter=longitude_formatter,
                yformatter=latitude_formatter,
                xaxis="bottom",
                yaxis="left",
            )

        map_widget = pn.panel(
            pn.bind(highlighted_map, selection.param.window),
            sizing_mode="stretch_both",
            min_height=520,
        )

    meta = [
        f"### {source.name}",
        f"**Pings:** {n:,}",
        f"**Coverage:** {str(times[0])[:19]} → {str(times[-1])[:19]} UTC",
        f"**Channels:** {len(channels)}",
    ]
    if source.path is not None:
        meta.append(f"**File:** `{source.path.name}`")
    meta.extend(
        ["### Frequencies"]
        + [
            f"- {available[ch]:g} kHz: `{ch}`" if ch in available else f"- `{ch}`"
            for ch in channels
        ]
    )

    # expose all source metadata without filling the sidebar with long histories
    attributes = {k: v for k, v in ds.attrs.items() if k.lower() != "history"}
    details = []
    if attributes:
        details.append(
            (
                "Dataset attributes",
                pn.pane.Markdown(
                    "\n\n".join(
                        f"**{key}**\n\n```text\n{value}\n```" for key, value in attributes.items()
                    )
                ),
            )
        )
    history = next((v for k, v in ds.attrs.items() if k.lower() == "history"), None)
    if history is not None:
        details.append(("History", pn.pane.Str(str(history))))

    interval = selection.param.window
    clim = color.param.value_throttled
    optional_tabs = []
    for tab_name, content in extra_tabs or []:
        # Optional recipes may provide a native Panel object or a factory
        # that receives the two shared reactive Parameter references.
        optional_tabs.append((tab_name, content(interval, clim) if callable(content) else content))

    visualization_controls = pn.Row(
        pn.Column(color, width=310),
        pn.Column(cmap, width=180),
        sizing_mode="stretch_width",
    )

    tabs = pn.Tabs(
        (
            "Multi-frequency",
            pn.Column(
                visualization_controls,
                pn.bind(multifrequency, interval, clim, cmap.param.value),
            ),
        ),
        (
            "Tricolor",
            pn.Column(
                pn.Row(*rgb_widgets),
                pn.bind(tricolor, interval, clim, *(widget.param.value for widget in rgb_widgets)),
            ),
        ),
        *optional_tabs,
        dynamic=True,
        sizing_mode="stretch_width",
    )
    sidebar = pn.Column(
        pn.pane.Markdown("\n\n".join(meta)),
        pn.Accordion(*details, active=[], sizing_mode="stretch_width")
        if details
        else pn.Spacer(height=0),
        sizing_mode="stretch_width",
    )
    navigator = pn.Column(
        "### Select acoustic interval",
        pn.bind(selection_label, interval),
        timeline,
        pn.Row(start_input, end_input),
        sizing_mode="stretch_width",
    )
    map_panel = pn.Column(
        "### Ship track",
        pn.Row(
            map_widget,
            sizing_mode="stretch_both",
            align="center",
        ),
        sizing_mode="stretch_both",
        margin=0,
    )
    # equal-width columns and equal-height cards for spatial/temporal selection
    navigation_row = pn.GridBox(
        pn.Card(navigator, hide_header=True, min_height=650, sizing_mode="stretch_both"),
        pn.Card(map_panel, hide_header=True, min_height=650, sizing_mode="stretch_both"),
        ncols=2,
        sizing_mode="stretch_width",
    )
    template = pn.template.FastListTemplate(
        title=title,
        sidebar_width=400,
        sidebar=[sidebar],
        main=[navigation_row, tabs],
    )
    return template
