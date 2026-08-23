import holoviews
import numpy
import xarray


def echogram(
    ds: xarray.Dataset,
    channel: str | list[str],
    var_name: str = "Sv",
    x_dim: str = "ping_time",
    vert_dim: str = "echo_range",
):
    """
    Create single- or multi-channel echograms.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing the variable to visualize.
    channel : str or list[str]
        Channel or channels to plot.
    var_name : str, optional
        Name of the variable to visualize. Default is ``"Sv"``.
    x_dim : str, optional
        Name of the horizontal dimension. Default is ``"ping_time"``.
    vert_dim : str, optional
        Name of the vertical dimension. Default is ``"echo_range"``.

    Returns
    -------
    holoviews.Image or holoviews.Layout
        A single echogram or a vertical layout of echograms.
    """
    if isinstance(channel, str):
        return single_echogram(
            ds=ds,
            channel=channel,
            var_name=var_name,
            x_dim=x_dim,
            vert_dim=vert_dim,
        )

    echograms = [
        single_echogram(
            ds=ds,
            channel=ch,
            var_name=var_name,
            x_dim=x_dim,
            vert_dim=vert_dim,
        )
        for ch in channel
    ]

    return holoviews.Layout(echograms).cols(1)


def single_echogram(
    ds: xarray.Dataset,
    channel: str,
    var_name: str = "Sv",
    x_dim: str = "ping_time",
    vert_dim: str = "echo_range",
):
    """
    Create an echogram for one acoustic channel.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing the variable to visualize.
    channel : str
        Channel to plot.
    var_name : str, optional
        Name of the variable to visualize. Default is ``"Sv"``.
    x_dim : str, optional
        Name of the horizontal dimension. Default is ``"ping_time"``.
    vert_dim : str, optional
        Name of the vertical dimension. Default is ``"echo_range"``.

    Returns
    -------
    holoviews.Image
        Echogram for the selected channel.
    """
    dataset = holoviews.Dataset(
        ds[[var_name]].sel(
            channel=channel,
        )
    )

    return (
        dataset.to(
            holoviews.Image,
            kdims=[
                x_dim,
                vert_dim,
            ],
            vdims=[
                var_name,
            ],
        )
        .relabel(str(channel))
        .opts(
            invert_yaxis=True,
        )
    )


def tricolor_echogram(
    ds: xarray.Dataset,
    channel: list[str],
    vmin: float,
    vmax: float,
    var_name: str = "Sv",
    x_dim: str = "ping_time",
    vert_dim: str = "echo_range",
):
    """
    Create a tricolor RGB echogram.

    Parameters
    ----------
    ds : xarray.Dataset
        Dataset containing the variable to visualize.
    channel : list[str]
        Exactly three channels used for the red, green, and blue components.
    vmin : float
        Minimum value used for normalization.
    vmax : float
        Maximum value used for normalization.
    var_name : str, optional
        Name of the variable to visualize. Default is ``"Sv"``.
    x_dim : str, optional
        Name of the horizontal dimension. Default is ``"ping_time"``.
    vert_dim : str, optional
        Name of the vertical dimension. Default is ``"echo_range"``.

    Returns
    -------
    holoviews.RGB
        Tricolor echogram.

    Notes
    -----
    ``vmin`` and ``vmax`` are data-normalization limits rather than
    ordinary display limits.
    """
    if len(channel) != 3:
        raise ValueError("Exactly 3 channels are required for a tricolor echogram.")

    rgb = [
        _convert_to_color(
            ds=ds,
            channel=ch,
            vmin=vmin,
            vmax=vmax,
            var_name=var_name,
            x_dim=x_dim,
            vert_dim=vert_dim,
        )
        for ch in channel
    ]

    return holoviews.RGB(
        (
            ds[x_dim].data,
            ds[vert_dim].data,
            rgb[0],
            rgb[1],
            rgb[2],
        )
    ).opts(
        invert_yaxis=True,
    )


def _convert_to_color(
    ds: xarray.Dataset,
    channel: str,
    vmin: float,
    vmax: float,
    var_name: str = "Sv",
    x_dim: str = "ping_time",
    vert_dim: str = "echo_range",
):
    """Normalize one channel of a variable to [0, 1] for RGB display."""
    if vmax <= vmin:
        raise ValueError("vmax must be greater than vmin.")

    data = ds[var_name].sel(
        channel=channel,
    )

    data = data.clip(
        min=vmin,
        max=vmax,
    )

    normalized = (data - vmin) / (vmax - vmin)

    return numpy.asarray(
        normalized.transpose(
            vert_dim,
            x_dim,
        ).data
    )
