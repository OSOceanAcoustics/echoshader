import holoviews
import numpy
import panel as pn
import xarray

from .context import AppContext
from .controls import build_control
from .interactions import INTERACTIONS
from .registry import ELEMENTS
from .selection import (
    SELECTIONS,
    apply_selection,
)
from .sources import (
    DataSource,
    build_source,
)
from .state import AppState


def _build_sources(
    config: dict,
    context: AppContext,
):
    """Build configured data sources."""

    source_configs = config.get(
        "data",
        {},
    )

    data_sources = {}
    pending = dict(
        source_configs
    )

    while pending:
        progress = False

        for name in list(
            pending
        ):
            source_config = pending[
                name
            ]

            dependency = source_config.get(
                "depends_on"
            )

            if (
                dependency is not None
                and dependency not in data_sources
            ):
                continue

            source = build_source(
                source_config,
                context=context,
            )

            source.reload()

            data_sources[
                name
            ] = source

            del pending[
                name
            ]

            progress = True

        if not progress:
            raise ValueError(
                "Could not resolve data-source dependencies: "
                f"{list(pending)}"
            )

    for (
        name,
        source_config,
    ) in source_configs.items():
        dependency = source_config.get(
            "depends_on"
        )

        if dependency is None:
            continue

        parent = data_sources[
            dependency
        ]

        child = data_sources[
            name
        ]

        parent.param.watch(
            lambda event, child=child: child.reload(),
            "data",
        )

    for source in data_sources.values():
        source.start_refresh()

    return data_sources


def _build_controls(
    config: dict,
    state: AppState,
):
    """Build controls and connect them to shared values."""

    controls = {}

    for (
        name,
        control_config,
    ) in config.get(
        "controls",
        {},
    ).items():
        config_copy = dict(
            control_config
        )

        args = dict(
            config_copy.get(
                "args",
                {},
            )
        )

        write_name = config_copy.get(
            "write"
        )

        if write_name is not None:
            shared_value = state.get_value(
                write_name
            )

            if (
                shared_value.value is not None
                and "value" not in args
            ):
                args[
                    "value"
                ] = shared_value.value

        config_copy[
            "args"
        ] = args

        control = build_control(
            config_copy
        )

        controls[
            name
        ] = control

        if write_name is not None:
            shared_value = state.get_value(
                write_name
            )

            if shared_value.value is None:
                shared_value.value = control.value

            else:
                control.value = shared_value.value

            def update_value(
                event,
                value_state=shared_value,
            ):
                value_state.value = event.new

            control.param.watch(
                update_value,
                "value",
            )

    return controls


def _get_data(
    source,
):
    """Return reactive or static source data."""

    if isinstance(
        source,
        DataSource,
    ):
        return source.param.data

    return source


def _get_current_data(
    source,
):
    """Return the current concrete data value."""

    if isinstance(
        source,
        DataSource,
    ):
        return source.data

    if callable(
        source
    ):
        return source()

    return source


def _apply_element_options(
    element,
    options: dict,
):
    """
    Apply HoloViews options to a simple element or composite layout.

    For Layout/NdLayout objects, options such as cmap, width and height
    must be applied to the leaf visualization elements rather than the
    layout container itself.
    """

    if not options:
        return element

    if not isinstance(
        element,
        (
            holoviews.Layout,
            holoviews.NdLayout,
        ),
    ):
        return element.opts(
            **options
        )

    option_specs = []
    handled_types = set()

    container_types = {
        "Layout",
        "NdLayout",
        "Overlay",
        "NdOverlay",
    }

    for child in element.traverse(
        lambda child: child
    ):
        child_type = type(
            child
        ).__name__

        if child_type in container_types:
            continue

        if child_type in handled_types:
            continue

        try:
            option_type = getattr(
                holoviews.opts,
                child_type,
            )

        except AttributeError:
            continue

        option_specs.append(
            option_type(
                **options
            )
        )

        handled_types.add(
            child_type
        )

    if not option_specs:
        return element

    return element.opts(
        *option_specs
    )


def _apply_view(
    data,
    view_config: dict | None,
):
    """Apply lightweight display-only data reduction."""

    if not view_config:
        return data

    max_pings = view_config.get(
        "max_pings"
    )

    if max_pings is None:
        return data

    ping_dim = view_config.get(
        "ping_dim",
        "ping_time",
    )

    if ping_dim not in data.dims:
        return data

    n_pings = data.sizes[
        ping_dim
    ]

    if n_pings <= max_pings:
        return data

    indices = numpy.linspace(
        0,
        n_pings - 1,
        max_pings,
        dtype=int,
    )

    return data.isel(
        {
            ping_dim: indices,
        }
    )


