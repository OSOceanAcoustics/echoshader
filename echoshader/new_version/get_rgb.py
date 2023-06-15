import numpy


def convert_to_color(ds_Sv, channel_sel, th_bottom, th_top):
    da_color = ds_Sv.sel(channel=channel_sel)
    da_color = da_color.where(
        da_color <= th_top, other=th_top
    )  # set to ceiling at the top
    da_color = da_color.where(da_color >= th_bottom)  # threshold at the bottom
    da_color = da_color.expand_dims("channel")
    # da_color = ((da_color - th_bottom) / (th_top - th_bottom) *255).astype('int')
    # # this would produce false extreme values from float NaNs
    da_color = (da_color - th_bottom) / (th_top - th_bottom)
    da_color = numpy.squeeze(da_color.Sv.data).transpose().compute()
    return da_color
