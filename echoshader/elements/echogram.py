import holoviews
import numpy
import panel
import param
import xarray

from echoshader.box import get_box_stream
from echoshader.utils import gram_opts


def echogram(
    channel: list[str],
    MVBS_ds: xarray.Dataset = None,
    cmap: str | list[str] = None,
    sv_range_slider: panel.widgets.EditableRangeSlider = None,
    colormap: panel.widgets.LiteralInput = None,
    update_gram_flag: param.Event = None,
    rgb_composite: bool = False,
    vert_dim: str | None = "echo_range",
    bounds: holoviews.DynamicMap = None,
    time_range_opts: list[holoviews.opts] = [],
):
    """
    Display echogram plots based on specified parameters.

    Attached Widgets
    ----------------
    colormap : panel.widgets.LiteralInput
        A widget to control the colormap for echograms.
        https://holoviews.org/user_guide/Colormaps.html

    Sv_range_slider : panel.widgets.EditableRangeSlider
        A slider widget to control the Sv range.

    Parameters
    ----------
    channel : List[str], optional
        List of frequency channels. Default is None.
    cmap : Union[str, List[str]], optional
        Colormap for the echogram plot. Default is None.
        https://holoviews.org/user_guide/Colormaps.html
    vmin : float, optional
        Minimum value for Sv range. Default is None.
    vmax : float, optional
        Maximum value for Sv range. Default is None.
    rgb_composite : bool, optional
        Enable RGB tricolor echogram. Default is False.
    vert_dim : str, optional
        Name of the vertical dimension. Default is echo_range.
    opts : list[holoviews.opts], optional
        Additional options for plotting. Default is an empty list.
        https://holoviews.org/user_guide/Applying_Customizations.html#option-list-syntax

    Returns
    -------
    holoviews.Overlay
        Echogram plot.

    Examples
    --------
    echogram = MVBS_ds.eshader.echogram(vmin = -80, vmax = -30)

    panel.Row(echogram)
    """

    def _build(sv_range_slider, colormap, update_gram_flag):
        if rgb_composite is True:
            if channel is None or not isinstance(channel, list):
                raise ValueError("Channel must be a list of strings.")
            if len(channel) != 3:
                raise ValueError(
                    "Channel must have exactly 3 frequency channels for tricolor echogram."
                )

            return _tricolor_echogram_plot(
                MVBS_ds, bounds, sv_range_slider, channel, vert_dim, time_range_opts
            )

        else:
            if channel is None:
                channels = MVBS_ds.channel.values.tolist()
            else:
                channels = channel

            return _echogram_plot(
                MVBS_ds, bounds, channels, cmap, sv_range_slider, vert_dim, time_range_opts
            )

    return panel.bind(
        _build,
        sv_range_slider=sv_range_slider,
        colormap=colormap,
        update_gram_flag=update_gram_flag,
    )


def _tricolor_echogram_plot(
    MVBS_ds: xarray.Dataset,
    bounds: holoviews.DynamicMap,
    sv_range_slider: panel.widgets.EditableRangeSlider,
    channel: list[str],
    vert_dim: str | None = "echo_range",
    time_range_opts: list[holoviews.opts] = [],
):
    """
    Generate a tricolor echogram plot based on current parameters.

    Returns
    -------
    holoviews.Overlay
        Tricolor echogram plot.
    """

    rgb_map = {}
    rgb_map[channel[0]] = "R"
    rgb_map[channel[1]] = "G"
    rgb_map[channel[2]] = "B"

    echogram = tricolor_echogram(
        MVBS_ds,
        sv_range_slider.value[0],
        sv_range_slider.value[1],
        rgb_map,
        vert_dim,
    ).opts(time_range_opts)

    # get box stream from echogram
    box_stream = get_box_stream(echogram)

    # add subscriber to update unified box select
    box_stream.add_subscriber(_update_gram_box)

    # set inital value of box stream
    _update_gram_box(tuple(echogram.lbrt))

    reset_stream = holoviews.streams.PlotReset(source=echogram)

    reset_stream.add_subscriber(_update_gram_reset)

    return (echogram * bounds).opts(gram_opts)


def _echogram_plot(
    MVBS_ds: xarray.Dataset,
    bounds: holoviews.DynamicMap,
    channel: list[str],
    cmap: str | list[str],
    sv_range_slider: panel.widgets.EditableRangeSlider,
    vert_dim: str | None = "echo_range",
    time_range_opts: list[holoviews.opts] = [],
):
    """
    Generate an echogram plot based on current parameters.

    Returns
    -------
    holoviews.Layout
        Layout of echogram plots.
    """

    echograms_list = []

    for channel in channel:
        echogram = single_echogram(
            MVBS_ds,
            channel,
            cmap,
            sv_range_slider.value,
            vert_dim,
        ).opts(time_range_opts)

        # get box stream from echogram
        box_stream = get_box_stream(echogram)

        # add subscriber to update unified box select
        box_stream.add_subscriber(_update_gram_box)

        echograms_list.append(echogram)

    # set inital value of box stream
    _update_gram_box(tuple(echograms_list[0].lbrt))

    reset_stream = holoviews.streams.PlotReset(source=echograms_list[0])

    reset_stream.add_subscriber(_update_gram_reset)

    # get echograms stack
    echograms = holoviews.Layout(echograms_list).cols(1)

    return (echograms * bounds).opts(gram_opts)


