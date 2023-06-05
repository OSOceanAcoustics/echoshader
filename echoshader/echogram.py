import warnings

import holoviews
import hvplot.xarray  # noqa
import pandas
import panel
import param

warnings.simplefilter("ignore")


class Echogram(param.Parameterized):
    """
    A class for plotting basic echogram

    Attributes
    ----------
    MVBS_ds : xarray.Dataset
        MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'

    plot_types : str
        Usually using 'image' or 'quadmesh'
        See 'image' in : https://hvplot.holoviz.org/reference/xarray/image.html#xarray-gallery-image
        See 'quadmesh' in : https://hvplot.holoviz.org/reference/xarray/quadmesh.html#xarray-gallery-quadmesh
        Notice : When using 'quadmesh', box_select or other tools may not be applicable

    datetime_range_input_model : bool
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

    gram_opts : holoviews.opts
        Modify the style of echogram
        See more in : http://holoviews.org/user_guide/Applying_Customizations.html
        Or see more in : https://hvplot.holoviz.org/user_guide/Customization.html

    bound_opts : holoviews.opts
        Modify the style of bound
        See more in : https://hvplot.holoviz.org/user_guide/Customization.html
        Or see more in : https://hvplot.holoviz.org/user_guide/Customization.html

    gram_cols : int
        Number of columns when viewing all grams
        If the value is set to '1', there will be only one layout column
        If there are three kinds of grams(frequencies) and the value is set to '3', there will be only one layout Row(three Columns)

    time_range_picker : panel.widgets
        Picker panel widget used to input datetime range
        See more in : https://panel.holoviz.org/reference/widgets/DatetimeRangePicker.html#widgets-gallery-datetimerangepicker

    datetime_range_input : panel.widgets
        Input panel widget used to input datetime range
        See more in : https://panel.holoviz.org/reference/widgets/DatetimeRangeInput.html

    channel_select : panel.widgets
        Select panel widget used to select frequency
        See more in : https://panel.holoviz.org/reference/widgets/Select.html#widgets-gallery-select

    color_map : panel.widgets
        Text input panel widget used to input colormap
        See more in : https://panel.holoviz.org/reference/widgets/TextInput.html#widgets-gallery-textinput

    range_clim : panel.widgets
        Editable range slider widget used to select clim range
        See more in : https://panel.holoviz.org/reference/widgets/EditableRangeSlider.html#widgets-gallery-editablerangeslider

    widgets : panel.widgets
        Arrange multiple panel objects in a vertical container
        See more in : https://panel.holoviz.org/reference/layouts/WidgetBox.html#layouts-gallery-widgetbox

    gram : hvplot.image
        Echogram
        Only be accessed after calling method 'view_gram()'

    box : holoviews.streams.BoundsXY
        Bound values of select box
        Only be accessed after calling method 'view_gram()'

    bounds : holoviews.streams.Bounds
        Bounds plot in echogram
        Only be accessed after calling method 'view_gram()'

    all_gram : holoviews.NdLayout
        Echograms with all frequencies
        Only be accessed after calling method 'view_all_gram()'

    Methods
    -------
    view_gram():
        Get a single echogram which can be controlled by widgets attributes

    view_all_gram():
        Get all echograms which can be controlled by widgets attributes

    get_box_data():
        Get MVBS data with a specific frequency in select box

    get_all_box_data():
        Get MVBS data with all frequencies in select box

    Examples
    --------
        echogram = Echogram(MVBS_ds)

        echogram.bound_opts = holoviews.opts(line_color='black')

        panel.Row(echogram.widgets, echogram.view_gram)

    """  # noqa

    def __init__(self, MVBS_ds):
        """
        Constructs all the necessary attributes for the echogram object.

        Parameters
        ----------
        MVBS_ds : xarray.Dataset
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'

        Returns
        -------
        self
        """
        super().__init__()

        self.MVBS_ds = MVBS_ds

        # set this to 'quadmesh' to avoid "not evenly sampled" error
        self.plot_types = "image"

        # set this to 'False' to use time_range_picker
        self.datetime_range_input_model = True

        self.lower_time = pandas.to_datetime(self.MVBS_ds.ping_time.data[0])

        self.upper_time = pandas.to_datetime(self.MVBS_ds.ping_time.data[-1])

        # http://holoviews.org/user_guide/Applying_Customizations.html
        self.gram_opts = holoviews.opts(invert_yaxis=False, tools=["hover","box_select"])

        self.bound_opts = holoviews.opts(line_width=1.5, line_color="white")

        self.gram_cols = 1

        self._sync_widget()

    def _sync_widget(self):
        """
        Constructs all the necessary widgets attributes
        """

        # Param Substitute
        # start_input = param.Date(bounds=(self.lower_time, self.upper_time),
        #                          default=self.lower_time,
        #                          doc="Select start time")

        # end_input = param.Date(bounds=(self.lower_time, self.upper_time),
        #                        default=self.upper_time,
        #                        doc="Select end time")

        # https://panel.holoviz.org/reference/widgets/DatetimeRangePicker.html#widgets-gallery-datetimerangepicker

        self.time_range_picker = panel.widgets.DatetimeRangePicker(
            name="Datetime Range Picker", value=(self.lower_time, self.upper_time)
        )

        # https://panel.holoviz.org/reference/widgets/DatetimeRangeInput.html

        self.datetime_range_input = panel.widgets.DatetimeRangeInput(
            name="Datetime Range Input",
            start=self.lower_time,
            end=self.upper_time,
            value=(self.lower_time, self.upper_time),
        )

        # Currently datetimeRangeSlider doesn't exist in panel ( v0.13.1, 2022-7-30 )
        # AttributeError: module 'panel.widgets' has no attribute 'DatetimeRangeSlider'

        # https://panel.holoviz.org/reference/widgets/DatetimeRangeSlider.html#widgets-gallery-datetimerangeslider

        # self.datetime_range_input = panel.widgets.DatetimeRangeSlider(
        #     name='Datetime Range Input',
        #     start=self.lower_time,
        #     end=self.upper_time,
        #     value=(self.lower_time, self.upper_time))

        # Param Substitute
        # select_channel = param.Selector(objects=
        #                                 self.MVBS_ds.channel.values.tolist(),
        #                                 doc="Select channel")

        # https://panel.holoviz.org/reference/widgets/Select.html#widgets-gallery-select

        self.channel_select = panel.widgets.Select(
            name="Channel Select", options=self.MVBS_ds.channel.values.tolist()
        )

        # Param Substitute
        # color_map = param.String(default="jet", doc="Colormap")

        # https://panel.holoviz.org/reference/widgets/TextInput.html#widgets-gallery-textinput

        self.color_map = panel.widgets.TextInput(name="Color Map", placeholder="jet")

        # Param Substitute
        # range_clim = param.Range(bounds=(self.MVBS_ds.Sv.actual_range[0],
        #                                  self.MVBS_ds.Sv.actual_range[-1]),
        #                                  doc="Select clim")

        # https://panel.holoviz.org/reference/widgets/EditableRangeSlider.html#widgets-gallery-editablerangeslider

        self.range_clim = panel.widgets.EditableRangeSlider(
            name="Sv Range Slider",
            start=self.MVBS_ds.Sv.actual_range[0],
            end=self.MVBS_ds.Sv.actual_range[-1],
            value=(self.MVBS_ds.Sv.actual_range[0], self.MVBS_ds.Sv.actual_range[-1]),
            step=0.01,
        )

        # https://panel.holoviz.org/reference/layouts/WidgetBox.html#layouts-gallery-widgetbox

        self.widgets = panel.WidgetBox(
            str(self.lower_time) + " to " + str(self.upper_time),
            self.datetime_range_input
            if self.datetime_range_input_model is True
            else self.time_range_picker,
            self.channel_select,
            self.color_map,
            self.range_clim,
        )

    # https://panel.holoviz.org/user_guide/APIs.html#parameterized-classes
    @param.depends(
        "datetime_range_input.value",
        "time_range_picker.value",
        "channel_select.value",
        "color_map.value",
        "range_clim.value",
    )
    def view_gram(self):
        """
        Create a echogram combined with bounds(created by select_box)

        Returns
        -------
        holoviews.NdLayout
            Combined layout plots(single echogram + boound)
            See more in : https://holoviews.org/user_guide/Composing_Elements.html
            Or see more in : https://holoviews.org/user_guide/Building_Composite_Objects.html
        """
        start_time = (
            self.datetime_range_input.value[0]
            if self.datetime_range_input_model is True
            else self.time_range_picker.value[0]
        )

        end_time = (
            self.datetime_range_input.value[-1]
            if self.datetime_range_input_model is True
            else self.time_range_picker.value[-1]
        )

        time_range = slice(start_time, end_time)

        channel = self.channel_select.value

        clim = self.range_clim.value

        color_map = "jet" if len(self.color_map.value) == 0 else self.color_map.value

        rasterize = True if self.plot_types == "image" else False

        self.gram = (
            self.MVBS_ds.Sv.sel(channel=channel, ping_time=time_range)
            .hvplot(
                kind=self.plot_types,
                x="ping_time",
                y="echo_range",
                title="Channel : " + channel,
                cmap=color_map,
                clim=clim,
                rasterize=rasterize,
                xlabel="Time (UTC)",
                ylabel="Depth (m)",
                clabel="Sv(dB)",
            )
            .options(self.gram_opts)
        )

        # get box from echogram
        self.box = holoviews.streams.BoundsXY(
            source=self.gram,
            bounds=(
                self.MVBS_ds.sel(ping_time=time_range).ping_time.values[0],
                self.MVBS_ds.echo_range.values[0],
                self.MVBS_ds.sel(ping_time=time_range).ping_time.values[-1],
                self.MVBS_ds.echo_range.values[-1],
            ),
        )

        # plot box
        self.bounds = holoviews.DynamicMap(
            lambda bounds: holoviews.Bounds(bounds).opts(self.bound_opts),
            streams=[self.box],
        )

        return self.gram * self.bounds

    @param.depends(
        "datetime_range_input.value",
        "time_range_picker.value",
        "color_map.value",
        "range_clim.value",
    )
    def view_all_gram(self):
        """
        Create echograms combined with bounds(created by select_box)

        Returns
        -------
        holoviews.NdLayout
            Combined layout plots(multiple echograms + boound)
            See more in : https://holoviews.org/user_guide/Composing_Elements.html
            Or see more in : https://holoviews.org/user_guide/Building_Composite_Objects.html
        """
        start_time = (
            self.datetime_range_input.value[0]
            if self.datetime_range_input_model is True
            else self.time_range_picker.value[0]
        )

        end_time = (
            self.datetime_range_input.value[-1]
            if self.datetime_range_input_model is True
            else self.time_range_picker.value[-1]
        )

        time_range = slice(start_time, end_time)

        clim = self.range_clim.value

        color_map = "jet" if len(self.color_map.value) == 0 else self.color_map.value

        rasterize = True if self.plot_types == "image" else False

        self.all_gram = (
            self.MVBS_ds.Sv.sel(
                ping_time=time_range, channel=self.MVBS_ds.channel.values[0]
            )
            .hvplot(
                kind=self.plot_types,
                x="ping_time",
                y="echo_range",
                title="Channel : " + self.MVBS_ds.channel.values[0],
                cmap=color_map,
                clim=clim,
                rasterize=rasterize,
                xlabel="Time (UTC)",
                ylabel="Depth (m)",
                clabel="Sv(dB)",
            )
            .opts(self.gram_opts)
        )

        for index, channel in enumerate(self.MVBS_ds.channel.values):
            if index == 0:
                continue

            self.all_gram += (
                self.MVBS_ds.Sv.sel(ping_time=time_range, channel=channel)
                .hvplot(
                    kind=self.plot_types,
                    x="ping_time",
                    y="echo_range",
                    title="Channel : " + channel,
                    cmap=color_map,
                    clim=clim,
                    rasterize=rasterize,
                )
                .opts(self.gram_opts)
            )
            # get box from echogram

        self.box = holoviews.streams.BoundsXY(
            source=self.all_gram[0],
            bounds=(
                self.MVBS_ds.sel(ping_time=time_range).ping_time.values[0],
                self.MVBS_ds.echo_range.values[0],
                self.MVBS_ds.sel(ping_time=time_range).ping_time.values[-1],
                self.MVBS_ds.echo_range.values[-1],
            ),
        )

        # plot box
        self.bounds = holoviews.DynamicMap(
            lambda bounds: holoviews.Bounds(bounds).opts(self.bound_opts),
            streams=[self.box],
        )

        return self.all_gram.cols(self.gram_cols) * self.bounds

    def get_box_data(self):
        """
        Get MVBS_ds data with a specific frequency from echogram in selected box

        Returns
        -------
        MVBS_ds : xarray.Dataset
        """
        return self.MVBS_ds.sel(
            channel=self.channel_select.value,
            ping_time=slice(self.box.bounds[0], self.box.bounds[2]),
            echo_range=slice(self.box.bounds[1], self.box.bounds[3]) if self.box.bounds[3]>self.box.bounds[1] else slice(self.box.bounds[3], self.box.bounds[1])
        )

    def get_all_box_data(self):
        """
        Get MVBS_ds data with all frequencies from echogram in selected box

        Returns
        -------
        MVBS_ds : xarray.Dataset
        """
        return self.MVBS_ds.sel(
            ping_time=slice(self.box.bounds[0], self.box.bounds[2]),
            echo_range=slice(self.box.bounds[1], self.box.bounds[3]) if self.box.bounds[3]>self.box.bounds[1] else slice(self.box.bounds[3], self.box.bounds[1])
        )


def erase_error():
    """Get a panel widget to toggle off warning info

    Returns
    -------
    erase_widget : panel.pane.HTML
        Create a panel widget to toggle off warning info
        Designed for erasing errors caused by not even-sampled Sv image
        see more in : https://panel.holoviz.org/reference/panes/HTML.html#panes-gallery-html

    Examples
    --------
        erase_widget = erase_error()
    """
    erase_widget = panel.pane.HTML(
        """<script>code_show_err=false;
         function code_toggle_err() {
             if (code_show_err){
                 $('div.output_stderr').hide();
             }
             else {
                 $('div.output_stderr').show();
             }
         code_show_err = !code_show_err
        }
        $( document ).ready(code_toggle_err);
        </script>
        To toggle on/off error:
        Click <a href="javascript:code_toggle_err()">Here</a>."""
    )

    return erase_widget
