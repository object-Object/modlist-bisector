from pathlib import Path
from typing import Iterator


def multi_glob(path: Path, *patterns: str) -> Iterator[Path]:
    for pattern in patterns:
        yield from path.glob(pattern)


def multi_rglob(path: Path, *patterns: str) -> Iterator[Path]:
    for pattern in patterns:
        yield from path.rglob(pattern)
