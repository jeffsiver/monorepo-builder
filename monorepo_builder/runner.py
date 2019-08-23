from typing import Optional

import click

from monorepo_builder.build_executor import BuildExecutor, ProjectBuildRequests
from monorepo_builder.configuration import ConfigurationManager
from monorepo_builder.console import write_to_console
from monorepo_builder.project_list import ProjectListManager, Projects
from monorepo_builder.projects import Project


@click.command()
def run_build():
    Runner.run()


class Runner:
    @staticmethod
    def run():
        write_to_console("Starting the build", color="blue")
        write_to_console("Loading default configuration", color="blue")
        ConfigurationManager.load("config.json")
        runner = Runner()
        projects = runner.gather_projects()
        build_requests = runner.do_builds(projects)
        runner.finish_builds(projects, build_requests)

    def gather_projects(self) -> Projects:
        write_to_console("Creating Project List", color="blue")
        projects = Projects.projects_factory()
        write_to_console("Identifying projects requiring a build")
        BuildRunner().identify_projects_needing_build(projects)
        return projects

    def do_builds(self, projects: Projects) -> ProjectBuildRequests:
        build_requests = BuildRunner().build_library_projects(projects)
        if build_requests.success:
            build_requests.extend(BuildRunner().build_standard_projects(projects))
        return build_requests

    def finish_builds(self, projects: Projects, build_requests: ProjectBuildRequests):
        if build_requests.success:
            write_to_console("All builds completed successfully, build file updated")
            ProjectListManager().save_project_list(projects)
        else:
            write_to_console("One of more builds failed", color="red")
        write_to_console("Completed", color="blue")


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


if __name__ == "__main__":
    run_build()
