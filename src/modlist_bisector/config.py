import tomllib
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel
from pydantic.functional_validators import AfterValidator

AbsolutePath = Annotated[Path, AfterValidator(Path.resolve)]


class Config(BaseModel):
    root: AbsolutePath
    required: set[str]
    extra_deps: dict[str, list[str]]

    @classmethod
    def load(cls, path: Path):
        with path.open("rb") as f:
            return cls.model_validate(tomllib.load(f))
