from pathlib import Path
from unittest.mock import MagicMock

from monorepo_builder.configuration import Configuration, ConfigurationManager
from monorepo_builder.projects import Project, ProjectType, File


class TestProject:
    def test_is_library_project(self, mocker):
        configuration_mock = MagicMock(spec=Configuration, library_folder_name="lib")
        mocker.patch.object(
            ConfigurationManager, "get", return_value=configuration_mock
        )
        mocker.patch.object(Project, "path", MagicMock(parts=("first", "lib", "third")))
        project = Project(project_path="something/lib/project")
        assert project.project_type == ProjectType.Library

    def test_is_library_project_only_when_full_folder_name_used(self, mocker):
        configuration_mock = MagicMock(spec=Configuration, library_folder_name="lib")
        mocker.patch.object(
            ConfigurationManager, "get", return_value=configuration_mock
        )
        mocker.patch.object(
            Project, "path", MagicMock(parts=("first", "library", "third"))
        )
        project = Project(project_path="something/library/project")
        assert project.project_type == ProjectType.Standard

    def test_is_regular_project(self, mocker):
        configuration_mock = MagicMock(spec=Configuration, library_folder_name="lib")
        mocker.patch.object(
            ConfigurationManager, "get", return_value=configuration_mock
        )
        mocker.patch.object(
            Project, "path", MagicMock(parts=("first", "project", "third"))
        )
        project = Project(project_path="something/web/project")
        assert project.project_type == ProjectType.Standard

    def test_path(self, mocker):
        path_mock = mocker.patch("monorepo_builder.projects.Path")
        project = Project(project_path="this")
        assert project.path is path_mock.return_value
        path_mock.assert_called_once_with("this")

    def test_project_has_not_changed(self):
        current_file_1 = MagicMock(spec=File, file="first", last_changed_time=1)
        current_file_2 = MagicMock(spec=File, file="second", last_changed_time=1)
        current_project = Project(
            project_path="here", file_list=[current_file_2, current_file_1]
        )
        previous_file_1 = MagicMock(spec=File, file="first", last_changed_time=1)
        previous_file_2 = MagicMock(spec=File, file="second", last_changed_time=1)
        project_from_last_run = MagicMock(
            spec=Project, file_list=[previous_file_1, previous_file_2]
        )

        current_project.mark_if_build_needed(project_from_last_run)

        assert current_project.needs_build is False

    def test_project_has_changed_with_different_file_count(self):
        current_file_1 = MagicMock(spec=File)
        current_project = Project(project_path="here", file_list=[current_file_1])
        previous_file_1 = MagicMock(spec=File)
        previous_file_2 = MagicMock(spec=File)
        project_from_last_run = MagicMock(
            spec=Project, file_list=[previous_file_2, previous_file_1]
        )

        current_project.mark_if_build_needed(project_from_last_run)

        assert current_project.needs_build is True

    def test_project_from_previous_run_is_none(self):
        current_file_1 = MagicMock(spec=File, file="first", last_changed_time=1)
        current_file_2 = MagicMock(spec=File, file="second", last_changed_time=1)
        current_project = Project(
            project_path="here", file_list=[current_file_1, current_file_2]
        )

        current_project.mark_if_build_needed(None)

        assert current_project.needs_build is True

    def test_project_has_changed_with_with_unmatching_files(self):
        current_file_1 = MagicMock(spec=File, file="first", last_changed_time=1)
        current_file_2 = MagicMock(spec=File, file="second", last_changed_time=1)
        current_project = Project(
            project_path="here", file_list=[current_file_1, current_file_2]
        )
        previous_file_1 = MagicMock(spec=File, file="first", last_changed_time=1)
        previous_file_2 = MagicMock(spec=File, file="other", last_changed_time=1)
        project_from_last_run = MagicMock(
            spec=Project, file_list=[previous_file_1, previous_file_2]
        )

        current_project.mark_if_build_needed(project_from_last_run)

        assert current_project.needs_build is True

    def test_project_has_changed_with_with_matching_files_and_different_times(self):
        current_file_1 = MagicMock(spec=File, file="first", last_changed_time=1)
        current_file_2 = MagicMock(spec=File, file="second", last_changed_time=1)
        current_project = Project(
            project_path="here", file_list=[current_file_1, current_file_2]
        )
        previous_file_1 = MagicMock(spec=File, file="first", last_changed_time=1)
        previous_file_2 = MagicMock(spec=File, file="second", last_changed_time=2)
        project_from_last_run = MagicMock(
            spec=Project, file_list=[previous_file_1, previous_file_2]
        )

        current_project.mark_if_build_needed(project_from_last_run)

        assert current_project.needs_build is True


class TestFile:
    def test_file_factory(self):
        file = MagicMock(spec=Path, **{"__str__.return_value": "me"})
        file.stat.return_value.st_mtime = 1000
        result = File.file_factory(file)
        assert result.file == "me"
        assert result.last_changed_time == 1000
