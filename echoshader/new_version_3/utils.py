gram_opts = {
    "Image": {
        "cmap": "jet",
        "colorbar": True,
        "tools": ["box_select", "lasso_select", "hover"],
        "invert_yaxis": False,
        "width": 600,
    },
    "RGB": {
        "tools": ["box_select", "lasso_select", "hover"],
        "invert_yaxis": False,
        "width": 600,
    },
    "Points": {"color": "blue", "tools": ["hover"], "size": 10, "width": 600},
    "Path": {"color": "red", "tools": ["hover"], "line_width": 1, "width": 600},
    "Tiles": {"tools": ["box_select"]},
    "Histogram": {"fontsize": {"legend": 5}, "width": 600},
    "Table": {"width": 600},
    "Bounds": {"line_width": 1, "line_color": "white"},
}

curtain_opts = {"width": 700, "height": 500}

tiles = [
    "CartoDark",
    "CartoEco",
    "CartoLight",
    "CartoMidnight",
    "ESRI",
    "EsriImagery",
    "EsriNatGeo",
    "EsriOceanBase",
    "EsriOceanReference",
    "EsriReference",
    "EsriTerrain",
    "EsriUSATopo",
    "OSM",
    "OpenTopoMap",
    "StamenLabels",
    "StamenTerrain",
    "StamenTerrainRetina",
    "StamenToner",
    "StamenTonerBackground",
    "StamenWatercolor",
]

EPSG_mercator = "EPSG:3857"

EPSG_coordsys = "EPSG:4326"