from unittest.mock import MagicMock

from monorepo_builder.project_list import ProjectListManager, Projects
from monorepo_builder.projects import Project
from monorepo_builder.runner import BuildRunner, run_build


class TestRunBuild:
    def test_run_build(self, mocker):
        projects = MagicMock(spec=Projects)
        projects_factory_mock = mocker.patch.object(
            Projects, "projects_factory", return_value=projects
        )
        identify_projects_needing_build_mock = mocker.patch.object(
            BuildRunner, "identify_projects_needing_build"
        )
        build_library_projects_mock = mocker.patch.object(
            BuildRunner, "build_library_projects"
        )
        build_standard_projects_mock = mocker.patch.object(
            BuildRunner, "build_standard_projects"
        )

        run_build()

        projects_factory_mock.assert_called_once()
        identify_projects_needing_build_mock.assert_called_once_with(projects)
        build_library_projects_mock.assert_called_once_with(projects)
        build_standard_projects_mock.assert_called_once_with(projects)


class TestBuildRunner:
    def test_set_project_needs_build_flag(self, mocker):
        project_1 = MagicMock(spec=Project)
        project_1.name = "one"
        project_2 = MagicMock(spec=Project)
        project_2.name = "two"
        project_3 = MagicMock(spec=Project)
        project_3.name = "three"
        projects = Projects()
        projects.extend([project_1, project_2, project_3])
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

        project_1.identify_if_build_needed.assert_called_once_with(previous_2)
        project_2.identify_if_build_needed.assert_called_once_with(previous_1)
        project_3.identify_if_build_needed.assert_called_once_with(None)
