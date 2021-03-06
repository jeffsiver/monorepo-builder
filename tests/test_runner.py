from pathlib import Path
from unittest.mock import MagicMock

from monorepo_builder.build_executor import ProjectBuildRequests
from monorepo_builder.configuration import ConfigurationManager, Configuration
from monorepo_builder.project_list import ProjectListManager, Projects
from monorepo_builder.projects import Project
from monorepo_builder.runner import BuildRunner, Runner
from monorepo_builder.version import ProjectVersionManager, ProjectVersions


class TestRunner:
    def test_run_build_successful(self, mocker):
        projects = MagicMock(spec=Projects)
        gather_projects_mock = mocker.patch.object(
            Runner, "gather_projects", return_value=projects
        )
        requests = MagicMock(spec=ProjectBuildRequests, success=True)
        do_builds_mock = mocker.patch.object(Runner, "do_builds", return_value=requests)
        finish_builds_mock = mocker.patch.object(Runner, "finish_builds_on_success")
        setup_mock = mocker.patch.object(Runner, "setup")

        Runner.run("1.0")

        gather_projects_mock.assert_called_once()
        do_builds_mock.assert_called_once_with(projects)
        finish_builds_mock.assert_called_once_with(projects, "1.0")
        setup_mock.assert_called_once()

    def test_run_build_fails(self, mocker):
        projects = MagicMock(spec=Projects)
        gather_projects_mock = mocker.patch.object(
            Runner, "gather_projects", return_value=projects
        )
        requests = MagicMock(spec=ProjectBuildRequests, success=False)
        do_builds_mock = mocker.patch.object(Runner, "do_builds", return_value=requests)
        finish_builds_mock = mocker.patch.object(Runner, "finish_builds_on_failure")
        setup_mock = mocker.patch.object(Runner, "setup")

        Runner.run("1.0")

        gather_projects_mock.assert_called_once()
        do_builds_mock.assert_called_once_with(projects)
        finish_builds_mock.assert_called_once_with(requests)
        setup_mock.assert_called_once()

    def test_setup(self, mocker):
        mocker.patch("monorepo_builder.runner.write_to_console")
        configuration_load_mock = mocker.patch.object(ConfigurationManager, "load")
        configuration = MagicMock(spec=Configuration, installer_folder="here")
        mocker.patch.object(ConfigurationManager, "get", return_value=configuration)
        path_mock = mocker.patch.object(Path, "__init__", return_value=None)
        mkdir_mock = mocker.patch.object(Path, "mkdir")

        Runner().setup()

        configuration_load_mock.assert_called_once_with("monorepo-builder-config.json")
        path_mock.assert_called_once_with("here")
        mkdir_mock.assert_called_once_with(exist_ok=True)

    def test_gather_projects(self, mocker):
        mocker.patch("monorepo_builder.runner.write_to_console")
        projects = MagicMock(spec=Projects)
        mocker.patch.object(Projects, "projects_factory", return_value=projects)
        identify_projects_needing_build_mock = mocker.patch.object(
            BuildRunner, "identify_projects_needing_build"
        )

        result = Runner().gather_projects()

        assert result is projects
        identify_projects_needing_build_mock.assert_called_once_with(projects)

    def test_do_builds_all_succeed(self, mocker):
        mocker.patch("monorepo_builder.runner.write_to_console")
        projects = MagicMock(spec=Projects)
        requests = MagicMock(spec=ProjectBuildRequests, success=True)
        build_library_projects_mock = mocker.patch.object(
            BuildRunner, "build_library_projects", return_value=requests
        )
        build_standard_projects_mock = mocker.patch.object(
            BuildRunner, "build_standard_projects"
        )

        result = Runner().do_builds(projects)

        assert result is requests
        build_library_projects_mock.assert_called_once_with(projects)
        build_standard_projects_mock.assert_called_once_with(projects)
        requests.extend.assert_called_once_with(
            build_standard_projects_mock.return_value
        )

    def test_do_builds_library_builds_fail(self, mocker):
        mocker.patch("monorepo_builder.runner.write_to_console")
        projects = MagicMock(spec=Projects)
        requests = MagicMock(spec=ProjectBuildRequests, success=False)
        build_library_projects_mock = mocker.patch.object(
            BuildRunner, "build_library_projects", return_value=requests
        )
        build_standard_projects_mock = mocker.patch.object(
            BuildRunner, "build_standard_projects"
        )

        result = Runner().do_builds(projects)

        assert result is requests
        build_library_projects_mock.assert_called_once_with(projects)
        build_standard_projects_mock.assert_not_called()
        requests.extend.assert_not_called()

    def test_do_builds_library_builds_succeed_standard_builds_fail(self, mocker):
        mocker.patch("monorepo_builder.runner.write_to_console")
        requests = MagicMock(spec=ProjectBuildRequests, success=True)
        projects = MagicMock(spec=Projects)

        std_requests = MagicMock()

        def handle_standard_return(arg):
            requests.success = False
            return std_requests

        build_library_projects_mock = mocker.patch.object(
            BuildRunner, "build_library_projects", return_value=requests
        )
        build_standard_projects_mock = mocker.patch.object(
            BuildRunner, "build_standard_projects", side_effect=handle_standard_return
        )

        result = Runner().do_builds(projects)

        assert result is requests
        build_library_projects_mock.assert_called_once_with(projects)
        build_standard_projects_mock.assert_called_once_with(projects)
        requests.extend.assert_called_once_with(std_requests)

    def test_finish_builds_on_success(self, mocker):
        projects = MagicMock(spec=Projects)
        save_project_list_mock = mocker.patch.object(
            ProjectListManager, "save_project_list"
        )
        version_list = MagicMock(spec=ProjectVersions)
        build_version_list_mock = mocker.patch.object(
            ProjectVersionManager, "build_version_list", return_value=version_list
        )
        save_version_list_mock = mocker.patch.object(
            ProjectVersionManager, "save_version_list"
        )

        Runner().finish_builds_on_success(projects, "vers")

        save_project_list_mock.assert_called_once_with(projects)
        build_version_list_mock.assert_called_once_with(projects, "vers")
        save_version_list_mock.assert_called_once_with(version_list)

    def test_finish_builds_on_failure(self, mocker):
        mocker.patch("monorepo_builder.runner.write_to_console")
        requests = MagicMock(spec=ProjectBuildRequests, success=False)

        Runner().finish_builds_on_failure(requests)


