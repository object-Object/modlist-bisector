from enum import Enum, auto

from modlist_bisector.models.state import State


class StepResult(Enum):
    CONTINUE = auto()
    """The binary reduction algorithm has not yet terminated."""
    DONE = auto()
    """"""
    FAILED = auto()


def get_modlist(state: State) -> set[str]:
    return flatten_closures(state.S + state.D[: state.m + 1])


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
