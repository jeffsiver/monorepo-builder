import os
import shutil
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import List, Optional

import boto3

from monorepo_builder.configuration import (
    ConfigurationManager,
    InstallerLocationType,
    Configuration,
)
from monorepo_builder.console import write_to_console
from monorepo_builder.project_list import Projects
from monorepo_builder.projects import Project, ProjectType


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
            if project_build_request.project.project_type == ProjectType.Library:
                InstallerManager().copy_installer_to_shared_folder(
                    project_build_request
                )
        return project_build_requests

    def run_build(self, project_build_request: ProjectBuildRequest):
        write_to_console(
            f"{project_build_request.project.name} Building", color="blue", bold=True
        )
        if not project_build_request.project.needs_build:
            project_build_request.build_status = BuildRequestStatus.NotNeeded
            write_to_console("Build not needed")
            return

        InstallerManager().copy_installers_to_project(project_build_request.project)
        result = subprocess.run(
            ["./build.sh"], cwd=project_build_request.project.project_path
        )
        project_build_request.build_status = BuildRequestStatus.Complete
        project_build_request.run_successful = result.returncode == 0


class InstallerManager:
    def __init__(self):
        self._s3_bucket = None

    def copy_installer_to_shared_folder(
        self, project_build_request: ProjectBuildRequest
    ):
        configuration = ConfigurationManager.get()
        dist_folder = f"{project_build_request.project.project_path}/{configuration.project_distributable_folder}"
        for installer in Path(dist_folder).iterdir():
            if configuration.installer_location_type == InstallerLocationType.folder:
                shutil.copy(str(installer), configuration.installer_folder)
            if configuration.installer_location_type == InstallerLocationType.s3:
                self._get_s3_bucket(configuration).upload_file(
                    str(installer), installer.name
                )

    def _get_s3_bucket(self, configuration: Configuration):
        if not self._s3_bucket:
            self._s3_bucket = boto3.client("s3").Bucket(
                configuration.installer_s3_bucket
            )
        return self._s3_bucket

    def copy_installers_to_project(self, project: Project):
        configuration = ConfigurationManager.get()
        project_installer_folder = os.path.join(
            project.project_path, configuration.installer_folder
        )
        if configuration.installer_location_type == InstallerLocationType.folder:
            shutil.copytree(configuration.installer_folder, project_installer_folder)
        if configuration.installer_location_type == InstallerLocationType.s3:
            bucket = self._get_s3_bucket(configuration)
            for file in bucket.objects:
                bucket.download_file(
                    file.key, os.path.join(project_installer_folder, file.key)
                )
