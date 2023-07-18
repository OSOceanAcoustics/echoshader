import numpy


def convert_to_color(ds_Sv, channel_sel, th_bottom, th_top):
    """
    Convert a specific channel of backscatter data to a color array based on given thresholds.

    Args:
        ds_Sv (xr.Dataset): A dataset containing backscatter data.
        channel_sel (str, int): The selected channel to convert to color.
        th_bottom (float, int): The lower threshold value.
        th_top (float, int): The upper threshold value.

    Returns:
        numpy.ndarray: A numpy array representing the converted color data.

    Example usage:
        # Assuming `ds_Sv` is a dataset with backscatter data
        color_array = convert_to_color(ds_Sv, 'certain_channel', -80, -30)
        print(color_array)
    """
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
