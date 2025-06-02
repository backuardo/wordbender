import re
from pathlib import Path
from textwrap import dedent

from wordlist_generators.prompt_templates import (
    PromptTemplate,
    create_simple_prompt,
)
from wordlist_generators.wordlist_generator import WordlistGenerator


class DirectoryWordlistGenerator(WordlistGenerator):
    """Generator for directory/file brute-forcing wordlists."""

    MIN_LENGTH = 1
    MAX_LENGTH = 255
    VALID_CHARS_PATTERN = re.compile(r"^[a-zA-Z0-9\-_.~/]+$")

    def __init__(self, output_file: Path | None = None):
        super().__init__(output_file)

    def _get_default_output_path(self) -> Path:
        """Return the default output path for directory wordlists."""
        return Path("directory_wordlist.txt")

    def _get_system_prompt(self) -> str:
        """Return the system prompt for directory/file generation."""
        focus_areas = [
            "Common directory patterns (admin, backup, config, logs, temp)",
            "Framework-specific paths (wp-admin, wp-content for WordPress)",
            "File extensions (.bak, .old, .config, .log, .zip)",
            "Environment indicators (dev, test, staging, prod)",
            "API endpoints (api/v1, rest, graphql)",
            "Hidden files and directories (.git, .env, .htaccess)",
            "Backup patterns (backup.zip, site.tar.gz, dump.sql)",
            "Technology-specific paths based on seed context",
        ]

        return create_simple_prompt(
            """\
            You are an expert in generating directory/file paths for web fuzzing tools.

            Given these seed words: {seed_words}

            Generate exactly {wordlist_length} directory and file paths for web bruteforcing.

            IMPORTANT FORMAT RULES:
            - NO leading slashes (correct: admin, api/v1, NOT: /admin, /api/v1)
            - Include both single-level and multi-level paths
            - Mix directories and files with extensions
            - Use only: letters, numbers, hyphens, underscores, dots, tildes, forward slashes

            Examples of valid paths:
            admin
            api/v1/users
            backup.zip
            .git/config
            static/js/app.js
            wp-content/uploads

            Focus on:
            {focus_areas}

            Output ONLY the paths, one per line, no explanations.\
            """,
            seed_words="{seed_words}",
            wordlist_length="{wordlist_length}",
            focus_areas=PromptTemplate.format_list(focus_areas),
        )

    def _validate_word(self, word: str) -> bool:
        """Validate a word as a valid directory/file path component."""
        if not word:
            return False

        if len(word) < self.MIN_LENGTH or len(word) > self.MAX_LENGTH:
            return False

        # No double dots (path traversal)
        if ".." in word:
            return False

        if word.startswith(".") and len(word) == 1:
            return False
        if word.startswith("/") or word.endswith("/"):
            return False

        return bool(self.VALID_CHARS_PATTERN.match(word))

    def get_seed_hints(self) -> str:
        """Return hints about what seed words to provide."""
        return dedent(
            """\
            For effective directory/file wordlists, provide information about the target:
            • Technology: Framework names (WordPress, Django, Laravel, Spring)
            • Company: Name, abbreviations, product names, project codenames
            • Platform: Server type (Apache, Nginx, IIS), language (PHP, Python, Java)
            • Purpose: Application type (ecommerce, blog, API, admin panel)
            • Version: Known version numbers or release names
            • Industry: Sector-specific terms that might appear in paths
            • Known paths: Any discovered directories or naming patterns

            Example: wordpress acmecorp blog php apache ecommerce payment\
            """
        )

    def _get_detailed_system_prompt(self) -> str:
        """Return the detailed system prompt for directory/file generation."""
        role = (
            "You are a cybersecurity expert specializing in web application "
            "reconnaissance and directory/file discovery patterns for ethical "
            "penetration testing."
        )

        task = (
            "Generate a targeted directory and file wordlist based on technology "
            "stack and organizational context. Focus on realistic paths that "
            "developers commonly use, including hidden files, backups, and "
            "framework-specific directories."
        )

        context_items = [
            "Web frameworks and CMS platforms (WordPress, Django, etc.)",
            "Programming languages and their common patterns",
            "Company names and project identifiers",
            "Application purpose and functionality",
            "Server software and deployment patterns",
            "Version control and development artifacts",
            "Backup and archive naming conventions",
        ]
        context = (
            "The seed words represent technical and organizational context including:\n"
            + PromptTemplate.format_list(context_items)
        )

        methodology_steps = [
            "**Analyze seed words** to identify:\n"
            "   - Technology indicators (framework names, languages, platforms)\n"
            "   - Organizational terms (company names, product names, project codes)\n"
            "   - Domain context (e-commerce, blog, API service, etc.)\n"
            "   - Any specific naming patterns or conventions",
            "**Generate universal path patterns**:\n"
            "   - **Admin/Management**: admin, dashboard, manage, panel, control\n"
            "   - **API/Services**: api, api/v1, api/v2, graphql, rest, services\n"
            "   - **Authentication**: auth, login, signin, logout, register\n"
            "   - **User areas**: user, users, profile, account, members\n"
            "   - **Content**: uploads, media, images, files, documents\n"
            "   - **Development**: dev, test, staging, debug, demo, sandbox\n"
            "   - **Configuration**: config, settings, setup, install\n"
            "   - **System**: backup, temp, cache, logs, tmp",
            "**Apply technology-specific patterns** based on identified stack:\n"
            "   - If web framework detected, include framework-specific paths\n"
            "   - If language detected, include common directories for that language\n"
            "   - If CMS detected, include CMS-specific admin and content paths\n"
            "   - If build tool detected, include build output directories",
            "**Include common files with extensions**:\n"
            "   - Config files: config.json, settings.ini, .env, .htaccess\n"
            "   - Backups: backup.zip, dump.sql, site.tar.gz, [name].bak\n"
            "   - Documentation: README.md, changelog.txt, TODO.txt\n"
            "   - Hidden files: .git/config, .env.local, .DS_Store",
            "**Create contextual combinations**:\n"
            "   - Combine seed terms with common patterns\n"
            "   - Use both single-level and nested paths\n"
            "   - Include versioned endpoints (v1, v2, 2023, etc.)\n"
            "   - Mix general and specific paths",
        ]
        methodology = PromptTemplate.format_numbered_list(methodology_steps)

        input_spec = (
            "Seed words: {seed_words}\nTarget output length: {wordlist_length} paths"
        )

        output_requirements = [
            "Output exactly {wordlist_length} directory/file paths",
            "One path per line, no other text",
            "Valid URL path characters only (alphanumeric, -, _, ., ~)",
            "No path traversal sequences (..)",
            "No leading slashes",
            "No duplicates",
            "Mix of directories and files with extensions",
            "Prioritize most likely paths based on context",
        ]

        constraints = [
            "Do NOT include full URLs or domain names",
            "Do NOT include query parameters or fragments",
            "Do NOT include invalid filesystem characters",
            "Do NOT include explanations or categories",
            "Do NOT include extremely long paths (>255 chars)",
        ]

        return PromptTemplate.create_prompt(
            role=role,
            task=task,
            context=context,
            methodology=methodology,
            input_spec=input_spec,
            output_requirements=PromptTemplate.format_list(output_requirements),
            constraints=PromptTemplate.format_list(constraints),
            additional_sections={"context_analysis": context},
        )

    def get_usage_instructions(self) -> str:
        """Return instructions for using the generated wordlist."""
        return dedent(
            """\
            Next steps:
            1. Use with directory brute-forcing tools:
               • ffuf: ffuf -u https://target.com/FUZZ -w directory_wordlist.txt
               • gobuster: gobuster dir -u https://target.com -w directory_wordlist.txt
               • dirbuster: Load wordlist in GUI
               • wfuzz: wfuzz -c -z file,directory_wordlist.txt https://target.com/FUZZ

            2. Enhance discovery with:
               • Extensions: -x php,asp,html,js,txt,zip,bak
               • Recursive scanning for discovered directories
               • Custom headers for authenticated scanning
               • Response filtering by size/status

            3. Look for interesting responses:
               • 200 OK - Accessible resources
               • 403 Forbidden - Exists but restricted
               • 301/302 - Redirects revealing structure
               • 401 - Authentication required

            Tip: The AI considers your technology stack to generate framework-specific paths!\
            """
        )
