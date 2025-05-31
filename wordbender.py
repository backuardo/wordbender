import sys

import click
from rich.console import Console

from cli.app import WordbenderApp
from cli.commands import batch_cmd, config_cmd, generate_cmd

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Wordbender - an LLM-powered targeted wordlist generator script"""
    if ctx.invoked_subcommand is None:
        try:
            app = WordbenderApp()
            app.run_interactive_session()
        except Exception as e:
            console.print(f"[red]Failed to initialize application: {e}[/red]")
            sys.exit(1)


cli.add_command(config_cmd)
cli.add_command(generate_cmd)
cli.add_command(batch_cmd)


def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
