from unittest.mock import MagicMock

from monorepo_builder.project_list import ProjectList, ProjectListManager
from monorepo_builder.projects import Project
from monorepo_builder.runner import BuildRunner, run_build


class TestRunBuild:
    def test_run_build(self, mocker):
        load_mock = mocker.patch.object(BuildRunner, "load")
        identify_projects_needing_build_mock = mocker.patch.object(
            BuildRunner, "identify_projects_needing_build"
        )

        run_build()

        load_mock.assert_called_once()
        identify_projects_needing_build_mock.assert_called_once()


class TestBuildRunner:
    def test_load(self, mocker):
        current_project_list = [MagicMock(spec=Project)]
        build_current_project_list_mock = mocker.patch.object(
            ProjectList, "build_current_project_list", return_value=current_project_list
        )
        previous_project_list = [MagicMock(spec=Project)]
        load_list_from_last_successful_run_mock = mocker.patch.object(
            ProjectListManager,
            "load_list_from_last_successful_run",
            return_value=previous_project_list,
        )

        BuildRunner().load()

        build_current_project_list_mock.assert_called_once()
        load_list_from_last_successful_run_mock.assert_called_once()

    def test_set_project_needs_build_flag(self):
        build_runner = BuildRunner()
        current_project_1 = MagicMock(spec=Project)
        current_project_1.name = "one"
        current_project_2 = MagicMock(spec=Project)
        current_project_2.name = "two"
        current_project_3 = MagicMock(spec=Project)
        current_project_3.name = "three"
        build_runner._project_list = [
            current_project_1,
            current_project_2,
            current_project_3,
        ]
        previous_project_1 = MagicMock(spec=Project)
        previous_project_1.name = "two"
        previous_project_2 = MagicMock(spec=Project)
        previous_project_2.name = "one"
        build_runner._previous_project_list = [previous_project_1, previous_project_2]

        build_runner.identify_projects_needing_build()

        current_project_1.identify_if_build_needed.assert_called_once_with(
            previous_project_2
        )
        current_project_2.identify_if_build_needed.assert_called_once_with(
            previous_project_1
        )
        current_project_3.identify_if_build_needed.assert_called_once_with(None)
