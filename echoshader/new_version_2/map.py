import xarray
import geoviews
import pandas

def tile(
        map_tiles: str,
        opt_tile: geoviews.opts,
        ):
    tiles = getattr(geoviews.tile_sources, map_tiles).opts(opt_tile)

    return tiles

def track(
    MVBS_ds: xarray.Dataset,
    opts_line: geoviews.opts,
    opts_point: geoviews.opts,
):
    all_pd_data = pandas.concat(
        [
            pandas.DataFrame(MVBS_ds.longitude.values, columns=["Longitude"]),
            pandas.DataFrame(MVBS_ds.latitude.values, columns=["Latitude"]),
            pandas.DataFrame(MVBS_ds.ping_time.values, columns=["Ping Time"]),
        ],
        axis=1,
    )

    all_pd_data = all_pd_data.dropna(axis=0, how="any")

    # plot start node
    starting_data = all_pd_data.iloc[0].values.tolist()

    starting_node = geoviews.Points(
        [starting_data],
        kdims=["Longitude", "Latitude"],
    ).opts(opts_point)

    # check if all rows has the same latitude and Longitude
    if all_pd_data["Longitude"].nunique() == 1 & all_pd_data["Latitude"].nunique() == 1:
        return starting_node

    # plot path
    line = geoviews.Path(
        [all_pd_data],
        kdims=["Longitude", "Latitude"],
        vdims=["Ping Time", "Longitude", "Latitude"],
    ).opts(opts_line)

    return line * starting_node