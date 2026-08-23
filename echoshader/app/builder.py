import panel as pn
import xarray

from .context import AppContext
from .controls import build_control
from .interactions import get_box_plot, get_box_stream
from .registry import ELEMENTS
from .selection import select_box
from .sources import DataSource, build_source


def _build_sources(
    config: dict,
    context: AppContext,
):
    """Build configured data sources and resolve dependencies."""

    source_configs = config.get(
        "data",
        {},
    )

    data_sources = {}
    pending = dict(
        source_configs
    )

    # --------------------------------------------------------------
    # Initial source construction
    #
    # Sources with dependencies are only built once their parent
    # source exists. This allows a parent source to export context
    # values used by the dependent source path.
    # --------------------------------------------------------------

    while pending:
        progress = False

        for name in list(
            pending
        ):
            source_config = pending[
                name
            ]

            dependency = (
                source_config.get(
                    "depends_on",
                )
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

            # Initial load.
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

    # --------------------------------------------------------------
    # Dependency updates
    #
    # If a parent source changes, reload dependent sources.
    # --------------------------------------------------------------

    for (
        name,
        source_config,
    ) in source_configs.items():

        dependency = (
            source_config.get(
                "depends_on",
            )
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
            lambda event, child=child:
                child.reload(),
            "data",
        )

    # --------------------------------------------------------------
    # Periodic refresh
    #
    # Start callbacks only after all sources and dependencies exist.
    # --------------------------------------------------------------

    for source in data_sources.values():
        source.start_refresh()

    return data_sources


def _build_controls(
    config: dict,
):
    """Build all configured controls."""

    controls = {}

    for (
        name,
        control_config,
    ) in config.get(
        "controls",
        {},
    ).items():

        controls[
            name
        ] = build_control(
            control_config,
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


def _apply_element_options(
    element,
    options: dict,
):
    """Apply HoloViews options to a visualization element."""

    if not options:
        return element

    return element.opts(
        **options,
    )


def _build_element(
    element_config: dict,
    data,
    runtime_options: dict | None = None,
):
    """Build one visualization element."""

    element_type = (
        element_config[
            "type"
        ]
    )

    if element_type not in ELEMENTS:
        raise ValueError(
            f"Unknown element type: "
            f"{element_type!r}."
        )

    element_func = (
        ELEMENTS[
            element_type
        ]
    )

    args = dict(
        element_config.get(
            "args",
            {},
        )
    )

    options = dict(
        element_config.get(
            "opts",
            {},
        )
    )

    if runtime_options:
        options.update(
            runtime_options,
        )

    plot = element_func(
        data,
        **args,
    )

    return _apply_element_options(
        plot,
        options,
    )


def _get_option_bindings(
    config: dict,
    element_name: str,
    controls: dict,
):
    """
    Return reactive HoloViews option bindings for one element.

    Binding targets currently use the form::

        element_name.opts.option_name

    Example::

        original.opts.clim
    """

    option_bindings = {}

    for binding in config.get(
        "bindings",
        [],
    ):

        source_name = (
            binding[
                "source"
            ]
        )

        if source_name not in controls:
            raise ValueError(
                f"Unknown control: "
                f"{source_name!r}."
            )

        targets = binding.get(
            "target",
            [],
        )

        if isinstance(
            targets,
            str,
        ):
            targets = [
                targets,
            ]

        for target in targets:

            parts = target.split(
                "."
            )

            if len(parts) != 3:
                raise ValueError(
                    f"Invalid binding target: "
                    f"{target!r}. "
                    "Expected "
                    "'element.opts.option'."
                )

            (
                target_element,
                target_kind,
                option_name,
            ) = parts

            if (
                target_element
                != element_name
            ):
                continue

            if target_kind != "opts":
                raise ValueError(
                    "Only '.opts.<option>' "
                    "bindings are currently "
                    "supported."
                )

            option_bindings[
                option_name
            ] = (
                controls[
                    source_name
                ].param.value
            )

    return option_bindings


def _build_reactive_element(
    config: dict,
    name: str,
    element_config: dict,
    data_source,
    controls: dict,
):
    """Build a visualization responsive to data and controls."""

    data = _get_data(
        data_source,
    )

    option_bindings = (
        _get_option_bindings(
            config=config,
            element_name=name,
            controls=controls,
        )
    )

    return pn.bind(
        lambda data, cfg=element_config, **runtime_options:
            _build_element(
                cfg,
                data,
                runtime_options=runtime_options,
            ),
        data=data,
        **option_bindings,
    )


def _resolve_layout_child(
    child,
    objects: dict,
):
    """Resolve one layout child."""

    # --------------------------------------------------------------
    # Named element / control
    # --------------------------------------------------------------

    if isinstance(
        child,
        str,
    ):
        if child not in objects:
            raise ValueError(
                f"Unknown layout object: "
                f"{child!r}."
            )

        return objects[
            child
        ]

    # --------------------------------------------------------------
    # Nested layout
    # --------------------------------------------------------------

    if isinstance(
        child,
        dict,
    ):
        return _build_layout(
            child,
            objects,
        )

    raise TypeError(
        "Layout children must be "
        "object names or nested layout "
        "configuration dictionaries."
    )


def _build_layout(
    layout_config: dict,
    objects: dict,
):
    """Build a recursive Panel layout from configuration."""

    layout_type = (
        layout_config.get(
            "type",
            "column",
        )
    )

    children_config = (
        layout_config.get(
            "children",
            [],
        )
    )

    sizing_mode = (
        layout_config.get(
            "sizing_mode",
            None,
        )
    )

    # --------------------------------------------------------------
    # Column
    # --------------------------------------------------------------

    if layout_type == "column":

        children = [
            _resolve_layout_child(
                child,
                objects,
            )
            for child
            in children_config
        ]

        return pn.Column(
            *children,
            sizing_mode=sizing_mode,
        )

    # --------------------------------------------------------------
    # Row
    # --------------------------------------------------------------

    if layout_type == "row":

        children = [
            _resolve_layout_child(
                child,
                objects,
            )
            for child
            in children_config
        ]

        return pn.Row(
            *children,
            sizing_mode=sizing_mode,
        )

    # --------------------------------------------------------------
    # Tabs
    # --------------------------------------------------------------

    if layout_type == "tabs":

        tabs = []

        for child in children_config:

            if not isinstance(
                child,
                dict,
            ):
                raise TypeError(
                    "Tab children must be "
                    "layout configuration "
                    "dictionaries."
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

            tab_content = (
                _build_layout(
                    tab_config,
                    objects,
                )
            )

            tabs.append(
                (
                    title,
                    tab_content,
                )
            )

        return pn.Tabs(
            *tabs,
            dynamic=layout_config.get(
                "dynamic",
                False,
            ),
            sizing_mode=sizing_mode,
        )

    raise ValueError(
        f"Unknown layout type: "
        f"{layout_type!r}."
    )


def build_app(
    config: dict,
    datasets: dict[str, xarray.Dataset] | None = None,
    context: dict | None = None,
):
    """
    Build an Echoshader application from declarative configuration.

    Parameters
    ----------
    config : dict
        Visualization application configuration.

    datasets : dict[str, xarray.Dataset], optional
        Named datasets supplied directly to the application.

        Explicitly supplied datasets override configured
        sources with the same names.

    context : dict, optional
        Runtime values available when resolving configured
        source paths.

        Values supplied here override values defined in the
        configuration's ``context`` section.

    Returns
    -------
    panel.viewable.Viewable
        Renderable Panel application.
    """

    objects = {}

    # --------------------------------------------------------------
    # Runtime context
    # --------------------------------------------------------------

    context_values = dict(
        config.get(
            "context",
            {},
        )
    )

    if context is not None:
        context_values.update(
            context,
        )

    app_context = AppContext(
        values=context_values,
    )

    # --------------------------------------------------------------
    # Data sources
    # --------------------------------------------------------------

    data_sources = (
        _build_sources(
            config=config,
            context=app_context,
        )
    )

    # Directly supplied datasets are still supported.
    if datasets is not None:
        data_sources.update(
            datasets,
        )

    # --------------------------------------------------------------
    # Controls
    # --------------------------------------------------------------

    controls = (
        _build_controls(
            config,
        )
    )

    # --------------------------------------------------------------
    # Element definitions
    # --------------------------------------------------------------

    element_configs = (
        config.get(
            "elements",
            {},
        )
    )

    # --------------------------------------------------------------
    # First pass
    #
    # Build elements whose sources already exist.
    # --------------------------------------------------------------

    for (
        name,
        element_config,
    ) in element_configs.items():

        data_name = (
            element_config[
                "data"
            ]
        )

        if (
            data_name
            not in data_sources
        ):
            continue

        objects[
            name
        ] = _build_reactive_element(
            config=config,
            name=name,
            element_config=element_config,
            data_source=data_sources[
                data_name
            ],
            controls=controls,
        )

    # --------------------------------------------------------------
    # Interactions
    # --------------------------------------------------------------

    for interaction in config.get(
        "interactions",
        [],
    ):

        interaction_type = (
            interaction[
                "type"
            ]
        )

        source_name = (
            interaction[
                "source"
            ]
        )

        output_name = (
            interaction[
                "output"
            ]
        )

        if (
            interaction_type
            != "box_select"
        ):
            raise ValueError(
                f"Unknown interaction "
                f"type: "
                f"{interaction_type!r}."
            )

        if source_name not in objects:
            raise ValueError(
                f"Interaction source "
                f"{source_name!r} "
                "does not exist."
            )

        source = (
            objects[
                source_name
            ]
        )

        box_stream = (
            get_box_stream(
                source,
            )
        )

        box_overlay = (
            get_box_plot(
                box_stream,
            )
        )

        objects[
            source_name
        ] = (
            source
            * box_overlay
        )

        source_data_name = (
            element_configs[
                source_name
            ]["data"]
        )

        source_data = (
            _get_data(
                data_sources[
                    source_data_name
                ]
            )
        )

        selection_args = (
            interaction.get(
                "args",
                {},
            )
        )

        selected_data = (
            pn.bind(
                select_box,
                ds=source_data,
                bounds=(
                    box_stream
                    .param
                    .bounds
                ),
                **selection_args,
            )
        )

        # Interaction creates a new
        # reactive data source.
        data_sources[
            output_name
        ] = selected_data

    # --------------------------------------------------------------
    # Second pass
    #
    # Build elements depending on sources created by interactions.
    # --------------------------------------------------------------

    for (
        name,
        element_config,
    ) in element_configs.items():

        if name in objects:
            continue

        data_name = (
            element_config[
                "data"
            ]
        )

        if (
            data_name
            not in data_sources
        ):
            raise ValueError(
                f"Unknown data source: "
                f"{data_name!r}."
            )

        data_source = (
            data_sources[
                data_name
            ]
        )

        objects[
            name
        ] = _build_reactive_element(
            config=config,
            name=name,
            element_config=element_config,
            data_source=data_source,
            controls=controls,
        )

    # --------------------------------------------------------------
    # Objects exposed to layout
    # --------------------------------------------------------------

    layout_objects = {
        **objects,
        **controls,
    }

    # --------------------------------------------------------------
    # Layout
    # --------------------------------------------------------------

    layout_config = (
        config.get(
            "layout",
            {
                "type": "column",
                "children": list(
                    layout_objects,
                ),
            },
        )
    )

    return _build_layout(
        layout_config,
        layout_objects,
    )