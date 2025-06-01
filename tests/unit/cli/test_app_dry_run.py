from unittest.mock import Mock, patch

import pytest

from cli.app import WordbenderApp
from llm_services.llm_service import LlmProvider


class TestWordlistGenerationDryRun:
    @pytest.fixture
    def app(self):
        return WordbenderApp()

    @pytest.fixture
    def mock_generator(self, tmp_path):
        generator = Mock()
        generator.__class__.__name__ = "PasswordWordlistGenerator"
        generator.output_file = tmp_path / "test.txt"
        generator.build_prompt.return_value = "test prompt"
        return generator

    @pytest.fixture
    def mock_llm_service(self):
        service = Mock()
        service.provider = LlmProvider.ANTHROPIC
        service.model_name = "test-model"
        return service

    def test_dry_run_prevents_generation_and_save(
        self, app, mock_generator, mock_llm_service
    ):
        options = {"dry_run": True}

        result = app.generate_wordlist(
            mock_generator, mock_llm_service, ["test"], options
        )

        assert result is True
        mock_generator.generate.assert_not_called()
        mock_generator.save.assert_not_called()

    def test_dry_run_builds_prompt(self, app, mock_generator, mock_llm_service):
        options = {"dry_run": True}

        app.generate_wordlist(mock_generator, mock_llm_service, ["test"], options)

        mock_generator.build_prompt.assert_called_once()

    def test_dry_run_returns_false_on_prompt_error(
        self, app, mock_generator, mock_llm_service
    ):
        mock_generator.build_prompt.side_effect = ValueError("error")
        options = {"dry_run": True}

        result = app.generate_wordlist(
            mock_generator, mock_llm_service, ["test"], options
        )

        assert result is False

    def test_normal_mode_still_generates_and_saves(
        self, app, mock_generator, mock_llm_service
    ):
        mock_generator.generate.return_value = ["word1", "word2"]
        options = {"dry_run": False}

        with patch("cli.app.yaspin"):
            result = app.generate_wordlist(
                mock_generator, mock_llm_service, ["test"], options
            )

        assert result is True
        mock_generator.generate.assert_called_once_with(mock_llm_service)
        mock_generator.save.assert_called_once()
