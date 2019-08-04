from pathlib import Path
from unittest.mock import MagicMock, call

from monorepo_builder.configuration import Configuration, ConfigurationManager
from monorepo_builder.projects import (
    Project,
    ProjectType,
    ProjectListBuilder,
    ProjectList,
    File,
    ProjectFileListBuilder,
)


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


class TestProjectList:
    def test_build_project_list(self, mocker):
        project1 = MagicMock(spec=Project)
        project2 = MagicMock(spec=Project)
        list1 = [project1, project2]
        project3 = MagicMock(spec=Project)
        list2 = [project3]
        get_projects_mock = mocker.patch.object(
            ProjectListBuilder, "get_projects", side_effect=[list1, list2, []]
        )
        mocker.patch.object(
            ConfigurationManager,
            "get",
            return_value=MagicMock(
                monorepo_root_folder="root",
                library_folder_name="lib",
                standard_folder_list=["folder1", "folder2"],
            ),
        )
        result = ProjectList().build_project_list()
        assert len(result) == 3
        assert project1 in result
        assert project2 in result
        assert project3 in result
        assert get_projects_mock.call_args_list == [
            call("root/lib"),
            call("root/folder1"),
            call("root/folder2"),
        ]


class TestProjectListBuilder:
    def test_get_list_of_projects_for_folder(self, mocker):
        path_mock = mocker.patch("monorepo_builder.projects.Path")
        project_1 = MagicMock(name="project1", **{"is_dir.return_value": False})
        project_2 = MagicMock(
            name="project2",
            **{"is_dir.return_value": True, "__str__.return_value": "something"},
        )
        path_mock.return_value.iterdir.return_value = [project_1, project_2]
        project_mock = mocker.patch.object(Project, "__init__", return_value=None)

        result = ProjectListBuilder().get_projects("here")

        assert len(result) == 1
        path_mock.assert_called_once_with("here")
        project_mock.assert_called_once_with(project_path="something")


class TestFile:
    def test_file_factory(self, mocker):
        file = MagicMock(spec=Path, **{"__str__.return_value": "me"})
        file.stat.return_value.st_mtime = 1000
        result = File.file_factory(file)
        assert result.file == "me"
        assert result.last_changed_time == 1000


