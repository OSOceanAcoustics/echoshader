import geoviews
import pandas
import xarray
from utils import gram_opts


def convert_MVBS_to_pandas(MVBS_ds: xarray.Dataset):
    all_pd_data = pandas.concat(
        [
            pandas.DataFrame(MVBS_ds.longitude.values, columns=["Longitude"]),
            pandas.DataFrame(MVBS_ds.latitude.values, columns=["Latitude"]),
            pandas.DataFrame(MVBS_ds.ping_time.values, columns=["Ping Time"]),
        ],
        axis=1,
    )

    all_pd_data = all_pd_data.dropna(axis=0, how="any")

    return all_pd_data


def tile(map_tiles: str):
    tiles = getattr(geoviews.tile_sources, map_tiles).opts(gram_opts)

    return tiles


def track(MVBS_ds: xarray.Dataset):
    all_pd_data = convert_MVBS_to_pandas(MVBS_ds)

    starting_data = all_pd_data.iloc[0].values.tolist()

    # plot starting point
    starting_point = geoviews.Points(
        [starting_data],
        kdims=["Longitude", "Latitude"],
    ).opts(gram_opts)

    # plot ship path
    ship_path = geoviews.Path(
        [all_pd_data],
        kdims=["Longitude", "Latitude"],
        vdims=["Ping Time", "Longitude", "Latitude"],
    ).opts(gram_opts)

    return ship_path * starting_point


def point(MVBS_ds: xarray.Dataset):
    all_pd_data = convert_MVBS_to_pandas(MVBS_ds)

    starting_data = all_pd_data.iloc[0].values.tolist()

    # plot moored point
    moored_point = geoviews.Points(
        [starting_data],
        kdims=["Longitude", "Latitude"],
    ).opts(gram_opts)

    return moored_point
