import pickle
from pathlib import Path
from typing import List

from monorepo_builder.configuration import ConfigurationManager
from monorepo_builder.projects import Project, ProjectFileListBuilder


class ProjectList:
    def build_current_project_list(self) -> List[Project]:
        project_list: List[Project] = []
        self._get_library_projects(project_list)
        self._get_standard_projects(project_list)
        return project_list

    def _get_library_projects(self, project_list: List[Project]):
        library_root_folder = f"{ConfigurationManager().get().monorepo_root_folder}/{ConfigurationManager().get().library_folder_name}"
        project_list.extend(
            ProjectListFactory().get_projects_in_folder(library_root_folder)
        )

    def _get_standard_projects(self, project_list: List[Project]):
        for standard_folder_name in ConfigurationManager().get().standard_folder_list:
            standard_folder = f"{ConfigurationManager().get().monorepo_root_folder}/{standard_folder_name}"
            project_list.extend(
                ProjectListFactory().get_projects_in_folder(standard_folder)
            )


class ProjectListManager:
    def load_list_from_last_successful_run(self) -> List[Project]:
        file = Path(ConfigurationManager.get().project_list_filename)
        if not file.exists():
            return []
        with open(ConfigurationManager.get().project_list_filename, "rb") as file:
            return pickle.loads(file.read())

    def save_project_list(self, project_list: List[Project]):
        with open(ConfigurationManager.get().project_list_filename, "wb") as file:
            file.write(pickle.dumps(project_list))


class ProjectListFactory:
    def get_projects_in_folder(self, folder) -> List[Project]:
        project_list: List[Project] = []
        for project in Path(folder).iterdir():
            if project.is_dir():
                project_path = str(project)
                project_list.append(
                    Project(
                        project_path=project_path,
                        file_list=ProjectFileListBuilder().build(project_path),
                    )
                )
        return project_list
