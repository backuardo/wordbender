import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from wordlist_generators.wordlist_generator import WordlistGenerator

TEST_WORDLIST_FILE = "test_wordlist.txt"
TEST_PROMPT_TEMPLATE = "Test prompt with {seed_words} and {wordlist_length}"
TEST_HINTS = "Test hints"
TEST_INSTRUCTIONS = "Test instructions"
TEST_WORDS = ["word1", "word2", "word3"]
DEFAULT_WORDLIST_LENGTH = 100
MIN_WORD_LENGTH = 3


class ConcreteWordlistGenerator(WordlistGenerator):

    def _get_default_output_path(self) -> Path:
        return Path(TEST_WORDLIST_FILE)

    def _get_system_prompt(self) -> str:
        return TEST_PROMPT_TEMPLATE

    def _validate_word(self, word: str) -> bool:
        return len(word) >= MIN_WORD_LENGTH

    def get_seed_hints(self) -> str:
        return TEST_HINTS

    def get_usage_instructions(self) -> str:
        return TEST_INSTRUCTIONS


class TestWordlistGenerator:

    @pytest.fixture
    def generator(self):
        return ConcreteWordlistGenerator()

    def test_initialization(self, generator):
        assert generator.seed_words == []
        assert generator.generated_words == []
        assert generator.wordlist_length == DEFAULT_WORDLIST_LENGTH
        assert generator.output_file == Path(TEST_WORDLIST_FILE)
        assert generator.additional_instructions is None

    def test_initialization_with_custom_output(self):
        custom_path = Path("/custom/path/wordlist.txt")
        generator = ConcreteWordlistGenerator(output_file=custom_path)
        assert generator.output_file == custom_path

    def test_seed_words_property(self, generator):
        generator._seed_words = ["test1", "test2"]
        seeds = generator.seed_words
        seeds.append("test3")
        assert generator.seed_words == ["test1", "test2"]

    def test_generated_words_property(self, generator):
        generator._generated_words = TEST_WORDS[:2]
        words = generator.generated_words
        words.append("word3")
        assert generator.generated_words == TEST_WORDS[:2]

    def test_wordlist_length_setter_valid(self, generator):
        generator.wordlist_length = 50
        assert generator.wordlist_length == 50

    def test_wordlist_length_setter_invalid(self, generator):
        with pytest.raises(ValueError, match="Wordlist length must be positive"):
            generator.wordlist_length = 0

        with pytest.raises(ValueError, match="Wordlist length must be positive"):
            generator.wordlist_length = -10

    def test_output_file_setter(self, generator):
        new_path = Path("/new/path/wordlist.txt")
        generator.output_file = new_path
        assert generator.output_file == new_path

    def test_additional_instructions_handling(self, generator):
        instructions = "Generate only short words"
        generator.additional_instructions = instructions
        assert generator.additional_instructions == instructions

        generator.additional_instructions = None
        assert generator.additional_instructions is None

        generator.additional_instructions = ""
        assert generator.additional_instructions == ""

        generator.additional_instructions = "   \t\n  "
        assert generator.additional_instructions == "   \t\n  "

    def test_add_seed_words_valid(self, generator):
        generator.add_seed_words("word1", "word2", "word3")
        assert generator.seed_words == ["word1", "word2", "word3"]

        generator.add_seed_words("word4")
        assert generator.seed_words == ["word1", "word2", "word3", "word4"]

    def test_add_seed_words_with_whitespace(self, generator):
        generator.add_seed_words("  word1  ", "\tword2\n", " word3 ")
        assert generator.seed_words == ["word1", "word2", "word3"]

    def test_add_seed_words_empty(self, generator):
        with pytest.raises(ValueError, match="No valid seed words provided"):
            generator.add_seed_words("", "  ", "\t\n")

    def test_clear_seed_words(self, generator):
        generator.add_seed_words("word1", "word2")
        generator.clear_seed_words()
        assert generator.seed_words == []

    def test_build_prompt_no_seeds(self, generator):
        with pytest.raises(ValueError, match="No seed words provided"):
            generator.build_prompt()

    def test_build_prompt_basic(self, generator):
        generator.add_seed_words("test1", "test2")
        generator.wordlist_length = 50
        prompt = generator.build_prompt()
        assert prompt == "Test prompt with test1, test2 and 50"

    def test_build_prompt_with_additional_instructions(self, generator):
        generator.add_seed_words("test1", "test2")
        generator.wordlist_length = 50
        generator.additional_instructions = "Only short words"
        prompt = generator.build_prompt()
        expected = "Test prompt with test1, test2 and 50\n\nAdditional instructions: Only short words"
        assert prompt == expected

    def test_prompt_injection_protection(self, generator):
        problematic_seeds = [
            "normal",
            "word{malicious}",
            "test\ninjection",
            "word\\escape",
        ]
        generator.add_seed_words(*problematic_seeds)
        generator.wordlist_length = 10

        prompt = generator.build_prompt()
        assert "10" in prompt
        assert "normal" in prompt
        assert len(prompt) > 0

    def test_generate_success(self, generator):
        mock_service = Mock()
        mock_service.generate_words.return_value = ["word1", "word2", "word3", "in"]

        generator.add_seed_words("test")
        result = generator.generate(mock_service)

        assert result == ["word1", "word2", "word3"]
        assert generator.generated_words == ["word1", "word2", "word3"]
        mock_service.generate_words.assert_called_once()

    def test_generate_llm_error(self, generator):
        mock_service = Mock()
        mock_service.generate_words.side_effect = Exception("API error")

        generator.add_seed_words("test")
        with pytest.raises(
            RuntimeError, match="Failed to generate words from LLM: API error"
        ):
            generator.generate(mock_service)

    def test_generate_empty_response(self, generator):
        mock_service = Mock()
        mock_service.generate_words.return_value = []

        generator.add_seed_words("test")
        with pytest.raises(ValueError, match="LLM returned empty response"):
            generator.generate(mock_service)

    def test_generate_no_valid_words(self, generator):
        mock_service = Mock()
        mock_service.generate_words.return_value = ["a", "b", "c"]

        generator.add_seed_words("test")
        with pytest.raises(
            ValueError, match="No valid words generated after processing"
        ):
            generator.generate(mock_service)

    def test_process_generated_words(self, generator):
        words = ["valid1", "  valid2  ", "", "duplicate", "duplicate", "xx"]
        processed = generator._process_generated_words(words)

        assert processed == [
            "valid1",
            "valid2",
            "duplicate",
        ]

    @patch("builtins.print")
    def test_process_generated_words_warning(self, mock_print, generator):
        words = ["valid", "xx", "yy"]
        generator._process_generated_words(words)

        mock_print.assert_called_with("Warning: 2 words failed validation")

    def test_concurrent_modification_safety(self, generator):
        generator.add_seed_words("test1", "test2")
        seeds = generator.seed_words
        original_length = len(seeds)

        seeds.append("malicious")
        assert len(generator.seed_words) == original_length
        assert "malicious" not in generator.seed_words

        generator._generated_words = ["word1", "word2"]
        words = generator.generated_words
        words.clear()
        assert len(generator.generated_words) == 2

    def test_save_no_words(self, generator):
        with pytest.raises(ValueError, match="No words have been generated"):
            generator.save()

    def test_save_default_path(self, generator, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        generator._generated_words = TEST_WORDS
        generator.save()

        saved_file = tmp_path / TEST_WORDLIST_FILE
        assert saved_file.exists()
        assert saved_file.read_text() == "word1\nword2\nword3\n"

    def test_save_custom_path(self, generator, tmp_path):
        generator._generated_words = ["word1", "word2"]
        custom_path = tmp_path / "custom" / "wordlist.txt"
        generator.save(path=custom_path)

        assert custom_path.exists()
        assert custom_path.read_text() == "word1\nword2\n"

    def test_save_append_mode(self, generator, tmp_path):
        output_file = tmp_path / "wordlist.txt"
        output_file.write_text("existing1\nexisting2\n")

        generator._generated_words = ["new1", "new2"]
        generator.save(path=output_file, append=True)

        assert output_file.read_text() == "existing1\nexisting2\nnew1\nnew2\n"

    def test_save_create_parent_directory(self, generator, tmp_path):
        generator._generated_words = ["word1"]
        nested_path = tmp_path / "deep" / "nested" / "dir" / "wordlist.txt"
        generator.save(path=nested_path)

        assert nested_path.exists()
        assert nested_path.parent.exists()

    def test_save_directory_creation_error(self, generator, tmp_path):
        generator._generated_words = ["word1"]
        bad_path = tmp_path / "file_not_dir"
        bad_path.write_text("content")

        with pytest.raises(IOError, match="Failed to create directory"):
            generator.save(path=bad_path / "wordlist.txt")

    def test_large_wordlist_handling(self, generator):
        mock_service = Mock()
        large_wordlist = [f"word{i}" for i in range(10000)]
        mock_service.generate_words.return_value = large_wordlist

        generator.add_seed_words("test")
        result = generator.generate(mock_service)

        assert len(result) <= len(large_wordlist)
        assert all(generator._validate_word(w) for w in result)

    def test_unicode_handling(self, generator):
        mock_service = Mock()
        unicode_words = ["café", "naïve", "résumé", "validword", "münchen"]
        mock_service.generate_words.return_value = unicode_words

        generator.add_seed_words("test")
        result = generator.generate(mock_service)

        assert "validword" in result
        assert len(result) >= 1

    def test_empty_and_whitespace_seed_words(self, generator):
        with pytest.raises(ValueError, match="No valid seed words"):
            generator.add_seed_words("", "   ", "\t\n", "")

        generator.add_seed_words("valid", "", "  also_valid  ", "\tinvalid\n")
        assert len(generator.seed_words) >= 2
        assert "valid" in generator.seed_words
        assert "also_valid" in generator.seed_words

    @patch("pathlib.Path.open", side_effect=IOError("Permission denied"))
    def test_save_write_error(self, mock_open, generator, tmp_path):
        generator._generated_words = ["word1"]

        with pytest.raises(IOError, match="Failed to write to file"):
            generator.save(path=tmp_path / "wordlist.txt")
