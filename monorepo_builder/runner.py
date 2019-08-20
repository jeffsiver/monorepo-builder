from typing import List, Optional

from monorepo_builder.build_executor import BuildExecutor, ProjectBuildRequests
from monorepo_builder.project_list import ProjectListManager, Projects
from monorepo_builder.projects import Project


def run_build():
    build_runner = BuildRunner()
    projects = Projects.projects_factory()
    build_runner.identify_projects_needing_build(projects)
    library_results = build_runner.build_library_projects(projects)
    standard_results = build_runner.build_standard_projects(projects)


class BuildRunner:
    def identify_projects_needing_build(self, projects: Projects):
        previous_projects = ProjectListManager().load_list_from_last_successful_run()
        for project in projects:
            previous_project = self._get_previous_project_by_name(
                previous_projects, project.name
            )
            project.identify_if_build_needed(previous_project)

    def _get_previous_project_by_name(
        self, previous_projects: Optional[Projects], name: str
    ) -> Optional[Project]:
        if not previous_projects:
            return None
        for project in previous_projects:
            if project.name == name:
                return project
        return None

    def build_library_projects(self, projects: Projects) -> ProjectBuildRequests:
        return BuildExecutor().execute_builds(
            ProjectBuildRequests.library_projects(projects)
        )

    def build_standard_projects(self, projects: Projects) -> ProjectBuildRequests:
        return BuildExecutor().execute_builds(
            ProjectBuildRequests.standard_projects(projects)
        )
