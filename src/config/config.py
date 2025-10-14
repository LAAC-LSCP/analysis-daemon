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

from src.core.types import Model


class DatabaseConfig(BaseModel):
    url: str = Field(min_length=1)


class ScriptConfig(BaseModel):
    script_name: str = Field(min_length=1)
    script_path: Path
    model_name: str

    @model_validator(mode="after")
    def check_model_name_valid(self) -> "ScriptConfig":
        if self.model_name not in [m.value for m in Model]:
            raise ValidationError(f"Model name not in {[m.value for m in Model]}", [])

        return self


class FileSystemConfig(BaseModel):
    dataset_name: str = Field(min_length=1)
    path: DirectoryPath
    scripts: List[ScriptConfig]

    @model_validator(mode="after")
    def check_scripts_exist(self) -> "FileSystemConfig":
        for script in self.scripts:
            script_abs_path = self.path / script.script_path

            if not script_abs_path.is_file():
                raise ValidationError(
                    f"File at {str(script_abs_path)} does not exist", []
                )

        return self


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
