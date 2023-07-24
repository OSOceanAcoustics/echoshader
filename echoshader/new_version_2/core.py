import param
import xarray
from echogram import echogram_single_frequency
from map import point, tile, track


@xarray.register_dataset_accessor("eshader")
class Echoshader(param.Parameterized):
    def __init__(self, MVBS_ds: xarray.Dataset):
        super().__init__()

        self.MVBS_ds = MVBS_ds

    def echogram_single_frequency(self):
        return echogram_single_frequency(self.MVBS_ds)

    def tile(self):
        return tile()

    def track(self):
        return track()

    def point(self):
        return point()
