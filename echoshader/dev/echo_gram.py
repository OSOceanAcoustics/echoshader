"""echo_gram.py module.

use panel to get a echogram with control widgets

if users just want a simple echogram
    import hvplot.xarray and directly call fuction ds_Sv.hvplot()
    like below:
    plot=ds_Sv.hvplot(
        kind='image',
        x='ping_time',
        y='echo_range',
        c='Sv', 
        title='Echogram',
        cmap='jet',
        clim=()-80,-30),
        rasterize=True,
        width=600,
        height=400,
        flip_yaxis=True)
"""

import param
import hvplot.xarray
import panel as pn
pn.extension()

import datetime
import pandas

import warnings
warnings.simplefilter("ignore")

def echogram(MVBS):
    '''Get a echogram with control components

    Parameters
    ----------
    MVBS : MVBS_ds data set or ds_Sv data array

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
    
    '''

    def getMVBS():
        # help class Echogram get MVBS

        return MVBS

    # below annotation once used to help get a datepicker
    # but now time range input used instead

    # def get_date_range():
    #     start_date = datetime.date(
    #         pandas.to_datetime(MVBS.ping_time.data[0]).year,
    #         pandas.to_datetime(MVBS.ping_time.data[0]).month,
    #         pandas.to_datetime(MVBS.ping_time.data[0]).day)

    #     end_date = datetime.date(
    #         pandas.to_datetime(MVBS.ping_time.data[-1]).year,
    #         pandas.to_datetime(MVBS.ping_time.data[-1]).month,
    #         pandas.to_datetime(MVBS.ping_time.data[-1]).day)

    #     return start_date, end_date

    # def get_date(date_picker):
    #     start_time = str(date_picker.year)+"-"\
    #     +str(date_picker.month)+"-"\
    #     +str(date_picker.day)+"T00:00:00"

    #     end_time = str(date_picker.year)+"-"\
    #     +str(date_picker.month)+"-"\
    #     +str(date_picker.day)+"T23:59:59"

    #     return start_time, end_time

    def get_time_range():
        # get time range according to MVBS input

        start_time = pandas.to_datetime(MVBS.ping_time.data[0])

        end_time = pandas.to_datetime(MVBS.ping_time.data[-1])

        return start_time, end_time

    class Echogram(param.Parameterized):

        MVBS = getMVBS()

        # start_date, end_date = get_date_range()

        # select_date = param.CalendarDate(default=start_date,
        #                                  bounds=(start_date, end_date),
        #                                  doc="Select date")

        start_time, end_time = get_time_range()

        start_input = param.Date(bounds=(start_time, end_time),
                                 default=start_time,
                                 doc="Select start time")

        end_input = param.Date(bounds=(start_time, end_time),
                               default=end_time,
                               doc="Select end time")

        select_channel = param.Selector(objects=MVBS.channel.values.tolist(),
                                        doc="Select channel")

        range_clim = param.Range(bounds=(MVBS.Sv.actual_range[0],
                                         MVBS.Sv.actual_range[-1]),
                                 doc="Select clim")

        color_map = param.String(default="jet", doc="Colormap")

        # sometimes it report errors because of non-even sampled data
        # input "quadmesh" to get rid of it
        # but in this situation, rasterize may not applied
        chart_type = param.String(default="image", doc="Type of chart")

        @param.depends('start_input', 'end_input', 'select_channel',
                       'range_clim', 'color_map', 'chart_type')
        def view(self):

            # date_picker = self.select_date
            # start_time, end_time = get_date(date_picker)

            start_input_time = self.start_input

            end_input_time = self.end_input

            time_range = slice(start_input_time, end_input_time)

            channel = self.select_channel

            clim = self.range_clim

            color_map = self.color_map

            chart_type = self.chart_type

            rasterize = True if chart_type == 'image' else False

            gram=self.MVBS.Sv.sel(channel=channel,ping_time=time_range).hvplot(
                kind=chart_type,
                x='ping_time',
                y='echo_range',
                title='Sv : '+ channel,
                cmap=color_map,
                clim=clim,
                rasterize=rasterize)\
            .options(invert_yaxis=True)

            return gram

    return Echogram()
