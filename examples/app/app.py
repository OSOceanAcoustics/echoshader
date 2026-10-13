from pathlib import Path

from echoshader.app.builder import build_app
from echoshader.app.config import load_config


config = load_config(
    Path(__file__).with_name(
        "app_config.yaml"
    )
)

build_app(
    config
).servable()