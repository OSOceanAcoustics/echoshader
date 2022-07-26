import holoviews
from holoviews import streams
import geoviews


def plot_track(platform_ds, map_tiles=geoviews.tile_sources.Wikipedia):
    # conver xarray data to geoviews data
    xr_dataset = geoviews.Dataset(platform_ds,
                                  kdims=['time1'],
                                  vdims=['longitude', 'latitude'])

    #plot path
    ship_track = xr_dataset.to(geoviews.Path,
                               kdims=['longitude', 'latitude'],
                               vdims=['time1']).opts(width=600,
                                                     height=450,
                                                     color='blue',
                                                     tools=['hover'])

    #add map tiles
    return ship_track * map_tiles


def plot_bounds(box):
    # plot select box in echogram
    bounds = holoviews.DynamicMap(lambda bounds: holoviews.Bounds(bounds).opts(
        line_width=1, line_color='white'),
                                  streams=[box])

    return bounds


def get_box_data(box, MVBS_ds):
    # call this function to get select box data in real time
    return MVBS_ds.sel(ping_time=slice(box.bounds[0], box.bounds[2]),
                       echo_range=slice(box.bounds[3], box.bounds[1]))


def plot_map(gram, MVBS_ds, map_tiles=geoviews.tile_sources.Wikipedia):
    # plot combined map and echogram with select box function
    box = streams.BoundsXY(
        source=gram,
        bounds=(MVBS_ds.ping_time.values[0], MVBS_ds.echo_range.values[-1],
                MVBS_ds.ping_time.values[-1], MVBS_ds.echo_range.values[0]))

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

    selected_are = holoviews.DynamicMap(plot_selected, streams=[box])

    return gram * bounds + selected_are