def single_echogram(
    MVBS_ds: xarray,
    channel: str,
    cmap: str | list[str],
    value_range: tuple[float, float],
    vert_dim: str | None = "echo_range",
):
    """
    Generate an echogram for a single frequency channel.

    This function takes an xarray.Dataset containing MVBS (Multibeam Backscatter) data,
    extracts the data for a specific frequency channel, and generates an echogram for
    that channel using Holoviews. The echogram is a visual representation of the
    backscatter values (Sv) over time (ping_time) and depth (echo_range).

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        xarray.Dataset containing MVBS data.
    channel : str
        The name of the frequency channel for which the echogram will be generated.
        It should be a valid channel name present in the 'channel' dimension of MVBS_ds.
    cmap : str or List[str]
        The colormap(s) to use for the echogram. It can be a single colormap name or
        a list of colormap names for each frequency channel (if multiple colormaps are used).
        Input list like ['#0000ff', '#00ffff'] to customize colormap.
    value_range : tuple[float, float]
        The minimum and maximum value for the color scale of the echogram.
    vert_dim : str, optional
        The name of the vertical dimension, must be 1D.

    Returns
    -------
    holoviews.element.Image
        An echogram for the specified frequency channel, displaying the backscatter values (Sv)
        over time (ping_time) and depth (echo_range). The echogram is rendered using Holoviews
        with the provided colormap and color scale limits.

    Examples
    --------
    # Assuming MVBS_ds is an xarray.Dataset containing MVBS data
    # Generate an echogram for the channel 'GPT 38 kHz 00907208dd13 5-1 OOI.38|200'
    echogram = echogram_single_frequency(
        MVBS_ds,
        channel='GPT 38 kHz 00907208dd13 5-1 OOI.38|200',
        cmap='jet',
        value_range=(-80,-30)
    )

    # Display the echogram using Panel
    Panel.Row(echogram)
    """
    gram_opts["Image"]["cmap"] = cmap

    gram_opts["Image"]["clim"] = value_range

    gram_opts["Image"]["title"] = channel

    gram_opts["Image"]["invert_yaxis"] = True

    dataset = holoviews.Dataset(MVBS_ds.sel(channel=channel))

    echogram = dataset.to(
        holoviews.Image,
        vdims=["Sv"],  # color: Sv
        kdims=["ping_time", vert_dim],  # x: ping_time, y: vert_dim
    ).opts(gram_opts)

    return echogram


def convert_to_color(MVBS_ds: xarray, channel_sel: str, th_bottom: float, th_top: float):
    """
    Convert backscatter data to a color array based on threshold values.

    This function takes an xarray.Dataset containing MVBS (Multibeam Backscatter) data,
    extracts the data for a specific `channel_sel`, and converts the backscatter values (Sv)
    to a color array based on specified threshold values. Values above `th_top` and below
    `th_bottom` are masked (NaN), and the remaining values are scaled
    to a range between 0 and 1, representing colors from minimum to maximum.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        xarray.Dataset containing MVBS data.
    channel_sel : str
        The name of the frequency channel for which the color array will be generated.
        It should be a valid channel name present in the 'channel' dimension of MVBS_ds.
    th_bottom : float
        The lower threshold value for backscatter data.
    th_top : float
        The upper threshold value for backscatter data.

    Returns
    -------
    numpy.ndarray
        A color array representing backscatter data of the specified `channel_sel`.
        Values are scaled between 0 and 1, with NaN values for backscatter data below `th_bottom`.

    Examples
    --------
    # Assuming MVBS_ds is an xarray.Dataset containing MVBS data
    # Convert backscatter data of 'GPT 38 kHz 00907208dd13 5-1 OOI.38|200' to a color array
    color_array = convert_to_color(
        MVBS_ds,
        channel_sel='GPT 38 kHz 00907208dd13 5-1 OOI.38|200',
        th_bottom=-80.0,
        th_top=-40.0
    )
    """
    da_color = MVBS_ds.sel(channel=channel_sel)
    da_color = da_color.where(da_color <= th_top, other=th_top)  # set to ceiling at the top
    da_color = da_color.where(da_color >= th_bottom, other=th_bottom)  # threshold at the bottom
    da_color = da_color.expand_dims("channel")
    da_color = (da_color - th_bottom) / (th_top - th_bottom)
    da_color = numpy.squeeze(da_color.Sv.data).transpose()
    return da_color


