from echo_lib import *


def simpleHist(ds_Sv,
               clim=(-80, -30),
               cmap='jet',
               width=600,
               height=300):
    '''
    input Sv DataArray with a specific channel,
    like ds_MVBS.Sv.sel(channel='GPT  38 kHz 00907208dd13 5-1 OOI.38|200'),
    to get a simple side hist, which is tuned by box zoom (rangeXY)
    '''

    echogram = ds_Sv.hvplot(kind='image',
                            x='ping_time',
                            y='echo_range',
                            c='Sv',
                            clim=clim,
                            cmap=cmap,
                            rasterize=False,
                            width=width,
                            height=height,
                            flip_yaxis=True)

    def selectedRangeHist(x_range, y_range):
        # Apply current ranges
        obj = echogram.select(ping_time=x_range,
                              echo_range=y_range) if x_range and y_range else echogram

        # Compute histogram
        return hv.operation.histogram(obj)

    # Define a RangeXY stream linked to the image
    rangexy = hv.streams.RangeXY(source=echogram)
    hist = hv.DynamicMap(selectedRangeHist, streams=[rangexy])
    return echogram << hist



def echoHist(MVBS):
    
    '''
    input Sv DataSet,
    like ds_MVBS
    to get a hist with describe, which is tuned by box select (boxXY)
    '''
    
    def getMVBS():
        return MVBS
    
    class EchoHist(param.Parameterized):
        
        MVBS=getMVBS()
        
        start_date=dt.date(pd.to_datetime(MVBS.ping_time.data[0]).year,
                       pd.to_datetime(MVBS.ping_time.data[0]).month,
                       pd.to_datetime(MVBS.ping_time.data[0]).day)
        
        end_date=dt.date(pd.to_datetime(MVBS.ping_time.data[-1]).year,
                     pd.to_datetime(MVBS.ping_time.data[-1]).month,
                     pd.to_datetime(MVBS.ping_time.data[-1]).day)
        
        select_date=param.CalendarDate(default=start_date,bounds=(start_date, end_date),doc="Select date")
        
        select_channel= param.Selector(objects=MVBS.channel.values.tolist(),doc="Select channel")
        
        range_clim=param.Range(bounds=(MVBS.Sv.actual_range[0],MVBS.Sv.actual_range[-1]),doc="Select clim")
        
        color_map= param.String(default="jet", doc="Colormap")
        
        bin_size= param.Integer(24, bounds=(1, 200),doc="Bin size")
        
        show_all_freq= param.Boolean(False, doc="Show hist with all frequencies")
        
        @param.depends('select_date','select_channel','range_clim','color_map','bin_size','show_all_freq')
        def view(self):
            
            date_picker=self.select_date
            
            channel=self.select_channel
            
            clim=self.range_clim
            
            color_map=self.color_map
            
            show_all_freq=self.show_all_freq
            
            bin_size=self.bin_size
            
            start_time = str(date_picker.year)+"-"\
            +str(date_picker.month)+"-"\
            +str(date_picker.day)+"T00:00:00"
            
            end_time = str(date_picker.year)+"-"\
            +str(date_picker.month)+"-"\
            +str(date_picker.day)+"T23:59:59"
            
            time_range=slice(start_time,end_time)
                        
            echogram=self.MVBS.Sv.sel(channel=channel,ping_time=time_range).hvplot(
                kind='image',
                x='ping_time',
                y='echo_range',
                c='Sv', 
                title='Sv : '+ channel,
                cmap=color_map,
                clim=clim,
                rasterize=True,
                width=800,
                height=400)\
            .options(invert_yaxis=True)
             
            
            # Define a RangeXY stream linked to the image
        
            box = streams.BoundsXY(source=echogram, bounds=(self.MVBS.ping_time.values[0],
                                                    self.MVBS.echo_range.values[-1],
                                                    self.MVBS.ping_time.values[-1],
                                                    self.MVBS.echo_range.values[0]))

            bounds = hv.DynamicMap(lambda bounds: hv.Bounds(bounds).opts(line_width=1,
                                line_color='white'), streams=[box])
            
            def selectedBoxTable(bounds):
                # Apply current ranges
                obj_df = self.MVBS.sel(channel=channel,
                                       ping_time=slice(bounds[0],bounds[2]),
                                       echo_range=slice(bounds[3],bounds[1])).Sv.to_dataframe()
        
                skew = obj_df['Sv'].skew()
                kurt = obj_df['Sv'].kurt()
        
                obj_desc = obj_df.describe().reset_index()
        
                obj_desc.loc[len(obj_desc)] = ['skew', skew]
                obj_desc.loc[len(obj_desc)] = ['kurtosis', kurt]
                # Compute histogram
                return hv.Table(obj_desc.values, 'stat', 'value')
    

            def selectedBoxHist(bounds):
                # Apply current ranges
                obj_df = self.MVBS.sel(channel=channel,ping_time=slice(bounds[0],bounds[2]),
                                    echo_range=slice(bounds[3],bounds[1])).Sv.to_dataframe()
        
                # Compute histogram
                return obj_df.hvplot.hist('Sv',bins=bin_size)
            
                    
#             def selectedBoxAllHist(bounds):       
                
#                 histAll=self.MVBS.Sv.sel(
#                     ping_time=slice(bounds[0],bounds[2]),
#                     echo_range=slice(bounds[3],bounds[1])).hvplot.hist(
#                     'Sv',
#                     by='channel',
#                     bins=bin_size,
#                     subplots=False,
#                     alpha=0.6,
#                     legend='top',
#                     width=800,
#                     height=400)
                
#                 # Compute histogram
#                 return histAll

            table = hv.DynamicMap(selectedBoxTable, streams=[box])
            
            hist1 = hv.DynamicMap(selectedBoxHist, streams=[box])
#             hist2 = hv.DynamicMap(selectedBoxAllHist, streams=[box])
                         
            def getData():
                return self.MVBS.sel(channel=channel,
                                     ping_time=slice(box.bounds[0],box.bounds[2]),
                                     echo_range=slice(box.bounds[3],box.bounds[1]))
            
            return pn.Tabs(('echograme',echogram*bounds),('describe',table),('hist',hist1))
                            
    echohist=EchoHist()
    
    return pn.Row(echohist.param,echohist.view)