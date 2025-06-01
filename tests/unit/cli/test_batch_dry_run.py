from unittest.mock import Mock, patch

import pytest

from cli.commands import BatchProcessor


class TestBatchProcessingDryRun:

    @pytest.fixture
    def mock_config(self):
        config = Mock()
        config.get_api_key.return_value = "test-key"
        config.select_provider.return_value = "test-provider"
        return config

    @pytest.fixture
    def batch_processor(self, mock_config, monkeypatch):
        monkeypatch.setattr("cli.commands.Config", lambda: mock_config)
        processor = BatchProcessor()

        mock_generator = Mock()
        mock_generator.build_prompt.return_value = "test prompt"
        processor.generator_factory.create = Mock(return_value=mock_generator)

        return processor

    @pytest.fixture
    def seed_file(self, tmp_path):
        seed_file = tmp_path / "seeds.txt"
        seed_file.write_text("seed1\nseed2\nseed3")
        return seed_file

    def test_dry_run_does_not_create_output_file(
        self, batch_processor, seed_file, tmp_path
    ):
        output_file = tmp_path / "output.txt"

        with patch("rich.console.Console.print"):
            batch_processor.process(
                input_file=seed_file,
                wordlist_type="password",
                output=output_file,
                length=50,
                provider="test-provider",
                batch_size=2,
                dry_run=True,
            )

        assert not output_file.exists()

    def test_dry_run_vs_normal_mode(self, batch_processor, seed_file, monkeypatch):
        mock_process_batches = Mock()
        monkeypatch.setattr(
            batch_processor, "_process_all_batches", mock_process_batches
        )

        with patch("rich.console.Console.print"):
            batch_processor.process(
                input_file=seed_file,
                wordlist_type="password",
                output=None,
                length=50,
                provider="test-provider",
                batch_size=2,
                dry_run=True,
            )

        mock_process_batches.assert_not_called()