def _build_element(
    element_config: dict,
    data,
    runtime_values: dict | None = None,
):
    """Build one visualization element."""

    element_type = element_config[
        "type"
    ]

    if element_type not in ELEMENTS:
        raise ValueError(
            f"Unknown element type: {element_type!r}."
        )

    element_func = ELEMENTS[
        element_type
    ]

    data = _apply_view(
        data,
        element_config.get(
            "view"
        ),
    )

    args = dict(
        element_config.get(
            "args",
            {},
        )
    )

    if runtime_values:
        args.update(
            runtime_values
        )

    options = dict(
        element_config.get(
            "opts",
            {},
        )
    )

    plot = element_func(
        data,
        **args,
    )

    return _apply_element_options(
        plot,
        options,
    )


def _parse_observe(
    element_config: dict,
):
    """Normalize state observed by one element."""

    observe = element_config.get(
        "observe",
        {},
    )

    if observe is None:
        observe = {}

    if isinstance(
        observe,
        str,
    ):
        observe = {
            "selection": observe,
        }

    if not isinstance(
        observe,
        dict,
    ):
        raise TypeError(
            "'observe' must be a mapping."
        )

    return {
        "selection": observe.get(
            "selection"
        ),
        "projection": observe.get(
            "projection"
        ),
        "drop": observe.get(
            "drop",
            True,
        ),
        "values": observe.get(
            "values",
            {},
        ),
    }


def _resolve_value_dependencies(
    state: AppState,
    values_config: dict,
):
    """
    Convert YAML value observations into reactive dependencies.

    Example:

    values:
      channel:
        - rgb_red
        - rgb_green
        - rgb_blue
    """

    dependencies = {}
    specifications = {}

    for (
        argument_name,
        value_names,
    ) in values_config.items():
        if isinstance(
            value_names,
            str,
        ):
            value_names = [
                value_names,
            ]

        if not isinstance(
            value_names,
            list,
        ):
            raise TypeError(
                "Observed values must be a value name "
                "or a list of value names."
            )

        dependency_names = []

        for (
            index,
            value_name,
        ) in enumerate(
            value_names
        ):
            dependency_name = (
                f"value__{argument_name}__{index}"
            )

            dependencies[
                dependency_name
            ] = state.get_value(
                value_name
            ).param.value

            dependency_names.append(
                dependency_name
            )

        specifications[
            argument_name
        ] = dependency_names

    return (
        dependencies,
        specifications,
    )


def _build_runtime_values(
    bindings: dict,
    specifications: dict,
):
    """Convert shared values into function argument values."""

    runtime_values = {}

    for (
        argument_name,
        dependency_names,
    ) in specifications.items():
        values = [
            bindings[
                dependency_name
            ]
            for dependency_name in dependency_names
        ]

        if len(
            values
        ) == 1:
            runtime_values[
                argument_name
            ] = values[
                0
            ]

        else:
            runtime_values[
                argument_name
            ] = values

    return runtime_values


def _build_reactive_element(
    state: AppState,
    element_config: dict,
    data_source,
):
    """Build an element observing shared application state."""

    data = _get_data(
        data_source
    )

    observe = _parse_observe(
        element_config
    )

    dependencies = {
        "data": data,
    }

    selection_name = observe[
        "selection"
    ]

    if selection_name is not None:
        selection = state.get_selection(
            selection_name
        )

        dependencies[
            "selection_value"
        ] = selection.param.value

    (
        value_dependencies,
        value_specifications,
    ) = _resolve_value_dependencies(
        state,
        observe[
            "values"
        ],
    )

    dependencies.update(
        value_dependencies
    )

    def build(
        data,
        selection_value=None,
        **bindings,
    ):
        if selection_name is not None:
            data = apply_selection(
                data,
                selection_value,
                projection=observe[
                    "projection"
                ],
                drop=observe[
                    "drop"
                ],
            )

        runtime_values = _build_runtime_values(
            bindings,
            value_specifications,
        )

        return _build_element(
            element_config,
            data,
            runtime_values=runtime_values,
        )

    return pn.bind(
        build,
        **dependencies,
    )


def _get_interaction_sources(
    plot,
    element_name: str | None = None,
):
    """
    Return visualization elements that can own an interaction stream.

    A simple plot returns one source. A composite Layout returns its
    visualization leaves, allowing the same interaction to work on
    each echogram in a multi-channel layout.
    """

    elements = plot.traverse(
        lambda element: element
    )

    if element_name is not None:
        matches = [
            element
            for element in elements
            if type(
                element
            ).__name__ == element_name
        ]

        if not matches:
            available = sorted(
                {
                    type(
                        element
                    ).__name__
                    for element in elements
                }
            )

            raise ValueError(
                f"Could not find interaction element "
                f"{element_name!r}. "
                f"Available elements: {available}."
            )

        return matches

    if not isinstance(
        plot,
        (
            holoviews.Layout,
            holoviews.NdLayout,
        ),
    ):
        return [
            plot,
        ]

    container_types = {
        "Layout",
        "NdLayout",
        "Overlay",
        "NdOverlay",
    }

    return [
        element
        for element in elements
        if type(
            element
        ).__name__ not in container_types
    ]


