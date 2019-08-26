import pickle
from pathlib import Path
from typing import Dict, Optional

from monorepo_builder.configuration import ConfigurationManager
from monorepo_builder.project_list import Projects
from monorepo_builder.projects import Project


class ProjectVersions(dict, Dict[str, str]):
    def get_version(self, project: Project) -> Optional[str]:
        if project.project_path in self:
            return self[project.project_path]
        return None

    def add_project(self, project: Project, version: str):
        self[project.project_path] = version


class ProjectVersionManager:
    def build_version_list(
        self, projects: Projects, current_version: str
    ) -> ProjectVersions:
        project_versions = ProjectVersions()
        previous_project_versions = self.load_previous_version_list()
        for project in projects:
            project_versions[project.project_path] = self._calculate_version(
                project, current_version, previous_project_versions
            )
        return project_versions

    def _calculate_version(
        self,
        project: Project,
        current_version: str,
        previous_project_versions: ProjectVersions,
    ) -> str:
        if project.needs_build:
            return current_version
        if project.project_path in previous_project_versions:
            return previous_project_versions[project.project_path]
        return current_version

    def get_version(self, project: Project):
        pass

    def load_previous_version_list(self) -> ProjectVersions:
        version_filename = ConfigurationManager.get().version_list_filename
        file = Path(version_filename)
        if not file.exists():
            return ProjectVersions()
        with open(version_filename, "rb") as file:
            return pickle.load(file)

    def save_version_list(self, project_versions: ProjectVersions):
        version_filename = ConfigurationManager.get().version_list_filename
        with open(version_filename, "wb") as file:
            pickle.dump(project_versions, file)
