import geoviews
import panel
import param

import echo_gram
import echo_curtain

import pandas


# https://geoviews.org/gallery/bokeh/tile_sources.html#bokeh-gallery-tile-sources
def plot_track(MVBS_ds,
               opts_line = geoviews.opts(width = 600, height = 400, \
               color = 'red',tools = ['hover'], line_width = 1),
               opts_point = geoviews.opts(color = 'red',\
               tools = ['hover'], size = 8),
               map_tiles= 'Wikipedia'):
               
        '''
        
        Parameters
        ----------
        MVBS_ds : xarray.Dataset
            MVBS Dataset with coordinates 'ping_time', 'channel', 'echo_range'
            MVBS Dataset has been combined with longitude & latitude coordinates using echopype
            
        opts_line : geoviews.opts, default : geoviews.opts(width = 600, height = 400, \
               color = 'red',tools = ['hover'], line_width = 1)
            Modify the style of line
            
        opts_point : geoviews.opts, default : geoviews.opts(color = 'red',\
               tools = ['hover'], size = 8)
            Modify the style of point
            
        map_tiles : str, default : 'Wikipedia'
            See more in : https://geoviews.org/gallery/bokeh/tile_sources.html
        
        Returns
        -------
        ship_track * start_node * tiles ：holoviews.Overlay
            Combined chart( track, start point and map tile )
        
        '''
        
    # conver xarray data to geoviews data
    all_pd_data = pandas.concat([
        pandas.DataFrame(MVBS_ds.longitude.values, columns=['Longitude']),
        pandas.DataFrame(MVBS_ds.latitude.values, columns=['Latitude']),
        pandas.DataFrame(MVBS_ds.ping_time.values, columns=['Ping Time'])
    ],
                                axis=1)

    all_pd_data = all_pd_data.dropna(axis=0, how='any')

    # get map tiles
    tiles = getattr(geoviews.tile_sources, map_tiles)

    # plot path
    ship_track = geoviews.Path([all_pd_data],
                               kdims=['Longitude', 'Latitude'],
                               vdims=['Ping Time','Longitude', 'Latitude'])\
                               .opts(opts_line)

    # plot start node
    start = all_pd_data.iloc[0].values.tolist()

    start_node = geoviews.Points([start],
                                  kdims=['Longitude', 'Latitude'],)\
                                  .opts(opts_point)

    return ship_track * start_node * tiles


