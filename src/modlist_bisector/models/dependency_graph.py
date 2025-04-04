from pathlib import Path

from .json import JSONBaseModel


class DependencyGraph(JSONBaseModel):
    """Mirror of `gay.object.dependencygrapher.api.DependencyGraph`."""

    dependencies: dict[str, set[str]]
    jars: dict[str, set[Path]]
