import xarray


def select_box(
    ds: xarray.Dataset,
    bounds: tuple | None,
    x_dim: str = "ping_time",
    y_dim: str = "echo_range",
) -> xarray.Dataset:
    """Select a rectangular region from a dataset."""

    if bounds is None:
        return ds

    left, bottom, right, top = bounds

    return ds.sel(
        {
            x_dim: slice(left, right),
            y_dim: slice(
                min(bottom, top),
                max(bottom, top),
            ),
        }
    )