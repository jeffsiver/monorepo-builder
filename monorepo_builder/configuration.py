import dataclasses
import json
from dataclasses import dataclass, field, Field
from pathlib import Path
from typing import List, Dict, Optional

from monorepo_builder.console import write_to_console


def create_default_standard_folder_list():
    return ["platform", "web"]


def create_default_filenames_to_skip():
    return [
        "bin",
        "lib",
        "include",
        "__pycache__",
        "reports",
        "node_modules",
        "dist",
        "build",
        "wheels",
        "installers",
        ".DS_Store",
        ".coverage",
        "coverage",
        "package-lock.json",
    ]


def create_default_extensions_to_skip():
    return ["egg-info"]


def get_current_folder():
    return str(Path.cwd())


@dataclass
class Configuration:
    monorepo_root_folder: str = field(
        default_factory=get_current_folder, metadata={"config": "rootFolder"}
    )
    library_folder_name: str = field(
        default="libraries", metadata={"config": "libraryFolder"}
    )
    standard_folder_list: List[str] = field(
        default_factory=create_default_standard_folder_list,
        metadata={"config": "standardFolders"},
    )
    filenames_to_skip: List[str] = field(
        default_factory=create_default_filenames_to_skip,
        metadata={"config": "fileNamesToSkip"},
    )
    extensions_to_skip: List[str] = field(
        default_factory=create_default_extensions_to_skip,
        metadata={"config": "extensionsToSkip"},
    )
    skip_hidden_files: bool = field(
        default=True, metadata={"config": "skipHiddenFiles"}
    )
    skip_hidden_folders: bool = field(
        default=True, metadata={"config": "skipHiddenFolders"}
    )
    project_list_filename: str = field(
        default=".projectlist", metadata={"config": "projectListFilename"}
    )

    @classmethod
    def build_from_settings(cls, configuration_settings: Dict):
        if "config" not in configuration_settings:
            raise InvalidConfigurationException()

        changes = {}
        for config_setting_key, config_setting_value in configuration_settings[
            "config"
        ].items():
            matching_field = cls._find_matching_field(config_setting_key)
            changes[matching_field.name] = config_setting_value
        return dataclasses.replace(Configuration(), **changes)

    @classmethod
    def _find_matching_field(cls, setting_name: str) -> Optional[Field]:
        for class_field in dataclasses.fields(Configuration):
            metadata = class_field.metadata
            if metadata["config"] == setting_name:
                return class_field
        raise InvalidConfigurationSettingException(setting_name)


class InvalidConfigurationException(Exception):
    def __init__(self):
        super().__init__("The configuration settings provided as invalid")


class InvalidConfigurationSettingException(Exception):
    def __init__(self, setting_name: str):
        super().__init__(f"The configuration setting {setting_name} is unrecognized")


class ConfigurationManager:
    configuration = None

    @classmethod
    def get(cls) -> Configuration:
        if not cls.configuration:
            cls.configuration = Configuration()
        return cls.configuration

    @classmethod
    def load(cls, configuration_filename: str) -> Configuration:
        if not Path(configuration_filename).exists():
            write_to_console(
                "Configuration file not found; default configuration used", color="red"
            )
            cls.configuration = Configuration()
            return cls.configuration

        read_configuration = json.load(configuration_filename)
        cls.configuration = Configuration.build_from_settings(read_configuration)
        return cls.configuration


if __name__ == "__main__":
    ConfigurationManager.load("t")
