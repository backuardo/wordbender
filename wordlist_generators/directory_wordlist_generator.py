import re
from pathlib import Path
from textwrap import dedent

from wordlist_generators.prompt_templates import (
    CommonPromptFragments,
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
            "You are a red team operator specializing in web application "
            "reconnaissance, directory traversal, and sensitive file discovery "
            "for authorized penetration testing. You understand real developer "
            "behaviors, emergency fixes, and where sensitive data actually lives."
        )

        task = (
            "Generate a targeted directory and file wordlist based on technology "
            "stack and organizational context. Focus on paths developers actually "
            "create under pressure, including forgotten backups, debug endpoints, "
            "and framework vulnerabilities."
        )

        context_items = [
            "Web frameworks and CMS platforms (WordPress, Django, Rails, etc.)",
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
            + "\n\n"
            + CommonPromptFragments.cultural_variation_instructions()
        )

        methodology_steps = [
            "**Chain-of-Thought Analysis**:\n"
            + CommonPromptFragments.chain_of_thought_instructions(),
            "**Analyze seed words** to identify:\n"
            "   - Technology indicators (framework names, languages, platforms)\n"
            "   - Organizational terms (company names, product names, project codes)\n"
            "   - Domain context (e-commerce, blog, API service, etc.)\n"
            "   - Regional/cultural indicators for path variations",
            "**Developer laziness patterns**:\n"
            "   - **Quick fixes**: temp, tmp, old, new, backup, test, TODO\n"
            "   - **Numbered versions**: admin1, backup2, test_v3\n"
            "   - **Date stamps**: backup_2023, logs_january, dump_01_15\n"
            "   - **Personal names**: john_backup, dev_mike, sarah_test\n"
            "**Framework vulnerability paths**:\n"
            "   - **WordPress**: wp-content/uploads, wp-json, xmlrpc.php\n"
            "   - **Laravel**: storage/logs, .env, public/vendor\n"
            "   - **Django**: static/admin, media/uploads, __pycache__\n"
            "   - **Spring**: actuator/health, swagger-ui, api-docs\n"
            "   - **Node.js**: node_modules, package-lock.json, .env.local",
            "**Sensitive file patterns**:\n"
            "   - **Configs**: .env, .env.prod, config.yml, settings.ini\n"
            "   - **Backups**: db_backup.sql, dump.tar.gz, site_backup.zip\n"
            "   - **Version control**: .git/HEAD, .svn/entries, .hg/store\n"
            "   - **IDE files**: .idea, .vscode, .project, workspace.xml\n"
            "   - **Cloud**: .aws/credentials, .azure, .gcloud",
            "**Emergency deployment artifacts**:\n"
            "   - Copy operations: Copy of admin, admin - Copy\n"
            "   - Before changes: admin_before_update, pre_migration\n"
            "   - Quick backups: admin.bak, admin.old, admin_OLD\n"
            "   - Archive attempts: admin.zip, admin.tar, admin.rar",
            "**API and debug endpoints**:\n"
            "   - Debug modes: debug, test, _debug, .debug\n"
            "   - API versions: api/v1, api/v2, api/internal, api/private\n"
            "   - GraphQL: graphql, graphiql, playground\n"
            "   - Health checks: health, status, ping, heartbeat",
            "**Shadow IT and unofficial paths**:\n"
            "   - Personal projects: myapp, testproject, demo\n"
            "   - Proof of concepts: poc, prototype, mvp\n"
            "   - Migration artifacts: legacy, deprecated, old_site\n"
            "   - Staging leaks: stage, staging, uat, preprod",
            "**Adversarial patterns**:\n"
            + CommonPromptFragments.adversarial_thinking_instructions(),
        ]
        methodology = PromptTemplate.format_numbered_list(methodology_steps)

        good_examples = [
            ("admin", "standard admin panel path"),
            ("wp-admin", "WordPress admin - framework specific"),
            ("backup.zip", "common backup file name"),
            (".env", "exposed environment file - critical"),
            ("api/v1/users", "versioned API endpoint"),
            (".git/config", "exposed git repository"),
            ("phpinfo.php", "information disclosure file"),
            ("test", "developer test directory"),
            ("admin_backup", "admin backup - lazy naming"),
            ("uploads/2023", "dated upload directory"),
            ("~admin", "backup file from vim/emacs"),
            ("admin.bak", "backup with common extension"),
            ("TODO.txt", "developer notes file"),
            ("dump.sql", "database dump file"),
        ]

        bad_examples = [
            ("/admin", "has leading slash - invalid format"),
            ("admin/", "has trailing slash - invalid format"),
            ("../../etc/passwd", "path traversal - not for wordlist"),
            ("https://example.com", "full URL - not a path"),
            ("admin?test=1", "has query parameters - invalid"),
        ]

        examples_section = CommonPromptFragments.create_few_shot_examples(
            good_examples, bad_examples
        )

        input_spec = (
            "Seed words: {seed_words}\nTarget output length: {wordlist_length} paths"
        )

        output_requirements = [
            "Output exactly {wordlist_length} directory/file paths",
            "One path per line, no other text",
            "Valid URL path characters only (alphanumeric, -, _, ., ~, /)",
            "No path traversal sequences (..)",
            "No leading or trailing slashes",
            "No duplicates",
            "Mix of directories and files with extensions",
            "Prioritize high-value targets (configs, backups, version control)",
            CommonPromptFragments.diversity_requirements(),
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
            additional_sections={
                "context_analysis": context,
                "examples": examples_section,
            },
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
