import tomllib
from pathlib import Path
from typing import Annotated, Self

from pydantic import AfterValidator, BaseModel, ValidationInfo


def _validate_ConfigRelativePath(value: Path, info: ValidationInfo):
    if value.is_absolute():
        return value

    match info.context:
        case {"config_path": Path() as config_path}:
            return (config_path / value).resolve()
        case _:
            raise RuntimeError(
                "config_path not found in context (try using Config.load() instead)"
            )


type ConfigRelativePath = Annotated[Path, AfterValidator(_validate_ConfigRelativePath)]


class Config(BaseModel):
    modloaders: list[str]
    """IDs of modloaders to attempt to load mods with."""
    mods_dirs: list[ConfigRelativePath]
    """Directories to look for mods in.

    Relative paths are resolved from the location of the config file.
    """

    @classmethod
    def load(cls, path: str | Path) -> Self:
        path = Path(path)
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data, context={"config_path": path})