class TestProjectFileListBuilder:
    def test_build_include_all_files(self, mocker):
        child1 = MagicMock(spec=Path, **{"is_dir.return_value": False})
        child2 = MagicMock(spec=Path, **{"is_dir.return_value": False})
        parent1 = MagicMock(
            spec=Path,
            **{"is_dir.return_value": True, "iterdir.return_value": [child1, child2]},
        )
        child3 = MagicMock(spec=Path, **{"is_dir.return_value": False})
        project_path = MagicMock(
            spec=Path, **{"iterdir.return_value": [parent1, child3]}
        )
        file1 = MagicMock(spec=File)
        file2 = MagicMock(spec=File)
        file3 = MagicMock(spec=File)
        file_factory_mock = mocker.patch.object(
            File, "file_factory", side_effect=[file1, file2, file3]
        )
        configuration = MagicMock(spec=Configuration)
        mocker.patch.object(ConfigurationManager, "get", return_value=configuration)
        process_file_mock = mocker.patch.object(
            ProjectFileListBuilder, "process_file", return_value=True
        )

        result = ProjectFileListBuilder().build(project_path)

        assert len(result) == 3
        assert file1 in result
        assert file2 in result
        assert file3 in result
        assert file_factory_mock.call_args_list == [
            call(child1),
            call(child2),
            call(child3),
        ]
        assert process_file_mock.call_args_list == [
            call(parent1, configuration),
            call(child1, configuration),
            call(child2, configuration),
            call(child3, configuration),
        ]

    def test_build_exclude_file(self, mocker):
        child1 = MagicMock(spec=Path, **{"is_dir.return_value": False})
        child2 = MagicMock(spec=Path, **{"is_dir.return_value": False})
        child3 = MagicMock(spec=Path, **{"is_dir.return_value": False})
        project_path = MagicMock(
            spec=Path, **{"iterdir.return_value": [child1, child2, child3]}
        )
        file1 = MagicMock(spec=File)
        file2 = MagicMock(spec=File)
        file_factory_mock = mocker.patch.object(
            File, "file_factory", side_effect=[file1, file2]
        )
        configuration = MagicMock(spec=Configuration)
        mocker.patch.object(ConfigurationManager, "get", return_value=configuration)
        process_file_mock = mocker.patch.object(
            ProjectFileListBuilder, "process_file", side_effect=[True, False, True]
        )

        result = ProjectFileListBuilder().build(project_path)

        assert len(result) == 2
        assert file1 in result
        assert file2 in result
        assert file_factory_mock.call_args_list == [call(child1), call(child3)]
        assert process_file_mock.call_args_list == [
            call(child1, configuration),
            call(child2, configuration),
            call(child3, configuration),
        ]

    def test_include_file(self,):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=True,
            extensions_to_skip=[".skip"],
            skip_hidden_folders=False,
        )
        file = MagicMock(spec=Path)
        file.name = "file.py"
        file.suffix = ".py"
        assert ProjectFileListBuilder().process_file(file, configuration)

    def test_exclude_file_because_of_name(self):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=True,
            extensions_to_skip=[".skip"],
            skip_hidden_folders=False,
        )
        file = MagicMock(spec=Path)
        file.name = "skip.this"
        file.suffix = ".this"
        assert ProjectFileListBuilder().process_file(file, configuration) is False

    def test_exclude_hidden_file(self):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=False,
            extensions_to_skip=[".skip"],
            skip_hidden_folders=False,
        )
        file = MagicMock(spec=Path)
        file.name = ".this"
        file.suffix = ".this"
        assert ProjectFileListBuilder().process_file(file, configuration)

    def test_include_hidden_folder(self):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=True,
            extensions_to_skip=[".skip"],
            skip_hidden_folders=False,
        )
        file = MagicMock(spec=Path)
        file.name = ".this"
        file.suffix = ".this"
        file.is_file.return_value = False
        assert ProjectFileListBuilder().process_file(file, configuration)

    def test_include_hidden_file_when_turned_off(self):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=False,
            extensions_to_skip=[".skip"],
            skip_hidden_folders=False,
        )
        file = MagicMock(spec=Path)
        file.name = ".this"
        file.suffix = ".this"
        assert ProjectFileListBuilder().process_file(file, configuration)

    def test_exclude_file_because_of_extension(self):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=True,
            extensions_to_skip=[".skip"],
            skip_hidden_folders=False,
        )
        file = MagicMock(spec=Path)
        file.name = "file.skip"
        file.suffix = ".skip"
        assert ProjectFileListBuilder().process_file(file, configuration) is False

    def test_exclude_folder_when_hidden(self):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=False,
            skip_hidden_folders=True,
            extensions_to_skip=[".skip"],
        )
        file = MagicMock(spec=Path)
        file.name = ".this"
        file.suffix = ".this"
        file.is_dir.return_value = True
        assert ProjectFileListBuilder().process_file(file, configuration) is False

    def test_include_folder_when_file(self):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=False,
            skip_hidden_folders=True,
            extensions_to_skip=[".skip"],
        )
        file = MagicMock(spec=Path)
        file.name = ".this"
        file.suffix = ".this"
        file.is_dir.return_value = False
        assert ProjectFileListBuilder().process_file(file, configuration)

    def test_include_folder_when_eclusion_turned_off(self):
        configuration = MagicMock(
            spec=Configuration,
            filenames_to_skip=["skip.this"],
            skip_hidden_files=False,
            skip_hidden_folders=False,
            extensions_to_skip=[".skip"],
        )
        file = MagicMock(spec=Path)
        file.name = ".this"
        file.suffix = ".this"
        file.is_dir.return_value = False
        assert ProjectFileListBuilder().process_file(file, configuration)
