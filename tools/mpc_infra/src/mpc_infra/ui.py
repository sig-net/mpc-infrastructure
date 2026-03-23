from contextlib import contextmanager

import questionary
from rich.console import Console
from rich.panel import Panel

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
