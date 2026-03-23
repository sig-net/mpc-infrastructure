from contextlib import contextmanager

import questionary
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()


def banner(title: str, subtitle: str | None = None) -> None:
    text = f"[bold cyan]{title}[/bold cyan]"
    if subtitle:
        text += f"\n[dim]{subtitle}[/dim]"
    console.print(Panel.fit(text, border_style="cyan"))


def info(message: str) -> None:
    console.print(f"[cyan]•[/cyan] {message}")


def success(message: str) -> None:
    console.print(f"[green]✓[/green] {message}")


def warn(message: str) -> None:
    console.print(f"[yellow]![/yellow] {message}")


def error(message: str) -> None:
    console.print(f"[red]✗[/red] {message}")


@contextmanager
def step(message: str):
    with console.status(f"[bold blue]{message}[/bold blue]", spinner="dots") as status:
        yield status


def select(message: str, choices: list[str], default: str | None = None) -> str:
    selected = questionary.select(
        message,
        choices=choices,
        default=default,
        use_indicator=True,
        use_shortcuts=False,
    ).ask()
    if selected is None:
        raise KeyboardInterrupt
    return selected


def render_outputs_table(outputs: dict[str, object]) -> None:
    table = Table(title="Terraform Outputs", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan")
    table.add_column("Value", style="white")
    for key, value in outputs.items():
        table.add_row(key, str(value))
    console.print(table)


def _resource_table(resources: dict[str, dict[str, str]]) -> Table:
    table = Table(title="Deployment Resources", show_header=True, header_style="bold magenta")
    table.add_column("Status", width=10)
    table.add_column("Resource", style="cyan")
    table.add_column("Detail", style="white")
    order = {"pending": 0, "running": 1, "complete": 2, "failed": 3}
    icon = {"pending": "…", "running": "▶", "complete": "✓", "failed": "✗"}
    color = {"pending": "yellow", "running": "blue", "complete": "green", "failed": "red"}
    for name, state in sorted(resources.items(), key=lambda item: (order.get(item[1]["status"], 9), item[0])):
        status = state["status"]
        table.add_row(f"[{color[status]}]{icon[status]} {status}[/{color[status]}]", name, state.get("detail", ""))
    return table


@contextmanager
def resource_progress(resources: dict[str, dict[str, str]]):
    with Live(_resource_table(resources), console=console, refresh_per_second=8) as live:
        yield lambda: live.update(_resource_table(resources))
