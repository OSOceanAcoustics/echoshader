"""echo_stats.py module

to help echogram get corresponding histograms and stats data
"""
import holoviews
import hvplot.pandas
import hvplot.xarray
from holoviews import streams


def simple_hist(echogram):
    """Equip an echogram with simple hist

    Parameters
    ----------
    echogram : hvplot.image
        holoview image MVBS_ds xr.Dataset with a specific frequency
        rasterize must be set to False
        like echogram = ds_Sv.sel(channel='GPT  38 kHz 00907208dd13 5-1 OOI.38|200').hvplot(kind='image',
                     x='ping_time',
                     y='echo_range',
                     c='Sv',
                     cmap='jet',
                     rasterize=False,
                     flip_yaxis=True)

    Returns
    -------
    type:
        param class
    describe:
        echogram with a side hist chart
    """

    def selected_range_hist(x_range, y_range):
        # Apply current ranges
        obj = (
            echogram.select(ping_time=x_range, echo_range=y_range)
            if x_range and y_range
            else echogram
        )

        # Compute histogram
        return holoviews.operation.histogram(obj)

    # Define a RangeXY stream linked to the image
    rangexy = holoviews.streams.RangeXY(source=echogram)
    hist = holoviews.DynamicMap(selected_range_hist, streams=[rangexy])
    return echogram << hist


# Define a RangeXY stream linked to the image
def plot_hist(echogram, MVBS, bin_size):
    """Equip an echogram with simple hist

    Parameters
    ----------
    echogram : hvplot.image
        holoview image MVBS_ds xr.Dataset with a specific frequency
        rasterize must be set to False
        like echogram = ds_Sv.sel(channel='GPT  38 kHz 00907208dd13 5-1 OOI.38|200').hvplot(kind='image',
                     x='ping_time',
                     y='echo_range',
                     c='Sv',
                     cmap='jet',
                     rasterize=False,
                     flip_yaxis=True)

    MVBS : xr.Dataset
        MVBS_ds xr.Dataset according to hvplot.image

    bin_size : int
        bin size of histogram

    Returns
    -------
    type:
        bounds : holoviews.Bounds
        hist : hvplot.hist
        table : holoviews.Table
    describe:
        use echogram * bounds to combine them
        to show all, use 'panel.Column(echogram * bounds, hist, table)'
    """
    box = streams.BoundsXY(
        source=echogram,
        bounds=(
            MVBS.ping_time.values[0],
            MVBS.echo_range.values[-1],
            MVBS.ping_time.values[-1],
            MVBS.echo_range.values[0],
        ),
    )

    bounds = holoviews.DynamicMap(
        lambda bounds: holoviews.Bounds(bounds).opts(line_width=1, line_color="white"),
        streams=[box],
    )

    def selected_box_table(bounds):
        # Apply current ranges
        obj_df = MVBS.sel(
            ping_time=slice(bounds[0], bounds[2]),
            echo_range=slice(bounds[3], bounds[1]),
        ).Sv.to_dataframe()

        skew = obj_df["Sv"].skew()
        kurt = obj_df["Sv"].kurt()

        obj_desc = obj_df.describe().reset_index()

        obj_desc.loc[len(obj_desc)] = ["skew", skew]
        obj_desc.loc[len(obj_desc)] = ["kurtosis", kurt]
        # Compute histogram
        return holoviews.Table(obj_desc.values, "stat", "value")

    def selected_box_hist(bounds):
        # Apply current ranges
        obj_df = MVBS.sel(
            ping_time=slice(bounds[0], bounds[2]),
            echo_range=slice(bounds[3], bounds[1]),
        ).Sv.to_dataframe()

        # Compute histogram
        return obj_df.hvplot.hist("Sv", bins=bin_size)

    table = holoviews.DynamicMap(selected_box_table, streams=[box])

    hist = holoviews.DynamicMap(selected_box_hist, streams=[box])

    def get_box_data():
        return MVBS.sel(
            ping_time=slice(box.bounds[0], box.bounds[2]),
            echo_range=slice(box.bounds[3], box.bounds[1]),
        )

    return bounds, hist, table
