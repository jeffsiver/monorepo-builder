from pathlib import Path
from unittest.mock import mock_open, patch, MagicMock, call

from monorepo_builder.configuration import ConfigurationManager, Configuration
from monorepo_builder.project_list import (
    ProjectListFactory,
    ProjectListManager,
    Projects,
)
from monorepo_builder.projects import ProjectFileListBuilder, File, Project, ProjectType


class TestProjects:
    def test_build_project_list(self, mocker):
        project1 = MagicMock(spec=Project)
        project2 = MagicMock(spec=Project)
        list1 = [project1, project2]
        project3 = MagicMock(spec=Project)
        list2 = [project3]
        get_projects_mock = mocker.patch.object(
            ProjectListFactory, "get_projects_in_folder", side_effect=[list1, list2, []]
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

        projects = Projects.projects_factory()

        assert len(projects) == 3
        assert project1 in projects
        assert project2 in projects
        assert project3 in projects
        assert get_projects_mock.call_args_list == [
            call("root/lib"),
            call("root/folder1"),
            call("root/folder2"),
        ]

    def test_library_projects_property(self, mocker):
        lib_project = MagicMock(spec=Project, project_type=ProjectType.Library)
        projects = Projects()
        projects.extend(
            [lib_project, MagicMock(spec=Project, project_type=ProjectType.Standard)]
        )

        library_projects = projects.library_projects

        assert len(library_projects) == 1
        assert lib_project in library_projects

    def test_standard_projects_property(self, mocker):
        std_project = MagicMock(spec=Project, project_type=ProjectType.Standard)
        projects = Projects()
        projects.extend(
            [std_project, MagicMock(spec=Project, project_type=ProjectType.Library)]
        )

        result = projects.standard_projects

        assert len(result) == 1
        assert std_project in result


class TestProjectListManager:
    def test_load_when_file_exists(self, mocker):
        path_mock = mocker.patch("monorepo_builder.project_list.Path")
        path_mock.return_value.exists.return_value = True
        pickle_mock = mocker.patch("monorepo_builder.project_list.pickle")
        pickle_mock.loads.return_value = "some data"
        mocker.patch.object(
            ConfigurationManager,
            "get",
            return_value=MagicMock(project_list_filename="here"),
        )
        m = mock_open(read_data="input")
        with patch("builtins.open", m):
            result = ProjectListManager().load_list_from_last_successful_run()
            assert result == "some data"
        path_mock.assert_called_once_with("here")
        m.assert_called_once_with("here", "rb")
        pickle_mock.loads.assert_called_once_with("input")

    def test_load_when_file_does_not_exist(self, mocker):
        path_mock = mocker.patch("monorepo_builder.project_list.Path")
        path_mock.return_value.exists.return_value = False
        mocker.patch.object(
            ConfigurationManager,
            "get",
            return_value=MagicMock(project_list_filename="here"),
        )
        result = ProjectListManager().load_list_from_last_successful_run()
        assert result == []
        path_mock.assert_called_once_with("here")

    def test_save_last_used_list(self, mocker):
        pickle_mock = mocker.patch("monorepo_builder.project_list.pickle")
        pickle_mock.dumps.return_value = "pickled data"
        m = mock_open()
        project_list_mock = [MagicMock(spec=Project)]
        mocker.patch.object(
            ConfigurationManager,
            "get",
            return_value=MagicMock(project_list_filename="here"),
        )
        with patch("builtins.open", m):
            ProjectListManager().save_project_list(project_list_mock)
        m.assert_called_once_with("here", "wb")
        m.return_value.write.assert_called_once_with("pickled data")
        pickle_mock.dumps.assert_called_once_with(project_list_mock)


class TestProjectFileListFactory:
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


class TestProjectListFactory:
    def test_get_projects_from_folder(self, mocker):
        mocker.patch("monorepo_builder.build_executor.write_to_console")
        path1_mock = MagicMock(
            **{"is_dir.return_value": True, "__str__.return_value": "first"}
        )
        path2_mock = MagicMock(
            **{"is_dir.return_value": True, "__str__.return_value": "second"}
        )
        file1_mock = MagicMock(
            **{"is_dir.return_value": False, "__str__.return_value": "thid"}
        )
        path_mock = mocker.patch(
            "monorepo_builder.project_list.Path",
            **{
                "return_value.iterdir.return_value": [
                    path1_mock,
                    file1_mock,
                    path2_mock,
                ],
                "return_value.exists.return_value": True,
            },
        )
        project1_mock = MagicMock(spec=Project)
        project2_mock = MagicMock(spec=Project)
        project_mock = mocker.patch(
            "monorepo_builder.project_list.Project",
            side_effect=[project1_mock, project2_mock],
        )
        file_builder_mock = mocker.patch.object(
            ProjectFileListBuilder, "build", side_effect=["numberone", "numbertwo"]
        )

        result = ProjectListFactory().get_projects_in_folder("start")

        assert result == [project1_mock, project2_mock]
        assert path_mock.call_args_list == [call("start"), call("start")]
        assert project_mock.call_args_list == [
            call(project_path="first", file_list="numberone"),
            call(project_path="second", file_list="numbertwo"),
        ]
        assert file_builder_mock.call_args_list == [call(path1_mock), call(path2_mock)]

    def test_get_projects_in_folder_when_folder_not_found(self, mocker):
        mocker.patch("monorepo_builder.build_executor.write_to_console")
        path_mock = mocker.patch.object(Path, "__init__", return_value=None)
        mocker.patch.object(Path, "exists", return_value=False)

        result = ProjectListFactory().get_projects_in_folder("here")

        assert result == []
        path_mock.assert_called_once_with("here")
