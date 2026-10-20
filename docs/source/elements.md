# Visualization elements

Echoshader provides reusable visualization elements for ocean sonar data. These elements can be used independently in notebooks and can also be composed into interactive applications.

## Available elements

| Element | Description | `ds.eshader` accessor |
| --- | --- | :---: |
| Echogram | Two-dimensional visualization of acoustic backscatter | ✓ |
| Tricolor echogram | RGB visualization combining three acoustic channels | ✓ |
| Track | Vessel or platform trajectory | ✓ |
| Curtain | Three-dimensional curtain visualization of acoustic data | ✓ |
| Histogram | Distribution of acoustic backscatter values | ✓ |
| Table | Summary table for an acoustic dataset | ✓ |
| Curve | Generic one-dimensional curve | — |
| NASC | One-dimensional NASC visualization | — |

The xarray accessor currently exposes echogram, tricolor echogram, track, curtain, histogram, and table visualizations. Curve and NASC are available as standalone elements.

## Echogram

Create a single-channel echogram from an xarray Dataset:

```python
ds.eshader.echogram(
    channel="WBT 400143-15 ES38B_ES",
    vert_dim="depth",
)
```

Multiple channels can also be displayed by passing a list of channel names.

## Tricolor echogram

Combine three channels into an RGB echogram:

```python
ds.eshader.tricolor_echogram(
    channel=[
        "WBT 400143-15 ES18_ES",
        "WBT 400143-15 ES38B_ES",
        "WBT 400143-15 ES120-7C_ES",
    ],
    vmin=-80,
    vmax=-50,
    vert_dim="depth",
)
```

## Track

Visualize the trajectory of a moving platform:

```python
ds.eshader.track()
```

A map tile source can also be selected with the `tile` argument.

## Curtain

Create a three-dimensional curtain visualization:

```python
ds.eshader.curtain(
    channel="WBT 400143-15 ES38B_ES",
    engine="plotly",
)
```

Plotly and PyVista backends are supported.

## Histogram

Visualize the distribution of acoustic backscatter:

```python
ds.eshader.hist()
```

Histograms can be overlaid or displayed separately.

## Table

Create a summary table for the dataset:

```python
ds.eshader.table()
```

## Curve

The curve element provides a simple one-dimensional HoloViews curve for data that do not require the acoustic Dataset accessor.

## NASC

The NASC element provides a one-dimensional visualization of nautical area scattering coefficient (NASC) data.

## Example notebook

Runnable examples for the visualization elements are available in:

[`examples/notebooks/element_examples.ipynb`](https://github.com/echostack-org/echoshader/blob/main/examples/notebooks/element_examples.ipynb)

The notebook demonstrates the individual elements directly. Higher-level interactions such as linked selections and shared controls are documented separately as part of the Echoshader application layer.


## Acoustic dataset validation and geometry

The `ds.eshader` accessor validates the basic acoustic structure. The `Sv` variable must use `(channel, ping_time, vertical)` dimensions with one of `range_sample`, `depth`, or `echo_range` as the vertical dimension. Ping times must be valid, strictly increasing timestamps.

For a direct validation report:

```python
from echoshader.validation import validate_dataset

result = validate_dataset(ds, tricolor_channels=ds.channel.values[:3].tolist())
print(result.vertical_dim, result.tricolor_ready, result.tricolor_reason)
```

**Valid acoustic data do not necessarily permit tricolor rendering.** Three transducers can share `range_sample` indices while having different physical `echo_range` or `depth` geometries. A tricolor image requires a common physical vertical grid. A geometry-matched Sv product or physically gridded MVBS product may meet that requirement, subject to validation; Echoshader does not automatically resample the input.

The elements are built on HoloViews, GeoViews, Plotly, and PyVista. Current echogram plots convert their selected data into plotting arrays; Datashader-based rasterization is not yet implemented.
