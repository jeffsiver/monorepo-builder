from typing import List, Optional

from monorepo_builder.project_list import ProjectList, ProjectListManager
from monorepo_builder.projects import Project


def run_build():
    build_runner = BuildRunner()
    build_runner.load()
    build_runner.identify_projects_needing_build()


class BuildRunner:
    def __init__(self):
        self._project_list: List[Project] = []
        self._previous_project_list: Optional[List[Project]] = None

    def load(self):
        self._project_list = ProjectList().build_current_project_list()
        self._previous_project_list = (
            ProjectListManager().load_list_from_last_successful_run()
        )

    def identify_projects_needing_build(self,):
        for project in self._project_list:
            previous_project = self._get_project_from_previous_list_by_name(
                project.name
            )
            project.identify_if_build_needed(previous_project)

    def _get_project_from_previous_list_by_name(self, name: str) -> Optional[Project]:
        if not self._previous_project_list:
            return None
        for project in self._previous_project_list:
            if project.name == name:
                return project
        return None
