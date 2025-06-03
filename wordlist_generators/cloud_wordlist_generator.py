import re
from pathlib import Path
from textwrap import dedent

from wordlist_generators.prompt_templates import (
    PromptTemplate,
    create_simple_prompt,
)
from wordlist_generators.wordlist_generator import WordlistGenerator


class CloudWordlistGenerator(WordlistGenerator):
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
            "You are a cloud security researcher who specializes in discovering "
            "exposed cloud resources through realistic enumeration techniques. "
            "You understand how real engineering teams name resources in practice."
        )

        task = (
            "Generate cloud resource names that real companies would actually use. "
            "Focus on practical, memorable names that developers create under "
            "pressure, not theoretical naming standards. Include internal project "
            "names, abbreviations, and the shortcuts teams really use."
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
        )

        methodology_steps = [
            "**Extract company identity**:\n"
            "   - Common abbreviations (tesla → tsl, tsla, t)\n"
            "   - Stock tickers, internal codes\n"
            "   - Project codenames based on company culture",
            "**Apply realistic naming patterns**:\n"
            "   - **Quick names**: tsl-temp, auto-test, vehicle-data\n"
            "   - **Project-based**: autopilot-dev, battery-metrics, fleet-logs\n"
            "   - **Team ownership**: ml-team-models, mobile-assets, platform-backups\n"
            "   - **Purpose-driven**: customer-exports, diagnostic-dumps, telemetry-raw\n"
            "   - **Time-based**: 2024-q1-reports, daily-snapshots, archive-old\n"
            "   - **Tool-specific**: jenkins-artifacts, terraform-state, k8s-configs",
            "**Mix predictable and creative names**:\n"
            "   - Some obvious: tesla-prod-s3, automotive-backup\n"
            "   - Some abbreviated: tsl-ml, auto-api, veh-data\n"
            "   - Some internal: project-titan, operation-bluesky\n"
            "   - Some functional: ota-updates, map-tiles, user-uploads",
            "**Consider real-world factors**:\n"
            "   - Developers often use shortcuts and abbreviations\n"
            "   - Legacy names persist even after reorganizations\n"
            "   - Internal project names leak into resource naming\n"
            "   - Convenience often trumps naming standards",
        ]
        methodology = PromptTemplate.format_numbered_list(methodology_steps)

        input_spec = (
            "Seed words: {seed_words}\n"
            "Target output length: {wordlist_length} resource names"
        )

        output_requirements = [
            "Output exactly {wordlist_length} cloud resource names",
            "One resource name per line, no other text",
            "Mix obvious and non-obvious but plausible names",
            "Include abbreviations and shortcuts developers would use",
            "Reflect how real teams name resources under time pressure",
            "Lowercase only, hyphens and underscores allowed",
            "Length: 3-63 characters per name",
            "No duplicates",
        ]

        constraints = [
            "Do NOT create overly formal or theoretical names",
            "Do NOT just combine seed words mechanically",
            "Do NOT ignore common developer shortcuts and habits",
            "Do NOT include explanations or categories",
            "Do NOT use special characters except hyphens and underscores",
        ]

        realistic_examples = {
            "realistic_patterns": dedent(
                """\
                Examples of realistic cloud resource names:
                - Quick development names: tsl-test, auto-demo, temp-data
                - Project names: autopilot-training, battery-sim, fleet-analytics
                - Abbreviated names: tsla-ml, veh-api, diag-logs
                - Tool-specific: jenkins-builds, airflow-dags, grafana-dashboards
                - Time-based: backup-2024, archive-q1, snapshot-daily
                - Team names: platform-tools, mobile-assets, ml-datasets
                - Internal refs: project-x, operation-sunset, team-alpha-data\
                """
            )
        }

        return PromptTemplate.create_prompt(
            role=role,
            task=task,
            context=context,
            methodology=methodology,
            input_spec=input_spec,
            output_requirements=PromptTemplate.format_list(output_requirements),
            constraints=PromptTemplate.format_list(constraints),
            additional_sections=realistic_examples,
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
