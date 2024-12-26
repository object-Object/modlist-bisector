import json
from pathlib import Path
from typing import Self

from pydantic import BaseModel


class State(BaseModel):
    mod_jars: dict[str, Path]
    """Mapping from modid to jar path."""

    S: list[frozenset[str]]
    """The list of closures of modids that we know are in the final set."""
    D: list[frozenset[str]]
    """The ordered set of closures of modids that are still to be searched."""

    L: int
    """The left index of the binary search."""
    R: int
    """The right index of the binary search."""
    m: int
    """The middle index of the binary search."""

    @classmethod
    def load(cls, path: str | Path) -> Self:
        path = Path(path)
        with path.open("rb") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def dump(self, path: str | Path):
        data = self.model_dump_json(round_trip=True)
        Path(path).write_text(data, encoding="utf-8")
