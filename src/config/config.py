import tomllib
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, HttpUrl, ValidationError


class DatabaseConfig(BaseModel):
    url: str = Field(min_length=1)


class JobsConfig(BaseModel):
    handler: str = Field(min_length=1)
    partition: Optional[str] = None


class HTTPConfig(BaseModel):
    base_url: HttpUrl


class ConfigModel(BaseModel):
    database: DatabaseConfig
    jobs: JobsConfig
    http: HTTPConfig


def load_config(file_path: Path) -> ConfigModel:
    """
    loads the config for the service from a toml file
    Args:
        file_path: path of the toml config file
    Returns:
    """
    with open(file_path, "rb") as f:
        raw = tomllib.load(f)

    try:
        return ConfigModel.model_validate(raw)
    except ValidationError as e:
        print("Invalid configuration:")
        print(e)
        raise
