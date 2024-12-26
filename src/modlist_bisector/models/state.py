from pydantic import BaseModel


class State(BaseModel):
    S: list[frozenset[str]]
    """The ordered set of closures of modids that we know are in the final set."""
    D: list[frozenset[str]]
    """The ordered set of closures of modids that are still to be searched."""
    L: int
    """The left index of the binary search."""
    R: int
    """The right index of the binary search."""
    m: int
    """The middle index of the binary search."""
