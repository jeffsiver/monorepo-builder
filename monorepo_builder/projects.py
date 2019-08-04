from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List

from monorepo_builder.configuration import ConfigurationManager, Configuration


class ProjectType(Enum):
    Library = (1,)
    Standard = (2,)


@dataclass(frozen=True)
class File:
    file: str
    last_changed_time: int

    @staticmethod
    def file_factory(file: Path):
        return File(str(file), file.stat().st_mtime)


class ProjectFileListBuilder:
    def build(self, path: Path) -> List[File]:
        files: List[File] = []
        configuration = ConfigurationManager.get()
        for file in path.iterdir():
            if not self.process_file(file, configuration):
                continue
            if file.is_dir():
                files.extend(self.build(file))
            else:
                files.append(File.file_factory(file))
        return files

    def process_file(self, file_path: Path, configuration: Configuration) -> bool:
        if file_path.name in configuration.filenames_to_skip:
            return False
        if configuration.skip_hidden_folders:
            if file_path.is_dir() and file_path.name.startswith("."):
                return False
        if configuration.skip_hidden_files:
            if file_path.is_file() and file_path.name.startswith("."):
                return False
        if file_path.suffix in configuration.extensions_to_skip:
            return False
        return True


@dataclass(frozen=True)
class Project:
    project_path: str
    file_list: List[File] = field(default_factory=list)

    @property
    def path(self) -> Path:
        return Path(self.project_path)

    @property
    def project_type(self) -> ProjectType:
        if ConfigurationManager().get().library_folder_name in self.path.parts:
            return ProjectType.Library
        return ProjectType.Standard


class ProjectList:
    def build_project_list(self) -> List[Project]:
        project_list: List[Project] = []
        self._get_library_projects(project_list)
        self._get_platform_projects(project_list)
        return project_list

    def _get_library_projects(self, project_list: List[Project]):
        library_root_folder = f"{ConfigurationManager().get().monorepo_root_folder}/{ConfigurationManager().get().library_folder_name}"
        project_list.extend(ProjectListBuilder().get_projects(library_root_folder))

    def _get_platform_projects(self, project_list: List[Project]):
        for standard_folder_name in ConfigurationManager().get().standard_folder_list:
            standard_folder = f"{ConfigurationManager().get().monorepo_root_folder}/{standard_folder_name}"
            project_list.extend(ProjectListBuilder().get_projects(standard_folder))


class ProjectListBuilder:
    def get_projects(self, folder) -> List[Project]:
        project_list: List[Project] = []
        for project in Path(folder).iterdir():
            if project.is_dir():
                project_list.append(Project(project_path=str(project)))
        return project_list
