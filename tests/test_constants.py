"""Shared test constants."""

# API Keys and Authentication
TEST_API_KEY = "test-key"
TEST_OPENROUTER_KEY = "test-openrouter-key"
TEST_ANTHROPIC_KEY = "test-anthropic-key"

# Model Names
TEST_MODEL_NAME = "test-model"
OPENROUTER_CLAUDE_OPUS_MODEL = "anthropic/claude-3-opus"
OPENROUTER_GPT4_MODEL = "openai/gpt-4-turbo-preview"
ANTHROPIC_CLAUDE3_OPUS_MODEL = "claude-3-opus-20240229"
ANTHROPIC_CLAUDE3_SONNET_MODEL = "claude-3-sonnet-20240229"
ANTHROPIC_CLAUDE3_HAIKU_MODEL = "claude-3-haiku-20240307"
ANTHROPIC_CLAUDE35_SONNET_MODEL = "claude-3-5-sonnet-20241022"
ANTHROPIC_CLAUDE35_HAIKU_MODEL = "claude-3-5-haiku-20241022"
ANTHROPIC_CLAUDE_OPUS4_MODEL = "claude-opus-4-20250514"
ANTHROPIC_CLAUDE_SONNET4_MODEL = "claude-sonnet-4-20250514"

# API URLs
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
CUSTOM_API_URL = "https://custom.api.com/v1/chat"

# HTTP Headers
ANTHROPIC_VERSION = "2023-06-01"
CONTENT_TYPE = "application/json"
DEFAULT_REFERER = "http://localhost"
DEFAULT_TITLE = "Wordlist Generator"

# Configuration
DEFAULT_PROVIDER = "openrouter"
DEFAULT_WORDLIST_TYPE = "password"
DEFAULT_WORDLIST_LENGTH = 100
TEST_TIMEOUT = 30
TEST_MAX_RETRIES = 3

# File Paths
PASSWORD_OUTPUT_FILE = "password_base_wordlist.txt"
SUBDOMAIN_OUTPUT_FILE = "subdomain_wordlist.txt"
DIRECTORY_OUTPUT_FILE = "directory_wordlist.txt"
CLOUD_RESOURCE_OUTPUT_FILE = "cloud_resource_wordlist.txt"
TEST_WORDLIST_FILE = "test_wordlist.txt"

# Validation Constants
PASSWORD_MIN_LENGTH = 3
PASSWORD_MAX_LENGTH = 30
SUBDOMAIN_MIN_LENGTH = 1
SUBDOMAIN_MAX_LENGTH = 63
DIRECTORY_MIN_LENGTH = 1
DIRECTORY_MAX_LENGTH = 255
CLOUD_RESOURCE_MIN_LENGTH = 3
CLOUD_RESOURCE_MAX_LENGTH = 63

# Test Data
SAMPLE_SEED_WORDS = ["test", "example", "demo"]
SAMPLE_WORDLIST = [
    "test123",
    "test@2024",
    "Example_Pass",
    "demo_secure",
    "TestExample",
]
GENERATED_WORDS = ["generated1", "generated2", "generated3"]

# Mock Responses
MOCK_LLM_RESPONSE = """test123
test@2024
Example_Pass
demo_secure
TestExample
invalid-word-123
test456
ExampleDemo
secure_demo"""

MOCK_OPENROUTER_RESPONSE = {
    "choices": [
        {
            "message": {
                "content": "test123\ntest@2024\nExample_Pass\ndemo_secure\nTestExample"
            }
        }
    ]
}

MOCK_ANTHROPIC_RESPONSE = {
    "content": [
        {
            "type": "text",
            "text": "test123\ntest@2024\nExample_Pass\ndemo_secure\nTestExample",
        }
    ]
}

# Service Discovery Constants
GENERATOR_DIR = "wordlist_generators"
LLM_SERVICES_DIR = "llm_services"
PASSWORD_GENERATOR_FILE = "password_wordlist_generator.py"
SUBDOMAIN_GENERATOR_FILE = "subdomain_wordlist_generator.py"
DIRECTORY_GENERATOR_FILE = "directory_wordlist_generator.py"
CLOUD_RESOURCE_GENERATOR_FILE = "cloud_resource_wordlist_generator.py"
OPENROUTER_SERVICE_FILE = "openrouter_llm_service.py"
ANTHROPIC_SERVICE_FILE = "anthropic_llm_service.py"
LLM_SERVICE_BASE_FILE = "llm_service.py"

# Test Prompt Templates
TEST_PROMPT_TEMPLATE = "Test prompt with {seed_words} and {wordlist_length}"
TEST_HINTS = "Test hints"
TEST_INSTRUCTIONS = "Test instructions"
