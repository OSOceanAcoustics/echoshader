# Echoshader

Echoshader is an open-source Python library for interactive ocean sonar visualization, built around the [HoloViz](https://holoviz.org/) ecosystem. It works alongside [Echopype](https://echopype.readthedocs.io/), which handles acoustic data conversion, calibration, and processing.

## Two ways to use Echoshader

**Standalone visualization elements** expose echograms, three-channel RGB echograms, vessel tracks, 3-D curtains, histograms, tables, curves, and NASC plots. They can be used in notebooks and scripts. See [Visualization elements](elements.md).

**A YAML-configured Panel application** combines selected acoustic visualizations with interactive navigation and shared controls. The current app uses a generic, predefined HoloViz layout rather than YAML-defined arbitrary controls or processing pipelines. See [Building an Echoshader application](app.md).

## Acoustic data and processing

Echoshader visualizes xarray acoustic datasets, including Zarr and NetCDF products. Calibration, geometry matching, and MVBS calculations should be performed upstream, such as with Echopype. Echoshader validates required coordinates and reports whether a dataset supports three-channel tricolor rendering; it does not silently regrid or modify acoustic measurements.

## Examples

The [element example notebook](https://github.com/echostack-org/echoshader/blob/main/examples/notebooks/element_examples.ipynb) demonstrates visualization elements. The [application example configuration](https://github.com/echostack-org/echoshader/blob/main/examples/app/app_config.yaml) shows the YAML keys used by the generic Panel app. Update its dataset path for your environment.
