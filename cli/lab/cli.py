"""Main CLI entry point for Local AI Lab."""

import click
from rich.console import Console
from rich.panel import Panel

from .commands.model import model
from .commands.agent import agent
from .commands.file import file_cmd
from .commands.chat import chat
from .commands.train import train
from .commands.multi_agent import multi

console = Console()


@click.group()
@click.version_option(version="0.1.0")
@click.pass_context
def main(ctx):
    """Local AI Lab - Dynamic Model-Agnostic AI Development Environment.
    
    A CLI-first tool for running multiple AI agents locally with Ollama.
    Supports fine-tuning via Google Colab and dynamic model selection.
    """
    pass


# Register commands
main.add_command(model)
main.add_command(agent)
main.add_command(file_cmd, name="file")
main.add_command(chat)
main.add_command(train)
main.add_command(multi)


@main.command()
def setup():
    """Initial setup for Local AI Lab."""
    from .core.registry import get_registry
    from .core.agent_config import get_agent_registry
    
    console.print(Panel.fit(
        "[bold green]Local AI Lab Setup[/bold green]\n\n"
        "Initializing configuration directories...",
        title="Welcome"
    ))
    
    # Initialize registries (creates default configs)
    model_registry = get_registry()
    agent_registry = get_agent_registry()
    
    console.print(f"[green]✓[/green] Model registry initialized at ~/.lab/config/models/")
    console.print(f"[green]✓[/green] Agent configs initialized at ~/.lab/config/agents/")
    
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Pull a base model: [cyan]lab model pull qwen2.5-coder-7b-instruct[/cyan]")
    console.print("  2. Spawn an agent: [cyan]lab agent spawn code[/cyan]")
    console.print("  3. Or run multi-agent: [cyan]lab multi demo --scenario feature-dev[/cyan]")
    console.print("  4. Start web UI: [cyan]lab server start[/cyan]")


@main.command()
def status():
    """Show system status."""
    from .core.registry import get_registry
    from .core.agent_config import get_agent_registry
    from .agents.orchestrator import get_orchestrator
    
    model_registry = get_registry()
    agent_registry = get_agent_registry()
    orchestrator = get_orchestrator()
    
    content = f"""
[bold cyan]Local AI Lab Status[/bold cyan]

[bold]Models:[/bold] {len(model_registry.list_models())} registered
[bold]Agents:[/bold] {len(agent_registry.list_agents())} configured
[bold]Active Sessions:[/bold] {len(orchestrator.sessions)}

[bold]Available Commands:[/bold]
  lab model list       - List available models
  lab agent list       - List available agents
  lab multi list       - List active multi-agent sessions
  lab multi demo       - Run a demo scenario
"""
    
    console.print(Panel(content, title="System Status"))


@main.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
def server(host, port):
    """Start the API server for Web UI."""
    import uvicorn
    from .server.api import app
    
    console.print(f"[green]Starting API server on {host}:{port}[/green]")
    uvicorn.run(app, host=host, port=port)


