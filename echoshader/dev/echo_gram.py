"""echo_gram.py module

use panel to get a echogram with control widgets
"""
import panel

panel.extension("vtk")

import warnings

import echo_map
import echo_stats
import hvplot.xarray
import pandas
import param

warnings.simplefilter("ignore")


def echogram(MVBS):
    """Get an echogram with control widgets

    Parameters
    ----------
    MVBS : xr.Dataset
        MVBS_ds data set or ds_Sv data array

    Returns
    -------
    type:
        param class
    describe:
        return values contains echogram and control widgets
        use 'panel.Row(echogram(MVBS).param,echogram(MVBS).view)'
        to get a complete panel
        echogram(MVBS).param shows param(control widgets)
        echogram(MVBS).view shows echogram image

    """

    def getMVBS():
        # help class Echogram get MVBS

        return MVBS

    def get_time_range():
        # get time range according to MVBS input

        start_time = pandas.to_datetime(MVBS.ping_time.data[0])

        end_time = pandas.to_datetime(MVBS.ping_time.data[-1])

        return start_time, end_time

    class Echogram(param.Parameterized):

        MVBS = getMVBS()

        start_time, end_time = get_time_range()

        start_input = param.Date(
            bounds=(start_time, end_time), default=start_time, doc="Select start time"
        )

        end_input = param.Date(
            bounds=(start_time, end_time), default=end_time, doc="Select end time"
        )

        select_channel = param.Selector(
            objects=MVBS.channel.values.tolist(), doc="Select channel"
        )

        range_clim = param.Range(
            bounds=(MVBS.Sv.actual_range[0], MVBS.Sv.actual_range[-1]),
            doc="Select clim",
        )

        color_map = param.String(default="jet", doc="Colormap")

        # sometimes it report errors because of non-even sampled data
        # input "quadmesh" to get rid of it
        # but in this situation, rasterize may not applied
        chart_type = param.String(default="image", doc="Type of chart")

        @param.depends(
            "start_input",
            "end_input",
            "select_channel",
            "range_clim",
            "color_map",
            "chart_type",
        )
        def view(self):

            start_input_time = self.start_input

            end_input_time = self.end_input

            time_range = slice(start_input_time, end_input_time)

            channel = self.select_channel

            clim = self.range_clim

            color_map = self.color_map

            chart_type = self.chart_type

            rasterize = True if chart_type == "image" else False

            gram = (
                self.MVBS.Sv.sel(channel=channel, ping_time=time_range)
                .hvplot(
                    kind=chart_type,
                    x="ping_time",
                    y="echo_range",
                    title="Sv : " + channel,
                    cmap=color_map,
                    clim=clim,
                    rasterize=rasterize,
                )
                .options(invert_yaxis=True)
            )

            return gram

    return Echogram()


def echogram_hist(MVBS):
    """Get an echogram and histogram with control widgets

    Parameters
    ----------
    MVBS : xr.Dataset
        MVBS_ds data set or ds_Sv data array

    Returns
    -------
    type:
        param class
    describe:
        return values contains echogram and control widgets
        use 'panel.Row(echogram(MVBS).param,echogram(MVBS).view)'
        to get a complete panel
        echogram(MVBS).param shows param(control widgets)
        echogram(MVBS).view shows echogram image

    """

    def getMVBS():
        # help class Echogram get MVBS

        return MVBS

    def get_time_range():
        # get time range according to MVBS input

        start_time = pandas.to_datetime(MVBS.ping_time.data[0])

        end_time = pandas.to_datetime(MVBS.ping_time.data[-1])

        return start_time, end_time

    class EchogramHist(param.Parameterized):

        MVBS = getMVBS()

        start_time, end_time = get_time_range()

        start_input = param.Date(
            bounds=(start_time, end_time), default=start_time, doc="Select start time"
        )

        end_input = param.Date(
            bounds=(start_time, end_time), default=end_time, doc="Select end time"
        )

        select_channel = param.Selector(
            objects=MVBS.channel.values.tolist(), doc="Select channel"
        )

        range_clim = param.Range(
            bounds=(MVBS.Sv.actual_range[0], MVBS.Sv.actual_range[-1]),
            doc="Select clim",
        )

        color_map = param.String(default="jet", doc="Colormap")

        bin_size = param.Integer(24, bounds=(1, 200), doc="Bin size")

        @param.depends(
            "start_input",
            "end_input",
            "select_channel",
            "range_clim",
            "color_map",
            "bin_size",
        )
        def view(self):
            start_input_time = self.start_input

            end_input_time = self.end_input

            time_range = slice(start_input_time, end_input_time)

            channel = self.select_channel

            clim = self.range_clim

            color_map = self.color_map

            bin_size = self.bin_size

            gram = (
                self.MVBS.Sv.sel(channel=channel, ping_time=time_range)
                .hvplot(
                    kind="image",
                    x="ping_time",
                    y="echo_range",
                    title="Sv : " + channel,
                    cmap=color_map,
                    clim=clim,
                    rasterize=True,
                )
                .options(invert_yaxis=True)
            )

            bounds, hist, table = echo_stats.plot_hist(
                gram, self.MVBS.sel(channel=channel, ping_time=time_range), bin_size
            )

            return panel.Column(gram * bounds, hist, table)

    return EchogramHist()


def echogram_map(MVBS):
    """Get an echogram and map with control widgets

    Parameters
    ----------
    MVBS : xr.Dataset
        MVBS_ds data set or ds_Sv data array

    Returns
    -------
    type:
        param class
    describe:
        return values contains echogram and control widgets
        use 'panel.Row(echogram(MVBS).param,echogram(MVBS).view)'
        to get a complete panel
        echogram(MVBS).param shows param(control widgets)
        echogram(MVBS).view shows echogram image

    """

    def getMVBS():
        # help class Echogram get MVBS

        return MVBS

    def get_time_range():
        # get time range according to MVBS input

        start_time = pandas.to_datetime(MVBS.ping_time.data[0])

        end_time = pandas.to_datetime(MVBS.ping_time.data[-1])

        return start_time, end_time

    class EchogramMap(param.Parameterized):

        MVBS = getMVBS()

        start_time, end_time = get_time_range()

        start_input = param.Date(
            bounds=(start_time, end_time), default=start_time, doc="Select start time"
        )

        end_input = param.Date(
            bounds=(start_time, end_time), default=end_time, doc="Select end time"
        )

        select_channel = param.Selector(
            objects=MVBS.channel.values.tolist(), doc="Select channel"
        )

        range_clim = param.Range(
            bounds=(MVBS.Sv.actual_range[0], MVBS.Sv.actual_range[-1]),
            doc="Select clim",
        )

        color_map = param.String(default="jet", doc="Colormap")

        @param.depends(
            "start_input", "end_input", "select_channel", "range_clim", "color_map"
        )
        def view(self):

            start_input_time = self.start_input

            end_input_time = self.end_input

            time_range = slice(start_input_time, end_input_time)

            channel = self.select_channel

            clim = self.range_clim

            color_map = self.color_map

            gram = (
                self.MVBS.Sv.sel(channel=channel, ping_time=time_range)
                .hvplot(
                    kind="image",
                    x="ping_time",
                    y="echo_range",
                    title="Sv : " + channel,
                    cmap=color_map,
                    clim=clim,
                    rasterize=True,
                )
                .options(invert_yaxis=True)
            )

            bound, track = echo_map.plot_map(
                gram, self.MVBS.sel(channel=channel, ping_time=time_range)
            )

            return panel.Column(gram * bound, track)

    return EchogramMap()