class EchoMap(echo_gram.Echogram):

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
        
    opts_line : geoviews.opts, default : geoviews.opts(width=600, height=400, color='blue', tools=['hover'], line_width=1)
        Modify the style of track in map
    
    opts_point : geoviews.opts, default : geoviews.opts(color='blue', tools=['hover'], size=8)
        Modify the style of start point in map
    
    opts_box_line : geoviews.opts, default : geoviews.opts(width=600, height=400, color='red', tools=['hover'], alpha=0.7, line_width=3)
        Modify the style of track in map responding to selected box
        
    opts_box_point : geoviews.opts, default : geoviews.opts(color='red', tools=['hover'], size=8)
        Modify the style of start point in map responding to selected box
        
    curtain_width : int, default : 700
        width of 2.5D curtain
    
    curtain_height : int, default : 500
        height of 2.5D curtain
        
    map_button : panel.widgets.Button
        Click to update the map and curtain
        See more in : https://panel.holoviz.org/reference/widgets/Button.html#widgets-gallery-button
        
    ratio_input : panel.widgets.FloatInput
        Input the value of curtain's Z spacing
        When this value is greater, height of curtain stretches more 
        See more in : https://panel.holoviz.org/reference/widgets/FloatInput.html#widgets-gallery-floatinput
       
    tile_select = panel.widgets.Select
        Choose tile type
        See more in : https://panel.holoviz.org/reference/widgets/Select.html#widgets-gallery-select
        See tile sources : https://geoviews.org/gallery/bokeh/tile_sources.html
        
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
        
    box_track : holoviews.Overlay
        Ship track responding to selected box echogram
        Only be accessed after calling method 'view_box_map()'
        
    all_track : holoviews.Overlay
        Ship track responding to echogram
        Only be accessed after calling method 'view_map()'
        
    curtain : pyvista.Plotter
        2.5D curtain responding to selected box echogram
        Only be accessed after calling method 'view_curtain()'
        
    Methods
    -------
    _sync_widget(self):
        Initialize widgets attributes
        Called in __init__(self, MVBS_ds, **params)
        
    _sync_widge_map(self):
        Initialize map-related widgets attributes
        Called in __init__(self, MVBS_ds, **params)  
        
    view_gram(self):
        Get single echogram with control panel widgets 
      
    view_all_gram(self):
        Get all echograms with control panel widgets 
        
    get_box_data(self): 
        Get MVBS data with a specific frequency in selected box
        
    get_all_box_data(self): 
        Get MVBS data with all frequencies in selected box
        
    view_box_map(self):
        Get map respongding to selected box echogram
        
    view_map(self):
        Get map respongding to echogram
        
    view_all_map(self):
        Get map respongding to echogram combined with map respongding to selected box echogram
        
    view_curtain(self):
        Get 2.5D curtain in a panel widget 
    
    Examples
    --------    
        echomap = echo_map.EchoMap(MVBS_ds)

        panel.Row(echomap.widgets, panel.Column(echomap.view_gram, echomap.view_all_map, echomap.view_curtain))
        
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
        None
        '''
        
        super().__init__(MVBS_ds)

        self.opts_line = geoviews.opts(width=600,
                                       height=400,
                                       color='blue',
                                       tools=['hover'],
                                       line_width=1)

        self.opts_point = geoviews.opts(color='blue', 
                                        tools=['hover'],
                                        size=8)

        self.opts_box_line = geoviews.opts(width=600,
                                           height=400,
                                           color='red',
                                           tools=['hover'],
                                           alpha=0.7,
                                           line_width=3)

        self.opts_box_point = geoviews.opts(color='red',
                                            tools=['hover'],
                                            size=8)

        self.curtain_width = 700

        self.curtain_height = 500

        self._sync_widge_map()

    def _sync_widge_map(self):
        '''
        Constructs all the necessary map widgets attributes 
        
        Parameters
        ----------
        None
        
        Returns
        -------
        None
        '''
        
        # https://panel.holoviz.org/reference/widgets/Button.html#widgets-gallery-button
        self.map_button = panel.widgets.Button(name='Update Map and Curtain 🗺️',
                                           button_type='primary')

        # https://panel.holoviz.org/reference/widgets/FloatInput.html#widgets-gallery-floatinput
        self.ratio_input = panel.widgets.FloatInput(
            name='Ratio Input (Curtain Z Spacing)', value=0.001, step=1e-5, start=0)

        # https://panel.holoviz.org/reference/widgets/Select.html#widgets-gallery-select
        # bokeh-gallery-tile-sources
        # https://geoviews.org/gallery/bokeh/tile_sources.html
        self.tile_select = panel.widgets.Select(
            name='Map Tile Select',
            value='Wikipedia',
            options=[
                'CartoDark', 'CartoEco', 'CartoLight', 'CartoMidnight', 'ESRI',
                'EsriImagery', 'EsriNatGeo', 'EsriOceanBase',
                'EsriOceanReference', 'EsriReference', 'EsriTerrain',
                'EsriUSATopo', 'OSM', 'OpenTopoMap', 'StamenLabels',
                'StamenTerrain', 'StamenTerrainRetina', 'StamenToner',
                'StamenTonerBackground', 'StamenWatercolor', 'Wikipedia'
            ])

        self.widgets = panel.WidgetBox(
            self.widgets,
            panel.WidgetBox(self.tile_select, self.ratio_input, self.map_button))

    @param.depends('map_button.value')
    def view_box_map(self):
        '''
        Create a map responding to selected box echogram
        
        Parameters
        ----------
        Self
        
        Returns
        -------
        self.box_track : holoviews.Overlay
            Combined chart( track, start point and map tile ) responding to selected box echogram
        '''
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        self.box_track = plot_track(self.MVBS_ds.sel(ping_time=time_range),
                                    map_tiles=self.tile_select.value,
                                    opts_line=self.opts_box_line,
                                    opts_point=self.opts_box_point)

        return self.box_track

    @param.depends('map_button.value')
    def view_map(self):
        '''
        Create a map responding to echogram
        
        Parameters
        ----------
        Self
        
        Returns
        -------
        self.box_track : holoviews.Overlay
            Combined chart( track, start point and map tile ) responding to echogram
        '''
        start_time = self.datetime_range_input.value[0] \
                     if self.datetime_range_input_model==True \
                     else self.time_range_picker.value[0]

        end_time = self.datetime_range_input.value[-1] \
                     if self.datetime_range_input_model==True \
                     else self.time_range_picker.value[-1]

        time_range = slice(start_time, end_time)

        self.all_track = plot_track(self.MVBS_ds.sel(ping_time=time_range),
                                    map_tiles=self.tile_select.value,
                                    opts_line=self.opts_line,
                                    opts_point=self.opts_point)

        return self.all_track
        
    @param.depends('map_button.value')
    def view_all_map(self):
        '''
        Create a combined map ( selected box echogram + echogram)
        
        Parameters
        ----------
        Self
        
        Returns
        -------
        self.box_track : holoviews.Overlay
            Combined chart( track, start point and map tile )
        '''
        return self.view_map() * self.view_box_map()

    @panel.depends('map_button.value')
    def view_curtain(self):
        '''
        Create a combined map ( selected box echogram + echogram)
        
        Parameters
        ----------
        Self
        
        Returns
        -------
        curtain_panel : panel.Row
            2.5D Pyvista curtain is chiseled in panel Row
        '''
        
        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        echo_range = slice(self.box.bounds[3], self.box.bounds[1])

        channel = self.channel_select.value

        color_map = 'jet' if len(self.color_map.value) == 0 \
                          else self.color_map.value

        clim = self.range_clim.value

        ratio = self.ratio_input.value

        self.curtain = echo_curtain.plot_curtain(self.MVBS_ds.sel(
            channel=channel, ping_time=time_range, echo_range=echo_range),
                                                 cmp=color_map,
                                                 clim=clim,
                                                 ratio=ratio)

        curtain_panel = panel.Row(
            panel.panel(self.curtain.ren_win,
                        height=self.curtain_height,
                        width=self.curtain_width,
                        orientation_widget=True))

        return curtain_panel