class TestBuildRunner:
    def test_set_project_needs_build_flag(self, mocker):
        lib_proj_1 = MagicMock(spec=Project, needs_build=True)
        lib_proj_1.name = "one"
        lib_proj_2 = MagicMock(spec=Project, needs_build=False)
        lib_proj_2.name = "libtwo"
        std_proj_1 = MagicMock(spec=Project)
        std_proj_1.name = "two"
        std_proj_2 = MagicMock(spec=Project)
        std_proj_2.name = "three"
        projects = MagicMock(
            spec=Projects,
            **{
                "__iter__.return_value": [lib_proj_1, std_proj_1, std_proj_2],
                "library_projects": [lib_proj_1, lib_proj_2],
                "standard_projects": [std_proj_1, std_proj_2],
            },
        )
        previous_1 = MagicMock(spec=Project)
        previous_1.name = "two"
        previous_2 = MagicMock(spec=Project)
        previous_2.name = "one"
        previous_projects = Projects()
        previous_projects.extend([previous_1, previous_2])
        mocker.patch.object(
            ProjectListManager,
            "load_list_from_last_successful_run",
            return_value=previous_projects,
        )

        BuildRunner().identify_projects_needing_build(projects)

        lib_proj_1.set_needs_build_due_to_file_changes.assert_called_once_with(
            previous_2
        )
        std_proj_1.set_needs_build_due_to_file_changes.assert_called_once_with(
            previous_1
        )
        std_proj_2.set_needs_build_due_to_file_changes.assert_called_once_with(None)
        std_proj_1.set_needs_build_due_to_updated_library_reference.assert_called_once_with(
            ["one"]
        )
        std_proj_2.set_needs_build_due_to_updated_library_reference.assert_called_once_with(
            ["one"]
        )
