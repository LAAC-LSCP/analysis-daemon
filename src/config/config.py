import tomllib
from pathlib import Path
from typing import List, Optional

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    ValidationError,
    model_validator,
)

from src.core.types import Operation


class DatabaseConfig(BaseModel):
    url: str = Field(min_length=1, description="Database URL")


class ScriptConfig(BaseModel):
    name: str = Field(min_length=1, description="Name of script")
    python_script_path: Path = Field(description="Path to the Python script")
    bash_script_path: Path = Field(description="Path to the bash script for the model")
    env_name: str = Field(description="Name of or path to the associated env file")
    model_name: str = Field(description="Short name of the model")

    @model_validator(mode="after")
    def check_model_name_valid(self) -> "ScriptConfig":
        if self.model_name not in [m.value for m in Operation]:
            raise ValidationError(f"Model not in {[m.value for m in Operation]}", [])

        return self


class JobsConfig(BaseModel):
    use_slurm: bool = Field(
        True, description="Whether to use slurm. Turn off for debugging"
    )
    handler: str = Field(min_length=1, description="Name of handler")
    partition: Optional[str] = Field(None, description="Job partition")


class HTTPConfig(BaseModel):
    base_url: HttpUrl = Field(description="Base URL of the site")
    client_id: str = Field(description="Client ID")
    client_secret: str = Field(description="Secret access key (do NOT share)")


class ConfigModel(BaseModel):
    database: DatabaseConfig
    jobs: JobsConfig
    http: HTTPConfig
    scripts: List[ScriptConfig]
    log_directory: Path = Field(
        default=Path("/tmp/logs"), description="Directory for log files"
    )
    conda_executable: Path = Field(description="Path to the Conda startup executable")
    echolalia_folder: Path = Field(description="Folder for all echolalia files")
    script_wrapper: Path = Field(
        description="Bash file that wraps around scripts, passes in variables \
            and activates environments"
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
