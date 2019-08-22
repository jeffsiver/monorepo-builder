from dataclasses import dataclass, field
from pathlib import Path
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


def get_current_folder():
    return Path.cwd()


@dataclass
class Configuration:
    # monorepo_root_folder: str = field(default_factory=get_current_folder)
    monorepo_root_folder: str = "/Users/jsiver/projects/monorepo-builder/example"
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
    project_list_filename: str = ".projectlist"


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
