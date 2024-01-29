import tomllib
from pathlib import Path
from typing import Annotated

from pydantic.functional_validators import AfterValidator

from .model import DefaultModel

AbsolutePath = Annotated[Path, AfterValidator(Path.resolve)]


class Config(DefaultModel):
    root: AbsolutePath
    overrides: dict[str, bool]
    extra_deps: dict[str, list[str]]

    @classmethod
    def load(cls, path: Path):
        with path.open("rb") as f:
            return cls.model_validate(tomllib.load(f))
