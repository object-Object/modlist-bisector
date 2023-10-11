import json
from pathlib import Path

LOG_PATTERN = "log_{}.json"


def load_log() -> list[list[str]]:
    paths = glob_logs()
    if not paths:
        return []

    data = max(paths).read_bytes()
    return json.loads(data) if data else []


def next_log(paths: list[Path]):
    next_index = len(paths)
    return Path(LOG_PATTERN.format(next_index))


def save_log(log: list[list[str]]):
    paths = glob_logs()
    path = max(paths) if paths else next_log([])
    with path.open("w") as f:
        json.dump(log, f, indent="  ")


def glob_logs():
    glob = LOG_PATTERN.format("*")
    return list(Path().glob(glob))
