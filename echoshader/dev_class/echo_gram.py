import panel

panel.extension("vtk")

import warnings

import holoviews
import hvplot.xarray
import pandas
import param
from holoviews import streams

warnings.simplefilter("ignore")


class Echogram(param.Parameterized):
    def __init__(self, MVBS_ds, **params):

        super().__init__(**params)

        self.MVBS_ds = MVBS_ds

        # set this to 'quadmesh' to avoid "not evenly sampled" error
        self.plot_types = "image"

        # set this to 'False' to use time_range_picker
        self.datetime_range_input_model = True

        self.lower_time = pandas.to_datetime(self.MVBS_ds.ping_time.data[0])

        self.upper_time = pandas.to_datetime(self.MVBS_ds.ping_time.data[-1])

        # http://holoviews.org/user_guide/Applying_Customizations.html
        self.gram_opts = holoviews.opts(invert_yaxis=True)

        self._sync_widget()

    def _sync_widget(self):

        # https://panel.holoviz.org/reference/widgets/DatetimeRangePicker.html#widgets-gallery-datetimerangepicker
        self.time_range_picker = panel.widgets.DatetimeRangePicker(
            name="Datetime Range Picker", value=(self.lower_time, self.upper_time)
        )

        # https://panel.holoviz.org/reference/widgets/DatetimeRangeInput.html

        # start_input = param.Date(bounds=(self.lower_time, self.upper_time),
        #                          default=self.lower_time,
        #                          doc="Select start time")

        # end_input = param.Date(bounds=(self.lower_time, self.upper_time),
        #                        default=self.upper_time,
        #                        doc="Select end time")

        self.datetime_range_input = panel.widgets.DatetimeRangeInput(
            name="Datetime Range Input",
            start=self.lower_time,
            end=self.upper_time,
            value=(self.lower_time, self.upper_time),
        )

        # DatetimeRangeSlider doesn't exist in panel ( v0.13.1, 2022-7-30 )
        # AttributeError: module 'panel.widgets' has no attribute 'DatetimeRangeSlider'
        # https://panel.holoviz.org/reference/widgets/DatetimeRangeSlider.html#widgets-gallery-datetimerangeslider
        # self.datetime_range_input = panel.widgets.DatetimeRangeSlider(
        #     name='Datetime Range Input',
        #     start=self.lower_time,
        #     end=self.upper_time,
        #     value=(self.lower_time, self.upper_time))

        # https://panel.holoviz.org/reference/widgets/Select.html#widgets-gallery-select

        # select_channel = param.Selector(objects=
        #                                 self.MVBS_ds.channel.values.tolist(),
        #                                 doc="Select channel")
        self.channel_select = panel.widgets.Select(
            name="Channel Select", options=self.MVBS_ds.channel.values.tolist()
        )

        # https://panel.holoviz.org/reference/widgets/TextInput.html#widgets-gallery-textinput

        # color_map = param.String(default="jet", doc="Colormap")
        self.color_map = panel.widgets.TextInput(name="Color Map", placeholder="jet")

        # https://panel.holoviz.org/reference/widgets/EditableRangeSlider.html#widgets-gallery-editablerangeslider

        # range_clim = param.Range(bounds=(self.MVBS_ds.Sv.actual_range[0],
        #                                  self.MVBS_ds.Sv.actual_range[-1]),
        #                                  doc="Select clim")
        self.range_clim = panel.widgets.EditableRangeSlider(
            name="Sv Range Slider",
            start=self.MVBS_ds.Sv.actual_range[0],
            end=self.MVBS_ds.Sv.actual_range[-1],
            value=(self.MVBS_ds.Sv.actual_range[0], self.MVBS_ds.Sv.actual_range[-1]),
            step=0.01,
        )

        self.widgets = panel.WidgetBox(
            str(self.lower_time) + " to " + str(self.upper_time),
            self.datetime_range_input
            if self.datetime_range_input_model == True
            else self.time_range_picker,
            self.channel_select,
            self.color_map,
            self.range_clim,
            erase_error(),
        )

    # https://panel.holoviz.org/user_guide/APIs.html#parameterized-classes
    @param.depends(
        "datetime_range_input.value",
        "time_range_picker.value",
        "channel_select.value",
        "color_map.value",
        "range_clim.value",
    )
    def view(self):

        start_time = (
            self.datetime_range_input.value[0]
            if self.datetime_range_input_model == True
            else self.time_range_picker.value[0]
        )

        end_time = (
            self.datetime_range_input.value[-1]
            if self.datetime_range_input_model == True
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
            )
            .options(self.gram_opts)
        )

        # get box from echogram
        self.box = holoviews.streams.BoundsXY(
            source=self.gram,
            bounds=(
                self.MVBS_ds.sel(ping_time=time_range).ping_time.values[0],
                self.MVBS_ds.echo_range.values[-1],
                self.MVBS_ds.sel(ping_time=time_range).ping_time.values[-1],
                self.MVBS_ds.echo_range.values[0],
            ),
        )

        # plot box
        self.bounds = holoviews.DynamicMap(
            lambda bounds: holoviews.Bounds(bounds).opts(
                line_width=2, line_color="white"
            ),
            streams=[self.box],
        )

        return self.gram * self.bounds

    def get_box_data(self):
        return self.MVBS_ds.sel(
            channel=self.channel_select.value,
            ping_time=slice(self.box.bounds[0], self.box.bounds[2]),
            echo_range=slice(self.box.bounds[3], self.box.bounds[1]),
        )


def erase_error():
    return panel.pane.HTML(
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
