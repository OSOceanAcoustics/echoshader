import holoviews
import numpy


def get_box_stream(source_pic, bounds: tuple = None):
    """
    Get the box stream data from the box select.

    Args:
        source_pic: The source picture or plot in holoviews ecosystem.
        bounds (tuple, optional): The bounds of the box select.

    Returns:
        holoviews.streams.BoundsXY: The box stream data.
    """
    box_stream = holoviews.streams.BoundsXY(
        source=source_pic,
        bounds=(
            source_pic.lbrt[0],
            source_pic.lbrt[1],
            source_pic.lbrt[2],
            source_pic.lbrt[3],
        )
        if bounds is None
        else bounds,
    )

    return box_stream


def get_lasso_stream(source_pic, geometry: numpy.array = None):
    """
    Get the lasso stream data from the box select.

    Args:
        source_pic: The source picture or plot in holoviews ecosystem.
        geometry (numpy.array, optional): The geometry coordinates of the lasso.

    Returns:
        holoviews.streams.Lasso: The lasso stream data.
    """
    lasso_stream = holoviews.streams.Lasso(
        source=source_pic,
        geometry=numpy.array(
            [
                [
                    source_pic.lbrt[0],
                    source_pic.lbrt[0],
                    source_pic.lbrt[2],
                    source_pic.lbrt[2],
                ],
                [
                    source_pic.lbrt[1],
                    source_pic.lbrt[3],
                    source_pic.lbrt[1],
                    source_pic.lbrt[3],
                ],
            ]
        )
        if geometry is None
        else geometry,
    )

    return lasso_stream


def get_box_plot(box_stream):
    """
    Generate a plot of a Bound based on the box select.

    Args:
        box_stream: The box stream data.

    Returns:
        holoviews.DynamicMap: A dynamic map representing the box plot.
    """
    box_opts = holoviews.opts(line_width=1, line_color="white")

    box_plot = holoviews.DynamicMap(
        lambda bounds: holoviews.Bounds(bounds).opts(box_opts),
        streams=[box_stream],
    )

    return box_plot
