import holoviews
import numpy


def get_box_stream(source_pic, bounds: tuple | None = None):
    if bounds is None:
        bounds = tuple(source_pic.lbrt)

    return holoviews.streams.BoundsXY(
        source=source_pic,
        bounds=bounds,
    )


def get_lasso_stream(
    source_pic: holoviews.element,
    geometry: numpy.ndarray | None = None,
):
    if geometry is None:
        left, bottom, right, top = source_pic.lbrt

        geometry = numpy.array(
            [
                [left, bottom],
                [left, top],
                [right, top],
                [right, bottom],
            ]
        )

    return holoviews.streams.Lasso(
        source=source_pic,
        geometry=geometry,
    )


def get_box_plot(box_stream):
    return holoviews.DynamicMap(
        lambda bounds: holoviews.Bounds(bounds),
        streams=[box_stream],
    )