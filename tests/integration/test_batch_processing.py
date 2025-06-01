from unittest.mock import Mock, patch

import pytest

from cli.commands import BatchProcessor
from config import Config

TEST_API_KEY = "test-key"
DEFAULT_PROVIDER = "openrouter"
DEFAULT_WORDLIST_TYPE = "password"
GENERATED_WORDS = ["generated1", "generated2", "generated3"]


class TestBatchProcessing:

    @pytest.fixture
    def mock_config(self):
        config = Mock(spec=Config)
        config.get_api_key.return_value = TEST_API_KEY
        config.get_preferences.return_value = {
            "default_provider": DEFAULT_PROVIDER,
            "default_wordlist_type": DEFAULT_WORDLIST_TYPE,
        }
        config.select_provider.return_value = DEFAULT_PROVIDER
        return config

    @pytest.fixture
    def batch_processor(self, mock_config, monkeypatch):
        monkeypatch.setattr("cli.commands.Config", lambda: mock_config)
        processor = BatchProcessor()

        mock_llm = Mock()
        mock_llm.generate_words.return_value = GENERATED_WORDS
        processor.llm_factory.create = Mock(return_value=mock_llm)

        return processor

    @pytest.fixture
    def seed_file(self, tmp_path):
        seed_file = tmp_path / "seeds.txt"
        seed_content = """
            seed1
            seed2
            seed3
            seed4
        """
        seed_file.write_text(seed_content)
        return seed_file

    @pytest.mark.integration
    def test_batch_file_parsing(self, batch_processor, seed_file, tmp_path):
        output_file = tmp_path / "output.txt"

        with patch("rich.console.Console.print"):
            batch_processor.process(
                input_file=seed_file,
                wordlist_type=DEFAULT_WORDLIST_TYPE,
                output=output_file,
                length=50,
                provider=DEFAULT_PROVIDER,
                batch_size=2,
            )

        assert output_file.exists()

        content = output_file.read_text()
        for word in GENERATED_WORDS:
            assert word in content

    @pytest.mark.integration
    def test_batch_empty_lines(self, batch_processor, tmp_path):
        seed_file = tmp_path / "seeds.txt"
        seed_content = """
            seed1

            seed2

        """
        seed_file.write_text(seed_content)
        output_file = tmp_path / "output.txt"

        with patch("rich.console.Console.print"):
            batch_processor.process(
                input_file=seed_file,
                wordlist_type="subdomain",
                output=output_file,
                length=30,
                provider=DEFAULT_PROVIDER,
                batch_size=1,
            )

        assert output_file.exists()

    @pytest.mark.integration
    def test_batch_error_handling(self, batch_processor, tmp_path):
        with patch("rich.console.Console.print") as mock_print:
            batch_processor.process(
                input_file=tmp_path / "nonexistent.txt",
                wordlist_type=DEFAULT_WORDLIST_TYPE,
                output=None,
                length=50,
                provider=DEFAULT_PROVIDER,
                batch_size=5,
            )

        mock_print.assert_any_call(
            f"[red]File not found: {tmp_path / 'nonexistent.txt'}[/red]"
        )

    @pytest.mark.integration
    def test_batch_progress_tracking(self, batch_processor, seed_file, tmp_path):
        output_file = tmp_path / "output.txt"

        with patch("rich.console.Console.print") as mock_print:
            batch_processor.process(
                input_file=seed_file,
                wordlist_type=DEFAULT_WORDLIST_TYPE,
                output=output_file,
                length=50,
                provider=DEFAULT_PROVIDER,
                batch_size=2,
            )

        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Found 4 seed words" in call for call in print_calls)
        assert any("Generated" in call for call in print_calls)

    @pytest.mark.integration
    def test_batch_with_generator_failure(self, batch_processor, seed_file, tmp_path):
        output_file = tmp_path / "output.txt"

        batch_processor.llm_factory.create.return_value.generate_words.side_effect = [
            GENERATED_WORDS,
            RuntimeError("API error"),
            GENERATED_WORDS,
        ]

        with patch("rich.console.Console.print") as mock_print:
            batch_processor.process(
                input_file=seed_file,
                wordlist_type=DEFAULT_WORDLIST_TYPE,
                output=output_file,
                length=50,
                provider=DEFAULT_PROVIDER,
                batch_size=2,
            )

        assert output_file.exists()

        print_calls = [str(call) for call in mock_print.call_args_list]
        assert any("Warning" in call for call in print_calls)

    @pytest.mark.integration
    def test_batch_output_content(self, batch_processor, tmp_path):
        seed_file = tmp_path / "seeds.txt"
        seed_content = "test\n"
        seed_file.write_text(seed_content)
        output_file = tmp_path / "output.txt"

        batch_processor.llm_factory.create.return_value.generate_words.return_value = [
            "testword1",
            "testword2",
            "testword3",
        ]

        with patch("rich.console.Console.print"):
            batch_processor.process(
                input_file=seed_file,
                wordlist_type=DEFAULT_WORDLIST_TYPE,
                output=output_file,
                length=50,
                provider=DEFAULT_PROVIDER,
                batch_size=5,
            )

        assert output_file.exists()
        content = output_file.read_text()
        assert content == "testword1\ntestword2\ntestword3\n"

    @pytest.mark.integration
    def test_batch_deduplication(self, batch_processor, tmp_path):
        seed_file = tmp_path / "seeds.txt"
        seed_content = "seed1\nseed2\n"
        seed_file.write_text(seed_content)
        output_file = tmp_path / "output.txt"

        batch_processor.llm_factory.create.return_value.generate_words.return_value = [
            "word1",
            "word2",
            "word1",
        ]

        with patch("rich.console.Console.print"):
            batch_processor.process(
                input_file=seed_file,
                wordlist_type=DEFAULT_WORDLIST_TYPE,
                output=output_file,
                length=50,
                provider=DEFAULT_PROVIDER,
                batch_size=1,
            )

        content = output_file.read_text().strip().split("\n")
        assert len(content) == 2
        assert content == ["word1", "word2"]
