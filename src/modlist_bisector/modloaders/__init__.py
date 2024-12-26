__all__ = [
    "MODLOADERS",
    "AnyMod",
    "FabricMod",
    "Mod",
    "QuiltMod",
]

from typing import Any

from .base import AnyMod, Mod
from .fabric import FabricMod
from .quilt import QuiltMod

MODLOADERS: dict[str, type[Mod[Any]]] = {
    mod_type.modloader: mod_type
    for mod_type in [
        FabricMod,
        QuiltMod,
    ]
}
