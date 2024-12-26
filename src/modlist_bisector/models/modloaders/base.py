from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Iterable, Self
from zipfile import ZipFile

from pydantic import BaseModel

type AnyMod = Mod[Any]


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
        mod = cls.try_load_zip(path)
        if mod is None:
            raise FileNotFoundError(
                f"Archive '{path}' does not contain file '{cls.meta_path}'"
            )
        return mod

    @classmethod
    def try_load_zip(cls, path: str | Path) -> Self | None:
        with ZipFile(path) as zf:
            try:
                info = zf.getinfo(cls.meta_path)
            except KeyError:
                return None
            raw_meta = zf.read(info).decode("utf-8")
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

    @abstractmethod
    def provides(self) -> Iterable[str]:
        """Modids provided by this mod."""

    @abstractmethod
    def jars(self) -> Iterable[Path]:
        """Nested jars provided by this mod."""
