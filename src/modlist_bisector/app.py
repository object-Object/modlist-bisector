from pathlib import Path
from typing import Annotated

from typer import Option, Typer

from modlist_bisector.models.config import Config
from modlist_bisector.utils.paths import multi_rglob

DEFAULT_CONFIG_FILE = "config.toml"


def _parse_config(value: str) -> Config:
    path = Path(value)
    if path.is_dir():
        path /= DEFAULT_CONFIG_FILE
    return Config.load(path)


ConfigOption = Annotated[
    Config,
    Option(
        "--config",
        "-c",
        show_default=DEFAULT_CONFIG_FILE,
        default_factory=lambda: DEFAULT_CONFIG_FILE,
        parser=_parse_config,
    ),
]


def load_mod(config: Config, path: Path):
    for mod_type in config.mod_types:
        if mod := mod_type.try_load_zip(path):
            return mod


app = Typer(
    pretty_exceptions_show_locals=False,
)


@app.command()
def start(config: ConfigOption):
    for mods_dir in config.mods_dirs:
        print(mods_dir)
        for mod_path in multi_rglob(mods_dir, "*.jar", "*.jar.disabled"):
            print(mod_path)
            print(load_mod(config, mod_path))


@app.command()
def reset():
    pass


if __name__ == "__main__":
    app()
