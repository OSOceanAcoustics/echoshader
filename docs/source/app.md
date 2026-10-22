# Building an Echoshader application

Echoshader provides a generic, read-only [Panel](https://panel.holoviz.org/) application for exploring calibrated acoustic datasets. It combines reusable visualization elements with a shared ping-time selection, channel and color controls, and vessel-track views where geographic positions are available.

The current application has a fixed HoloViz layout configured with a small YAML file. YAML selects the dataset and sets a few navigation/display options; it does not define an arbitrary graph of visualization elements, controls, or interactions. Future developments will allow application-specific features to be added through optional extensions, enabled and configured through YAML.

## Requirements

The default app expects an xarray Dataset containing `Sv`, a `channel` coordinate, and an increasing `datetime64` `ping_time` coordinate. The `Sv` variable has dimensions `(channel, ping_time, vertical)`, where `vertical` is `range_sample`, `depth`, or `echo_range`. Physical vertical coordinates such as `depth` and `echo_range` should be provided where appropriate. `frequency_nominal`, `latitude`, and `longitude` enable additional labeling and navigation features when available.

The app accepts existing **Zarr** or **NetCDF** datasets. Acoustic processing, calibration, navigation interpolation, and geometric resampling belong upstream, for example in Echopype. The app does not silently modify the acoustic data to make datasets plot-compatible.

## YAML configuration

Save a file named `app_config.yaml`:

```yaml
app:
  title: Echoshader - Application template
  source: survey
  route: basic

data:
  survey:
    type: zarr
    path: /path/to/your/calibrated_Sv.zarr
    label: Acoustic survey

navigation:
  max_pings: 500

display:
  max_range_samples: 1200
```

Change `path` to an existing local Zarr store. To use NetCDF, set `type: netcdf` and provide the corresponding file path. Relative data paths are resolved relative to the YAML file when launched through the application launcher.

`max_pings` limits the displayed ping-time window. `max_range_samples` limits vertical samples in supported dimensions; it is a display sampling control, not a transformation of the stored data.

## Launching the application

From Python:

```python
from echoshader.app import launch

launch("app_config.yaml", port=5007, address="127.0.0.1", show=True)
```

Alternatively, build the Panel template without serving it:

```python
from echoshader.app.builder import build_app
from echoshader.app.config import load_config

config = load_config("app_config.yaml")
app = build_app(config, config_dir=".")
```

The returned object is a `panel.template.FastListTemplate`. The launcher starts a Panel server. Its `port` keyword controls the server port; the `app.port` YAML key is not used by the current launcher.

## Interaction and display

The application offers a selected ping-time interval, linked date controls and vessel-track navigation when positions exist, single-channel and multi-frequency echograms, and a three-channel RGB view. Changing a selection requests the corresponding subset of the dataset.

A tricolor echogram requires three channels on a compatible physical vertical grid. The native Sv data from different transducers may have different physical sample geometries even if they share `range_sample` indices. Use a physically aligned dataset for tricolor visualization; do not treat sample numbers as meters.

## Validation and troubleshooting

Echoshader validates acoustic dataset structure and checks tricolor compatibility separately. An ordinary echogram may be valid even when three channels cannot be combined into an RGB plot.

- **No vessel track:** check for finite `latitude` and `longitude` values aligned with `ping_time`.
- **Mostly empty MVBS:** check whether your dataset includes time bins without recordings; the app preserves missing periods.
- **Tricolor geometry mismatch:** select a common physical geometry dataset, rather than forcing native channels onto one sample-index axis.
- **Slow rendering:** reduce the displayed ping window or prepare an appropriate coarser upstream product. Chunk sizing and display windows affect performance.

See [Visualization elements](elements.md) for standalone use.
