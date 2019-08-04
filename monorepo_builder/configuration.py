from dataclasses import dataclass, field
from typing import List


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


@dataclass
class Configuration:
    monorepo_root_folder: str = None
    library_folder_name: str = "libraries"
    standard_folder_list: List[str] = field(
        default_factory=create_default_standard_folder_list
    )
    filenames_to_skip: List[str] = field(
        default_factory=create_default_filenames_to_skip
    )
    extensions_to_skip: List[str] = field(
        default_factory=create_default_extensions_to_skip
    )
    skip_hidden_files: bool = True
    skip_hidden_folders: bool = True


class ConfigurationManager:
    configuration = None

    @classmethod
    def get(cls) -> Configuration:
        if not cls.configuration:
            cls.configuration = Configuration()
        return cls.configuration

    @classmethod
    def init(cls, configuration: Configuration):
        cls.configuration = configuration
