from pathlib import Path

from .json import JSONBaseModel


class State(JSONBaseModel):
    jars: dict[str, set[Path]]
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
