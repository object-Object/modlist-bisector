from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Iterable, Self
from zipfile import ZipFile

from pydantic import BaseModel


@dataclass
class Mod[T: BaseModel](ABC):
    modloader: ClassVar[str]
    meta_path: ClassVar[str]

    meta: T

    def __init_subclass__(cls, modloader: str, meta_path: str, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        cls.modloader = modloader
        cls.meta_path = meta_path

    @classmethod
    @abstractmethod
    def load_meta(cls, data: str) -> T:
        """Parses the raw mod metadata file into a typed model."""

    @classmethod
    def load_zip(cls, path: str | Path) -> Self:
        with ZipFile(path) as zf:
            raw_meta = zf.read(cls.meta_path).decode("utf-8")
        meta = cls.load_meta(raw_meta)
        return cls(meta=meta)

    @property
    @abstractmethod
    def id(self) -> str:
        """The modid of this mod."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of this mod."""

    @abstractmethod
    def dependencies(self) -> Iterable[str]:
        """Modids required by this mod."""
