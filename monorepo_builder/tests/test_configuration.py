from unittest.mock import MagicMock

from monorepo_builder.configuration import (
    create_default_standard_folder_list,
    Configuration,
    ConfigurationManager,
)


def test_create_default_standard_folder_list():
    result = create_default_standard_folder_list()
    assert result == ["platform", "web"]


class TestConfiguration:
    def test_default_value_standard_folder_list(self,):
        configuration = Configuration()
        assert configuration.standard_folder_list == ["platform", "web"]


class TestConfigurationManager:
    def test_get_for_the_first_time(self, mocker):
        configuration_mock = mocker.patch(
            "monorepo_builder.configuration.Configuration"
        )
        result = ConfigurationManager.get()
        assert result == configuration_mock.return_value

    def test_get_second_and_on_time(self, mocker):
        configuration_manager = ConfigurationManager()
        mocker.patch(
            "monorepo_builder.configuration.Configuration",
            side_effect=Exception("This should not be called"),
        )
        assert configuration_manager.get() == configuration_manager.configuration

    def test_init(self,):
        configuration_manager = ConfigurationManager()
        config = MagicMock(spec=Configuration)
        configuration_manager.init(config)

        assert configuration_manager.configuration == config
