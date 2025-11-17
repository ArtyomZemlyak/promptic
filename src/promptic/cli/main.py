"""Typer CLI entrypoint for the Promptic context engineering toolkit."""

from __future__ import annotations

import typer

app = typer.Typer(
    help="Utilities for authoring, previewing, and executing hierarchical context blueprints.",
    no_args_is_help=True,
)

blueprint_app = typer.Typer(help="Manage blueprint templates and previews.")
pipeline_app = typer.Typer(help="Run and inspect pipeline executions.")


@blueprint_app.command("preview")
def blueprint_preview() -> None:
    """Placeholder blueprint preview command."""

    # AICODE-TODO: Wire this command to the ContextPreviewer service in Phase 3.
    typer.echo("Blueprint preview is not implemented yet.")


@pipeline_app.command("run")
def pipeline_run() -> None:
    """Placeholder pipeline execution command."""

    # AICODE-TODO: Wire this command to the PipelineExecutor service in Phase 5.
    typer.echo("Pipeline execution is not implemented yet.")


app.add_typer(blueprint_app, name="blueprint")
app.add_typer(pipeline_app, name="pipeline")


def main() -> None:
    """Entry point for console_scripts."""

    app()


if __name__ == "__main__":
    main()
