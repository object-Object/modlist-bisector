from pydantic import BaseModel, ConfigDict

DEFAULT_CONFIG = ConfigDict(
    extra="forbid",
)


class DefaultModel(BaseModel):
    model_config = DEFAULT_CONFIG
