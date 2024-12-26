from pathlib import Path

from modlist_bisector.models.config import Config


def load_mod(config: Config, path: Path):
    for mod_type in config.mod_types:
        if mod := mod_type.try_load_zip(path):
            return mod
    raise ValueError(f"Failed to load mod: {path}")
