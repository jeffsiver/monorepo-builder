import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

import click

from monorepo_builder.console import write_to_console
from monorepo_builder.project_list import Projects
from monorepo_builder.projects import Project


class BuildRequestStatus(Enum):
    NotStarted = 1
    Running = 2
    Complete = 3
    NotNeeded = 4


@dataclass
class ProjectBuildRequest:
    project: Project
    build_status: BuildRequestStatus = field(
        default=BuildRequestStatus.NotStarted, init=False
    )
    run_successful: Optional[bool] = field(default=None, init=False)
    console_output: List[str] = field(default_factory=list, init=False)


class ProjectBuildRequests(list, List[ProjectBuildRequest]):
    @staticmethod
    def library_projects(projects: Projects) -> "ProjectBuildRequests":
        build_requests = ProjectBuildRequests()
        library_projects = projects.library_projects
        build_requests.extend(
            [
                ProjectBuildRequest(project=project)
                for project in library_projects
                if project.needs_build
            ]
        )
        return build_requests

    @staticmethod
    def standard_projects(projects: Projects) -> "ProjectBuildRequests":
        build_requests = ProjectBuildRequests()
        build_requests.extend(
            [
                ProjectBuildRequest(project=project)
                for project in projects.standard_projects
                if project.needs_build
            ]
        )
        return build_requests

    @property
    def success(self) -> bool:
        return len(self) == 0 or all([request.run_successful for request in self])

    @property
    def failed(self) -> "ProjectBuildRequests":
        return ProjectBuildRequests(
            [request for request in self if request.run_successful is False]
        )


class BuildExecutor:
    def execute_builds(
        self, project_build_requests: ProjectBuildRequests
    ) -> ProjectBuildRequests:
        for project_build_request in project_build_requests:
            self.run_build(project_build_request)
        return project_build_requests

    def run_build(self, project_build_request: ProjectBuildRequest):
        write_to_console(
            f"{project_build_request.project.name} Building", color="blue", bold=True
        )
        if not project_build_request.project.needs_build:
            project_build_request.build_status = BuildRequestStatus.NotNeeded
            write_to_console("Build not needed")
            return

        result = subprocess.run(
            ["./build.sh"],
            cwd=project_build_request.project.project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        project_build_request.build_status = BuildRequestStatus.Complete
        project_build_request.run_successful = result.returncode == 0
        project_build_request.console_output = result.stdout
        write_to_console(project_build_request.console_output)
