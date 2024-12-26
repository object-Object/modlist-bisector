# pyright: reportUnknownArgumentType=information
# pyright: reportUnknownMemberType=information
# pyright: reportUnknownVariableType=information

import fnmatch
import logging
from enum import Enum, auto
from typing import Any, Iterator

import networkx as nx

from modlist_bisector.models.config import Config
from modlist_bisector.models.modloaders.base import Mod
from modlist_bisector.models.state import State
from modlist_bisector.utils.mods import load_mod

logger = logging.getLogger(__name__)


class StepResult(Enum):
    CONTINUE = auto()
    """The binary reduction algorithm has not yet terminated."""
    DONE = auto()
    """"""
    FAILED = auto()


def setup_binary_reduction(config: Config) -> State:
    G = nx.DiGraph()

    for mods_dir in config.mods_dirs:
        logger.debug(f"Loading {mods_dir=}")
        for mod_path in mods_dir.rglob("*.jar"):
            logger.debug(f"Loading {mod_path=}")
            for ignore_path in config.ignored_paths:
                if fnmatch.fnmatch(mod_path.as_posix(), ignore_path):
                    logger.debug(
                        f"Path {mod_path} matches pattern {ignore_path}, skipping."
                    )
                    continue

            try:
                mod = load_mod(config, mod_path)
            except Exception:
                logger.error(f"Failed to load mod: {mod_path}")
                raise

            G.add_node(mod.id, path=mod_path, mod=mod)

    for modid, data in G.nodes(data=True):
        mod: Mod[Any] = data["mod"]
        for dependency in mod.dependencies():
            if dependency in G:
                G.add_edge(modid, dependency)
            else:
                logger.warning(f"Missing dependency for {modid}: {dependency}")

    S = set[frozenset[str]]()
    D = set[frozenset[str]]()

    for modid in G:
        closure = frozenset(get_closure(G, modid, set()))
        if modid in config.required_mods:
            S.add(closure)
        else:
            D.add(closure)

    for closure in S:
        try:
            D.remove(closure)
        except KeyError:
            pass

    state = State(
        mod_jars={modid: data["path"] for modid, data in G.nodes(data=True)},
        S=list(S),
        D=list(D),
        L=0,
        R=0,
        m=0,
    )
    reset_binary_search(state)
    return state


def get_closure(G: nx.DiGraph, modid: str, seen: set[str]) -> Iterator[str]:
    if modid in seen:
        return
    seen = seen | {modid}
    yield modid
    for _, dependency in G.out_edges(modid):
        yield from get_closure(G, dependency, seen)


def get_and_apply_modlist(state: State) -> tuple[set[str], set[str]]:
    enabled, disabled = get_modlist(state)
    apply_modlist(state, enabled, disabled)
    return enabled, disabled


def get_modlist(state: State) -> tuple[set[str], set[str]]:
    """Returns enabled, disabled."""
    enabled = flatten_closures(state.S + state.D[: state.m + 1])
    disabled = state.mod_jars.keys() - enabled
    return enabled, disabled


def apply_modlist(state: State, enabled: set[str], disabled: set[str]):
    for modid in enabled:
        enabled_path = state.mod_jars[modid]
        disabled_path = enabled_path.with_suffix(".jar.disabled")
        if disabled_path.exists():
            disabled_path.rename(enabled_path)

    for modid in disabled:
        enabled_path = state.mod_jars[modid]
        disabled_path = enabled_path.with_suffix(".jar.disabled")
        if enabled_path.exists():
            enabled_path.rename(disabled_path)


def step_binary_reduction(state: State, is_bad: bool) -> StepResult:
    if state.m < 0:
        if is_bad:
            return StepResult.DONE
        elif not state.D:
            return StepResult.FAILED
    else:
        if is_bad:
            state.R = state.m
        else:
            state.L = state.m + 1

    if state.L >= state.R:
        state.S.append(state.D[state.L])
        state.D = state.D[: state.L]
        reset_binary_search(state)
    else:
        state.m = (state.L + state.R) // 2

    return StepResult.CONTINUE


def reset_binary_search(state: State) -> None:
    state.D.sort(key=lambda v: cost(state.S + [v]))
    state.L = 0
    state.R = len(state.D)
    state.m = -1


def cost(closures: list[frozenset[str]]) -> float:
    return len(flatten_closures(closures))


def flatten_closures(closures: list[frozenset[str]]):
    return set(value for closure in closures for value in closure)
