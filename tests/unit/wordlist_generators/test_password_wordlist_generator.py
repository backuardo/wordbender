from pathlib import Path

import pytest

from tests.test_constants import PASSWORD_MAX_LENGTH as MAX_LENGTH
from tests.test_constants import PASSWORD_MIN_LENGTH as MIN_LENGTH
from tests.test_constants import PASSWORD_OUTPUT_FILE as DEFAULT_OUTPUT_FILE
from wordlist_generators.password_wordlist_generator import PasswordWordlistGenerator


class TestPasswordWordlistGenerator:

    @pytest.fixture
    def generator(self):
        return PasswordWordlistGenerator()

    def test_initialization_behavior(self, generator):
        assert generator.output_file.name == DEFAULT_OUTPUT_FILE
        assert generator.MIN_LENGTH > 0
        assert generator.MAX_LENGTH > generator.MIN_LENGTH

        custom_path = Path("/custom/passwords.txt")
        custom_generator = PasswordWordlistGenerator(output_file=custom_path)
        assert custom_generator.output_file == custom_path

    def test_get_system_prompt(self, generator):
        prompt = generator._get_system_prompt()
        assert "expert in generating base wordlists for password cracking" in prompt
        assert "{seed_words}" in prompt
        assert "{wordlist_length}" in prompt
        assert "Hashcat" in prompt
        assert "alphanumeric base words" in prompt

    def test_validate_word_valid(self, generator):
        valid_words = [
            "password",
            "test123",
            "ABC",
            "a" * MAX_LENGTH,
            "MixedCase123",
            "UPPERCASE",
            "lowercase",
        ]

        for word in valid_words:
            assert generator._validate_word(word), f"'{word}' should be valid"

    def test_validate_word_invalid(self, generator):
        invalid_words = [
            "",
            "ab",
            "a" * (MAX_LENGTH + 1),
            "pass@word",
            "pass-word",
            "pass_word",
            "pass word",
            "påssword",
            "😀",
        ]

        for word in invalid_words:
            assert not generator._validate_word(word), f"'{word}' should be invalid"

    def test_get_seed_hints(self, generator):
        hints = generator.get_seed_hints()
        assert "Personal info" in hints
        assert "First name" in hints
        assert "Important dates" in hints
        assert "Family & pets" in hints
        assert "Locations" in hints
        assert "Interests" in hints
        assert "Example:" in hints

    def test_get_usage_instructions(self, generator):
        instructions = generator.get_usage_instructions()
        assert "hashcat" in instructions
        assert "rules/best64.rule" in instructions
        assert "hybrid attacks" in instructions
        assert "base words" in instructions

    def test_build_prompt_integration(self, generator):
        generator.add_seed_words("john", "smith", "chicago")
        generator.wordlist_length = 50

        prompt = generator.build_prompt()
        assert "john, smith, chicago" in prompt
        assert "50" in prompt
        assert "password cracking" in prompt

    def test_build_prompt_with_additional_instructions(self, generator):
        generator.add_seed_words("test")
        generator.additional_instructions = "Focus on sports teams"

        prompt = generator.build_prompt()
        assert "Additional instructions: Focus on sports teams" in prompt

    @pytest.mark.parametrize(
        "length,expected",
        [
            (MIN_LENGTH - 1, False),
            (MIN_LENGTH, True),
            (15, True),
            (MAX_LENGTH, True),
            (MAX_LENGTH + 1, False),
        ],
    )
    def test_validate_word_length_boundaries(self, generator, length, expected):
        word = "a" * length if length > 0 else ""
        assert generator._validate_word(word) == expected

    @pytest.mark.parametrize(
        "word,expected",
        [
            ("abc123", True),
            ("ABC123", True),
            ("123abc", True),
            ("abcDEF", True),
            ("abc-123", False),
            ("abc_123", False),
            ("abc@123", False),
            ("abc 123", False),
        ],
    )
    def test_validate_word_character_patterns(self, generator, word, expected):
        assert generator._validate_word(word) == expected
