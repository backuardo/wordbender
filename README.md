![Wordbender Banner](banner.png)

# Wordbender

[![CI](https://github.com/backuardo/wordbender/actions/workflows/ci.yml/badge.svg)](https://github.com/backuardo/wordbender/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![MyPy checked](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)
[![Security: bandit](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)

Extensible LLM-powered wordlist generator for penetration testing. Creates intelligent, context-aware wordlists using AI to understand seed word relationships. Highly configurable with support for multiple wordlist types and LLM providers.

## What This Tool Does

Wordbender **does not** crack passwords, discover subdomains, or find directories directly. Instead, it generates intelligent wordlists based on your input that serve as input for other security tools:

- **For Password Cracking**: Generates base words that Hashcat will mutate with rules (adding numbers, special characters, capitalization patterns)
- **For Subdomain Discovery**: Creates potential subdomain names that tools like Gobuster will test against DNS servers
- **For Directory/File Brute-Forcing**: Generates paths that tools like ffuf, wfuzz, or dirbuster will test on web servers
- **For Cloud Resource Enumeration**: Creates realistic cloud resource names (S3 buckets, storage accounts, etc.) that tools like S3Scanner will test

Think of Wordbender as the "smart wordlist creator" that understands context and relationships, making your other tools more effective.

## Features

- **Multiple Wordlist Types**: Generate password base words, subdomain names, directory/file paths, or cloud resource names
- **AI-Powered Context Understanding**: Uses Claude, GPT-4, and other models to understand relationships between seed words
- **Smart Word Generation**: Creates semantically related words, variations, and compounds based on your input
- **Tool-Ready Output**: Generates wordlists in formats directly usable by Hashcat, Gobuster, ffuf, and other tools
- **Flexible Operation Modes**: Interactive CLI with helpful prompts, direct generation, or batch processing
- **Validation for Tool Compatibility**: Ensures generated words meet the requirements of target tools
- **Extensible**: Easy to add new wordlist types or LLM providers

## Installation

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wordbender.git
cd wordbender
```

2. Install dependencies using uv:
```bash
uv sync
```

3. Create a `.env` file with your API keys:
```bash
# This will create a .env.example file
uv run wordbender.py config --setup

# Copy the example file and add your keys
cp .env.example .env
```

4. Edit `.env` and add at least one API key:
```bash
# Wordbender API keys
#
# Add your API keys below:

# OpenAI
OPENAI_API_KEY=

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-key-here

# OpenRouter
OPENROUTER_API_KEY=your-openrouter-key-here

# Custom
CUSTOM_API_KEY=
```

## Usage

### Interactive Mode (Recommended for beginners)

The easiest way to use Wordbender is through interactive mode:

```bash
uv run wordbender.py
```

This will:
1. Display available wordlist types
2. Prompt you to select a type
3. Ask for seed words
4. Let you choose generation options
5. Select an LLM provider and model
6. Generate and save your wordlist

### Direct Generation

Generate wordlists directly from the command line:

```bash
# Generate password wordlist with specific seeds
uv run wordbender.py generate password -s john -s smith -s acme -l 200

# Generate subdomain wordlist
uv run wordbender.py generate subdomain -s google -s tech -l 100

# Generate directory/file wordlist
uv run wordbender.py generate directory -s wordpress -s blog -s php -l 200

# Generate cloud resource wordlist
uv run wordbender.py generate cloud-resource -s tesla -s aws -s s3 -l 150

# Specify output file
uv run wordbender.py generate password -s admin -o custom_passwords.txt

# Append to existing file
uv run wordbender.py generate subdomain -s api -s dev -o subdomains.txt --append
```

### Batch Processing

Process multiple seed word sets from a file:

```bash
# Create a seed file
cat > seeds.txt << EOF
apple
microsoft
google
amazon
EOF

# Generate wordlists for each seed
uv run wordbender.py batch seeds.txt subdomain

# With custom options
uv run wordbender.py batch seeds.txt password -l 150 -o batch_output.txt
```

### Configuration Management

```bash
# Show current configuration
uv run wordbender.py config --show

# Run setup wizard (interactive configuration)
uv run wordbender.py config --setup

# Set a specific API key
uv run wordbender.py config --set-key anthropic YOUR_API_KEY

# Set default preferences
uv run wordbender.py config --set-preference default_provider anthropic
uv run wordbender.py config --set-preference default_wordlist_length 150

# Reset all preferences to defaults
uv run wordbender.py config --reset
```

## Wordlist Types

### Password Wordlists
- **Purpose**: Generate base words that Hashcat will mutate into thousands of password variations
- **What it creates**: Clean, alphanumeric base words (3-30 characters) without numbers or special characters
- **How it's used**: Fed into Hashcat with rule files that add numbers, symbols, and capitalization patterns
- **Example flow**: "john" → Hashcat rules → "John123!", "j0hn@2023", "JOHN_98", etc.
- **Output**: `password_base_wordlist.txt`

### Subdomain Wordlists
- **Purpose**: Generate potential subdomain names for DNS enumeration tools
- **What it creates**: DNS-compliant labels (lowercase, alphanumeric with hyphens)
- **How it's used**: Fed into tools like Gobuster or ffuf that test each word against the target domain
- **Example flow**: "api-staging" → Gobuster → tests "api-staging.target.com"
- **Output**: `subdomain_wordlist.txt`

### Directory/File Wordlists
- **Purpose**: Generate paths for web directory and file brute-forcing
- **What it creates**: URL-safe paths including directories, files with extensions, and common web patterns
- **How it's used**: Fed into tools like ffuf, wfuzz, or dirbuster that test each path on the target server
- **Example flow**: "api/v1/users" → ffuf → tests "https://target.com/api/v1/users"
- **Output**: `directory_wordlist.txt`

### Cloud Resource Wordlists
- **Purpose**: Generate realistic cloud resource names for enumeration (S3 buckets, storage accounts, etc.)
- **What it creates**: Cloud provider-compliant resource names using company abbreviations and realistic patterns
- **How it's used**: Fed into tools like S3Scanner, CloudBrute, or bucket-stream that test for exposed resources
- **Example flow**: "tesla-backups-prod" → S3Scanner → tests "s3://tesla-backups-prod"
- **Output**: `cloud_resource_wordlist.txt`

## Supported LLM Providers and Models

### Anthropic (Direct API)
- Claude 3 Opus (`claude-3-opus-20240229`)
- Claude 3 Sonnet (`claude-3-sonnet-20240229`)
- Claude 3 Haiku (`claude-3-haiku-20240307`)
- Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`)
- Claude 3.5 Haiku (`claude-3-5-haiku-20241022`)
- Claude Opus 4 (`claude-opus-4-20250514`)
- Claude Sonnet 4 (`claude-sonnet-4-20250514`)

### OpenRouter
- Claude 3 Opus (`anthropic/claude-3-opus`)
- GPT-4 Turbo (`openai/gpt-4-turbo-preview`)

## Command Reference

### Global Options
- `-h, --help`: Show help message

### Generate Command
```bash
uv run wordbender.py generate [OPTIONS] WORDLIST_TYPE
```

Options:
- `-s, --seed TEXT`: Seed word(s) to base generation on (required, multiple allowed)
- `-l, --length INTEGER`: Number of words to generate (default: 100)
- `-o, --output PATH`: Output file path (default: auto-generated based on type)
- `--append`: Append to output file instead of overwriting
- `-p, --provider TEXT`: LLM provider to use
- `-m, --model TEXT`: Specific model to use
- `-i, --instructions TEXT`: Additional instructions for the LLM
- `--dry-run`: Preview the prompt without making API calls

### Batch Command
```bash
uv run wordbender.py batch [OPTIONS] SEED_FILE WORDLIST_TYPE
```

Options:
- `-l, --length INTEGER`: Words to generate per seed (default: 100)
- `-o, --output PATH`: Output file path
- `-p, --provider TEXT`: LLM provider to use
- `-b, --batch-size INTEGER`: Seeds to process per batch (default: 5)
- `--dry-run`: Preview the prompt without making API calls

### Config Command
```bash
uv run wordbender.py config [OPTIONS]
```

Options:
- `--setup`: Run interactive setup wizard
- `--show`: Display current configuration
- `--set-key TEXT TEXT`: Set API key for a provider
- `--set-preference TEXT TEXT`: Set a preference value
- `--reset`: Reset all preferences to defaults

## Examples

### Complete Security Assessment Workflow

1. **Gather target information** (reconnaissance phase):
   - Personal details, company info, technologies used, etc.

2. **Generate password base wordlist**:
```bash
uv run wordbender.py generate password \
  -s johnsmith -s acmecorp -s chicago -s bears -s fluffy \
  -l 500 -o acme_passwords.txt
```

3. **Feed into Hashcat for password cracking**:
```bash
# Crack NTLM hashes with word mutations
hashcat -a 0 -m 1000 hashes.txt acme_passwords.txt -r rules/best64.rule

# Hybrid attack with 4-digit years
hashcat -a 6 -m 1000 hashes.txt acme_passwords.txt ?d?d?d?d
```

4. **Generate subdomain wordlist**:
```bash
uv run wordbender.py generate subdomain \
  -s acme -s corp -s prod -s staging -s api \
  -l 200 -o acme_subdomains.txt
```

5. **Feed into subdomain enumeration tools**:
```bash
# DNS enumeration with Gobuster
gobuster dns -d acmecorp.com -w acme_subdomains.txt -t 50

# HTTP/HTTPS enumeration with ffuf
ffuf -u https://FUZZ.acmecorp.com -w acme_subdomains.txt
```

6. **Generate directory/file wordlist**:
```bash
uv run wordbender.py generate directory \
  -s acme -s wordpress -s php -s apache -s backup \
  -l 300 -o acme_directories.txt
```

7. **Feed into directory brute-forcing tools**:
```bash
# Directory enumeration with ffuf
ffuf -u https://acmecorp.com/FUZZ -w acme_directories.txt -mc 200,301,302,403

# With wfuzz
wfuzz -c -z file,acme_directories.txt --hc 404 https://acmecorp.com/FUZZ

# With gobuster
gobuster dir -u https://acmecorp.com -w acme_directories.txt -x php,bak,zip
```

8. **Generate cloud resource wordlist**:
```bash
uv run wordbender.py generate cloud-resource \
  -s acme -s acmecorp -s prod -s backup -s data \
  -l 300 -o acme_cloud_resources.txt
```

9. **Feed into cloud enumeration tools**:
```bash
# S3 bucket enumeration
python S3Scanner.py --list acme_cloud_resources.txt

# Multi-cloud enumeration
cloud_enum -k acme_cloud_resources.txt -t 10

# Check specific buckets
while read bucket; do
  aws s3 ls s3://$bucket --no-sign-request 2>/dev/null && echo "FOUND: $bucket"
done < acme_cloud_resources.txt
```

### Using Different Providers

```bash
# Use Anthropic directly with Claude 3.5 Sonnet
uv run wordbender.py generate password \
  -s admin -p anthropic -m claude-3-5-sonnet-20241022

# Use OpenRouter with GPT-4
uv run wordbender.py generate subdomain \
  -s api -p openrouter -m openai/gpt-4-turbo-preview

# Interactive mode will show all available providers and models
uv run wordbender.py
```

### Preview Before Generation

Use `--dry-run` to preview prompts before making API calls:

```bash
# Preview what would be sent to the LLM
uv run wordbender.py generate password -s admin -s test --dry-run

# Also works with batch processing
uv run wordbender.py batch seeds.txt subdomain --dry-run
```

## Troubleshooting

### No API Keys Configured
If you see "No API keys configured!", ensure:
1. You have created a `.env` file (not just `.env.example`)
2. At least one API key is properly set in the `.env` file
3. The API key variable names match exactly (e.g., `ANTHROPIC_API_KEY`)

### Rate Limiting
If you encounter rate limiting:
- The tool automatically retries with exponential backoff
- Consider using batch processing with smaller batch sizes
- Switch to a different provider temporarily

### Invalid Words Generated
Each wordlist type has specific validation rules:
- **Passwords**: Only alphanumeric, 3-30 characters
- **Subdomains**: Lowercase, alphanumeric with hyphens (not at start/end)
- **Directories**: Alphanumeric, hyphens, underscores, dots, tildes, forward slashes
- **Cloud Resources**: Lowercase, alphanumeric with hyphens and underscores (not at start/end), 3-63 characters

Words that don't meet criteria are automatically filtered out.

## Development

### Running Tests

```bash
# Install test dependencies (and dev tools)
uv sync --group dev --group test

# Run all tests
uv run pytest

# Run unit tests only
uv run pytest tests/unit

# Run integration tests only
uv run pytest tests/integration

# Run tests with coverage report
uv run pytest --cov

# Run tests in verbose mode
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_config.py

# Run tests matching a pattern
uv run pytest -k "test_password"
```

### Test Structure

The test suite is organized into:
- **Unit Tests** (`tests/unit/`): Test individual components in isolation
  - Configuration management
  - Wordlist generators
  - LLM services
  - Factory implementations
- **Integration Tests** (`tests/integration/`): Test complete workflows
  - End-to-end generation flows
  - Configuration and API key management
  - Batch processing

### Development Tools

This project uses modern Python development tools for code quality:

- **Ruff**: Fast linter and formatter (replaces black, isort, flake8)
- **MyPy**: Static type checking for better code reliability
- **Bandit**: Security vulnerability scanning
- **Pre-commit**: Automated hooks to run tools before commits

### Running Development Tools

```bash
# Format, lint, and type check code (run before committing)
uv run ruff check --fix . && uv run ruff format . && uv run mypy . && uv run bandit -c pyproject.toml -r .

# Individual tools
uv run ruff format .    # Format code
uv run ruff check .     # Lint code
uv run ruff check --fix . # Lint and fix issues
uv run mypy .           # Type checking
uv run bandit -c pyproject.toml -r . # Security linting

# Pre-commit hooks (recommended)
uv run pre-commit install      # Install hooks
uv run pre-commit run --all-files  # Run all hooks manually
```

### Adding New Wordlist Types

1. Create a new file in `wordlist_generators/`
2. Inherit from `WordlistGenerator` base class
3. Implement required methods:
   - `_get_default_output_path()`
   - `_get_system_prompt()`
   - `_validate_word()`
4. The new type will be automatically discovered

### Adding New LLM Providers

1. Create a new file in `llm_services/`
2. Inherit from `LlmService` base class
3. Implement required properties and methods:
   - `model_name` property
   - `provider` property
   - `_call_api()` method
4. Add the provider to `LlmProvider` enum if needed