@main.command()
@click.argument('prompt', nargs=-1, required=True)
@click.option('--dry-run', is_flag=True, help='Show routing plan without executing')
@click.option('--output-dir', '-o', default='.', help='Output directory for generated files')
def ask(prompt, dry_run, output_dir):
    """Ask the AI to do something - generates real code using Ollama.
    
    Examples:
        lab ask "create a calculator web app" -o ./calculator
        lab ask "review my code for security issues" -f app.py
        lab ask "set up docker for my nodejs app"
        lab ask "design a database schema for an e-commerce site"
    """
    import asyncio
    import os
    from .intelligence.prompt_router import get_prompt_router
    from .agents.orchestrator import get_orchestrator
    from .intelligence.ollama_client import get_ollama_client
    from .intelligence.code_generator import CodeGenerator
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    # Join prompt arguments
    full_prompt = ' '.join(prompt)
    
    # Check Ollama connection first
    client = get_ollama_client()
    if not client.check_connection():
        console.print("[red]Error: Cannot connect to Ollama.[/red]")
        console.print("\nPlease start Ollama first:")
        console.print("  [cyan]ollama serve[/cyan]")
        console.print("\nThen pull a model:")
        console.print("  [cyan]ollama pull qwen2.5-coder:7b[/cyan]")
        return
    
    console.print(Panel.fit(
        f"[bold blue]🧠 Understanding:[/bold blue] {full_prompt[:80]}...",
        title="Intelligent Router"
    ))
    
    # Parse intent and route
    router = get_prompt_router()
    result = router.route_to_agents(full_prompt)
    intent = result['intent']
    plan = result['execution_plan']
    
    # Show routing explanation
    console.print("\n[bold cyan]Routing Decision:[/bold cyan]")
    console.print(result['explanation'])
    
    # Show execution plan
    console.print("\n[bold cyan]Execution Plan:[/bold cyan]")
    for idx, step in enumerate(plan, 1):
        agent_name = {
            'code': '💻 Code Assistant',
            'security': '🔒 Security Expert',
            'ops': '⚙️ DevOps Engineer',
            'architect': '🏗️ System Architect'
        }.get(step['agent'], step['agent'])
        
        console.print(f"  {idx}. {agent_name}")
        console.print(f"     Task: {step['task'][:60]}...")
        if step['files']:
            console.print(f"     Files: {', '.join(step['files'][:3])}")
    
    if dry_run:
        console.print("\n[yellow]Dry run - no agents spawned.[/yellow]")
        return
    
    # Execute the plan
    console.print("\n[bold green]🚀 Executing with real AI...[/bold green]")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Use progress indicator
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        progress_task = progress.add_task("[cyan]AI is working...", total=None)
        
        # Spawn primary agent and generate code
        primary_step = plan[0]
        agent_type = primary_step['agent']
        task_desc = primary_step['task']
        
        # Determine appropriate action based on agent type
        if agent_type in ['code', 'architect'] and intent.task_type.value in ['code_generation', 'database_design']:
            # Use code generator for code tasks
            generator = CodeGenerator(output_dir=output_dir)
            language = _detect_language_from_task(full_prompt)
            
            try:
                gen_result = generator.generate(
                    task=full_prompt,
                    language=language
                )
                
                progress.update(progress_task, completed=True)
                
                if gen_result.success:
                    console.print(f"\n[bold green]✓ Code generated successfully![/bold green]\n")
                    
                    if gen_result.files_created:
                        console.print("[cyan]Files created:[/cyan]")
                        for f in gen_result.files_created:
                            console.print(f"  [green]+[/green] {f}")
                    
                    if gen_result.explanation:
                        console.print(f"\n[dim]{gen_result.explanation}[/dim]")
                    
                    console.print(f"\n[bold]Output:[/bold] {os.path.abspath(output_dir)}")
                    
                    # If there are more agents in the plan, run them too
                    if len(plan) > 1:
                        console.print("\n[cyan]Running additional agents...[/cyan]")
                        _run_additional_agents(plan[1:], full_prompt, output_dir)
                        
                else:
                    console.print(f"\n[bold red]✗ Generation failed[/bold red]")
                    for error in gen_result.errors:
                        console.print(f"  [red]• {error}[/red]")
                        
            except Exception as e:
                progress.update(progress_task, completed=True)
                console.print(f"\n[red]Error: {e}[/red]")
                
        elif agent_type == 'security':
            # Security audit
            files = primary_step.get('files', [])
            result = asyncio.run(_run_security_audit(task_desc, files, output_dir))
            progress.update(progress_task, completed=True)
            console.print(f"\n[bold cyan]Security Audit Results:[/bold cyan]")
            console.print(Panel(result, title="Security Expert"))
            
        elif agent_type == 'ops':
            # DevOps setup
            generator = CodeGenerator(output_dir=output_dir)
            gen_result = generator.generate(
                task=f"Create DevOps configuration: {full_prompt}",
                language="yaml"
            )
            progress.update(progress_task, completed=True)
            
            if gen_result.success:
                console.print(f"\n[bold green]✓ DevOps configs generated![/bold green]")
                for f in gen_result.files_created:
                    console.print(f"  [green]+[/green] {f}")
            else:
                console.print(f"\n[red]Failed to generate configs[/red]")
                
        else:
            # General query
            try:
                response = client.generate(
                    model="qwen2.5-coder:7b",
                    prompt=full_prompt,
                    options={"temperature": 0.7}
                )
                progress.update(progress_task, completed=True)
                console.print(f"\n[bold cyan]Response:[/bold cyan]")
                console.print(Panel(response.text))
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
    
    return None


def _run_additional_agents(plan_steps, original_prompt, output_dir):
    """Run additional agents in the plan."""
    import asyncio
    from .agents.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    
    session = orchestrator.create_session(
        name="Follow-up tasks",
        description="Additional agent tasks",
        agents=[step['agent'] for step in plan_steps],
        output_dir=output_dir
    )
    
    async def run_tasks():
        tasks = []
        for step in plan_steps:
            task = await orchestrator.spawn_agent_task(
                session_id=session.id,
                agent_type=step['agent'],
                task_description=step['task'],
                output_dir=output_dir
            )
            tasks.append(task)
        
        # Wait for all
        while any(t.status.value in ['pending', 'running'] for t in tasks):
            await asyncio.sleep(0.5)
        
        return tasks
    
    results = asyncio.run(run_tasks())
    
    for task in results:
        if task.status.value == 'completed':
            console.print(f"  [green]✓[/green] {task.agent_type}: Done")
        else:
            console.print(f"  [red]✗[/red] {task.agent_type}: Failed")


async def _run_security_audit(description, files, output_dir):
    """Run security audit."""
    from .intelligence.ollama_client import get_ollama_client
    
    client = get_ollama_client()
    
    # Read files if they exist
    file_contents = []
    for f in (files or []):
        import os
        file_path = os.path.join(output_dir, f)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    file_contents.append(f"=== {f} ===\n{content[:2000]}...")
            except:
                pass
    
    prompt = f"""Analyze the following code for security vulnerabilities:

Task: {description}

Files to analyze:
{chr(10).join(file_contents) if file_contents else 'No specific files provided - provide general security best practices'}

Provide a security analysis with:
1. Summary of findings
2. Critical issues (if any)
3. Recommendations for fixes"""

    try:
        response = client.generate(
            model="qwen2.5-coder:7b",
            prompt=prompt,
            system="You are a security expert. Analyze code for OWASP Top 10 vulnerabilities and common security issues.",
            options={"temperature": 0.3}
        )
        return response.text
    except Exception as e:
        return f"Security audit failed: {e}"


if __name__ == '__main__':
    main()
