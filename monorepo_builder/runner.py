from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import click

from monorepo_builder.build_executor import BuildExecutor, ProjectBuildRequests
from monorepo_builder.configuration import ConfigurationManager
from monorepo_builder.console import write_to_console
from monorepo_builder.project_list import ProjectListManager, Projects
from monorepo_builder.projects import Project
from monorepo_builder.version import ProjectVersionManager


@click.command()
@click.option(
    "--version",
    envvar="MONOREPO-BUILD-VERSION",
    default="1.0.0",
    show_envvar=True,
    required=True,
    prompt=True,
)
def run_build(version):
    Runner.run(version)


class Runner:
    @staticmethod
    def run(version: str):
        write_to_console("Starting the build", color="blue")
        runner = Runner()
        runner.setup()
        projects = runner.gather_projects()
        build_requests = runner.do_builds(projects)
        if build_requests.success:
            runner.finish_builds_on_success(projects)
        else:
            runner.finish_builds_on_failure(build_requests)
        write_to_console("Build complete", color="blue")

    def setup(self):
        write_to_console("Loading default configuration", color="blue")
        ConfigurationManager.load("monorepo-builder-config.json")

        write_to_console("Checking for installer folder")
        configuration = ConfigurationManager.get()
        Path(configuration.installers_folder).mkdir(exist_ok=True)

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

    def finish_builds_on_success(self, projects: Projects):
        write_to_console("All builds completed successfully, build file updated")
        ProjectListManager().save_project_list(projects)
        version_list = ProjectVersionManager().build_version_list(projects)
        ProjectVersionManager().save_version_list(version_list)

    def finish_builds_on_failure(self, build_requests: ProjectBuildRequests):
        write_to_console("Builds failed", color="red")
        for build_request in build_requests.failed:
            write_to_console(f"{build_request.project.name} failed")


class BuildRunner:
    def identify_projects_needing_build(self, projects: Projects):
        previous_projects = ProjectListManager().load_list_from_last_successful_run()
        for project in projects:
            previous_project = self._get_previous_project_by_name(
                previous_projects, project.name
            )
            project.mark_if_build_needed(previous_project)

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
