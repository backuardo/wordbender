from pathlib import Path

import pytest

from tests.test_constants import DIRECTORY_MAX_LENGTH as MAX_LENGTH
from tests.test_constants import DIRECTORY_MIN_LENGTH as MIN_LENGTH
from tests.test_constants import DIRECTORY_OUTPUT_FILE as DEFAULT_OUTPUT_FILE
from wordlist_generators.directory_wordlist_generator import (
    DirectoryWordlistGenerator,
)


class TestDirectoryWordlistGenerator:
    @pytest.fixture
    def generator(self):
        return DirectoryWordlistGenerator()

    def test_initialization_behavior(self, generator):
        assert generator.output_file.name == DEFAULT_OUTPUT_FILE
        assert generator.MIN_LENGTH == MIN_LENGTH
        assert generator.MAX_LENGTH == MAX_LENGTH

        custom_path = Path("/custom/directories.txt")
        custom_generator = DirectoryWordlistGenerator(output_file=custom_path)
        assert custom_generator.output_file == custom_path

    def test_get_system_prompt_contains_required_placeholders(self, generator):
        prompt = generator._get_system_prompt()
        assert "{seed_words}" in prompt
        assert "{wordlist_length}" in prompt

    def test_validate_word_valid(self, generator):
        valid_paths = [
            "admin",
            "backup",
            "config.php",
            "test123",
            "api_v1",
            ".htaccess",
            ".env",
            "backup.zip",
            "dump.sql",
            "node_modules",
            "test-file.bak",
            "~backup",
            "api/v1",
            "api/v2/users",
            "static/js/app.js",
            ".git/config",
            "wp-content/uploads",
            "a" * MAX_LENGTH,
        ]

        for path in valid_paths:
            assert generator._validate_word(path), f"'{path}' should be valid"

    def test_validate_word_invalid(self, generator):
        invalid_paths = [
            "",
            ".",
            "..",
            "../etc/passwd",
            "admin/../../etc",
            "/admin",
            "admin/",
            "a" * (MAX_LENGTH + 1),
            "admin@test",
            "admin test",
            "admin<script>",
            "admin|test",
            "tëst",
        ]

        for path in invalid_paths:
            assert not generator._validate_word(path), f"'{path}' should be invalid"

    def test_process_generated_words_deduplication(self, generator):
        words = ["admin", "backup", "admin", "config", "backup", "test"]
        processed = generator._process_generated_words(words)

        assert len(processed) == 4
        assert set(processed) == {"admin", "backup", "config", "test"}

    def test_process_generated_words_filters_invalid(self, generator):
        words = [
            "valid",
            "..",
            "also-valid",
            "/invalid",
            "admin/",
            "good.php",
            "api/v1",
        ]
        processed = generator._process_generated_words(words)

        assert ".." not in processed
        assert "/invalid" not in processed
        assert "admin/" not in processed
        assert "api/v1" in processed
        assert all(generator._validate_word(word) for word in processed)

    def test_get_seed_hints_returns_string(self, generator):
        hints = generator.get_seed_hints()
        assert isinstance(hints, str)
        assert len(hints) > 0

    def test_get_usage_instructions_returns_string(self, generator):
        instructions = generator.get_usage_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_build_prompt_includes_seed_words(self, generator):
        test_seeds = ["wordpress", "acmecorp", "php"]
        generator.add_seed_words(*test_seeds)
        generator.wordlist_length = 100

        prompt = generator.build_prompt()
        assert all(seed in prompt for seed in test_seeds)
        assert str(generator.wordlist_length) in prompt

    def test_build_prompt_with_additional_instructions(self, generator):
        generator.add_seed_words("test")
        test_instruction = "Focus on API endpoints"
        generator.additional_instructions = test_instruction

        prompt = generator.build_prompt()
        assert test_instruction in prompt

    @pytest.mark.parametrize(
        "length,expected",
        [
            (MIN_LENGTH - 1, False),
            (MIN_LENGTH, True),
            (100, True),
            (MAX_LENGTH, True),
            (MAX_LENGTH + 1, False),
        ],
    )
    def test_validate_word_length_boundaries(self, generator, length, expected):
        word = "a" * length if length > 0 else ""
        assert generator._validate_word(word) == expected

    @pytest.mark.parametrize(
        "path,expected",
        [
            ("admin", True),
            ("admin.php", True),
            ("admin-panel", True),
            ("admin_panel", True),
            (".git", True),
            (".env", True),
            ("backup~", True),
            ("api/v1", True),
            ("static/css/main.css", True),
            (".git/config", True),
            (".", False),
            ("..", False),
            ("../admin", False),
            ("/admin", False),
            ("admin/", False),
            ("admin/../etc", False),
        ],
    )
    def test_validate_word_patterns(self, generator, path, expected):
        assert generator._validate_word(path) == expected

    def test_validation_regex_accepts_valid_characters(self, generator):
        pattern = generator.VALID_CHARS_PATTERN

        valid_cases = [
            "admin",
            "test-123",
            "test_123",
            "file.php",
            "~backup",
            ".htaccess",
            "api/v1",
            "static/js/app.js",
        ]
        for case in valid_cases:
            assert pattern.match(case), f"Pattern should match '{case}'"

    def test_validation_regex_rejects_invalid_characters(self, generator):
        pattern = generator.VALID_CHARS_PATTERN

        invalid_cases = ["admin test", "admin@test", "admin|test", "admin<script>"]
        for case in invalid_cases:
            assert not pattern.match(case), f"Pattern should not match '{case}'"

    def test_default_output_path_returns_expected_filename(self, generator):
        default_path = generator._get_default_output_path()
        assert default_path.name == DEFAULT_OUTPUT_FILE

    def test_process_generated_words_simulates_llm_output(self, generator):
        llm_output = [
            "admin",
            "api/v1",
            "api/v2/users",
            ".env",
            ".env.local",
            "build/static",
            "node_modules",
            "package.json",
            "package-lock.json",
            "tsconfig.json",
            "dist/js/app.js",
            "public/assets",
            ".vercel/output",
            "backup.zip",
            "dump.sql",
            ".git/config",
            "wp-content/uploads",
            "static/css/main.css",
            "config/database.yml",
            "logs/error.log",
        ]

        processed = generator._process_generated_words(llm_output)

        assert len(processed) == len(llm_output)
        assert all(generator._validate_word(word) for word in processed)
        assert "api/v1" in processed
        assert ".git/config" in processed
        assert "build/static" in processed

    def test_process_generated_words_handles_mixed_valid_invalid(self, generator):
        valid_paths = ["admin", "api/v1", ".env", "backup.zip", ".git/config"]
        invalid_paths = [
            "/admin",
            "api/v1/",
            "../etc/passwd",
            "admin panel",
            "test@file",
            "",
            "a" * 256,
        ]

        llm_output = valid_paths + invalid_paths
        processed = generator._process_generated_words(llm_output)

        for path in valid_paths:
            assert path in processed

        for path in invalid_paths:
            assert path not in processed

        assert len(processed) == len(valid_paths)

    def test_validation_pattern_allows_forward_slashes(self, generator):
        common_directory_paths = [
            "api/v1",
            "api/v2/users",
            "static/js/app.js",
            ".git/config",
            "wp-content/uploads",
            "build/static/css",
            "dist/assets/images",
            "public/uploads/2024",
        ]

        for path in common_directory_paths:
            assert generator._validate_word(path), (
                f"Path '{path}' should be valid but was rejected. "
                f"This would cause all LLM-generated paths with slashes to fail."
            )
