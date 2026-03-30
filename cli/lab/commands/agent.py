"""Agent management commands."""

import os
import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..core.agent_config import get_agent_registry, AgentConfig
from ..core.registry import get_registry
from ..intelligence.code_generator import CodeGenerator
from ..agents.orchestrator import get_orchestrator

console = Console()


@click.group()
def agent():
    """Manage and spawn AI agents."""
    pass


@agent.command(name='list')
def list_agents():
    """List all available agents."""
    registry = get_agent_registry()
    agents = registry.list_agents()
    
    table = Table(title="Available Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    table.add_column("Default Model")
    table.add_column("Tools Count", justify="right")
    
    for agent_config in agents:
        default_model = agent_config.get_default_model()
        table.add_row(
            agent_config.slug,
            agent_config.name,
            agent_config.description[:50] + "..." if len(agent_config.description) > 50 else agent_config.description,
            default_model.id if default_model else "N/A",
            str(len(agent_config.tools))
        )
    
    console.print(table)


@agent.command()
@click.argument('agent_type')
@click.option('--model', help='Override default model')
@click.option('--task', '-t', help='Task for the agent to complete')
@click.option('--files', '-f', help='Comma-separated files to work on')
@click.option('--output-dir', '-o', default='.', help='Output directory for generated files')
@click.option('--interactive', '-i', is_flag=True, help='Interactive chat mode')
@click.option('--dry-run', is_flag=True, help='Show what would be done without executing')
def spawn(agent_type, model, task, files, output_dir, interactive, dry_run):
    """Spawn an agent to work on a task and generate code.
    
    Examples:
        lab agent spawn code --task "create a flask api with user auth"
        lab agent spawn code --task "build a react todo app" --output-dir ./my-app
        lab agent spawn security --files "app.py,models.py" --task "audit for vulnerabilities"
    """
    registry = get_agent_registry()
    
    # Try different agent ID patterns
    agent_config = (registry.get_agent(f"{agent_type}-assistant") or 
                   registry.get_agent(f"{agent_type}-expert") or 
                   registry.get_agent(f"{agent_type}-engineer") or
                   registry.get_agent(agent_type))
    
    if not agent_config:
        console.print(f"[red]Unknown agent type: {agent_type}[/red]")
        console.print("Available agents:")
        for a in registry.list_agents():
            console.print(f"  - {a.slug}: {a.name}")
        return
    
    # Validate model if specified
    if model:
        if not agent_config.is_model_compatible(model):
            compatible = agent_config.get_compatible_models()
            console.print(f"[red]Model '{model}' is not compatible with {agent_type} agent.[/red]")
            console.print(f"Compatible models: {', '.join(m.id for m in compatible)}")
            return
        selected_model = get_registry().get_model(model)
    else:
        selected_model = agent_config.get_default_model()
    
    model_name = selected_model.ollama_name if selected_model else "qwen2.5-coder:7b"
    
    # Parse files
    file_list = [f.strip() for f in files.split(',')] if files else []
    
    console.print(Panel.fit(
        f"[bold green]Spawning {agent_config.name}[/bold green]\n\n"
        f"[bold]Model:[/bold] {model_name}\n"
        f"[bold]Task:[/bold] {task or 'No specific task'}\n"
        f"[bold]Files:[/bold] {', '.join(file_list) if file_list else 'None'}\n"
        f"[bold]Output:[/bold] {os.path.abspath(output_dir)}",
        title=f"Agent: {agent_type}"
    ))
    
    if dry_run:
        console.print("\n[yellow]Dry run - showing execution plan:[/yellow]")
        console.print(f"  1. Connect to Ollama with model: {model_name}")
        console.print(f"  2. Send task: {task}")
        console.print(f"  3. Generate code and write to: {output_dir}")
        return
    
    if interactive:
        _run_interactive_mode(agent_type, model_name, agent_config.name)
        return
    
    if not task:
        console.print("[red]Error: --task is required (or use --interactive for chat mode)[/red]")
        console.print("\nExample:")
        console.print(f'  lab agent spawn {agent_type} --task "create a hello world python script"')
        return
    
    # Run the agent task
    _run_agent_task(agent_type, task, file_list, output_dir, model_name)


def _run_interactive_mode(agent_type: str, model_name: str, agent_name: str):
    """Run interactive chat mode."""
    from ..intelligence.ollama_client import get_ollama_client
    
    client = get_ollama_client()
    
    # Check Ollama connection
    if not client.check_connection():
        console.print("[red]Error: Cannot connect to Ollama.[/red]")
        console.print("Please start Ollama with: [cyan]ollama serve[/cyan]")
        return
    
    console.print(f"\n[cyan]Starting interactive session with {agent_name}...[/cyan]")
    console.print("Type 'exit' or 'quit' to end the session.\n")
    
    messages = []
    
    while True:
        try:
            user_input = console.input(f"[bold green]{agent_type}>[/bold green] ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                break
            
            messages.append({"role": "user", "content": user_input})
            
            console.print(f"[dim]{agent_type} is thinking...[/dim]\n")
            
            try:
                response = client.chat(
                    model=model_name,
                    messages=messages,
                    options={"temperature": 0.7}
                )
                
                assistant_response = response.text
                messages.append({"role": "assistant", "content": assistant_response})
                
                console.print(Panel(assistant_response, title=agent_name, border_style="green"))
                
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                
        except KeyboardInterrupt:
            break
    
    console.print(f"\n[yellow]Session ended.[/yellow]")


def _run_agent_task(agent_type: str, task: str, files: list, output_dir: str, model: str):
    """Run an agent task with code generation."""
    from ..intelligence.ollama_client import get_ollama_client
    
    client = get_ollama_client()
    
    # Check Ollama connection
    if not client.check_connection():
        console.print("[red]Error: Cannot connect to Ollama.[/red]")
        console.print("Please ensure Ollama is running:")
        console.print("  1. Start Ollama: [cyan]ollama serve[/cyan]")
        console.print("  2. Verify: [cyan]ollama list[/cyan]")
        return
    
    # Create output directory if needed
    os.makedirs(output_dir, exist_ok=True)
    
    # Show progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        progress_task = progress.add_task(f"[cyan]{agent_type} agent working...", total=None)
        
        # Use orchestrator for multi-step tasks, or direct code generation for simple tasks
        if agent_type in ['code', 'architect']:
            # Direct code generation
            generator = CodeGenerator(output_dir=output_dir, model=model)
            
            language = _detect_language_from_task(task)
            
            try:
                result = generator.generate(
                    task=task,
                    language=language,
                    existing_files=files
                )
                
                progress.update(progress_task, completed=True)
                
                if result.success:
                    console.print(f"\n[bold green]✓ Task completed successfully![/bold green]\n")
                    
                    if result.files_created:
                        console.print("[cyan]Files created:[/cyan]")
                        for f in result.files_created:
                            console.print(f"  [green]+[/green] {f}")
                    
                    if result.files_updated:
                        console.print("\n[cyan]Files updated:[/cyan]")
                        for f in result.files_updated:
                            console.print(f"  [yellow]~[/yellow] {f}")
                    
                    if result.explanation:
                        console.print(f"\n[dim]{result.explanation}[/dim]")
                    
                    # Show summary
                    console.print(f"\n[bold]Summary:[/bold]")
                    console.print(f"  Output directory: {os.path.abspath(output_dir)}")
                    console.print(f"  Total files: {len(result.files_created) + len(result.files_updated)}")
                    
                else:
                    console.print("\n[bold red]✗ Task failed[/bold red]\n")
                    for error in result.errors:
                        console.print(f"  [red]• {error}[/red]")
                    
                    if result.explanation:
                        console.print(f"\n[dim]{result.explanation}[/dim]")
                        
            except Exception as e:
                progress.update(progress_task, completed=True)
                console.print(f"\n[red]Error: {e}[/red]")
                
        else:
            # Use orchestrator for other agent types
            orchestrator = get_orchestrator()
            
            # Create a session
            session = orchestrator.create_session(
                name=f"{agent_type} task",
                description=task,
                agents=[agent_type],
                output_dir=output_dir
            )
            
            # Run the task
            async def run_task():
                agent_task = await orchestrator.spawn_agent_task(
                    session_id=session.id,
                    agent_type=agent_type,
                    task_description=task,
                    files=files,
                    output_dir=output_dir
                )
                
                # Wait for completion
                while agent_task.status.value in ['pending', 'running']:
                    await asyncio.sleep(0.5)
                
                return agent_task
            
            try:
                agent_task = asyncio.run(run_task())
                progress.update(progress_task, completed=True)
                
                if agent_task.status.value == 'completed':
                    console.print(f"\n[bold green]✓ Task completed![/bold green]\n")
                    console.print(agent_task.result)
                    
                    if agent_task.generation_result:
                        if agent_task.generation_result.files_created:
                            console.print("\n[cyan]Files created:[/cyan]")
                            for f in agent_task.generation_result.files_created:
                                console.print(f"  [green]+[/green] {f}")
                else:
                    console.print(f"\n[bold red]✗ Task failed[/bold red]")
                    if agent_task.error:
                        console.print(f"[red]{agent_task.error}[/red]")
                        
            except Exception as e:
                progress.update(progress_task, completed=True)
                console.print(f"\n[red]Error: {e}[/red]")


def _detect_language_from_task(task: str) -> str:
    """Detect programming language from task description."""
    task_lower = task.lower()
    
    if any(kw in task_lower for kw in ['python', 'flask', 'django', 'fastapi']):
        return 'python'
    elif any(kw in task_lower for kw in ['javascript', 'js', 'node', 'express', 'react']):
        return 'javascript'
    elif any(kw in task_lower for kw in ['typescript', 'ts', 'angular', 'nestjs']):
        return 'typescript'
    elif any(kw in task_lower for kw in ['go ', 'golang']):
        return 'go'
    elif any(kw in task_lower for kw in ['rust', 'cargo']):
        return 'rust'
    elif any(kw in task_lower for kw in ['java', 'spring']):
        return 'java'
    elif any(kw in task_lower for kw in ['docker', 'kubernetes', 'k8s']):
        return 'yaml'
    
    return 'python'  # Default


@agent.command()
@click.argument('name')
@click.option('--base-agent', default='code-assistant', help='Base agent to copy from')
@click.option('--model', help='Default model for this agent')
def create(name, base_agent, model):
    """Create a custom agent configuration."""
    registry = get_agent_registry()
    
    base = registry.get_agent(base_agent)
    if not base:
        console.print(f"[red]Base agent '{base_agent}' not found.[/red]")
        return
    
    # Create new agent config
    new_config = registry.create_agent(
        agent_id=name,
        name=f"Custom {name.title()} Agent",
        description=f"Custom agent based on {base_agent}",
        model_id=model or base.model.default,
        prompt_template=base.prompt.template,
        tools=base.tools
    )
    
    console.print(f"[green]Created custom agent:[/green] {name}")
    console.print(f"Config saved to: ~/.lab/config/agents/{name}.yaml")


@agent.command()
@click.argument('agent_type')
def info(agent_type):
    """Show detailed information about an agent."""
    registry = get_agent_registry()
    
    agent_config = (registry.get_agent(f"{agent_type}-assistant") or 
                   registry.get_agent(f"{agent_type}-expert") or 
                   registry.get_agent(agent_type))
    
    if not agent_config:
        console.print(f"[red]Agent '{agent_type}' not found.[/red]")
        return
    
    default_model = agent_config.get_default_model()
    compatible_models = agent_config.get_compatible_models()
    
    content = f"""
[bold cyan]Agent:[/bold cyan] {agent_config.name}
[bold]Slug:[/bold] {agent_config.slug}
[bold]Description:[/bold] {agent_config.description}

[bold cyan]Model Configuration:[/bold cyan]
[bold]Default Model:[/bold] {default_model.name if default_model else 'N/A'}
[bold]Compatible Models:[/bold] {', '.join(m.id for m in compatible_models)}
[bold]User Override:[/bold] {'Yes' if agent_config.model.allow_user_override else 'No'}

[bold cyan]Tools:[/bold cyan]
{chr(10).join(f'  - {tool}' for tool in agent_config.tools)}

[bold cyan]Training Configuration:[/bold cyan]
[bold]Datasets:[/bold] {', '.join(agent_config.training.datasets)}
[bold]LoRA r:[/bold] {agent_config.training.hyperparameters.get('lora_r', 'N/A')}
[bold]Max Steps:[/bold] {agent_config.training.hyperparameters.get('max_steps', 'N/A')}
    """
    
    console.print(Panel(content, title=f"Agent Info: {agent_type}"))
