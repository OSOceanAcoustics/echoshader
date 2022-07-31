"""echo_stats.py module

to help echogram get corresponding histograms and stats data
"""
import echo_gram
import holoviews
import hvplot.pandas
import hvplot.xarray
import pandas
import panel
import param


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


class EchoStats(echo_gram.Echogram):
    def __init__(self, MVBS_ds):
        super().__init__(MVBS_ds)

        self.hist_opts = holoviews.opts(width=700)
        self.table_opts = holoviews.opts.Table(width=600)
        self.hist_cols = 1
        self._sync_widge_stats()

    def _sync_widge_stats(self):

        # https://panel.holoviz.org/reference/widgets/Button.html#widgets-gallery-button
        self.button = panel.widgets.Button(
            name="Update Hist and Desc Table📊", button_type="primary"
        )

        # https://panel.holoviz.org/reference/widgets/IntInput.html
        self.bin_size_input = panel.widgets.IntInput(
            name="Bin Size Input", value=24, step=10, start=0
        )

        self.widgets = panel.WidgetBox(
            self.widgets, panel.WidgetBox(self.bin_size_input, self.button)
        )

    @param.depends("button.value")
    def view_box_table(self):
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        channel = self.channel_select.value

        # Apply current ranges
        obj_df = self.MVBS_ds.sel(
            channel=channel, ping_time=time_range, echo_range=echo_range
        ).Sv.to_dataframe()

        skew = obj_df["Sv"].skew()
        kurt = obj_df["Sv"].kurt()

        obj_desc = obj_df.describe().reset_index()

        obj_desc.loc[len(obj_desc)] = ["skew", skew]
        obj_desc.loc[len(obj_desc)] = ["kurtosis", kurt]
        obj_desc.loc[len(obj_desc)] = ["Channel", channel]

        # Compute histogram
        return holoviews.Table(obj_desc.values, "stat", "value").opts(self.table_opts)

    @param.depends("button.value")
    def view_box_hist(self):

        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        channel = self.channel_select.value

        # Apply current ranges
        obj_df = self.MVBS_ds.sel(
            channel=channel, ping_time=time_range, echo_range=echo_range
        ).Sv.to_dataframe()
        # Compute histogram
        return obj_df.hvplot.hist("Sv", bins=self.bin_size_input.value).opts(
            self.hist_opts
        )

    @param.depends("button.value")
    def view_all_table(self):
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        # Apply current ranges
        obj_df = self.MVBS_ds.sel(
            ping_time=time_range, echo_range=echo_range
        ).Sv.to_dataframe()

        skew = obj_df["Sv"].skew()
        kurt = obj_df["Sv"].kurt()

        obj_desc = obj_df.describe().reset_index()

        obj_desc.loc[len(obj_desc)] = ["skew", skew]
        obj_desc.loc[len(obj_desc)] = ["kurtosis", kurt]

        for channel in self.MVBS_ds.channel.values:

            obj_desc.loc[len(obj_desc)] = [" ", " "]

            obj_desc.loc[len(obj_desc)] = ["Channel", channel]

            obj_df_channel = self.MVBS_ds.sel(
                channel=channel, ping_time=time_range, echo_range=echo_range
            ).Sv.to_dataframe()

            skew = obj_df_channel["Sv"].skew()
            kurt = obj_df_channel["Sv"].kurt()

            obj_df_channel = obj_df_channel.describe().reset_index()

            obj_df_channel.loc[len(obj_df_channel)] = ["skew", skew]
            obj_df_channel.loc[len(obj_df_channel)] = ["kurtosis", kurt]

            head = pandas.DataFrame(data=["Channel", channel])

            obj_desc = pandas.concat([obj_desc, obj_df_channel])

        # Compute histogram
        return holoviews.Table(obj_desc.values, "stat", "value").opts(self.table_opts)

    @param.depends("button.value")
    def view_outlay_hist(self):

        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        return (
            self.MVBS_ds.sel(ping_time=time_range, echo_range=echo_range)
            .Sv.hvplot.hist(
                "Sv",
                by="channel",
                bins=self.bin_size_input.value,
                subplots=False,
                alpha=0.7,
                legend="top",
            )
            .opts(self.hist_opts)
        )

    @param.depends("button.value")
    def view_layout_hist(self):

        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        return (
            self.MVBS_ds.sel(ping_time=time_range, echo_range=echo_range)
            .Sv.hvplot.hist(
                "Sv",
                by="channel",
                bins=self.bin_size_input.value,
                subplots=True,
                legend="top",
            )
            .opts(self.hist_opts)
            .cols(self.hist_cols)
        )
