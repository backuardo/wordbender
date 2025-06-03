from pathlib import Path

import pytest

from tests.test_constants import CLOUD_RESOURCE_MAX_LENGTH as MAX_LENGTH
from tests.test_constants import CLOUD_RESOURCE_MIN_LENGTH as MIN_LENGTH
from tests.test_constants import CLOUD_RESOURCE_OUTPUT_FILE as DEFAULT_OUTPUT_FILE
from wordlist_generators.cloud_resource_wordlist_generator import (
    CloudResourceWordlistGenerator,
)


class TestCloudResourceWordlistGenerator:
    @pytest.fixture
    def generator(self):
        return CloudResourceWordlistGenerator()

    def test_initialization_behavior(self, generator):
        assert generator.output_file.name == DEFAULT_OUTPUT_FILE
        assert generator.MIN_LENGTH == MIN_LENGTH
        assert generator.MAX_LENGTH == MAX_LENGTH

        custom_path = Path("/custom/cloud_resources.txt")
        custom_generator = CloudResourceWordlistGenerator(output_file=custom_path)
        assert custom_generator.output_file == custom_path

    def test_prompt_has_required_placeholders(self, generator):
        prompt = generator._get_system_prompt()
        assert "{seed_words}" in prompt
        assert "{wordlist_length}" in prompt

    def test_validate_word_valid_cases(self, generator):
        valid_resources = [
            "abc",
            "api-bucket",
            "dev_server",
            "test123",
            "staging-v2",
            "us-east-1",
            "a" * MAX_LENGTH,
            "123",
            "test-123-api",
            "test_123_api",
            "prod-backup-2024",
            "company_data_lake",
        ]

        for resource in valid_resources:
            assert generator._validate_word(resource), f"'{resource}' should be valid"

    def test_validate_word_invalid_cases(self, generator):
        invalid_resources = [
            "",
            "-api",
            "api-",
            "_api",
            "api_",
            "a" * (MAX_LENGTH + 1),
            "aa",
            "api--test",
            "api__test",
            "api-_test",
            "api_-test",
            "api.test",
            "api test",
            "api@test",
        ]

        for resource in invalid_resources:
            assert not generator._validate_word(resource), (
                f"'{resource}' should be invalid"
            )

    def test_process_converts_to_lowercase(self, generator):
        words = ["API-BUCKET", "Dev_Server", "TEST123", "Mixed-Case_Name"]
        processed = generator._process_generated_words(words)

        expected = ["api-bucket", "dev_server", "test123", "mixed-case_name"]
        assert processed == expected

    def test_process_filters_invalid_words(self, generator):
        words = [
            "valid",
            "-invalid",
            "also-valid",
            "invalid-",
            "--bad",
            "good",
            "test__bad",
            "ok_name",
        ]
        processed = generator._process_generated_words(words)

        assert processed == ["valid", "also-valid", "good", "ok_name"]

    def test_integration_with_base_class(self, generator):
        generator.add_seed_words("acmecorp", "aws", "s3", "production")
        generator.wordlist_length = 100

        prompt = generator.build_prompt()
        assert "acmecorp, aws, s3, production" in prompt
        assert "100" in prompt

    @pytest.mark.parametrize(
        "length,expected",
        [
            (0, False),
            (MIN_LENGTH - 1, False),
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
        "resource,expected",
        [
            ("test", True),
            ("test-api", True),
            ("test_api", True),
            ("test-api-v2", True),
            ("test_api_v2", True),
            ("123-test", True),
            ("123_test", True),
            ("-test", False),
            ("_test", False),
            ("test-", False),
            ("test_", False),
            ("te--st", False),
            ("te__st", False),
            ("te-_st", False),
            ("te_-st", False),
            ("mix-under_score", True),
        ],
    )
    def test_validate_word_special_character_patterns(
        self, generator, resource, expected
    ):
        assert generator._validate_word(resource) == expected

    def test_case_insensitive_validation(self, generator):
        assert generator._validate_word("TEST")
        assert generator._validate_word("test")
        assert generator._validate_word("TeSt")

    def test_unicode_characters_rejected(self, generator):
        assert not generator._validate_word("tëst")
        assert not generator._validate_word("😀")
        assert not generator._validate_word("test™")

    def test_detailed_prompt_has_required_placeholders(self, generator):
        detailed_prompt = generator._get_detailed_system_prompt()
        assert "{seed_words}" in detailed_prompt
        assert "{wordlist_length}" in detailed_prompt
