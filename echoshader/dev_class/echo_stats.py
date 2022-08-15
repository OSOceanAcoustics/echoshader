import echo_gram
import holoviews
import hvplot.pandas
import hvplot.xarray
import pandas
import panel
import param


def simple_hist(echogram):
    """
    Equip an echogram with simple hist

    Parameters
    ----------
    echogram : hvplot.image
        holoview image MVBS_ds xarray.Dataset with a specific frequency
        rasterize must be set to False

    Returns
    -------
    echogram << hist : holoviews.NdLayout
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
    """
    A class for plotting basic echogram

    Attributes
    ----------
    MVBS_ds : xarray.Dataset
        MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'

    plot_types : str, default : 'image'
        Usually using 'image' or 'quadmesh'
        See 'image' in : https://hvplot.holoviz.org/reference/xarray/image.html#xarray-gallery-image
        See 'quadmesh' in : https://hvplot.holoviz.org/reference/xarray/quadmesh.html#xarray-gallery-quadmesh
        Notice : When using 'quadmesh', box_select or some tools may not be applicable

    datetime_range_input_model : bool, default : 'True'
        When 'True', use 'input' widget to input datetime range
        See more in: https://panel.holoviz.org/reference/widgets/DatetimeInput.html
        When 'False', use 'picker' widget to input datetime range
        See more in: https://panel.holoviz.org/reference/widgets/DatetimeRangePicker.html

    lower_time : datetime
        pandas datetime type
        Lower bound determined by MVBS input

    upper_time : datetime
        pandas datetime type
        Upper bound determined by MVBS input

    gram_opts : obj.opts, default : holoviews.opts(invert_yaxis=True)
        Modify the style of echogram
        See more in : http://holoviews.org/user_guide/Applying_Customizations.html
        Or see more in : https://hvplot.holoviz.org/user_guide/Customization.html

    bound_opts : obj.opts, default : holoviews.opts(line_width=1.5, line_color='white')
        Modify the style of bound
        See more in : https://hvplot.holoviz.org/user_guide/Customization.html
        Or see more in : https://hvplot.holoviz.org/user_guide/Customization.html

    gram_cols : int, default : 1
        Number of columns when viewing all grams
        If the value is set to '1', there will be only one layout column
        If there are three kinds grams(frequencies) and the value is set to '3', there will be only one layout Row (three Columns)

    hist_opts = holoviews.opts, default : holoviews.opts(width=700)
        Modify the style of hist
        See more in : http://holoviews.org/user_guide/Applying_Customizations.html
        Or see more in : https://hvplot.holoviz.org/user_guide/Customization.html

    table_opts = holoviews.opts, default : holoviews.opts(width=600)
        Modify the style of table
        See more in : http://holoviews.org/user_guide/Applying_Customizations.html
        Or see more in : https://hvplot.holoviz.org/user_guide/Customization.html

    hist_cols : int, default : 1
        Number of columns when viewing all hists
        If the value is set to '1', there will be only one layout column
        If there are three kinds hists(frequencies) and the value is set to '3', there will be only one layout Row (three Columns)

    time_range_picker : panel.widgets
        Picker panel widget to input datetime range
        See more in : https://panel.holoviz.org/reference/widgets/DatetimeRangePicker.html#widgets-gallery-datetimerangepicker

    datetime_range_input : panel.widgets
        Input panel widget to input datetime range
        See more in : https://panel.holoviz.org/reference/widgets/DatetimeRangeInput.html

    channel_select : panel.widgets
        Select panel widget to select frequency
        See more in : https://panel.holoviz.org/reference/widgets/Select.html#widgets-gallery-select

    color_map : panel.widgets
        Text input panel widget to input colormap
        See more in : https://panel.holoviz.org/reference/widgets/TextInput.html#widgets-gallery-textinput

    range_clim : panel.widgets
        Editable range slider widget to select clim range
        See more in : https://panel.holoviz.org/reference/widgets/EditableRangeSlider.html#widgets-gallery-editablerangeslider

    hist_button : panel.widgets.Button
        Click to update the hist and table
        See more in : https://panel.holoviz.org/reference/widgets/Button.html#widgets-gallery-button

    bin_size_input : panel.widgets.IntInput
        Input bin size for hist
        See more in : https://panel.holoviz.org/reference/widgets/IntInput.html

    widgets : panel.widgets
        Arrange multiple panel objects in a vertical container
        See more in : https://panel.holoviz.org/reference/layouts/WidgetBox.html#layouts-gallery-widgetbox

    gram : hvplot.image
        Echogram
        Only be accessed after calling method 'view_gram()'

    box : holoviews.streams.BoundsXY
        Bound values of selected box
        Only be accessed after calling method 'view_gram()'

    bounds : holoviews.streams.Bounds
        Bounds plot in echogram
        Only be accessed after calling method 'view_gram()'

    all_gram : holoviews.NdLayout
        Echograms with all frequencies
        Only be accessed after calling method 'view_all_gram()'

    Methods
    -------
    _sync_widget(self):
        Initialize widgets attributes
        Called in __init__(self, MVBS_ds, **params)

    view_gram(self):
        Get single echogram with control panel widgets

    view_all_gram(self):
        Get all echograms with control panel widgets

    get_box_data(self):
        Get MVBS data with a specific frequency in selected box

    get_all_box_data(self):
        Get MVBS data with all frequencies in selected box

    view_table(self):
        Get table describing Sv with specific frequency

    view_hist(self):
        Get hist describing box Sv with specific frequency

    view_all_table(self):
        Get table describing box Sv with all frequencies

    view_sum_hist(self):
        Get table describing all box Sv values

    view_outlay_hist(self):
        Get table describing box Sv values with all frequencies in form of outlay

    view_layout_hist(self):
        Get table describing box Sv values with all frequencies in form of layout

    Examples
    --------
        echostats = echo_stats.EchoStats(MVBS_ds)
        panel.Row(echostats.widgets,panel.Column(echostats.view_gram, echostats.view_all_table, echostats.view_outlay_hist))
    """

    def __init__(self, MVBS_ds):
        """
        Constructs all the necessary attributes for the echogram object.

        Parameters
        ----------
        MVBS_ds : xarray.Dataset
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'

        Returns
        -------
        None
        """
        super().__init__(MVBS_ds)

        self.hist_opts = holoviews.opts(width=700)

        self.table_opts = holoviews.opts(width=600)

        self.hist_cols = 1

        self._sync_widge_stats()

    def _sync_widge_stats(self):
        """
        Constructs all the necessary hist widgets attributes

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        # https://panel.holoviz.org/reference/widgets/Button.html#widgets-gallery-button
        self.hist_button = panel.widgets.Button(
            name="Update Hist and Desc Table📊", button_type="primary"
        )

        # https://panel.holoviz.org/reference/widgets/IntInput.html
        self.bin_size_input = panel.widgets.IntInput(
            name="Bin Size Input", value=24, step=10, start=0
        )

        self.widgets = panel.WidgetBox(
            self.widgets, panel.WidgetBox(self.bin_size_input, self.hist_button)
        )

    @param.depends("hist_button.value")
    def view_table(self):
        """
        Create a table describing stats info about box Sv with specific frequency

        Parameters
        ----------
        Self

        Returns
        -------
        holoviews.Table
            Show basic stats info, plus skew and kurtosis
        """
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

    @param.depends("hist_button.value")
    def view_hist(self):
        """
        Create a hist for box Sv with specific frequency

        Parameters
        ----------
        Self

        Returns
        -------
        hvplot.hist
        """

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

    @param.depends("hist_button.value")
    def view_all_table(self):
        """
        Create a table describing stats info about box Sv with all frequencies

        Parameters
        ----------
        Self

        Returns
        -------
        holoviews.Table
            Show basic stats info, plus skew and kurtosis
        """
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

    @param.depends("hist_button.value")
    def view_sum_hist(self):
        """
        Create a hist for box Sv values of all frequencies

        Parameters
        ----------
        Self

        Returns
        -------
        hvplot.hist
        """

        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        # Apply current ranges
        obj_df = self.MVBS_ds.sel(
            ping_time=time_range, echo_range=echo_range
        ).Sv.to_dataframe()
        # Compute histogram
        return obj_df.hvplot.hist("Sv", bins=self.bin_size_input.value).opts(
            self.hist_opts
        )

    @param.depends("hist_button.value")
    def view_outlay_hist(self):
        """
        Create a outlay hist for box Sv

        Parameters
        ----------
        Self

        Returns
        -------
        holoviews.NdLayout
        """
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        return (
            MVBS_ds.sel(ping_time=time_range, echo_range=echo_range)
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

    @param.depends("hist_button.value")
    def view_layout_hist(self):
        """
        Create a layout hist for box Sv

        Parameters
        ----------
        Self

        Returns
        -------
        holoviews.NdLayout
        """
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        return (
            MVBS_ds.sel(ping_time=time_range, echo_range=echo_range)
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
