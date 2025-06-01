from pathlib import Path

import pytest

from wordlist_generators.subdomain_wordlist_generator import (
    SubdomainWordlistGenerator,
)

from tests.test_constants import SUBDOMAIN_MAX_LENGTH as MAX_LENGTH
from tests.test_constants import SUBDOMAIN_MIN_LENGTH as MIN_LENGTH
from tests.test_constants import SUBDOMAIN_OUTPUT_FILE as DEFAULT_OUTPUT_FILE


class TestSubdomainWordlistGenerator:

    @pytest.fixture
    def generator(self):
        return SubdomainWordlistGenerator()

    def test_initialization_behavior(self, generator):
        assert generator.output_file.name == DEFAULT_OUTPUT_FILE
        assert generator.MIN_LENGTH >= 1
        assert generator.MAX_LENGTH <= 63

        custom_path = Path("/custom/subdomains.txt")
        custom_generator = SubdomainWordlistGenerator(output_file=custom_path)
        assert custom_generator.output_file == custom_path

    def test_get_system_prompt(self, generator):
        prompt = generator._get_system_prompt()
        assert "subdomain wordlists for penetration testing" in prompt
        assert "{seed_words}" in prompt
        assert "{wordlist_length}" in prompt
        assert "api, dev, staging" in prompt
        assert "lowercase, alphanumeric, hyphens" in prompt

    def test_validate_word_valid(self, generator):
        valid_subdomains = [
            "a",
            "api",
            "dev-server",
            "test123",
            "staging-v2",
            "us-east-1",
            "a" * MAX_LENGTH,
            "123",
            "test-123-api",
            "API",
            "Dev-Server",
        ]

        for subdomain in valid_subdomains:
            assert generator._validate_word(subdomain), f"'{subdomain}' should be valid"

    def test_validate_word_invalid(self, generator):
        invalid_subdomains = [
            "",
            "-api",
            "api-",
            "a" * (MAX_LENGTH + 1),
            "api--test",
            "api_test",
            "api.test",
            "api test",
            "api@test",
            "😀",
            "tëst",
        ]

        for subdomain in invalid_subdomains:
            assert not generator._validate_word(
                subdomain
            ), f"'{subdomain}' should be invalid"

    def test_process_generated_words_lowercase(self, generator):
        words = ["API", "Dev-Server", "TEST123", "Mixed-Case"]
        processed = generator._process_generated_words(words)

        expected = ["api", "dev-server", "test123", "mixed-case"]
        assert processed == expected

    def test_process_generated_words_validation(self, generator):
        words = ["valid", "-invalid", "also-valid", "invalid-", "--bad", "good"]
        processed = generator._process_generated_words(words)

        assert processed == ["valid", "also-valid", "good"]

    def test_get_seed_hints(self, generator):
        hints = generator.get_seed_hints()
        assert "Company:" in hints
        assert "Industry:" in hints
        assert "Technology:" in hints
        assert "Geographic:" in hints
        assert "Products:" in hints
        assert "Example:" in hints

    def test_get_usage_instructions(self, generator):
        instructions = generator.get_usage_instructions()
        assert "gobuster" in instructions
        assert "ffuf" in instructions
        assert "subfinder" in instructions
        assert "Certificate transparency" in instructions
        assert "wildcard DNS" in instructions

    def test_build_prompt_integration(self, generator):
        generator.add_seed_words("acme", "cloud", "newyork")
        generator.wordlist_length = 100

        prompt = generator.build_prompt()
        assert "acme, cloud, newyork" in prompt
        assert "100" in prompt
        assert "subdomain wordlists" in prompt

    @pytest.mark.parametrize(
        "length,expected",
        [
            (0, False),
            (MIN_LENGTH, True),
            (32, True),
            (MAX_LENGTH, True),
            (MAX_LENGTH + 1, False),
        ],
    )
    def test_validate_word_length_boundaries(self, generator, length, expected):
        if length == 0:
            word = ""
        else:
            word = "a" * length
        assert generator._validate_word(word) == expected

    @pytest.mark.parametrize(
        "subdomain,expected",
        [
            ("test", True),
            ("test-api", True),
            ("test-api-v2", True),
            ("123-test", True),
            ("test-123", True),
            ("-test", False),
            ("test-", False),
            ("te--st", False),
            ("te_st", False),
            ("te.st", False),
            ("TEST", True),
        ],
    )
    def test_validate_word_patterns(self, generator, subdomain, expected):
        assert generator._validate_word(subdomain) == expected

    def test_validation_regex_pattern_behavior(self, generator):
        pattern = generator.VALID_CHARS_PATTERN

        valid_cases = ["a", "test", "test-123", "a1b2c3"]
        for case in valid_cases:
            assert pattern.match(case), f"Pattern should match '{case}'"

        # Note: uppercase handled elsewhere
        invalid_cases = ["-test", "test-", "TEST"]
        for case in invalid_cases:
            assert not pattern.match(case), f"Pattern should not match '{case}'"
