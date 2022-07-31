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


class EchogramMap(echo_gram.Echogram):
    def __init__(self, MVBS_ds):

        super().__init__(MVBS_ds)

        self.opts_line = geoviews.opts(width=600,
                                       height=400,
                                       color='red',
                                       tools=['hover'],
                                       line_width=1),

        self.opts_point = geoviews.opts(color='red', tools=['hover'], size=8)

        self.opts_box_line = geoviews.opts(width=600,
                                           height=400,
                                           color='red',
                                           tools=['hover'],
                                           alpha=0.5,
                                           line_width=2)

        self.opts_box_point = geoviews.opts(color='red',
                                            tools=['hover'],
                                            size=8)

        self.curtain_width = 700

        self.curtain_height = 500

        self._sync_widge_map()

    def _sync_widge_map(self):

        # https://panel.holoviz.org/reference/widgets/Button.html#widgets-gallery-button
        self.button = panel.widgets.Button(name='Update Map and Curtain 🗺️',
                                           button_type='primary')

        # https://panel.holoviz.org/reference/widgets/FloatInput.html#widgets-gallery-floatinput
        self.ratio_input = panel.widgets.FloatInput(
            name='Ratio Input (Z Spacing)', value=0.001, step=1e-5, start=0)

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
            panel.WidgetBox(self.ratio_input, self.tile_select, self.button))

    @param.depends('button.value')
    def view_box_map(self):

        time_range = slice(self.box.bounds[0], self.box.bounds[2])

        self.box_track = plot_track(self.MVBS_ds.sel(ping_time=time_range),
                                    map_tiles=self.tile_select.value,
                                    opts_line=self.opts_box_line,
                                    opts_point=self.opts_box_point)

        return self.box_track

    @param.depends('button.value')
    def view_map(self):
        start_time = self.datetime_range_input.value[0] \
                     if self.datetime_range_input_model==True \
                     else self.time_range_picker.value[0]

        end_time = self.datetime_range_input.value[-1] \
                     if self.datetime_range_input_model==True \
                     else self.time_range_picker.value[-1]

        time_range = slice(start_time, end_time)

        self.all_track = plot_track(self.MVBS_ds.sel(ping_time=time_range),
                                    map_tiles=self.tile_select.value,
                                    opts_line=self.opts_box_line,
                                    opts_point=self.opts_box_point)

        return self.all_track

    @panel.depends('button.value')
    def view_curtain(self):

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
