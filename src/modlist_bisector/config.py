import tomllib
from pathlib import Path
from typing import Annotated, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    PrivateAttr,
    ValidationInfo,
    model_validator,
)

from modlist_bisector.modloaders import MODLOADERS, AnyMod


def _validate_ConfigRelativePath(value: Path, info: ValidationInfo):
    if value.is_absolute():
        return value

    match info.context:
        case {"config_dir": Path() as config_dir}:
            return (config_dir / value).resolve()
        case _:
            raise RuntimeError(
                "config_dir not found in context (try using Config.load() instead)"
            )


type ConfigRelativePath = Annotated[Path, AfterValidator(_validate_ConfigRelativePath)]


class Config(BaseModel):
    modloaders: list[str]
    """IDs of modloaders to attempt to load mods with."""
    mods_dirs: list[ConfigRelativePath]
    """Directories to look for mods in.

    Relative paths are resolved from the location of the config file.
    """

    _mod_types: list[type[AnyMod]] = PrivateAttr(default_factory=list)

    @classmethod
    def load(cls, path: str | Path) -> Self:
        path = Path(path).resolve()
        with path.open("rb") as f:
            data = tomllib.load(f)
        return cls.model_validate(data, context={"config_dir": path.parent})

    @property
    def mod_types(self):
        return self._mod_types

    @model_validator(mode="after")
    def _set_mod_types(self):
        for modloader in self.modloaders:
            mod_type = MODLOADERS.get(modloader)
            if mod_type is None:
                raise ValueError(f"Unknown modloader: {modloader}")
            self.mod_types.append(mod_type)
        return self
