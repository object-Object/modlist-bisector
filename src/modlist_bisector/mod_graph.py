import itertools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Self, TypeVar, overload

import networkx as nx

from .config import Config
from .modloaders import DISABLED_SUFFIX, ModData, load_mods
from .paths import rename_path

GRAPH_PATH = Path("graph.json")
LOG_PATH = Path("log.json")

_T = TypeVar("_T")


class ModNode(ModData):
    path: str
    is_good: bool | None
    enabled: bool


@dataclass(kw_only=True)
class ModGraph:
    config: Config
    G: nx.DiGraph
    """Graph of dependencies.
    
    For an edge `A -> B`, `A` needs `B`, so `A` must be disabled before `B`."""
    log: list[list[str]]

    @classmethod
    def load_mods(cls, config: Config | Path) -> Self:
        if isinstance(config, Path):
            config = Config.load(config)

        G = nx.DiGraph()

        for path, mod in load_mods(config.root):
            if path.suffix == DISABLED_SUFFIX:
                enabled = False
                path = path.with_suffix("")
            else:
                enabled = True

            node = ModNode(
                path=path.as_posix(),
                enabled=enabled,
                is_good=None,
                **mod.data(),
            )

            G.add_node(mod.id, **node)

            for dependency in itertools.chain(
                mod.depends_ids(),
                config.extra_deps.get(mod.id, []),
            ):
                G.add_edge(mod.id, dependency)

        for modid, node in list(G.nodes.items()):
            if not node:
                G.remove_node(modid)

        mod_graph = cls(
            config=config,
            G=G,
            log=[],
        )

        for modid in config.required:
            mod_graph.enable(modid)
            mod_graph.set_good(modid, True)

        return mod_graph

    @classmethod
    def load_file(cls, config: Config | Path) -> Self:
        if isinstance(config, Path):
            config = Config.load(config)

        with GRAPH_PATH.open() as f:
            G = nx.adjacency_graph(json.load(f))

        with LOG_PATH.open() as f:
            log = json.load(f)

        return cls(
            config=config,
            G=G,
            log=log,
        )

    def dump_file(self):
        self.log.append(
            sorted(modid for modid, node in self.nodes.items() if node["enabled"])
        )

        with GRAPH_PATH.open("w") as f:
            json.dump(nx.adjacency_data(self.G), f)
        with LOG_PATH.open("w") as f:
            json.dump(self.log, f)

    def assert_acyclic_pending(self):
        try:
            cycle = nx.find_cycle(self.pending_view())
        except nx.NetworkXNoCycle:
            pass
        else:
            raise ValueError(f"Cycle detected: {cycle}")

    @property
    def nodes(self) -> Mapping[str, ModNode]:
        return self.G.nodes

    @overload
    def node(self, modid: str) -> ModNode:
        ...

    @overload
    def node(self, modid: str, default: _T) -> ModNode | _T:
        ...

    def node(self, modid: str, default: _T = ...) -> ModNode | _T:
        if default is ...:
            return self.G.nodes[modid]
        return self.G.nodes.get(modid, default)

    def bisect(self):
        newly_disabled = 0
        enabled, disabled, total = self.count_nodes()

        for modid in itertools.islice(
            nx.topological_sort(self.pending_view()),
            enabled // 2,
        ):
            if self.node(modid)["is_good"] is not None:
                continue

            enabled -= 1
            disabled += 1
            if self.disable(modid):
                newly_disabled += 1

        print(f"Disabled {newly_disabled} mods ({enabled}/{total} remaining).")

    def set_disabled_good(self):
        for modid, node in self.pending_nodes().items():
            if not node["enabled"]:
                self.set_good(modid, True)

    def set_enabled_good(self):
        """
        disabled -> enabled
        enabled + parent of disabled -> enabled
        other -> disabled + bad
        """
        to_enable = set[str]()
        to_disable = set[str]()

        for modid, node in self.pending_nodes().items():
            if node["enabled"]:
                to_disable.add(modid)
            else:
                to_enable.add(modid)

        for modid in to_enable:
            self.enable(modid)
            for dependency in nx.descendants(self.G, modid):
                self.enable(dependency)
                to_disable.discard(dependency)

        for modid in to_disable:
            self.disable(modid)
            self.set_good(modid, True)

    def enable(self, modid: str):
        return self.set_enabled(modid, True)

    def disable(self, modid: str):
        return self.set_enabled(modid, False)

    def toggle(self, modid: str):
        node = self.node(modid)
        return self.set_enabled(modid, not node["enabled"])

    def set_enabled(self, modid: str, enabled: bool):
        node = self.node(modid)
        if enabled is node["enabled"]:
            return False

        # update the node
        self.G.add_node(modid, enabled=enabled)

        enabled_path, disabled_path = self.node_paths(node)
        if enabled:
            return rename_path(disabled_path, enabled_path)
        else:
            return rename_path(enabled_path, disabled_path)

    def set_good(self, modid: str, is_good: bool | None):
        self.G.add_node(modid, is_good=is_good)

    def node_paths(self, node: ModNode) -> tuple[Path, Path]:
        """node -> (enabled, disabled)"""
        enabled = self.config.root / node["path"]
        disabled = enabled.with_name(enabled.name + DISABLED_SUFFIX)
        return enabled, disabled

    def count_nodes(self) -> tuple[int, int, int]:
        """-> (enabled, disabled, total)"""
        enabled = disabled = total = 0

        for node in self.nodes.values():
            total += 1
            if node["is_good"] is not None:
                continue

            if node["enabled"]:
                enabled += 1
            else:
                disabled += 1

        return enabled, disabled, total

    def pending_nodes(self) -> dict[str, ModNode]:
        return {modid: node for modid, node in self.pending_view().nodes.items()}

    def pending_view(self):
        return nx.subgraph_view(
            self.G,
            filter_node=lambda modid: self.node(modid)["is_good"] is None,
        )
