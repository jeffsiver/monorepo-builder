import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

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
    console_output: List[str] = field(default_factory=List, init=False)


class ProjectBuildRequests(list, List[ProjectBuildRequest]):
    @staticmethod
    def library_projects(projects: Projects) -> "ProjectBuildRequests":
        build_requests = ProjectBuildRequests()
        build_requests.extend(
            [
                ProjectBuildRequest(project=project)
                for project in projects.library_projects
            ]
        )
        return build_requests

    @staticmethod
    def standard_projects(projects: Projects):
        build_requests = ProjectBuildRequests()
        build_requests.extend(
            [
                ProjectBuildRequest(project=project)
                for project in projects.standard_projects
            ]
        )
        return build_requests


class BuildExecutor:
    def execute_builds(
        self, project_build_requests: ProjectBuildRequests
    ) -> ProjectBuildRequests:
        for project_build_request in project_build_requests:
            self.run_build(project_build_request)
        return project_build_requests

    def run_build(self, project_build_request: ProjectBuildRequest):
        if not project_build_request.project.needs_build:
            project_build_request.build_status = BuildRequestStatus.NotNeeded
            return

        build_command = f"{project_build_request.project.project_path}/build.sh"
        result = subprocess.run(
            build_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        project_build_request.build_status = BuildRequestStatus.Complete
        project_build_request.run_successful = result.returncode == 0
        project_build_request.console_output = result.stdout