def _add_interaction_tools(
    plot,
    tools: list,
    active_tools: list,
    element_name: str | None = None,
):
    """
    Add interaction tools to simple or composite plots.

    Explicit child targets such as Points are handled directly.
    Layouts receive the tools on their leaf visualization elements.
    """

    if not tools:
        return plot

    if element_name is not None:
        try:
            option_type = getattr(
                holoviews.opts,
                element_name,
            )

        except AttributeError as exc:
            raise ValueError(
                f"No HoloViews option type exists for "
                f"{element_name!r}."
            ) from exc

        return plot.opts(
            option_type(
                tools=tools,
                active_tools=active_tools,
            )
        )

    if not isinstance(
        plot,
        (
            holoviews.Layout,
            holoviews.NdLayout,
        ),
    ):
        return plot.opts(
            tools=tools,
            active_tools=active_tools,
        )

    option_specs = []
    handled_types = set()

    for element in _get_interaction_sources(
        plot
    ):
        element_type = type(
            element
        ).__name__

        if element_type in handled_types:
            continue

        try:
            option_type = getattr(
                holoviews.opts,
                element_type,
            )

        except AttributeError:
            continue

        option_specs.append(
            option_type(
                tools=tools,
                active_tools=active_tools,
            )
        )

        handled_types.add(
            element_type
        )

    if not option_specs:
        return plot

    return plot.opts(
        *option_specs
    )


def _selection_is_empty(
    value,
):
    """Return True when a generated selection is empty."""

    if value is None:
        return True

    if isinstance(
        value,
        xarray.DataArray,
    ):
        return not bool(
            value.any().item()
        )

    return False


def _make_selection_callback(
    state: AppState,
    selection_name: str,
    source_name: str,
    interaction_type: str,
    data_source,
    selector,
    parameter_name: str,
    selection_args: dict,
):
    """Create a callback that writes shared selection state."""

    selection = state.get_selection(
        selection_name
    )

    def update_selection(
        event,
    ):
        data = _get_current_data(
            data_source
        )

        value = selector(
            data,
            **{
                parameter_name: event.new,
            },
            **selection_args,
        )

        if _selection_is_empty(
            value
        ):
            selection.clear()
            return

        selection.set(
            value,
            source=source_name,
            kind=interaction_type,
        )

    return update_selection


def _build_interactions(
    config: dict,
    state: AppState,
    data_sources: dict,
    objects: dict,
    element_configs: dict,
):
    """Attach interactions that write named shared selections."""

    for interaction in config.get(
        "interactions",
        [],
    ):
        interaction_type = interaction[
            "type"
        ]

        source_name = interaction[
            "source"
        ]

        selection_name = interaction[
            "write"
        ]

        if interaction_type not in INTERACTIONS:
            raise ValueError(
                f"Unknown interaction type: "
                f"{interaction_type!r}."
            )

        if interaction_type not in SELECTIONS:
            raise ValueError(
                f"No selector registered for "
                f"{interaction_type!r}."
            )

        if source_name not in objects:
            raise ValueError(
                f"Unknown interaction source: "
                f"{source_name!r}."
            )

        source_object = objects[
            source_name
        ]

        if callable(
            source_object
        ):
            source_plot = source_object()

        else:
            source_plot = source_object

        interaction_definition = INTERACTIONS[
            interaction_type
        ]

        source_element = interaction.get(
            "source_element"
        )

        source_plot = _add_interaction_tools(
            source_plot,
            tools=interaction_definition.get(
                "tools",
                [],
            ),
            active_tools=interaction_definition.get(
                "active_tools",
                [],
            ),
            element_name=source_element,
        )

        objects[
            source_name
        ] = source_plot

        stream_sources = _get_interaction_sources(
            source_plot,
            element_name=source_element,
        )

        source_data_name = element_configs[
            source_name
        ][
            "data"
        ]

        if source_data_name not in data_sources:
            raise ValueError(
                f"Unknown data source: "
                f"{source_data_name!r}."
            )

        source_data = data_sources[
            source_data_name
        ]

        selector = SELECTIONS[
            interaction_type
        ]

        parameter_name = interaction_definition[
            "parameter"
        ]

        callback = _make_selection_callback(
            state=state,
            selection_name=selection_name,
            source_name=source_name,
            interaction_type=interaction_type,
            data_source=source_data,
            selector=selector,
            parameter_name=parameter_name,
            selection_args=interaction.get(
                "args",
                {},
            ),
        )

        for stream_source in stream_sources:
            stream = interaction_definition[
                "stream"
            ](
                stream_source
            )

            stream.param.watch(
                callback,
                parameter_name,
            )

            state.get_selection(
                selection_name
            ).add_stream(
                stream
            )


