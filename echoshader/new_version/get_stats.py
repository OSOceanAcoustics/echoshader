import holoviews
import hvplot
import hvplot.xarray
import pandas
import xarray

hist_opts = holoviews.opts(width=700, fontsize={"legend": 5})

table_opts = holoviews.opts(width=700)


def plot_side_hist(echogram: hvplot.image):
    """
    Equip an echogram with simple hist

    Parameters
    ----------
    echogram : hvplot.image
        holoview image MVBS_ds xarray.Dataset with a specific frequency
        rasterize must be set to False

    Returns
    -------
    holoviews.NdLayout
        Echogram combined with a side hist

    Examples
    --------
        echogram = ds_Sv.sel(channel='GPT  38 kHz 00907208dd13 5-1 OOI.38|200').hvplot(
                    kind='image',
                     x='ping_time',
                     y='echo_range',
                     c='Sv',
                     cmap='jet',
                     rasterize=False,
                     flip_yaxis=True)

        simple_hist(echogram)
    """

    # Apply current ranges and compute histogram
    selected_range_hist = lambda x_range, y_range: holoviews.operation.histogram(
        echogram.select(ping_time=x_range, echo_range=y_range)
        if x_range and y_range
        else echogram
    )

    # Define a RangeXY stream linked to the image
    rangexy = holoviews.streams.RangeXY(source=echogram)
    hist = holoviews.DynamicMap(selected_range_hist, streams=[rangexy])

    return echogram << hist


def plot_hist(MVBS_ds: xarray.Dataset, bins: int = 24, overlay: bool = True):
    """
    Create histograms for the Sv data.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        A dataset containing the data for the histogram.
    bins : int, optional
        Number of bins to use for the histogram. Default is 24.
    overlay : bool, optional
        If True, multiple histograms will be overlaid on the same plot. If False, each histogram 
        will be plotted separately. Default is True.

    Returns
    -------
    holoviews.core.data.Dataset
        The histogram plot as a HoloViews object.

    Notes
    -----
    This function uses HoloViews' hvplot library to generate the histogram plot based on the 
    provided dataset. The dataset `MVBS_ds` should contain a variable named 'Sv', and the 
    histogram will be generated using this variable. Additional options for customization 
    can be applied using `hvplot.hist` and `hist_opts`.

    Example
    -------
        plot_hist(my_dataset, bins=30, overlay=False)
    """

    if overlay is True:
        hist = MVBS_ds.Sv.hvplot.hist(
            "Sv",
            by="channel",
            bins=bins,
            subplots=False,
            alpha=0.6,
            legend="top",
        ).opts(hist_opts)
    else:
        hist = (
            MVBS_ds.Sv.hvplot.hist(
                "Sv",
                by="channel",
                bins=bins,
                subplots=True,
                legend="top",
            )
            .opts(hist_opts)
            .cols(1)
        )

    return hist


def plot_table(MVBS_ds: xarray.Dataset):
    """
    Create a table describing statistics information for the Sv data.

    Parameters
    ----------
    MVBS_ds : xarray.Dataset
        A dataset containing the data for the table.

    Returns
    -------
    holoviews.Table
        A HoloViews Table object containing statistics information such as skew and kurtosis.

    Notes
    -----
    This function converts the data from the dataset `MVBS_d` into a pandas DataFrame and 
    calculates basic statistics like skew and kurtosis for the variable 'Sv'. The resulting 
    DataFrame is then transformed into a HoloViews Table. The function assumes that 
    the dataset contains a variable named 'Sv' that holds the data to be analyzed.

    Example
    -------
        plot_table(my_dataset)
    """
    obj_df_sum = MVBS_ds.Sv.to_dataframe()

    skew_sum = obj_df_sum["Sv"].skew()
    kurt_sum = obj_df_sum["Sv"].kurt()

    obj_desc = obj_df_sum.describe().reset_index()

    obj_desc = obj_desc.rename(columns={"Sv": "Sum"})
    obj_desc.loc[len(obj_desc)] = ["skew", skew_sum]
    obj_desc.loc[len(obj_desc)] = ["kurtosis", kurt_sum]

    for channel in MVBS_ds.channel.values:
        obj_df_channel = MVBS_ds.sel(channel=channel).Sv.to_dataframe()

        skew_channel = obj_df_channel["Sv"].skew()
        kurt_channel = obj_df_channel["Sv"].kurt()

        obj_df_channel = obj_df_channel.describe().reset_index()

        obj_df_channel = obj_df_channel.rename(columns={"Sv": channel})
        obj_df_channel.loc[len(obj_df_channel)] = ["skew", skew_channel]
        obj_df_channel.loc[len(obj_df_channel)] = ["kurtosis", kurt_channel]

        obj_desc = pandas.merge(obj_desc, obj_df_channel, on="index")

    table = holoviews.Table(obj_desc).opts(table_opts)

    return table
