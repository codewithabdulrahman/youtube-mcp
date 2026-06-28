"""
YouTube Content CLI — run `python -m commands.cli <command>` or `content <command>`.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from rich.console import Console
from rich.table import Table
from rich import print as rprint

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging.")
@click.pass_context
def cli(ctx, verbose):
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if verbose:
        import logging
        logging.basicConfig(level=logging.DEBUG)


# ─── Auth ──────────────────────────────────────────────────────────────────────

@cli.command()
@click.argument("client_secrets_file")
def auth(client_secrets_file):
    """Run the one-time Google OAuth2 authorization flow."""
    from services.google_auth import run_auth_flow
    creds = run_auth_flow(client_secrets_file)
    console.print(f"[green]Auth complete![/green] Refresh token saved.")
    console.print(f"Add to .env: GOOGLE_REFRESH_TOKEN={creds.refresh_token}")


# ─── Setup ─────────────────────────────────────────────────────────────────────

@cli.command()
def setup():
    """Initialize Google Sheet headers and Drive folder structure."""
    from services import sheets_service, drive_service
    console.print("Checking Google Sheet...")
    sheets_service.ensure_sheet_exists()
    console.print("Checking Google Drive folders...")
    drive_service.ensure_drive_structure()
    console.print("[green]Setup complete![/green]")


# ─── Research ─────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--topic", "-t", help="Specific topic to research.")
@click.option("--count", "-c", default=5, help="Number of new topics to suggest.")
@click.option("--category", default="", help="Content category.")
@click.option("--dry-run", is_flag=True, help="Preview without saving.")
@click.pass_context
def research(ctx, topic, count, category, dry_run):
    """Research a topic or find new ideas. Claude Code performs the synthesis."""
    from agents import research_agent

    if topic:
        console.print(f"[cyan]Gathering research brief for:[/cyan] {topic}")
        brief = research_agent.build_research_brief(topic)

        if dry_run:
            console.print("[yellow]DRY RUN — not saving to sheet[/yellow]")
            rprint(brief)
            return

        dups = brief["duplicate_check"]
        if dups:
            console.print(f"[yellow]Warning: {len(dups)} similar topic(s) found:[/yellow]")
            for d in dups[:3]:
                console.print(f"  • {d['topic']} (similarity: {d['similarity_score']}%)")
            if not click.confirm("Continue anyway?"):
                return

        console.print(f"\n[bold]Research brief ready.[/bold] Pass it to Claude to synthesize.")
        console.print(json.dumps(brief, indent=2, default=str))

    else:
        console.print(f"[cyan]Use Claude Code to research {count} new {category or 'general'} topics.[/cyan]")
        console.print("Suggested prompt: 'Research 5 new ideas about [topic]. Add them to the sheet.'")


# ─── Script ───────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--row", "-r", type=int, help="Sheet row number.")
@click.option("--topic", "-t", help="Video topic (finds row automatically).")
@click.option("--dry-run", is_flag=True, help="Preview context without saving.")
def script(row, topic, dry_run):
    """Load research and script prompt for Claude to write a script."""
    from agents import script_agent
    from services import sheets_service

    if topic and not row:
        videos = sheets_service.list_videos(limit=500)
        for v in videos:
            if topic.lower() in v["topic"].lower():
                row = v["row"]
                console.print(f"Found: row {row} — {v['topic']}")
                break

    if not row:
        console.print("[red]Provide --row or --topic[/red]")
        return

    context = script_agent.build_script_context(row=row)

    if dry_run:
        console.print("[yellow]DRY RUN — script context preview[/yellow]")
        console.print(f"Topic: {context['video']['topic']}")
        console.print(f"Has research: {context['has_research']}")
        console.print(f"Prompt length: {len(context['script_prompt'])} chars")
        return

    console.print(json.dumps(context, indent=2, default=str))


# ─── Visuals ──────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--row", "-r", type=int, required=True, help="Sheet row number.")
@click.option("--dry-run", is_flag=True)
def visuals(row, dry_run):
    """Load script and visuals prompt for Claude to generate scene descriptions."""
    from agents import visual_agent

    context = visual_agent.build_visual_context(row=row)

    if dry_run:
        console.print(f"Topic: {context['video']['topic']}")
        console.print(f"Has script: {context['has_script']}")
        return

    console.print(json.dumps(context, indent=2, default=str))


# ─── Schedule ─────────────────────────────────────────────────────────────────

@cli.command()
@click.option("--weeks", "-w", default=4, help="Number of weeks ahead.")
def schedule(weeks):
    """Show the publishing schedule."""
    from agents import publishing_agent

    result = publishing_agent.get_schedule(weeks=weeks)
    videos = result["videos"]

    if not videos:
        console.print(f"[yellow]No videos scheduled in the next {weeks} weeks.[/yellow]")
        return

    table = Table(title=f"Schedule — Next {weeks} Weeks")
    table.add_column("Row", style="dim")
    table.add_column("Topic")
    table.add_column("Status")
    table.add_column("Publish Date")
    table.add_column("Category")

    for v in videos:
        table.add_row(str(v["row"]), v["topic"], v["status"], v["publish_date"], v["category"])

    console.print(table)


# ─── Pending ──────────────────────────────────────────────────────────────────

@cli.command()
def pending():
    """Show videos needing scripts, thumbnails, or other actions."""
    from agents import publishing_agent

    summary = publishing_agent.get_workflow_summary()
    stats = summary["stats"]

    console.print("\n[bold cyan]Channel Pipeline[/bold cyan]")
    console.print(f"  Total: {stats['total']}")
    console.print(f"  Ideas: {stats.get('idea', 0)}")
    console.print(f"  In Research: {stats.get('researching', 0)}")
    console.print(f"  Research Complete: {stats.get('research_complete', 0)}")
    console.print(f"  Script Writing: {stats.get('script_writing', 0)}")
    console.print(f"  Script Complete: {stats.get('script_complete', 0)}")
    console.print(f"  Thumbnail Ready: {stats.get('thumbnail_ready', 0)}")
    console.print(f"  Scheduled: {stats.get('scheduled', 0)}")
    console.print(f"  Published: {stats.get('published', 0)}")

    pending_scripts = summary["pending_scripts"]
    if pending_scripts:
        console.print(f"\n[bold yellow]Needs Script ({len(pending_scripts)}):[/bold yellow]")
        for v in pending_scripts[:5]:
            console.print(f"  Row {v['row']}: {v['topic']}")


# ─── Stats ────────────────────────────────────────────────────────────────────

@cli.command()
def stats():
    """Show content statistics."""
    from services import sheets_service

    data = sheets_service.get_stats()
    table = Table(title="Content Stats")
    table.add_column("Status")
    table.add_column("Count", justify="right")

    for key, val in data.items():
        if key != "total":
            table.add_row(key.replace("_", " ").title(), str(val))

    console.print(table)
    console.print(f"\n[bold]Total: {data['total']}[/bold]")


# ─── List ─────────────────────────────────────────────────────────────────────

@cli.command("list")
@click.option("--status", "-s", help="Filter by status.")
@click.option("--category", "-c", help="Filter by category.")
@click.option("--limit", "-l", default=50)
def list_videos(status, category, limit):
    """List videos from the sheet."""
    from services import sheets_service

    videos = sheets_service.list_videos(status=status, category=category, limit=limit)

    if not videos:
        console.print("[yellow]No videos found.[/yellow]")
        return

    table = Table(title=f"Videos ({len(videos)})")
    table.add_column("Row", style="dim")
    table.add_column("ID")
    table.add_column("Topic")
    table.add_column("Status")
    table.add_column("Category")
    table.add_column("Priority")

    for v in videos:
        table.add_row(str(v["row"]), v["id"], v["topic"][:50], v["status"], v["category"], v["priority"])

    console.print(table)


if __name__ == "__main__":
    cli()
