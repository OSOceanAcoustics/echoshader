"""echo_map.py module

to help echogram get corresponding maps
"""
import holoviews
from holoviews import streams
import geoviews


def plot_track(MVBS_ds, map_tiles=geoviews.tile_sources.Wikipedia):
    '''simply get a map

    Parameters
    ----------
    MVBS : xr.Dataset
        MVBS_ds xr.Dataset

    map_tiles : geoviews.tile
        see: https://geoviews.org/gallery/bokeh/tile_sources.html#bokeh-gallery-tile-sources

    Returns
    -------
    type:
        selected_are * track : layout (geoviews)

    describe:
        use 'panel.Row(selected_are * track)' to show
    '''
    # conver xarray data to geoviews data
    xr_dataset = geoviews.Dataset(MVBS_ds,
                                  kdims=['ping_time'],
                                  vdims=['longitude', 'latitude'])

    #plot path
    ship_track = xr_dataset.to(geoviews.Path,
                               kdims=['longitude', 'latitude'],
                               vdims=['ping_time']).opts(width=600,
                                                         height=450,
                                                         color='blue',
                                                         tools=['hover'])

    #add map tiles
    return ship_track * map_tiles


def plot_map(gram, MVBS_ds, map_tiles=geoviews.tile_sources.Wikipedia):
    '''Equip an echogram with map

    Parameters
    ----------
    gram : hvplot.image
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

    map_tiles : geoviews.tile
        see: https://geoviews.org/gallery/bokeh/tile_sources.html#bokeh-gallery-tile-sources

    Returns
    -------
    type:
        bounds : holoviews.Bounds
        selected_are * track : layout (geoviews)

    describe:
        use echogram*bounds to combine them
        to show all, use 'panel.Column(echogram * bounds, selected_are * track)'
    '''
    # plot combined map and echogram with select box function
    box = streams.BoundsXY(
        source=gram,
        bounds=(MVBS_ds.ping_time.values[0], MVBS_ds.echo_range.values[-1],
                MVBS_ds.ping_time.values[-1], MVBS_ds.echo_range.values[0]))

    def plot_bounds(box):
        # plot select box in echogram
        bounds = holoviews.DynamicMap(lambda bounds: holoviews.Bounds(bounds).
                                      opts(line_width=1, line_color='white'),
                                      streams=[box])

        return bounds

    def get_box_data(box, MVBS_ds):
        # call this function to get select box data in real time
        return MVBS_ds.sel(ping_time=slice(box.bounds[0], box.bounds[2]),
                           echo_range=slice(box.bounds[3], box.bounds[1]))

    bounds = plot_bounds(box)

    def plot_selected(bounds):
        # plot specfic area in the map according the select data in echogram
        lon = MVBS_ds.sel(
            ping_time=slice(bounds[0], bounds[2])).longitude.values

        lat = MVBS_ds.sel(
            ping_time=slice(bounds[0], bounds[2])).latitude.values

        track = dict(Longitude=lon, Latitude=lat)

        path = geoviews.Path([track]).opts(line_width=4,
                                           color='red',
                                           alpha=0.8)

        begin = (lon[0], lat[0], 'begin')

        end = (lon[-1], lat[-1], 'end')

        points = geoviews.Points([begin, end]).opts(width=500,
                                                    height=475,
                                                    size=5,
                                                    color='white')

        return path * points * map_tiles

    def plot_ship_track(x_range, y_range):
        # Apply current ranges
        ship_track = plot_track(
            MVBS_ds.sel(ping_time=slice(x_range[0], x_range[1])))

        # Compute histogram
        return ship_track

    # Define a RangeXY stream linked to the image
    rangexy = holoviews.streams.RangeXY(source=gram)

    track = holoviews.DynamicMap(plot_ship_track, streams=[rangexy])

    selected_are = holoviews.DynamicMap(plot_selected, streams=[box])

    return bounds, selected_are * track