def tricolor_echogram(
    MVBS_ds: xarray,
    vmin: float,
    vmax: float,
    rgb_map: dict[str, str] = {},
    vert_dim: str | None = "echo_range",
):
    """
    Create a tricolor echogram for multiple frequency channels.

    This function generates a tricolor echogram from an xarray.Dataset containing MVBS
    (Multibeam Backscatter) data, where each color channel represents a different frequency
    channel's backscatter values. The function allows custom mapping of frequency channels to
    RGB color channels using the `rgb_map` dictionary.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        xarray.Dataset containing MVBS data.
    vmin : float
        The minimum value for the color scale of the echogram.
    vmax : float
        The maximum value for the color scale of the echogram.
    rgb_map : Dict[str, str], optional
        A dictionary specifying the mapping of frequency channels to RGB color channels.
        The keys are the frequency channel names, and the values are the corresponding
        RGB channel names. If not provided, the function will assign the first three frequency
        channels to the "R", "G", and "B" channels, respectively.
    vert_dim : str, optional
        Name of vertical dimension. Default is echo_range.

    Returns
    -------
    holoviews.element.RGB
        A tricolor echogram, where each color channel represents the backscatter values (Sv) of
        a different frequency channel. The echogram is rendered using Holoviews with the provided
        colormap and color scale limits.

    Examples
    --------
    # Assuming MVBS_ds is an xarray.Dataset containing MVBS data
    # Create a tricolor echogram for the first three frequency channels
    tricolor_plot = tricolor_echogram(MVBS_ds, vmin=-80.0, vmax=-40.0)

    # Alternatively, provide a custom mapping of frequency channels to RGB channels
    rgb_mapping = {
        'GPT 38 kHz 00907208dd13 5-1 OOI.38|200': 'R',
        'GPT 50 kHz 00907208dd13 5-1 OOI.50|200': 'G',
        'GPT 200 kHz 00907208dd13 5-1 OOI.200|200': 'B',
    }
    tricolor_plot = tricolor_echogram(MVBS_ds, vmin=-80.0, vmax=-40.0, rgb_map=rgb_mapping)

    # Display the tricolor echogram using Panel
    Panel.Row(tricolor_plot)
    """

    gram_opts["RGB"]["invert_yaxis"] = True

    if rgb_map == {}:
        rgb_map[MVBS_ds.channel.values[0]] = "R"
        rgb_map[MVBS_ds.channel.values[1]] = "G"
        rgb_map[MVBS_ds.channel.values[2]] = "B"

    rgb_ch = {"R": None, "G": None, "B": None}

    for ch, color in rgb_map.items():
        rgb_ch[color] = convert_to_color(MVBS_ds, channel_sel=ch, th_bottom=vmin, th_top=vmax)

    rgb = holoviews.RGB(
        (
            MVBS_ds.ping_time.data,
            MVBS_ds[vert_dim].data,
            rgb_ch["R"],
            rgb_ch["G"],
            rgb_ch["B"],
        )
    ).opts(gram_opts)

    return rgb


def _update_gram_box(
    bounds, MVBS_ds_in_gram_box, update_track_flag, gram_box_stream, control_mode_select, vert_dim
):
    """
    Update the gram box based on given bounds.

    Parameters
    ----------
    bounds : tuple
        Bounds of the gram box in the format (left, bottom, right, top).
    """
    gram_box_stream.update(bounds=bounds)

    MVBS_ds_in_gram_box = _extract_data_from_gram_box(MVBS_ds_in_gram_box, bounds, vert_dim)

    if control_mode_select.value is True:
        update_track_flag.event()


def _update_gram_reset(update_gram_flag):
    """
    Event handler for resetting the gram box.
    """
    update_gram_flag.event()


def _extract_data_from_gram_box(MVBS_ds, bounds, vert_dim):
    """
    Extract data from the gram box based on given bounds.

    Parameters
    ----------
    bounds : tuple
        Bounds of the gram box in the format (left, bottom, right, top).

    Returns
    -------
    xarray.Dataset
        Extracted dataset within the specified bounds.
    """
    if bounds is None:
        MVBS_ds_in_gram_box = MVBS_ds

    else:
        MVBS_ds_in_gram_box = MVBS_ds.sel(
            {
                "ping_time": slice(bounds[0], bounds[2]),
                vert_dim: (
                    slice(bounds[1], bounds[3])
                    if bounds[3] > bounds[1]
                    else slice(bounds[3], bounds[1])
                ),
            },
        )

    return MVBS_ds_in_gram_box
