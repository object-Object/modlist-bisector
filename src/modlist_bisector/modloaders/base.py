from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel


@dataclass
class Mod[T: BaseModel](ABC):
    modloader: ClassVar[str]
    meta_path: ClassVar[Path]

    meta: T

    def __init_subclass__(cls, modloader: str, meta_path: str | Path, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        cls.modloader = modloader
        cls.meta_path = Path(meta_path)

    @classmethod
    @abstractmethod
    def load_meta(cls, data: str) -> T:
        """Parses the raw mod metadata file into a typed model."""

    @property
    @abstractmethod
    def id(self) -> str:
        """The modid of this mod."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of this mod."""
