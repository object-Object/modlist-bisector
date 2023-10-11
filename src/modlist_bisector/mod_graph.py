import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Self, TypeVar, overload

import networkx as nx

from .config import Config
from .mod_log import glob_logs, load_log, next_log, save_log
from .modloaders import DISABLED_SUFFIX, ModData, load_mods
from .paths import rename_path

GRAPH_PATH = Path("graph.json")


_T = TypeVar("_T")


class ModNode(ModData):
    path: str
    """Path relative to the root"""
    enabled: bool
    """If the mod should be enabled or not"""
    locked: bool
    """If true, ensure the mod's state is the same as `self.enabled`"""


@dataclass(kw_only=True)
class ModGraph:
    config: Config
    G: nx.DiGraph
    """Graph of dependencies.
    
    For an edge `A -> B`, `A` needs `B`, so `A` must be disabled before `B`."""

    @classmethod
    def build(cls, config: Config | Path, *, reset: bool) -> Self:
        next_log(glob_logs()).touch()

        if isinstance(config, Path):
            config = Config.load(config)

        G = nx.DiGraph()

        for path, mod in load_mods(config.root):
            enabled = path.suffix != DISABLED_SUFFIX
            if not enabled:
                path = path.with_suffix("")

            node = ModNode(
                path=path.as_posix(),
                enabled=enabled,
                locked=False,
                **mod.data(),
            )

            G.add_node(mod.id, **node)

            for dependency in mod.depends_ids():
                G.add_edge(mod.id, dependency)

        mod_graph = cls(config=config, G=G).sync()
        return mod_graph.reset() if reset else mod_graph

    @classmethod
    def load(cls, config: Config | Path) -> Self:
        if isinstance(config, Path):
            config = Config.load(config)

        with GRAPH_PATH.open() as f:
            G = nx.adjacency_graph(json.load(f))

        return cls(config=config, G=G).sync()

    def sync(self):
        # sync locks with config
        for modid, enabled in self.config.overrides.items():
            node = self.node(modid)
            node |= {"locked": True, "enabled": enabled}

        # sync deps with config
        for modid, dependencies in self.config.extra_deps.items():
            for dependency in dependencies:
                self.G.add_edge(modid, dependency)

        # remove nodes without dependency data
        for modid, node in list(self.nodes.items()):
            if not node:
                self.G.remove_node(modid)

        self.assert_acyclic_pending()

        # sync folder with graph and ensure deps
        for modid in nx.topological_sort(self.G):
            node = self.node(modid)
            for ancestor in nx.ancestors(self.G, modid):
                if self.node(ancestor)["enabled"]:
                    node["enabled"] = True
                    break
            # enable the mod if an ancestor is enabled OR if it was already enabled
            # otherwise disable it
            self.set_enabled(modid, node["enabled"], force=True)

        return self  # for chaining

    def save(self):
        with GRAPH_PATH.open("w") as f:
            json.dump(nx.adjacency_data(self.G), f)

        log = load_log()
        log.append(self.dump_enabled())
        save_log(log)

        return self

    def reset(self):
        for modid in self.nodes:
            self.enable(modid)
        self.sync()
        return self

    def dump_enabled(self):
        return sorted(modid for modid, node in self.nodes.items() if node["enabled"])

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
            return self.nodes[modid]
        return self.nodes.get(modid, default)

    def bisect(self):
        enabled, _, total = self.count_nodes()
        to_disable = enabled // 2
        newly_disabled = 0

        for modid in nx.topological_sort(self.G):
            if self.node(modid)["locked"]:
                continue

            enabled -= 1
            if not self.disable(modid):
                continue

            newly_disabled += 1
            if newly_disabled >= to_disable:
                break

        print(f"Disabled {newly_disabled} mods ({enabled}/{total} remaining).")
        return self

    def set_disabled_good(self):
        for modid, node in self.pending_nodes().items():
            if not node["enabled"]:
                self.set_good(modid, True)
        return self

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

        return self

    def enable(self, modid: str):
        return self.set_enabled(modid, True)

    def disable(self, modid: str):
        return self.set_enabled(modid, False)

    def toggle(self, modid: str):
        node = self.node(modid)
        return self.set_enabled(modid, not node["enabled"])

    def set_enabled(self, modid: str, enabled: bool, *, force: bool = False):
        node = self.node(modid)
        if not force and enabled is node["enabled"]:
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
            if node["locked"]:
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
            filter_node=lambda modid: not self.node(modid)["locked"],
        )
