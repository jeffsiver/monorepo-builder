from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from monorepo_builder.configuration import Configuration, ConfigurationManager
from monorepo_builder.projects import (
    Project,
    ProjectType,
    File,
    RequirementsFileNotFoundException,
)


class TestProject:
    def test_get_project_name(self, mocker):
        path_mock = MagicMock()
        path_mock.name = "callmeIsmael"
        mocker.patch.object(Project, "path", path_mock)
        project = Project(project_path="path")

        assert project.name == "callmeIsmael"

    def test_get_project_name_replaces_underscores(self, mocker):
        path_mock = MagicMock()
        path_mock.name = "call_me-Ismael"
        mocker.patch.object(Project, "path", path_mock)
        project = Project(project_path="path")

        assert project.name == "call-me-Ismael"

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

        current_project.set_needs_build_due_to_file_changes(project_from_last_run)

        assert current_project.needs_build is False

    def test_project_has_changed_with_different_file_count(self):
        current_file_1 = MagicMock(spec=File)
        current_project = Project(project_path="here", file_list=[current_file_1])
        previous_file_1 = MagicMock(spec=File)
        previous_file_2 = MagicMock(spec=File)
        project_from_last_run = MagicMock(
            spec=Project, file_list=[previous_file_2, previous_file_1]
        )

        current_project.set_needs_build_due_to_file_changes(project_from_last_run)

        assert current_project.needs_build is True

    def test_project_from_previous_run_is_none(self):
        current_file_1 = MagicMock(spec=File, file="first", last_changed_time=1)
        current_file_2 = MagicMock(spec=File, file="second", last_changed_time=1)
        current_project = Project(
            project_path="here", file_list=[current_file_1, current_file_2]
        )

        current_project.set_needs_build_due_to_file_changes(None)

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

        current_project.set_needs_build_due_to_file_changes(project_from_last_run)

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

        current_project.set_needs_build_due_to_file_changes(project_from_last_run)

        assert current_project.needs_build is True

    def test_set_needs_build_due_to_updated_library_reference_yes(self, mocker):
        updated_library_names = ["one", "two"]
        project_references_updated_library_mock = mocker.patch.object(
            Project, "project_references_updated_library", return_value=True
        )
        set_needs_build_mock = mocker.patch.object(Project, "set_needs_build")

        project = Project(project_path="path")
        project.set_needs_build_due_to_updated_library_reference(updated_library_names)

        project_references_updated_library_mock.assert_called_once_with(
            updated_library_names
        )
        set_needs_build_mock.assert_called_once()

    def test_set_needs_build_due_to_updated_library_reference_no(self, mocker):
        updated_library_names = ["one", "two"]
        project_references_updated_library_mock = mocker.patch.object(
            Project, "project_references_updated_library", return_value=False
        )
        set_needs_build_mock = mocker.patch.object(Project, "set_needs_build")

        project = Project(project_path="path")
        project.set_needs_build_due_to_updated_library_reference(updated_library_names)

        project_references_updated_library_mock.assert_called_once_with(
            updated_library_names
        )
        set_needs_build_mock.assert_not_called()

    def test_project_does_reference_updated_library(self, mocker):
        requirements = "one\ntwo\nthree\nmine"
        mocker.patch.object(
            Project, "read_requirements_file", return_value=requirements
        )
        library_project_names = ["blah", "two", "else"]

        project = Project(project_path="path")
        result = project.project_references_updated_library(library_project_names)

        assert result is True

    def test_project_does_not_reference_updated_library(self, mocker):
        requirements = "not\nplus\nthree\nmine"
        mocker.patch.object(
            Project, "read_requirements_file", return_value=requirements
        )
        library_project_names = ["one", "two", "else"]

        project = Project(project_path="path")
        result = project.project_references_updated_library(library_project_names)

        assert result is False

    def test_read_requirements_file_for_python(self, mocker):
        join_mock = mocker.patch(
            "monorepo_builder.projects.os.path.join", side_effect=["file1", "file2"]
        )
        path_mock = mocker.patch.object(Path, "__init__", return_value=None)
        project = Project(project_path="here")
        exist_mock = mocker.patch.object(Path, "exists", return_value=True)
        mocker.patch.object(Path, "read_text", return_value="content")

        result = project.read_requirements_file()

        assert join_mock.call_args_list == [
            call("here", "requirements.txt"),
            call("here", "package.json"),
        ]
        path_mock.assert_called_once_with("file1")
        exist_mock.assert_called_once()
        assert result == "content"

    def test_read_requirements_file_for_node(self, mocker):
        join_mock = mocker.patch(
            "monorepo_builder.projects.os.path.join", side_effect=["file1", "file2"]
        )
        path_mock = mocker.patch.object(Path, "__init__", return_value=None)
        project = Project(project_path="here")
        exist_mock = mocker.patch.object(Path, "exists", side_effect=[False, True])
        mocker.patch.object(Path, "read_text", return_value="content")

        result = project.read_requirements_file()

        assert join_mock.call_args_list == [
            call("here", "requirements.txt"),
            call("here", "package.json"),
        ]
        assert path_mock.call_args_list == [call("file1"), call("file2")]
        assert exist_mock.call_count == 2
        assert result == "content"

    def test_read_requirements_file_not_found(self, mocker):
        join_mock = mocker.patch(
            "monorepo_builder.projects.os.path.join", side_effect=["file1", "file2"]
        )
        path_mock = mocker.patch.object(Path, "__init__", return_value=None)
        project = Project(project_path="here")
        exist_mock = mocker.patch.object(Path, "exists", side_effect=[False, False])
        mocker.patch.object(Project, "name", return_value="project")

        with pytest.raises(RequirementsFileNotFoundException):
            project.read_requirements_file()

        assert join_mock.call_args_list == [
            call("here", "requirements.txt"),
            call("here", "package.json"),
        ]
        assert path_mock.call_args_list == [call("file1"), call("file2")]
        assert exist_mock.call_count == 2


class TestFile:
    def test_file_factory(self):
        file = MagicMock(spec=Path, **{"__str__.return_value": "me"})
        file.stat.return_value.st_mtime = 1000
        result = File.file_factory(file)
        assert result.file == "me"
        assert result.last_changed_time == 1000
