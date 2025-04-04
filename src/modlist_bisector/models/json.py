import json
from pathlib import Path
from typing import Self

from pydantic import BaseModel


class JSONBaseModel(BaseModel):
    @classmethod
    def load(cls, path: str | Path) -> Self:
        path = Path(path)
        with path.open("rb") as f:
            data = json.load(f)
        return cls.model_validate(data)

    def dump(self, path: str | Path):
        data = self.model_dump_json(round_trip=True)
        Path(path).write_text(data, encoding="utf-8")
