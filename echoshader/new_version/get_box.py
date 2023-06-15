import holoviews

# get box stream data from box select
def get_box_stream(echogram):
        box_stream = holoviews.streams.BoundsXY(
            source=echogram,
            bounds=(
                echogram.lbrt[0],
                echogram.lbrt[1],
                echogram.lbrt[2],
                echogram.lbrt[3],
            ),
        )

        return box_stream

# plot box based on box select
def get_box_plot(box_stream):
        box_opts = holoviews.opts(line_width=1, line_color="white")

        box_plot = holoviews.DynamicMap(
            lambda bounds: holoviews.Bounds(bounds).opts(box_opts),
            streams=[box_stream],
        )

        return box_plot