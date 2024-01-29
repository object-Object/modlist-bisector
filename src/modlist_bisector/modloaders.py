from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Iterable, Self, TypedDict
from zipfile import ZipFile

from pydantic import Field
from pydantic.config import ConfigDict
from tqdm import tqdm
from typing_extensions import Unpack

from .model import DefaultModel

DISABLED_SUFFIX = ".disabled"

ALLOWED_SUFFIXES = (
    ".jar",
    f".jar{DISABLED_SUFFIX}",
)


def find_mods(root: Path):
    with tqdm(desc="Loading mods", leave=False) as bar:
        for path in root.rglob("*.jar*"):
            bar.set_postfix_str(path.name)
            bar.update(1)

            if path.name.endswith(ALLOWED_SUFFIXES) and path.is_file():
                yield path


def load_mods(root: Path):
    for path in find_mods(root):
        path_from_root = path.relative_to(root)

        with ZipFile(path) as jar:
            mod = load_mod(jar)

        yield path_from_root, mod


def load_mod(jar: ZipFile):
    for mod_type in [
        FabricMod,
        QuiltMod,
    ]:
        if mod_type.FILENAME in jar.NameToInfo:
            return mod_type.load(jar)
    raise ValueError(f"Mod metadata not found: {jar}")


class ModData(TypedDict):
    name: str


class BaseMod(DefaultModel, ABC):
    FILENAME: ClassVar[str]

    def __init_subclass__(cls, filename: str, **kwargs: Unpack[ConfigDict]):
        super().__init_subclass__(**kwargs)
        cls.FILENAME = filename

    @classmethod
    def load(cls, jar: ZipFile) -> Self:
        with jar.open(cls.FILENAME) as f:
            raw_data = f.read()
        data = raw_data.decode("utf-8").replace("\n", "")
        return cls.model_validate_json(data)

    @abstractmethod
    def data(self) -> ModData:
        ...

    @abstractmethod
    def depends_ids(self) -> Iterable[str]:
        ...


class FabricMod(BaseMod, filename="fabric.mod.json"):
    id: str
    name: str
    depends: dict[str, str | list[str]] = Field(default_factory=dict)

    def data(self):
        return ModData(
            name=self.name,
        )

    def depends_ids(self):
        return self.depends.keys()


class QuiltMod(BaseMod, filename="quilt.mod.json"):
    quilt_loader: QuiltLoader

    class QuiltLoader(DefaultModel):
        id: str
        name: str | None = None
        metadata: Metadata | None = None
        depends: list[str | Depends]

        class Metadata(DefaultModel):
            name: str

        class Depends(DefaultModel):
            id: str

        def get_name(self):
            if self.name is not None:
                return self.name
            if self.metadata is not None:
                return self.metadata.name
            return self.id

    @property
    def id(self):
        return self.quilt_loader.id

    def data(self):
        return ModData(
            name=self.quilt_loader.get_name(),
        )

    def depends_ids(self):
        for dependency in self.quilt_loader.depends:
            match dependency:
                case str(modid):
                    yield modid
                case QuiltMod.QuiltLoader.Depends(id=modid):
                    yield modid
