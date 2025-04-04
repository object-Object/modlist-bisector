# pyright: reportUnknownArgumentType=information
# pyright: reportUnknownMemberType=information
# pyright: reportUnknownVariableType=information

import logging
from enum import Enum, auto
from typing import Iterator

import networkx as nx

from modlist_bisector.models.dependency_graph import DependencyGraph
from modlist_bisector.models.state import State

logger = logging.getLogger(__name__)


IGNORED_DEPENDENCIES = {
    "java",
    "minecraft",
    "fabric",
    "fabricloader",
    "quilt_loader",
}


class StepResult(Enum):
    CONTINUE = auto()
    """The binary reduction algorithm has not yet terminated."""
    DONE = auto()
    """"""
    FAILED = auto()


def setup_binary_reduction(graph: DependencyGraph, required_mods: set[str]) -> State:
    G = nx.DiGraph()
    for modid, dependencies in graph.dependencies.items():
        for dependency in dependencies:
            G.add_edge(modid, dependency)

    S = set[frozenset[str]]()
    D = set[frozenset[str]]()

    for modid in G:
        closure = frozenset(get_closure(G, modid, set()))
        if modid in required_mods:
            S.add(closure)
        else:
            D.add(closure)

    for closure in S:
        try:
            D.remove(closure)
        except KeyError:
            pass

    state = State(
        jars=graph.jars,
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
    disabled = state.jars.keys() - enabled
    return enabled, disabled


def apply_modlist(state: State, enabled: set[str], disabled: set[str]):
    newly_enabled = set[str]()
    newly_disabled = set[str]()

    for modid in enabled:
        for enabled_path in state.jars[modid]:
            disabled_path = enabled_path.with_suffix(".jar.disabled")
            if disabled_path.exists():
                disabled_path.rename(enabled_path)
                newly_enabled.add(modid)

    for modid in disabled:
        for enabled_path in state.jars[modid]:
            disabled_path = enabled_path.with_suffix(".jar.disabled")
            if enabled_path.exists():
                enabled_path.rename(disabled_path)
                newly_disabled.add(modid)

    n = len(enabled) + len(disabled)
    logger.info(
        f"Enabled: {len(enabled) - len(newly_enabled) + len(newly_disabled)}/{n} -> {len(enabled)}/{n}\n"
        + "\n".join(
            [f"+ {modid}" for modid in sorted(newly_enabled)]
            + [f"- {modid}" for modid in sorted(newly_disabled)]
        )
    )


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