def _resolve_layout_child(
    child,
    objects: dict,
):
    """Resolve one configured layout child."""

    if isinstance(
        child,
        str,
    ):
        if child not in objects:
            raise ValueError(
                f"Unknown layout object: {child!r}."
            )

        return objects[
            child
        ]

    if isinstance(
        child,
        dict,
    ):
        return _build_layout(
            child,
            objects,
        )

    raise TypeError(
        "Layout children must be names "
        "or nested layout dictionaries."
    )


def _build_layout(
    layout_config: dict,
    objects: dict,
):
    """Build a recursive Panel layout."""

    layout_type = layout_config.get(
        "type",
        "column",
    )

    children_config = layout_config.get(
        "children",
        [],
    )

    sizing_mode = layout_config.get(
        "sizing_mode"
    )

    layout_kwargs = {}

    if sizing_mode is not None:
        layout_kwargs[
            "sizing_mode"
        ] = sizing_mode

    if layout_type == "column":
        return pn.Column(
            *[
                _resolve_layout_child(
                    child,
                    objects,
                )
                for child in children_config
            ],
            **layout_kwargs,
        )

    if layout_type == "row":
        return pn.Row(
            *[
                _resolve_layout_child(
                    child,
                    objects,
                )
                for child in children_config
            ],
            **layout_kwargs,
        )

    if layout_type == "tabs":
        tabs = []

        for child in children_config:
            if not isinstance(
                child,
                dict,
            ):
                raise TypeError(
                    "Tab children must be layout dictionaries."
                )

            title = child.get(
                "title",
                "Untitled",
            )

            tab_config = dict(
                child
            )

            tab_config.pop(
                "title",
                None,
            )

            tab_config.setdefault(
                "type",
                "column",
            )

            tabs.append(
                (
                    title,
                    _build_layout(
                        tab_config,
                        objects,
                    ),
                )
            )

        return pn.Tabs(
            *tabs,
            dynamic=layout_config.get(
                "dynamic",
                False,
            ),
            **layout_kwargs,
        )

    raise ValueError(
        f"Unknown layout type: {layout_type!r}."
    )


def build_app(
    config: dict,
    datasets: dict[str, xarray.Dataset] | None = None,
    context: dict | None = None,
):
    """Build an Echoshader application."""

    state = AppState()

    # ----------------------------------------------------------
    # Runtime context
    # ----------------------------------------------------------

    context_values = dict(
        config.get(
            "context",
            {},
        )
    )

    if context is not None:
        context_values.update(
            context
        )

    app_context = AppContext(
        values=context_values
    )

    # ----------------------------------------------------------
    # Shared values
    # ----------------------------------------------------------

    for (
        name,
        value,
    ) in config.get(
        "values",
        {},
    ).items():
        state.get_value(
            name,
            default=value,
        )

    # ----------------------------------------------------------
    # Shared selections
    # ----------------------------------------------------------

    for name in config.get(
        "selections",
        {},
    ):
        state.get_selection(
            name
        )

    # ----------------------------------------------------------
    # Data
    # ----------------------------------------------------------

    data_sources = _build_sources(
        config=config,
        context=app_context,
    )

    if datasets is not None:
        data_sources.update(
            datasets
        )

    for (
        name,
        source,
    ) in data_sources.items():
        state.set_dataset(
            name,
            source,
        )

    # ----------------------------------------------------------
    # Controls
    # ----------------------------------------------------------

    controls = _build_controls(
        config=config,
        state=state,
    )

    # ----------------------------------------------------------
    # Elements
    # ----------------------------------------------------------

    element_configs = config.get(
        "elements",
        {},
    )

    objects = {}

    for (
        name,
        element_config,
    ) in element_configs.items():
        data_name = element_config[
            "data"
        ]

        if data_name not in data_sources:
            raise ValueError(
                f"Unknown data source: "
                f"{data_name!r}."
            )

        objects[
            name
        ] = _build_reactive_element(
            state=state,
            element_config=element_config,
            data_source=data_sources[
                data_name
            ],
        )

    # ----------------------------------------------------------
    # Interactions
    # ----------------------------------------------------------

    _build_interactions(
        config=config,
        state=state,
        data_sources=data_sources,
        objects=objects,
        element_configs=element_configs,
    )

    # ----------------------------------------------------------
    # Layout
    # ----------------------------------------------------------

    layout_objects = {
        **objects,
        **controls,
    }

    layout_config = config.get(
        "layout",
        {
            "type": "column",
            "children": list(
                layout_objects
            ),
        },
    )

    app = _build_layout(
        layout_config,
        layout_objects,
    )

    # Useful during development/debugging.
    app._echoshader_state = state

    return app