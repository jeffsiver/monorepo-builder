import pickle
from pathlib import Path
from typing import List

from monorepo_builder.configuration import ConfigurationManager
from monorepo_builder.projects import Project, ProjectFileListBuilder, ProjectType


class Projects(list, List[Project]):
    @property
    def library_projects(self) -> List[Project]:
        return [
            project for project in self if project.project_type == ProjectType.Library
        ]

    @property
    def standard_projects(self) -> List[Project]:
        return [
            project for project in self if project.project_type == ProjectType.Standard
        ]

    @staticmethod
    def projects_factory():
        projects = Projects()
        projects._get_library_projects()
        projects._get_standard_projects()
        return projects

    def _get_library_projects(self,):
        library_root_folder = f"{ConfigurationManager().get().monorepo_root_folder}/{ConfigurationManager().get().library_folder_name}"
        self.extend(ProjectListFactory().get_projects_in_folder(library_root_folder))

    def _get_standard_projects(self,):
        for standard_folder_name in ConfigurationManager().get().standard_folder_list:
            standard_folder = f"{ConfigurationManager().get().monorepo_root_folder}/{standard_folder_name}"
            self.extend(ProjectListFactory().get_projects_in_folder(standard_folder))


class ProjectListManager:
    def load_list_from_last_successful_run(self) -> Projects:
        file = Path(ConfigurationManager.get().project_list_filename)
        if not file.exists():
            return Projects()
        with open(ConfigurationManager.get().project_list_filename, "rb") as file:
            return pickle.loads(file.read())

    def save_project_list(self, projects: Projects):
        with open(ConfigurationManager.get().project_list_filename, "wb") as file:
            file.write(pickle.dumps(projects))


class ProjectListFactory:
    def get_projects_in_folder(self, folder) -> List[Project]:
        if not Path(folder).exists():
            return []

        project_list: List[Project] = []
        for project in Path(folder).iterdir():
            if project.is_dir():
                project_path = str(project)
                project_list.append(
                    Project(
                        project_path=project_path,
                        file_list=ProjectFileListBuilder().build(project),
                    )
                )
        return project_list
