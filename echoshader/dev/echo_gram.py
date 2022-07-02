from echo_lib import *


def simpleEchogram(
    ds_Sv, clim=(-80, -30), cmap="jet", rasterize=True, width=600, height=300
):
    """
    input echopype MVBS DataSet / Sv DataArray to get a simple echogram
    """

    plot = ds_Sv.hvplot(
        kind="image",
        x="ping_time",
        y="echo_range",
        c="Sv",
        title="Echogram",
        cmap=cmap,
        clim=clim,
        rasterize=rasterize,
        width=width,
        height=height,
        flip_yaxis=True,
    )

    return plot


def echogram(MVBS):

    """
    input echopype MVBS DataSet / Sv DataArray to get a echogram with components
    """

    def getMVBS():
        return MVBS

    class Echogram(param.Parameterized):

        MVBS = getMVBS()

        start_date = dt.date(
            pd.to_datetime(MVBS.ping_time.data[0]).year,
            pd.to_datetime(MVBS.ping_time.data[0]).month,
            pd.to_datetime(MVBS.ping_time.data[0]).day,
        )

        end_date = dt.date(
            pd.to_datetime(MVBS.ping_time.data[-1]).year,
            pd.to_datetime(MVBS.ping_time.data[-1]).month,
            pd.to_datetime(MVBS.ping_time.data[-1]).day,
        )

        select_date = param.CalendarDate(
            default=start_date, bounds=(start_date, end_date), doc="Select date"
        )

        select_channel = param.Selector(
            objects=MVBS.channel.values.tolist(), doc="Select channel"
        )

        range_clim = param.Range(
            bounds=(MVBS.Sv.actual_range[0], MVBS.Sv.actual_range[-1]),
            doc="Select clim",
        )

        color_map = param.String(default="jet", doc="colormap")

        @param.depends("select_date", "select_channel", "range_clim", "color_map")
        def view(self):

            date_picker = self.select_date
            channel = self.select_channel
            clim = self.range_clim
            color_map = self.color_map

            start_time = (
                str(date_picker.year)
                + "-"
                + str(date_picker.month)
                + "-"
                + str(date_picker.day)
                + "T00:00:00"
            )

            end_time = (
                str(date_picker.year)
                + "-"
                + str(date_picker.month)
                + "-"
                + str(date_picker.day)
                + "T23:59:59"
            )

            time_range = slice(start_time, end_time)

            plot1 = (
                self.MVBS.Sv.sel(channel=channel, ping_time=time_range)
                .hvplot.image(
                    x="ping_time",
                    y="echo_range",
                    c="Sv",
                    title="Sv : " + channel,
                    cmap=color_map,
                    clim=clim,
                    rasterize=True,
                )
                .options(invert_yaxis=True)
            )

            return plot1

    echogram = Echogram()

    return pn.Row(echogram.param, echogram.view)
