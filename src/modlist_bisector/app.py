import logging
from pathlib import Path
from typing import Annotated

from typer import Argument, Option, Typer

from modlist_bisector.binary_reduction import (
    StepResult,
    apply_modlist,
    get_and_apply_modlist,
    get_modlist,
    setup_binary_reduction,
    step_binary_reduction,
)
from modlist_bisector.models.dependency_graph import DependencyGraph
from modlist_bisector.models.state import State
from modlist_bisector.utils.logging import setup_logging

logger = logging.getLogger(__name__)


DEFAULT_STATE_FILE = "state.json"


def _parse_state_path(value: str) -> Path:
    path = Path(value)
    if path.is_dir():
        path /= DEFAULT_STATE_FILE
    return path


StatePathOption = Annotated[
    Path,
    Option(
        "--state",
        "-s",
        show_default=DEFAULT_STATE_FILE,
        default_factory=lambda: DEFAULT_STATE_FILE,
        parser=_parse_state_path,
    ),
]

VerbosityOption = Annotated[int, Option("--verbose", "-v", count=True)]


app = Typer(
    pretty_exceptions_show_locals=False,
)


@app.command()
def start(
    *,
    dependency_graph_path: Annotated[Path, Argument()] = Path("dependencygrapher.json"),
    state_path: StatePathOption,
    required_mods: Annotated[
        list[str],
        Option("-r", "--require-mod", default_factory=list),
    ],
    verbosity: VerbosityOption = 0,
):
    setup_logging(verbosity)
    graph = DependencyGraph.load(dependency_graph_path)
    state = setup_binary_reduction(graph, set(required_mods))
    get_and_apply_modlist(state)
    state.dump(state_path)


@app.command()
def good(
    state_path: StatePathOption,
    verbosity: VerbosityOption = 0,
):
    setup_logging(verbosity)
    step(state_path, is_bad=False)


@app.command()
def bad(
    state_path: StatePathOption,
    verbosity: VerbosityOption = 0,
):
    setup_logging(verbosity)
    step(state_path, is_bad=True)


@app.command()
def reset(
    state_path: StatePathOption,
    verbosity: VerbosityOption = 0,
):
    setup_logging(verbosity)
    state = State.load(state_path)
    apply_modlist(state, enabled=set(state.jars.keys()), disabled=set())
    state_path.unlink()
    logger.info("Reenabled all mods.")


@app.command()
def status(
    state_path: StatePathOption,
    verbosity: VerbosityOption = 0,
):
    setup_logging(verbosity)
    state = State.load(state_path)
    enabled, disabled = get_modlist(state)
    n = len(enabled) + len(disabled)
    logger.info("\n  ".join([f"Enabled: {len(enabled)}/{n}"] + sorted(enabled)))
    logger.info("\n  ".join([f"Disabled: {len(disabled)}/{n}"] + sorted(disabled)))


def step(state_path: Path, is_bad: bool):
    state = State.load(state_path)
    match step_binary_reduction(state, is_bad):
        case StepResult.CONTINUE:
            get_and_apply_modlist(state)
        case StepResult.DONE:
            enabled, _ = get_modlist(state)
            logger.info(
                "\n  ".join(["Successfully found minimal modlist:"] + sorted(enabled))
            )
        case StepResult.FAILED:
            logger.error("Failed to reproduce issue with full modlist. (???)")
    state.dump(state_path)


if __name__ == "__main__":
    app()
