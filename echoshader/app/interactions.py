import holoviews


def get_point_selection_stream(
    source,
    index=None,
):
    """Create a point/index selection stream."""

    kwargs = {
        "source": source,
    }

    if index is not None:
        kwargs[
            "index"
        ] = index

    return holoviews.streams.Selection1D(
        **kwargs,
    )


def get_box_stream(
    source,
    bounds=None,
):
    """Create a rectangular selection stream."""

    kwargs = {
        "source": source,
    }

    if bounds is not None:
        kwargs[
            "bounds"
        ] = bounds

    return holoviews.streams.BoundsXY(
        **kwargs,
    )


def get_lasso_stream(
    source,
    geometry=None,
):
    """Create a lasso selection stream."""

    kwargs = {
        "source": source,
    }

    if geometry is not None:
        kwargs[
            "geometry"
        ] = geometry

    return holoviews.streams.Lasso(
        **kwargs,
    )


INTERACTIONS = {
    "point_select": {
        "stream": get_point_selection_stream,
        "parameter": "index",
        "tools": [
            "box_select",
        ],
        "active_tools": [
            "box_select",
        ],
    },
    "box_select": {
        "stream": get_box_stream,
        "parameter": "bounds",
        "tools": [
            "box_select",
        ],
        "active_tools": [
            "box_select",
        ],
    },
    "lasso_select": {
        "stream": get_lasso_stream,
        "parameter": "geometry",
        "tools": [
            "lasso_select",
        ],
        "active_tools": [
            "lasso_select",
        ],
    },
}