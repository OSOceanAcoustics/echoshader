import holoviews
import hvplot.xarray

import pandas

hist_opts = holoviews.opts(width=700, fontsize={'legend': 5})

table_opts = holoviews.opts(width=700)

def plot_side_hist(echogram):
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
        echogram = ds_Sv.sel(channel='GPT  38 kHz 00907208dd13 5-1 OOI.38|200').hvplot(kind='image',
                     x='ping_time',
                     y='echo_range',
                     c='Sv',
                     cmap='jet',
                     rasterize=False,
                     flip_yaxis=True)

        simple_hist(echogram)
    """

    # Apply current ranges and compute histogram
    selected_range_hist = lambda x_range, y_range: \
        holoviews.operation.histogram(
            echogram.select(ping_time=x_range, echo_range=y_range)
            if x_range and y_range
            else echogram
        )

    # Define a RangeXY stream linked to the image
    rangexy = holoviews.streams.RangeXY(source=echogram)
    hist = holoviews.DynamicMap(selected_range_hist, streams=[rangexy])

    return echogram << hist
 
def plot_hist(MVBS_ds,
              bins,
              overlay):
    """
    Create a hist for box Sv with a specific frequency

    Returns
    -------
    hvplot.hist
    """
    if overlay is True: 
        hist = MVBS_ds.Sv.hvplot.hist( 
            "Sv",
            by="channel",
            bins=bins,
            subplots= False,
            alpha=0.6,
            legend="top",
        ).opts(hist_opts)
    else:
        hist = MVBS_ds.Sv.hvplot.hist( 
            "Sv",
            by="channel",
            bins=bins,
            subplots= True,
            legend="top",
        ).opts(hist_opts).cols(1)        

    return hist

def plot_table(MVBS_ds):
    # Apply current ranges
    obj_df_sum = MVBS_ds.Sv.to_dataframe()

    skew_sum = obj_df_sum["Sv"].skew()
    kurt_sum = obj_df_sum["Sv"].kurt()

    obj_desc = obj_df_sum.describe().reset_index()

    obj_desc = obj_desc.rename(columns={'Sv': 'Sum'})
    obj_desc.loc[len(obj_desc)] = ["skew", skew_sum]
    obj_desc.loc[len(obj_desc)] = ["kurtosis", kurt_sum]
    
    for channel in MVBS_ds.channel.values:
        obj_df_channel = MVBS_ds.sel(channel=channel).Sv.to_dataframe()

        skew_channel = obj_df_channel["Sv"].skew()
        kurt_channel = obj_df_channel["Sv"].kurt()

        obj_df_channel = obj_df_channel.describe().reset_index()

        obj_df_channel = obj_df_channel.rename(columns={'Sv': channel})
        obj_df_channel.loc[len(obj_df_channel)] = ["skew", skew_channel]
        obj_df_channel.loc[len(obj_df_channel)] = ["kurtosis", kurt_channel]

        obj_desc = pandas.merge(obj_desc, obj_df_channel, on='index')

    table = holoviews.Table(obj_desc).opts(table_opts)

    return table
