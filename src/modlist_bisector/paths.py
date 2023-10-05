from pathlib import Path


def rename_path(source: Path, target: Path) -> bool:
    """Returns `False` if the path was already renamed. Raises if both paths exist."""
    match source.exists(), target.exists():
        case True, False:
            source.rename(target)
            return True
        case False, True:
            return False
        case True, True:
            raise RuntimeError(f"Both paths already exist: {source} and {target}")
        case _:
            raise FileNotFoundError(source)
