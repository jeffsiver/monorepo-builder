import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

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


@dataclass
class Project:
    project_path: str
    file_list: List[File] = field(default_factory=list)
    needs_build: bool = field(default=False)

    @property
    def path(self) -> Path:
        return Path(self.project_path)

    @property
    def name(self) -> str:
        path = self.path
        return path.name.replace("_", "-")

    @property
    def project_type(self) -> ProjectType:
        if ConfigurationManager().get().library_folder_name in self.path.parts:
            return ProjectType.Library
        return ProjectType.Standard

    def set_needs_build(self):
        self.needs_build = True

    def set_needs_build_due_to_file_changes(
        self, project_from_last_run: "Optional[Project]"
    ):
        self.needs_build = self._did_files_change_from_last_run(project_from_last_run)

    def set_needs_build_due_to_updated_library_reference(
        self, updated_library_names: List[str]
    ):
        if self.project_references_updated_library(updated_library_names):
            self.set_needs_build()

    def _did_files_change_from_last_run(
        self, project_from_last_run: "Optional[Project]"
    ) -> bool:
        if not project_from_last_run:
            return True
        if len(self.file_list) != len(project_from_last_run.file_list):
            return True
        sorted_current_file_list = sorted(self.file_list, key=lambda x: x.file)
        sorted_last_file_list = sorted(
            project_from_last_run.file_list, key=lambda x: x.file
        )
        for current, previous in zip(sorted_current_file_list, sorted_last_file_list):
            if current.file != previous.file:
                return True
            if current.last_changed_time != previous.last_changed_time:
                return True
        return False

    def project_references_updated_library(
        self, library_project_names: List[str]
    ) -> bool:
        ## Should be updated to parse the requirements to match against entire project names.
        ## For example, a library project name of "thing" will match to a requirements of "something".
        requirements = self.read_requirements_file()
        for library_project_name in library_project_names:
            if library_project_name in requirements:
                return True
        return False

    def read_requirements_file(self) -> str:
        requirement_filenames = [
            os.path.join(self.project_path, "requirements.txt"),
            os.path.join(self.project_path, "package.json"),
        ]
        for requirement_filename in requirement_filenames:
            requirement_file_path = Path(requirement_filename)
            if requirement_file_path.exists():
                return requirement_file_path.read_text()
        raise RequirementsFileNotFoundException(self)


class RequirementsFileNotFoundException(Exception):
    def __init__(self, project: Project):
        super().__init__(f"Requirements file not found for {project.name}")
