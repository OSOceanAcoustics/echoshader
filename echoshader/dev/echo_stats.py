from echo_lib import *


def simpleHist(ds_Sv,
               clim=(-80, -30),
               cmap='jet',
               width=600,
               height=300):
    '''
    input Sv DataArray/DataSet with a specific channel,
    like ds_MVBS.Sv.sel(channel='GPT  38 kHz 00907208dd13 5-1 OOI.38|200'),
    to get a simple side hist, which is tuned by box zoom (rangeXY)
    '''

    echogram = ds_Sv.hvplot(kind='image',
                            x='ping_time',
                            y='echo_range',
                            c='Sv',
                            clim=clim,
                            cmap=cmap,
                            rasterize=False,
                            width=width,
                            height=height,
                            flip_yaxis=True)

    def selectedRangeHist(x_range, y_range):
        # Apply current ranges
        obj = echogram.select(ping_time=x_range,
                              echo_range=y_range) if x_range and y_range else echogram

        # Compute histogram
        return hv.operation.histogram(obj)

    # Define a RangeXY stream linked to the image
    rangexy = hv.streams.RangeXY(source=echogram)
    hist = hv.DynamicMap(selectedRangeHist, streams=[rangexy])
    return echogram << hist


def hist(ds_Sv,
         boxSelect=True,
         clim=(-80, -30),
         cmap='jet',
         width=600,
         height=300):
    '''
    input Sv DataArray with a specific channel,
    like ds_MVBS.Sv.sel(channel='GPT  38 kHz 00907208dd13 5-1 OOI.38|200'),
    to get a hist with describe, which is tuned by box select (boxXY)
    '''

    echogram = ds_Sv.hvplot(kind='image',
                            x='ping_time',
                            y='echo_range',
                            c='Sv',
                            clim=clim,
                            cmap=cmap,
                            rasterize=False,
                            width=width,
                            height=height,
                            flip_yaxis=True)

    def selectedBoxTable(bounds):
        # Apply current ranges
        obj = echogram.select(ping_time=(bounds[0], bounds[2]),
                              echo_range=(bounds[1], bounds[3])) if bounds else echogram
        obj_df = obj.data.to_dataframe()

        skew = obj_df['Sv'].skew()
        kurt = obj_df['Sv'].kurt()

        obj_desc = obj_df.describe().reset_index()

        obj_desc.loc[len(obj_desc)] = ['skew', skew]
        obj_desc.loc[len(obj_desc)] = ['kurtosis', kurt]
        # Compute histogram
        return hv.Table(obj_desc.values, 'stat', 'value')

    def selectedBoxHist(bounds):
        # Apply current ranges
        obj = echogram.select(ping_time=(bounds[0], bounds[2]),
                              echo_range=(bounds[1], bounds[3])) if bounds else echogram
        obj_df = obj.data.to_dataframe()

        # Compute histogram
        return obj_df.hvplot.hist('Sv')

    echogram.options(tools=['box_select'])

    # Define a RangeXY stream linked to the image
    box = streams.BoundsXY(source=echogram, bounds=(ds_Sv.ping_time.values[0],
                                                    ds_Sv.echo_range.values[0],
                                                    ds_Sv.ping_time.values[0],
                                                    ds_Sv.echo_range.values[0]))

    bounds = hv.DynamicMap(lambda bounds: hv.Bounds(bounds).opts(line_width=1,
                                                                 line_color='white'), streams=[box])

    table = hv.DynamicMap(selectedBoxTable, streams=[box])

    hist = hv.DynamicMap(selectedBoxHist, streams=[box])

    return pn.Column(pn.Row(echogram*bounds, table), hist)
