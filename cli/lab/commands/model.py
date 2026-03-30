"""Model management commands."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..core.registry import get_registry
from ..core.model_info import ModelCapability

console = Console()


@click.group()
def model():
    """Manage AI models."""
    pass


@model.command()
@click.option('--fine-tunable', is_flag=True, help='Show only fine-tunable models')
@click.option('--capability', type=str, help='Filter by capability (code, chat, reasoning, etc.)')
@click.option('--family', type=str, help='Filter by model family (qwen, llama, codellama)')
def list(fine_tunable, capability, family):
    """List all registered models."""
    registry = get_registry()
    
    # Parse filters
    cap = None
    if capability:
        try:
            cap = ModelCapability(capability.lower())
        except ValueError:
            console.print(f"[red]Invalid capability: {capability}[/red]")
            return
    
    fam = None
    if family:
        from ..core.model_info import ModelFamily
        try:
            fam = ModelFamily(family.lower())
        except ValueError:
            console.print(f"[red]Invalid family: {family}[/red]")
            return
    
    models = registry.list_models(
        capability=cap,
        fine_tunable_only=fine_tunable,
        family=fam
    )
    
    if not models:
        console.print("[yellow]No models found matching criteria.[/yellow]")
        return
    
    table = Table(title="Available Models")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Family", style="blue")
    table.add_column("Parameters")
    table.add_column("Context")
    table.add_column("Fine-tunable", style="yellow")
    table.add_column("Capabilities")
    
    for m in models:
        table.add_row(
            m.id,
            m.name,
            m.family.value,
            m.parameters,
            str(m.context_length),
            "✓" if m.is_fine_tunable() else "✗",
            ", ".join(c.value for c in m.capabilities)
        )
    
    console.print(table)


@model.command()
@click.argument('model_id')
def info(model_id):
    """Show detailed information about a model."""
    registry = get_registry()
    model = registry.get_model(model_id)
    
    if not model:
        console.print(f"[red]Model '{model_id}' not found.[/red]")
        return
    
    content = f"""
[bold cyan]Model:[/bold cyan] {model.name}
[bold]ID:[/bold] {model.id}
[bold]Description:[/bold] {model.description or 'N/A'}
[bold]Provider:[/bold] {model.provider}
[bold]Ollama Name:[/bold] {model.ollama_name}
[bold]HuggingFace ID:[/bold] {model.huggingface_id or 'N/A'}

[bold cyan]Specifications:[/bold cyan]
[bold]Family:[/bold] {model.family.value}
[bold]Parameters:[/bold] {model.parameters}
[bold]Context Length:[/bold] {model.context_length}
[bold]License:[/bold] {model.license or 'Unknown'}

[bold cyan]Capabilities:[/bold cyan]
{', '.join(c.value for c in model.capabilities)}

[bold cyan]Fine-tuning:[/bold cyan]
[bold]Supported:[/bold] {'Yes' if model.is_fine_tunable() else 'No'}
[bold]Trainer:[/bold] {model.fine_tuning.trainer if model.is_fine_tunable() else 'N/A'}
[bold]Quantizations:[/bold] {', '.join(model.fine_tuning.quantizations) if model.is_fine_tunable() else 'N/A'}
[bold]Recommended LoRA r:[/bold] {model.fine_tuning.recommended_lora_r if model.is_fine_tunable() else 'N/A'}
    """
    
    console.print(Panel(content, title=f"Model Info: {model_id}"))


@model.command()
@click.argument('model_id')
def pull(model_id):
    """Pull a model from Ollama."""
    registry = get_registry()
    model = registry.get_model(model_id)
    
    if not model:
        console.print(f"[red]Model '{model_id}' not found in registry.[/red]")
        console.print("Run 'lab model list' to see available models.")
        return
    
    console.print(f"[green]Pulling {model.name} from Ollama...[/green]")
    console.print(f"[dim]Running: ollama pull {model.ollama_name}[/dim]")
    
    import subprocess
    try:
        result = subprocess.run(
            ['ollama', 'pull', model.ollama_name],
            capture_output=True,
            text=True,
            check=True
        )
        console.print(f"[green]Successfully pulled {model.name}![/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to pull model:[/red]")
        console.print(e.stderr)
    except FileNotFoundError:
        console.print("[red]Ollama not found. Please install Ollama first.[/red]")


@model.command()
@click.option('--name', prompt='Model name', help='Display name for the model')
@click.option('--ollama-name', prompt='Ollama model name', help='Name in Ollama (e.g., llama3.1:8b)')
@click.option('--hf-id', prompt='HuggingFace ID', help='HuggingFace model ID')
@click.option('--family', prompt='Model family', type=click.Choice(['qwen', 'llama', 'codellama', 'mistral', 'deepseek', 'custom']))
@click.option('--parameters', prompt='Parameters (e.g., 7B)', default='7B')
def add(name, ollama_name, hf_id, family, parameters):
    """Add a new model to the registry."""
    from ..core.model_info import ModelInfo, ModelFamily
    
    # Generate ID from name
    model_id = name.lower().replace(' ', '-').replace('_', '-')
    
    model_info = ModelInfo(
        id=model_id,
        name=name,
        provider='ollama',
        ollama_name=ollama_name,
        huggingface_id=hf_id or None,
        family=ModelFamily(family),
        parameters=parameters,
        capabilities=['code', 'chat']
    )
    
    registry = get_registry()
    registry.add_model(model_info)
    
    console.print(f"[green]Added model '{model_id}' to registry.[/green]")
    console.print(f"Run 'lab model pull {model_id}' to download it.")
