import tomllib
from pathlib import Path
from typing import List, Optional

from pydantic import (
    BaseModel,
    DirectoryPath,
    Field,
    HttpUrl,
    ValidationError,
    model_validator,
)

from src.core.types import OperationName


class DatabaseConfig(BaseModel):
    url: str = Field(min_length=1)


class ScriptConfig(BaseModel):
    name: str = Field(min_length=1)
    path: Path
    model_name: str

    @model_validator(mode="after")
    def check_model_name_valid(self) -> "ScriptConfig":
        if self.model_name not in [m.value for m in OperationName]:
            raise ValidationError(
                f"Model not in {[m.value for m in OperationName]}", []
            )

        return self


class FileSystemConfig(BaseModel):
    dataset_name: str = Field(min_length=1)
    path: DirectoryPath


class JobsConfig(BaseModel):
    handler: str = Field(min_length=1)
    partition: Optional[str] = None


class HTTPConfig(BaseModel):
    base_url: HttpUrl
    client_id: str
    client_secret: str


class ConfigModel(BaseModel):
    database: DatabaseConfig
    jobs: JobsConfig
    http: HTTPConfig
    filesystems: List[FileSystemConfig]
    scripts: List[ScriptConfig]
    log_directory: Path = Field(
        default=Path("/tmp/logs"), description="Directory for log files"
    )


def load_config(file_path: Path) -> ConfigModel:
    """
    loads the config for the service from a toml file
    Args:
        file_path: path of the toml config file
    Returns: a config object
    """
    with open(file_path, "rb") as f:
        raw = tomllib.load(f)

    try:
        return ConfigModel.model_validate(raw)
    except ValidationError as e:
        print("Invalid configuration:")
        print(e)
        raise
