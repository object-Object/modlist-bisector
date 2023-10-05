from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Iterator, NotRequired, TypedDict
from zipfile import ZipFile

import networkx as nx
from pydantic import BaseModel, Field, model_validator

FABRIC_FILE = "fabric.mod.json"
QUILT_FILE = "quilt.mod.json"


class Config(BaseModel):
    root: Path
    required: set[str]
    extra_deps: dict[str, list[str]]


class Manifest(BaseModel):
    root: Path
    mods: dict[str, Mod] = Field(default_factory=dict)
    started: bool = False

    @classmethod
    def load_mods(cls, mods_dir: Path):
        config_data = Path("config.toml").read_text("utf-8")
        config = Config.model_validate(tomllib.loads(config_data))

        mods_dir = mods_dir.resolve()
        manifest = Manifest(root=mods_dir)

        for mod_path in mods_dir.rglob("*.jar"):
            mod_path = mod_path.relative_to(mods_dir)
            print(f"Loading {mod_path}")

            with ZipFile(mods_dir / mod_path) as jar:
                mod = Mod.load(jar, mod_path)

                if mod.id in config.required:
                    continue
                if mod.id in config.extra_deps:
                    mod.depends += config.extra_deps[mod.id]

                manifest.mods[mod.id] = mod

        manifest.recalc_graph()
        return manifest

    @classmethod
    def load_file(cls, path: str | Path):
        data = Path(path).read_text("utf-8")
        return cls.model_validate_json(data)

    @model_validator(mode="after")
    def _do_add_edges(self):
        self._G = nx.DiGraph()
        self._G.nodes
        self.recalc_graph()
        return self

    def dump_file(self, path: str | Path):
        data = self.model_dump_json(
            indent=2,
            round_trip=True,
        )
        Path(path).write_text(data, "utf-8")

    def recalc_graph(self):
        self._G.clear()

        for mod in self.mods.values():
            if mod.disabled:
                continue

            self._G.add_node(mod)
            for dep_id in mod.depends:
                if dep_id not in self.mods:
                    continue

                dep = self.mods[dep_id]
                if dep.disabled:
                    continue

                self._G.add_edge(mod, dep)

    def bisect(self):
        remaining = len(self.mods) // 2
        while remaining > 0:
            for mod in list(self.mods_without_dependents()):
                self._G.remove_node(mod)
                mod.disable(self.root)

                remaining -= 1
                if remaining <= 0:
                    break

        enabled, disabled = self.get_partitions()
        print(f"{len(enabled)} enabled, {len(disabled)} disabled")

    def drop_disabled(self):
        _, disabled = self.get_partitions()
        for mod in disabled:
            del self.mods[mod.id]

    def drop_enabled(self):
        # TODO: this needs to take dependencies into account
        # there could be an enabled dep for a disabled mod
        enabled, disabled = self.get_partitions()
        for mod in enabled:
            del self.mods[mod.id]
        for mod in disabled:
            mod.disabled = False

    def fix_deps(self):
        # TODO: this doesn't actually work because _G doesn't contain disabled.
        # should have two graphs, enabled and all
        config_data = Path("config.toml").read_text("utf-8")
        config = Config.model_validate(tomllib.loads(config_data))

        for required in config.required:
            if required in self.mods:
                del self.mods[required]

        for id, deps in config.extra_deps.items():
            if id in self.mods:
                self.mods[id].depends += deps

        self.recalc_graph()
        for mod in self.mods_with_dependents():
            if mod.disabled:
                mod.enable(self.root)

    def get_partitions(self):
        enabled = list[Mod]()
        disabled = list[Mod]()

        for mod in self.mods.values():
            if mod.disabled:
                disabled.append(mod)
            else:
                enabled.append(mod)

        return enabled, disabled

    def mods_with_dependents(self) -> Iterator[Mod]:
        for mod, in_degree in self._G.in_degree():
            if in_degree > 0:
                yield mod

    def mods_without_dependents(self) -> Iterator[Mod]:
        for mod, in_degree in self._G.in_degree():
            if in_degree == 0:
                yield mod


class Mod(BaseModel):
    name: str
    path: Path
    id: str
    disabled: bool = False
    depends: list[str]

    @classmethod
    def load(cls, jar: ZipFile, path: Path):
        filenames = set(jar.namelist())
        if FABRIC_FILE in filenames:
            return parse_fabric_mod(jar, path)
        elif QUILT_FILE in filenames:
            return parse_quilt_mod(jar, path)
        else:
            raise RuntimeError(f"Unsupported mod type")

    def enable(self, root: Path):
        self.disabled = False
        path = (root / self.path).resolve()
        if path.name.endswith(".disabled"):
            path.rename(path.with_suffix(""))

    def disable(self, root: Path):
        self.disabled = True
        path = (root / self.path).resolve()
        if not path.name.endswith(".disabled"):
            path.rename(path.with_suffix(path.suffix + ".disabled"))

    def __repr__(self) -> str:
        return f"Mod({self.id})"

    def __eq__(self, other: object) -> bool:
        match other:
            case Mod():
                return self.id == other.id
            case _:
                return super().__eq__(other)

    def __hash__(self) -> int:
        return self.id.__hash__()


class FabricModData(TypedDict):
    id: str
    name: str
    depends: NotRequired[dict[str, str | list[str]]]
    """modid -> version(s)"""


class QuiltModData(TypedDict):
    quilt_loader: dict[
        {
            "id": str,
            "name": NotRequired[str],
            "metadata": NotRequired[dict[{"name": str}]],
            "depends": list[str | dict[{"id": str}]],
        }
    ]


def parse_fabric_mod(jar: ZipFile, path: Path) -> Mod:
    mod_data: FabricModData = _load_mod_json(jar, FABRIC_FILE)
    return Mod(
        id=mod_data["id"],
        name=mod_data["name"],
        path=path,
        depends=list(mod_data.get("depends", {}).keys()),
    )


def parse_quilt_mod(jar: ZipFile, path: Path) -> Mod:
    mod_data: QuiltModData = _load_mod_json(jar, QUILT_FILE)
    quilt_loader = mod_data["quilt_loader"]

    match quilt_loader:
        case {"metadata": {"name": str(name)}}:
            pass
        case {"name": str(name)}:
            pass
        case _:
            name = quilt_loader["id"]

    return Mod(
        id=quilt_loader["id"],
        name=name,
        path=path,
        depends=[_parse_quilt_dep(v) for v in quilt_loader["depends"]],
    )


def _load_mod_json(jar: ZipFile, filename: str):
    with jar.open(filename) as f:
        data = f.read().decode("utf-8").replace("\n", "")
    return json.loads(data)


def _parse_quilt_dep(value: str | dict[{"id": str}]):
    match value:
        case str(id):
            return id
        case {"id": str(id)}:
            return id
        case _:
            raise TypeError(f"Unhandled dependency type: {value}")
