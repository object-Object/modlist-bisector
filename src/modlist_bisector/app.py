import logging
from pathlib import Path
from typing import Annotated

from typer import Option, Typer

from modlist_bisector.binary_reduction import (
    StepResult,
    apply_modlist,
    get_and_apply_modlist,
    get_modlist,
    setup_binary_reduction,
    step_binary_reduction,
)
from modlist_bisector.models.config import Config
from modlist_bisector.models.state import State
from modlist_bisector.utils.logging import setup_logging

logger = logging.getLogger(__name__)


DEFAULT_CONFIG_FILE = "config.toml"
DEFAULT_STATE_FILE = "state.json"


def _parse_config_path(value: str) -> Path:
    path = Path(value)
    if path.is_dir():
        path /= DEFAULT_CONFIG_FILE
    return path


ConfigPathOption = Annotated[
    Path,
    Option(
        "--config",
        "-c",
        show_default=DEFAULT_CONFIG_FILE,
        default_factory=lambda: DEFAULT_CONFIG_FILE,
        parser=_parse_config_path,
    ),
]


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
    config_path: ConfigPathOption,
    state_path: StatePathOption,
    verbosity: VerbosityOption = 0,
):
    setup_logging(verbosity)
    config = Config.load(config_path)
    state = setup_binary_reduction(config)
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
    apply_modlist(state, enabled=set(state.mod_jars.keys()), disabled=set())
    state_path.unlink()


def step(state_path: Path, is_bad: bool):
    state = State.load(state_path)
    match step_binary_reduction(state, is_bad):
        case StepResult.CONTINUE:
            get_and_apply_modlist(state)
        case StepResult.DONE:
            logger.info("Successfully found minimal modlist.")
        case StepResult.FAILED:
            logger.error("Failed to reproduce issue with full modlist. (???)")
    enabled, _ = get_modlist(state)
    print(",".join(sorted(enabled)))
    state.dump(state_path)


if __name__ == "__main__":
    app()
