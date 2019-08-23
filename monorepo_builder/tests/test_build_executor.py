from subprocess import CompletedProcess
from unittest.mock import MagicMock, call

from monorepo_builder.build_executor import (
    ProjectBuildRequests,
    ProjectBuildRequest,
    BuildRequestStatus,
    BuildExecutor,
)
from monorepo_builder.project_list import Projects
from monorepo_builder.projects import Project, ProjectType


class TestProjectBuildRequests:
    def test_library_projects_filters_to_library_projects_needing_build(self, mocker):
        lib1 = MagicMock(
            spec=Project, project_type=ProjectType.Library, needs_build=True
        )
        lib2 = MagicMock(
            spec=Project, project_type=ProjectType.Library, needs_build=False
        )
        std = MagicMock(spec=Project, project_type=ProjectType.Standard)
        projects = Projects()
        projects.extend([lib1, lib2, std])
        req = MagicMock(spec=ProjectBuildRequest)
        project_build_request_mock = mocker.patch(
            "monorepo_builder.build_executor.ProjectBuildRequest", return_value=req
        )

        result = ProjectBuildRequests.library_projects(projects)

        assert len(result) == 1
        assert req in result
        project_build_request_mock.assert_called_once_with(project=lib1)

    def test_standard_projects_filters_as_expected(self, mocker):
        lib = MagicMock(spec=Project, project_type=ProjectType.Library)
        std1 = MagicMock(
            spec=Project, project_type=ProjectType.Standard, needs_build=True
        )
        std2 = MagicMock(
            spec=Project, project_type=ProjectType.Standard, needs_build=False
        )
        projects = Projects()
        projects.extend([lib, std1, std2])
        req = MagicMock(spec=ProjectBuildRequest)
        project_build_request_mock = mocker.patch(
            "monorepo_builder.build_executor.ProjectBuildRequest", return_value=req
        )

        result = ProjectBuildRequests.standard_projects(projects)

        assert len(result) == 1
        assert req in result
        project_build_request_mock.assert_called_once_with(project=std1)

    def test_success_all_successful(self):
        request1 = MagicMock(spec=ProjectBuildRequest, run_successful=True)
        request2 = MagicMock(spec=ProjectBuildRequest, run_successful=True)
        requests = ProjectBuildRequests()
        requests.extend([request1, request2])

        assert requests.success is True

    def test_success_true_when_no_projects_run(self):
        requests = ProjectBuildRequests()

        assert requests.success is True

    def test_success_all_failed(self):
        request1 = MagicMock(spec=ProjectBuildRequest, run_successful=False)
        request2 = MagicMock(spec=ProjectBuildRequest, run_successful=False)
        requests = ProjectBuildRequests()
        requests.extend([request1, request2])

        assert requests.success is False

    def test_success_some_success_some_failed(self):
        request1 = MagicMock(spec=ProjectBuildRequest, run_successful=False)
        request2 = MagicMock(spec=ProjectBuildRequest, run_successful=True)
        requests = ProjectBuildRequests()
        requests.extend([request1, request2])

        assert requests.success is False


class TestBuildExecutor:
    def test_execute_builds(self, mocker):
        run_build_mock = mocker.patch.object(BuildExecutor, "run_build")
        project_build_requests = ProjectBuildRequests()
        build_request_1 = MagicMock(spec=ProjectBuildRequest)
        build_request_2 = MagicMock(spec=ProjectBuildRequest)
        project_build_requests.extend([build_request_1, build_request_2])

        result = BuildExecutor().execute_builds(project_build_requests)

        assert result is project_build_requests
        assert run_build_mock.call_args_list == [
            call(build_request_1),
            call(build_request_2),
        ]

    def test_run_build_successful(self, mocker):
        mocker.patch("monorepo_builder.build_executor.write_to_console")
        subprocess_mock = mocker.patch("monorepo_builder.build_executor.subprocess")
        subprocess_mock.PIPE = "pipe"
        subprocess_mock.STDOUT = "stdout"
        run_result = MagicMock(
            spec=CompletedProcess, returncode=0, stdout=["one", "two"]
        )
        subprocess_mock.run.return_value = run_result
        project = MagicMock(spec=Project, project_path="here", needs_build=True)
        build_request = MagicMock(spec=ProjectBuildRequest, project=project)

        BuildExecutor().run_build(build_request)

        assert build_request.run_successful is True
        assert build_request.build_status == BuildRequestStatus.Complete
        assert build_request.console_output == ["one", "two"]
        subprocess_mock.run.assert_called_once_with(
            ["./build.sh"], cwd="here", stdout="pipe", stderr="stdout"
        )

    def test_run_build_failed(self, mocker):
        mocker.patch("monorepo_builder.build_executor.write_to_console")
        subprocess_mock = mocker.patch("monorepo_builder.build_executor.subprocess")
        subprocess_mock.PIPE = "pipe"
        subprocess_mock.STDOUT = "stdout"
        run_result = MagicMock(
            spec=CompletedProcess, returncode=1, stdout=["one", "two"]
        )
        subprocess_mock.run.return_value = run_result
        project = MagicMock(spec=Project, project_path="here", needs_build=True)
        build_request = MagicMock(spec=ProjectBuildRequest, project=project)

        BuildExecutor().run_build(build_request)

        assert build_request.run_successful is False
        assert build_request.build_status == BuildRequestStatus.Complete
        assert build_request.console_output == ["one", "two"]
        subprocess_mock.run.assert_called_once_with(
            ["./build.sh"], cwd="here", stdout="pipe", stderr="stdout"
        )

    def test_run_build_not_needed(self, mocker):
        subprocess_mock = mocker.patch("monorepo_builder.build_executor.subprocess")
        project = MagicMock(spec=Project, project_path="here", needs_build=False)
        build_request = MagicMock(spec=ProjectBuildRequest, project=project)

        BuildExecutor().run_build(build_request)

        assert build_request.build_status == BuildRequestStatus.NotNeeded
        subprocess_mock.run.assert_not_called()
