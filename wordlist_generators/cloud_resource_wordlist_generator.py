import re
from pathlib import Path
from textwrap import dedent

from wordlist_generators.prompt_templates import (
    CommonPromptFragments,
    PromptTemplate,
    create_simple_prompt,
)
from wordlist_generators.wordlist_generator import WordlistGenerator


class CloudResourceWordlistGenerator(WordlistGenerator):
    """Generator for cloud resource enumeration wordlists."""

    MIN_LENGTH = 3
    MAX_LENGTH = 63
    VALID_CHARS_PATTERN = re.compile(r"^[a-z0-9]([a-z0-9\-_]*[a-z0-9])?$")

    def __init__(self, output_file: Path | None = None):
        super().__init__(output_file)

    def _get_default_output_path(self) -> Path:
        return Path("cloud_resource_wordlist.txt")

    def _get_system_prompt(self) -> str:
        focus_areas = [
            "Company abbreviations and variations (e.g., tesla → tsl, tsla)",
            "Realistic project codenames and internal references",
            "Common cloud naming patterns that real engineers use",
            "Mix obvious names with less predictable but plausible ones",
            "Department abbreviations (eng, mktg, ops, fin)",
            "Regional variations beyond standard AWS regions",
            "Internal tool names and platform references",
            "Data classification terms (public, internal, confidential)",
            "Service-specific patterns based on the cloud provider",
            "Version/iteration patterns (alpha, beta, rc, release)",
        ]

        naming_patterns = [
            "Short abbreviations: tsl-data, auto-ml, vehicle-api",
            "Project names: autopilot-models, battery-analytics, fleet-data",
            "Internal tools: telemetry-processor, ota-staging, diagnostics-cache",
            "Team buckets: mobility-assets, energy-backups, ai-training-data",
            "Time-based: quarterly-reports, daily-exports, snapshot-archive",
            "Purpose-specific: customer-uploads, firmware-releases, map-tiles",
        ]

        return create_simple_prompt(
            """\
            You are an expert in cloud infrastructure penetration testing who understands
            how real companies name their cloud resources in practice.

            Given these seed words: {seed_words}

            Generate exactly {wordlist_length} realistic cloud resource names that a
            company might actually use. Think like a developer or DevOps engineer who
            needs practical, memorable names.

            Key principles:
            {focus_areas}

            Example realistic patterns:
            {naming_patterns}

            Important: Avoid overly generic combinations. Make names that sound like
            what you'd find in a real company's cloud infrastructure.

            Output ONLY resource names (lowercase, hyphens/underscores allowed).
            One name per line, no explanations.\
            """,
            seed_words="{seed_words}",
            wordlist_length="{wordlist_length}",
            focus_areas=PromptTemplate.format_list(focus_areas),
            naming_patterns=PromptTemplate.format_list(naming_patterns),
        )

    def _validate_word(self, word: str) -> bool:
        if not word:
            return False

        word_lower = word.lower()

        if len(word_lower) < self.MIN_LENGTH or len(word_lower) > self.MAX_LENGTH:
            return False

        if (
            "--" in word_lower
            or "__" in word_lower
            or "-_" in word_lower
            or "_-" in word_lower
        ):
            return False

        return bool(self.VALID_CHARS_PATTERN.match(word_lower))

    def _process_generated_words(self, words: list[str]) -> list[str]:
        lowercase_words = [word.lower() for word in words]
        return super()._process_generated_words(lowercase_words)

    def get_seed_hints(self) -> str:
        return dedent(
            """\
            For effective cloud resource wordlists, provide diverse context:
            • Company: Name, stock ticker, common abbreviations
            • Industry: Automotive, finance, healthcare, retail, etc.
            • Products: Main products, services, or platforms
            • Technology: Cloud provider (AWS/Azure/GCP), tech stack
            • Projects: Known project names or internal initiatives
            • Geography: Headquarters, major offices, target markets
            • Culture: Any known internal terminology or naming patterns

            Example: tesla automotive aws s3 autopilot california energy

            The more context provided, the more realistic the generated names!\
            """
        )

    def _get_detailed_system_prompt(self) -> str:
        role = (
            "You are a red team cloud security specialist who discovers "
            "exposed cloud resources by understanding how real engineering teams "
            "name resources during migrations, under deadlines, and when dealing "
            "with technical debt."
        )

        task = (
            "Generate cloud resource names that real companies would actually use, "
            "including migration artifacts, misconfigured test resources that became "
            "production, personal developer buckets, and the naming chaos that occurs "
            "during rapid scaling and cloud migrations."
        )

        context_items = [
            "Company names and common abbreviations (tesla → tsla, tsl, t)",
            "Industry-specific terminology and jargon",
            "Real project codenames and internal references",
            "Team structures and how they actually name things",
            "Developer shortcuts and practical naming habits",
            "Time pressure and convenience in naming decisions",
            "Legacy naming patterns that persist over time",
            "Mix of formal and informal naming conventions",
        ]
        context = (
            "Analyze the seed words to understand the organization's context:\n"
            + PromptTemplate.format_list(context_items)
            + "\n\n"
            + CommonPromptFragments.cultural_variation_instructions()
        )

        methodology_steps = [
            "**Chain-of-Thought Analysis**:\n"
            + CommonPromptFragments.chain_of_thought_instructions(),
            "**Extract company identity**:\n"
            "   - Common abbreviations (tesla → tsl, tsla, t)\n"
            "   - Stock tickers, internal codes\n"
            "   - Project codenames based on company culture\n"
            "   - Acquisition names that might persist",
            "**Migration and misconfiguration patterns**:\n"
            "   - **Lift-and-shift**: onprem-backup, datacenter-archive, legacy-app\n"
            "   - **Test-to-prod**: test-bucket-do-not-delete, poc-data, demo-prod\n"
            "   - **Personal buckets**: john-test, sarah-dev, mike-backup\n"
            "   - **Temporary-permanent**: temp-logs-2019, quick-fix, hotfix-data\n"
            "   - **Multi-cloud confusion**: aws-backup-in-azure, gcp-migration",
            "**Developer convenience patterns**:\n"
            "   - **Quick names**: test, temp, data, backup, stuff, misc\n"
            "   - **Numbered iterations**: test1, test2, test-v3, backup-old\n"
            "   - **Date stamps**: backup-20231225, logs-jan, dump-q1-2024\n"
            "   - **Copy operations**: prod-copy, backup-of-backup, old-old-data",
            "**Shadow IT and unofficial resources**:\n"
            "   - **Side projects**: hackathon-2023, innovation-lab, skunkworks\n"
            "   - **Department buckets**: marketing-assets, sales-leads, hr-docs\n"
            "   - **Contractor resources**: vendor-uploads, consultant-data, external\n"
            "   - **Proof of concepts**: poc-ml, prototype-api, mvp-backend",
            "**Realistic naming evolution**:\n"
            "   - Start formal: company-production-data\n"
            "   - Get abbreviated: comp-prod, cprod, cp-data\n"
            "   - Personal shortcuts: my-data, team-stuff, proj-files\n"
            "   - Emergency names: urgent-backup, critical-restore, asap-data",
            "**Regional and office-specific patterns**:\n"
            "   - Office locations: sf-backup, nyc-data, london-assets\n"
            "   - Regional compliance: gdpr-backup, ccpa-data, hipaa-archive\n"
            "   - Time zones: pst-logs, est-backup, gmt-data\n"
            "   - Language mixing: datos-backup, donnees-archive",
            "**Adversarial patterns**:\n"
            + CommonPromptFragments.adversarial_thinking_instructions(),
        ]
        methodology = PromptTemplate.format_numbered_list(methodology_steps)

        good_examples = [
            ("tesla-prod", "obvious production bucket"),
            ("tsla-ml", "abbreviated company + department"),
            ("autopilot-dev", "project name + environment"),
            ("test-bucket-do-not-delete", "test resource that became critical"),
            ("john-backup", "personal developer bucket"),
            ("temp-2019", "temporary bucket from years ago"),
            ("poc-data", "proof of concept that went to production"),
            ("legacy-app-backup", "migration artifact"),
            ("q1-reports", "time-based naming"),
            ("jenkins-artifacts", "CI/CD related bucket"),
            ("hotfix-jan23", "emergency fix bucket"),
            ("vendor-uploads", "third-party integration"),
            ("tf-state", "terraform state - abbreviated"),
            ("old-old-prod", "multiple migration layers"),
        ]

        bad_examples = [
            ("bucket123456", "random numbers without context"),
            ("aaaaaaa", "repeated characters"),
            ("my-s3-bucket", "generic S3 reference"),
            ("test-test-test", "excessive repetition"),
            ("super-long-bucket-name-that-exceeds-limits", "too long"),
        ]

        examples_section = CommonPromptFragments.create_few_shot_examples(
            good_examples, bad_examples
        )

        input_spec = (
            "Seed words: {seed_words}\n"
            "Target output length: {wordlist_length} resource names"
        )

        output_requirements = [
            "Output exactly {wordlist_length} cloud resource names",
            "One resource name per line, no other text",
            "Mix obvious and non-obvious but plausible names",
            "Include migration artifacts and misconfigurations",
            "Reflect real naming chaos from rapid scaling",
            "Lowercase only, hyphens and underscores allowed",
            "Length: 3-63 characters per name",
            "No duplicates",
            CommonPromptFragments.diversity_requirements(),
        ]

        constraints = [
            "Do NOT create overly formal or theoretical names",
            "Do NOT just combine seed words mechanically",
            "Do NOT ignore common developer shortcuts and habits",
            "Do NOT include explanations or categories",
            "Do NOT use special characters except hyphens and underscores",
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
        return dedent(
            """\
            Next steps:
            1. Use with cloud enumeration tools:
               • S3 buckets: aws s3 ls s3://BUCKET_NAME (check each name)
               • Azure: az storage account check-name --name RESOURCE_NAME
               • GCP: gsutil ls gs://BUCKET_NAME
               • Multiple: cloud_enum -k wordlist.txt -t 10

            2. Combine with automated scanning:
               • bucket-stream: Monitor certificate transparency for new buckets
               • S3Scanner: python S3Scanner.py --list cloud_resource_wordlist.txt
               • CloudBrute: ./cloudbrute -d company.com -w cloud_resource_wordlist.txt

            3. Check for misconfigurations:
               • Public read/write permissions
               • Exposed sensitive data
               • Overly permissive CORS policies
               • Missing encryption

            Tip: Many organizations follow predictable naming patterns - combine this
            wordlist with permutation tools for comprehensive coverage!\
            """
        )
