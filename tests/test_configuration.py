from pathlib import PurePath, Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from monorepo_builder.configuration import (
    create_default_standard_folder_list,
    Configuration,
    ConfigurationManager,
    get_current_folder,
    InvalidConfigurationSettingException,
    InvalidConfigurationException,
)


def test_create_default_standard_folder_list():
    result = create_default_standard_folder_list()
    assert result == ["platform", "web"]


def test_get_current_folder(mocker):
    path = MagicMock(spec=PurePath, **{"__str__.return_value": "here"})
    mocker.patch("monorepo_builder.configuration.Path.cwd", return_value=path)

    result = get_current_folder()

    assert result == "here"


class TestConfiguration:
    def test_default_value_standard_folder_list(self,):
        configuration = Configuration()
        assert configuration.standard_folder_list == ["platform", "web"]

    def test_build_from_settings(self,):
        configuration_settings = {
            "config": {
                "rootFolder": "start here",
                "libraryFolder": "lib",
                "standardFolders": ["std1", "std2"],
                "fileNamesToSkip": ["skip.me"],
                "extensionsToSkip": [".whl"],
                "skipHiddenFolders": False,
                "skipHiddenFiles": False,
                "projectListFilename": "list.me",
            }
        }
        configuration = Configuration.build_from_settings(configuration_settings)

        assert configuration.monorepo_root_folder == "start here"
        assert configuration.library_folder_name == "lib"
        assert configuration.standard_folder_list == ["std1", "std2"]
        assert configuration.filenames_to_skip == ["skip.me"]
        assert configuration.extensions_to_skip == [".whl"]
        assert configuration.skip_hidden_folders is False
        assert configuration.skip_hidden_files is False
        assert configuration.project_list_filename == "list.me"

    def test_build_from_settings_raises_exception_with_invalid_setting(self):
        configuration_settings = {"config": {"whatIsDat": "value"}}
        with pytest.raises(InvalidConfigurationSettingException) as excp:
            Configuration.build_from_settings(configuration_settings)
            assert "whatIsDate" in excp.value

    def test_build_from_settings_raises_exception_when_config_not_found(self):
        configuration_settings = {"something in the ": "way she moves"}
        with pytest.raises(InvalidConfigurationException):
            Configuration.build_from_settings(configuration_settings)


class TestConfigurationManager:
    def test_get_for_the_first_time_should_cache(self, mocker):
        configuration_mock = mocker.patch(
            "monorepo_builder.configuration.Configuration"
        )
        result = ConfigurationManager.get()
        assert result == configuration_mock.return_value

    def test_get_second_time_should_use_cached_version(self, mocker):
        configuration_manager = ConfigurationManager()
        mocker.patch(
            "monorepo_builder.configuration.Configuration",
            side_effect=Exception("This should not be called"),
        )
        assert configuration_manager.get() == configuration_manager.configuration

    def test_load_file_not_found(self, mocker):
        mocker.patch("monorepo_builder.configuration.write_to_console")
        path_mock = mocker.patch.object(Path, "__init__", return_value=None)
        mocker.patch.object(Path, "exists", return_value=False)
        configuration_mock = mocker.patch(
            "monorepo_builder.configuration.Configuration"
        )

        result = ConfigurationManager.load("test_file")

        assert ConfigurationManager.configuration is configuration_mock.return_value
        path_mock.assert_called_once_with("test_file")

    def test_load_configuration(self, mocker):
        mocker.patch("monorepo_builder.configuration.write_to_console")
        path_mock = mocker.patch.object(Path, "__init__", return_value=None)
        mocker.patch.object(Path, "exists", return_value=True)
        read_configuration = {"test": "value"}
        json_load_mock = mocker.patch(
            "monorepo_builder.configuration.json.load", return_value=read_configuration
        )
        configuration = MagicMock(spec=Configuration)
        build_from_settings_mock = mocker.patch.object(
            Configuration, "build_from_settings", return_value=configuration
        )
        file = mock_open()
        with patch("builtins.open", file):
            ConfigurationManager.load("configuration file")

        file.assert_called_with("configuration file", "r")
        # json_load_mock.assert_called_once_with(file)

        path_mock.assert_called_once_with("configuration file")
        build_from_settings_mock.assert_called_once_with(read_configuration)
        assert ConfigurationManager.configuration is configuration
