import echo_gram

import holoviews
import hvplot.xarray
import hvplot.pandas
import param
import panel

import pandas

def simple_hist(echogram):
    '''
    Equip an echogram with simple hist

    Parameters
    ----------
    echogram : hvplot.image
        holoview image MVBS_ds xarray.Dataset with a specific frequency
        rasterize must be set to False

    Returns
    -------
    holoviews.NdLayout
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
    '''
    def selected_range_hist(x_range, y_range):
        # Apply current ranges
        obj = echogram.select(
            ping_time=x_range,
            echo_range=y_range) if x_range and y_range else echogram

        # Compute histogram
        return holoviews.operation.histogram(obj)

    # Define a RangeXY stream linked to the image
    rangexy = holoviews.streams.RangeXY(source=echogram)
    hist = holoviews.DynamicMap(selected_range_hist, streams=[rangexy])
    return echogram << hist


class EchoStats(echo_gram.Echogram):
    """
    A class for plotting echogram with statistic info
    
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
        
    hist_opts = holoviews.opts
        Modify the style of hist
        See more in : http://holoviews.org/user_guide/Applying_Customizations.html
        Or see more in : https://hvplot.holoviz.org/user_guide/Customization.html
    
    table_opts = holoviews.opts
        Modify the style of table
        See more in : http://holoviews.org/user_guide/Applying_Customizations.html
        Or see more in : https://hvplot.holoviz.org/user_guide/Customization.html    
        
    hist_cols : int
        Number of columns when viewing all hists
        If the value is set to '1', there will be only one layout column
        If there are three kinds hists(frequencies) and the value is set to '3', there will be only one layout Row(three Columns)
        
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
        
    hist_button : panel.widgets.Button
        Button panel widget used to update the hist and table
        See more in : https://panel.holoviz.org/reference/widgets/Button.html#widgets-gallery-button
    
    bin_size_input : panel.widgets.IntInput
        Intinput panel widget used to input bin size for hist
        See more in : https://panel.holoviz.org/reference/widgets/IntInput.html
        
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
        Get a single echogram which can be controled by widgets attributes
      
    view_all_gram():
        Get all echograms which can be controled by widgets attributes
        
    get_box_data(): 
        Get MVBS data with a specific frequency in select box
        
    get_all_box_data(): 
        Get MVBS data with all frequencies in select box
    
    view_table():
        Get a table describing Sv with a specific frequency
        
    view_hist():
        Get a hist describing box Sv with a specific frequency
        
    view_all_table():
        Get a table describing box Sv with all frequencies
        
    view_sum_hist():
        Get a table describing all box Sv values
        
    view_overlay_hist():
        Get a table describing box Sv values with all frequencies in form of 'overlay'
        See more in : https://holoviews.org/user_guide/Composing_Elements.html#overlay
        
    view_layout_hist():
        Get a table describing box Sv values with all frequencies in form of 'layout'
        See more in : https://holoviews.org/user_guide/Composing_Elements.html#layout
        
    Examples
    --------    
        echostats = echo_stats.EchoStats(MVBS_ds)
        panel.Row(echostats.widgets, panel.Column(echostats.view_gram, echostats.view_all_table, echostats.view_outlay_hist))        
    """
    def __init__(self, MVBS_ds):
        '''
        Constructs all the necessary attributes for the echogram object.
        
        Parameters
        ----------
        MVBS_ds : xarray.Dataset
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'
        
        Returns
        -------
        self
        '''
        super().__init__(MVBS_ds)

        self.hist_opts = holoviews.opts(width=700)
        
        self.table_opts = holoviews.opts(width=600)
        
        self.hist_cols = 1
        
        self._sync_widge_stats()

    def _sync_widge_stats(self):
        '''
        Constructs all the necessary hist widgets attributes        
        '''
        # https://panel.holoviz.org/reference/widgets/Button.html#widgets-gallery-button
        self.hist_button = panel.widgets.Button(name='Update Hist and Desc Tabel📊',
                                           button_type='primary')

        # https://panel.holoviz.org/reference/widgets/IntInput.html
        self.bin_size_input = panel.widgets.IntInput(name='Bin Size Input',
                                                     value=24,
                                                     step=10,
                                                     start=0)

        self.widgets = panel.WidgetBox(
            self.widgets, panel.WidgetBox(self.bin_size_input, self.hist_button))

    @param.depends('hist_button.value')
    def view_table(self):
        '''
        Create a table describing stats info about box Sv with a specific frequency

        Returns
        -------
        holoviews.Table
            Show basic stats info which contains skew and kurtosis
        '''
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        channel = self.channel_select.value

        # Apply current ranges
        obj_df = self.MVBS_ds.sel(channel=channel,
                                  ping_time=time_range,
                                  echo_range=echo_range)\
                                .Sv.to_dataframe()

        skew = obj_df['Sv'].skew()
        kurt = obj_df['Sv'].kurt()

        obj_desc = obj_df.describe().reset_index()

        obj_desc.loc[len(obj_desc)] = ['skew', skew]
        obj_desc.loc[len(obj_desc)] = ['kurtosis', kurt]
        obj_desc.loc[len(obj_desc)] = ['Channel', channel]

        # Compute histogram
        return holoviews.Table(obj_desc.values, 'stat',
                               'value').opts(self.table_opts)

    @param.depends('hist_button.value')
    def view_hist(self):
        '''
        Create a hist for box Sv with a specific frequency
                
        Returns
        -------
        hvplot.hist
        '''

        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        channel = self.channel_select.value

        # Apply current ranges
        obj_df = self.MVBS_ds.sel(channel=channel,
                                  ping_time=time_range,
                                  echo_range=echo_range)\
                                .Sv.to_dataframe()
        # Compute histogram
        return obj_df.hvplot.hist('Sv', bins=self.bin_size_input.value).opts(
            self.hist_opts)
                        
    @param.depends('hist_button.value')
    def view_all_table(self):
        '''
        Create a table describing stats info about box Sv with all frequencies
                
        Returns
        -------
        holoviews.Table
            Show basic stats info which contains skew and kurtosis
        '''
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        # Apply current ranges
        obj_df = self.MVBS_ds.sel(ping_time=time_range,
                                  echo_range=echo_range)\
                                .Sv.to_dataframe()

        skew = obj_df['Sv'].skew()
        kurt = obj_df['Sv'].kurt()

        obj_desc = obj_df.describe().reset_index()

        obj_desc.loc[len(obj_desc)] = ['skew', skew]
        obj_desc.loc[len(obj_desc)] = ['kurtosis', kurt]

        for channel in self.MVBS_ds.channel.values:

            obj_desc.loc[len(obj_desc)] = [' ', ' ']

            obj_desc.loc[len(obj_desc)] = ['Channel', channel]

            obj_df_channel = self.MVBS_ds.sel(channel=channel,
                                            ping_time=time_range,
                                            echo_range=echo_range)\
                                .Sv.to_dataframe()

            skew = obj_df_channel['Sv'].skew()
            kurt = obj_df_channel['Sv'].kurt()

            obj_df_channel = obj_df_channel.describe().reset_index()

            obj_df_channel.loc[len(obj_df_channel)] = ['skew', skew]
            obj_df_channel.loc[len(obj_df_channel)] = ['kurtosis', kurt]

            head = pandas.DataFrame(data=['Channel', channel])

            obj_desc = pandas.concat([obj_desc, obj_df_channel])

        # Compute histogram
        return holoviews.Table(obj_desc.values, 'stat',
                               'value').opts(self.table_opts)
                               
    @param.depends('hist_button.value')
    def view_sum_hist(self):
        '''
        Create a hist for box Sv values of all frequencies
                
        Returns
        -------
        hvplot.hist
        '''

        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        # Apply current ranges
        obj_df = self.MVBS_ds.sel(ping_time=time_range,
                                  echo_range=echo_range)\
                                .Sv.to_dataframe()
        # Compute histogram
        return obj_df.hvplot.hist('Sv', bins=self.bin_size_input.value).opts(
            self.hist_opts)            
            
    @param.depends('hist_button.value')
    def view_overlay_hist(self):
        '''
        Create a overlay hist for box Sv
        
        Returns
        -------
        holoviews.NdLayout
            See more in : https://holoviews.org/user_guide/Composing_Elements.html#overlay
        '''
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        return MVBS_ds.sel(ping_time=time_range,
                                echo_range=echo_range)\
                                .Sv.hvplot.hist('Sv',
                                                by='channel',
                                                bins=self.bin_size_input.value,
                                                subplots=False,
                                                alpha=0.7,
                                                legend='top').opts(self.hist_opts)

    @param.depends('hist_button.value')
    def view_layout_hist(self):
        '''
        Create a layout hist for box Sv
        
        Returns
        -------
        holoviews.NdLayout
            See more in : https://holoviews.org/user_guide/Composing_Elements.html#layout
        '''
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        return MVBS_ds.sel(ping_time=time_range,
                                echo_range=echo_range)\
                                .Sv.hvplot.hist('Sv',
                                                by='channel',
                                                bins=self.bin_size_input.value,
                                                subplots=True,
                                                legend='top').opts(self.hist_opts).cols(self.hist_cols)
