from unittest.mock import MagicMock, mock_open, patch

from monorepo_builder.configuration import Configuration, ConfigurationManager
from monorepo_builder.project_list import Projects
from monorepo_builder.projects import Project
from monorepo_builder.version import ProjectVersionManager, ProjectVersions


class TestProjectVersions:
    def test_get_version_project_found(self):
        project_versions = ProjectVersions()
        project_versions["path1"] = "1.0"
        project_versions["num2"] = "1.3"

        project = MagicMock(spec=Project, project_path="path1")
        assert project_versions.get_version(project) == "1.0"

    def test_get_version_project_not_found(self):
        project_versions = ProjectVersions()
        project_versions["path1"] = "1.0"
        project_versions["num2"] = "1.3"

        project = MagicMock(spec=Project, project_path="notfound")
        assert project_versions.get_version(project) is None

    def test_add_project(self):
        project_versions = ProjectVersions()
        project = MagicMock(spec=Project, project_path="path")
        project_versions.add_project(project, "1.0")

        assert "path" in project_versions
        assert project_versions["path"] == "1.0"


class TestProjectVersion:
    def test_build_version_list_all_new(self, mocker):
        mocker.patch.object(
            ProjectVersionManager, "load_previous_version_list", return_value=None
        )

        project1 = MagicMock(spec=Project, project_path="path1")
        project2 = MagicMock(spec=Project, project_path="path2")
        projects = Projects()
        projects.extend([project1, project2])

        project_version_list = ProjectVersionManager().build_version_list(
            projects, "1.0.0"
        )

        assert len(project_version_list) == 2
        assert "path1" in project_version_list
        assert "path2" in project_version_list
        assert project_version_list["path1"] == "1.0.0"
        assert project_version_list["path2"] == "1.0.0"

    def test_load_previous_version_list_not_found(self, mocker):
        configuration = MagicMock(spec=Configuration, version_list_filename="file")
        mocker.patch.object(ConfigurationManager, "get", return_value=configuration)
        path_mock = mocker.patch("monorepo_builder.version.Path")
        path_mock.return_value.exists.return_value = False
        project_versions_mock = mocker.patch("monorepo_builder.version.ProjectVersions")

        result = ProjectVersionManager().load_previous_version_list()

        assert result is project_versions_mock.return_value
        path_mock.assert_called_once_with("file")

    def test_load_previous_version_list_found(self, mocker):
        configuration = MagicMock(spec=Configuration, version_list_filename="file")
        mocker.patch.object(ConfigurationManager, "get", return_value=configuration)
        path_mock = mocker.patch("monorepo_builder.version.Path")
        path_mock.return_value.exists.return_value = True
        open_mock = mock_open()
        versions_mock = MagicMock(spec=ProjectVersions)
        loads_mock = mocker.patch(
            "monorepo_builder.version.pickle.load", return_value=versions_mock
        )

        with patch("builtins.open", open_mock):
            result = ProjectVersionManager().load_previous_version_list()

        open_mock.assert_called_once_with("file", "rb")
        assert result is versions_mock
        path_mock.assert_called_once_with("file")
        loads_mock.assert_called_once_with(open_mock.return_value)

    def test_save_previous_version_list(self, mocker):
        configuration = MagicMock(spec=Configuration, version_list_filename="file")
        mocker.patch.object(ConfigurationManager, "get", return_value=configuration)
        dump_mock = mocker.patch("monorepo_builder.version.pickle.dump")
        open_mock = mock_open()
        project_versions = MagicMock(spec=ProjectVersions)

        with patch("builtins.open", open_mock):
            ProjectVersionManager().save_version_list(project_versions)

        open_mock.assert_called_once_with("file", "wb")
        dump_mock.assert_called_once_with(project_versions, open_mock.return_value)
