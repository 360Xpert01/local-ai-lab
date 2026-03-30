"""Multi-agent parallel execution commands."""

import asyncio
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text

from ..agents.orchestrator import get_orchestrator, AgentStatus
from ..core.agent_config import get_agent_registry

console = Console()


@click.group()
def multi():
    """Multi-agent parallel execution commands."""
    pass


@multi.command()
@click.option('--name', default="Multi-Agent Session", help='Session name')
@click.option('--agents', required=True, help='Comma-separated agent types (code,security,ops,architect)')
@click.option('--task', required=True, help='Main task description')
@click.option('--files', help='Comma-separated list of files to work on')
@click.option('--parallel', is_flag=True, help='Run all agents in parallel')
@click.option('--pipeline', is_flag=True, help='Run agents in pipeline mode (architect → code → security)')
def spawn(name, agents, task, files, parallel, pipeline):
    """Spawn multiple agents to work on a task."""
    agent_types = [a.strip() for a in agents.split(',')]
    file_list = [f.strip() for f in files.split(',')] if files else []
    
    # Validate agents
    registry = get_agent_registry()
    for agent_type in agent_types:
        agent_config = registry.get_agent(f"{agent_type}-assistant") or registry.get_agent(f"{agent_type}-expert") or registry.get_agent(agent_type)
        if not agent_config:
            console.print(f"[red]Unknown agent type: {agent_type}[/red]")
            console.print("Available agents: code, security, ops, architect")
            return
    
    # Create session
    orchestrator = get_orchestrator()
    session = orchestrator.create_session(
        name=name,
        description=task,
        agents=agent_types
    )
    
    console.print(f"[green]Created session:[/green] {session.id}")
    console.print(f"[dim]Agents:[/dim] {', '.join(agent_types)}")
    console.print(f"[dim]Task:[/dim] {task}\n")
    
    # Setup message bus listener
    def on_event(event):
        if event["type"] == "agent.started":
            console.print(f"[blue]▶ {event['data']['agent_type']}[/blue] started: {event['data']['description'][:50]}...")
        elif event["type"] == "agent.completed":
            console.print(f"[green]✓ {event['data']['agent_type']}[/green] completed")
        elif event["type"] == "agent.failed":
            console.print(f"[red]✗ {event['data']['agent_type']}[/red] failed: {event['data']['error']}")
    
    orchestrator.message_bus.subscribe_all(on_event)
    
    # Run agents
    if pipeline:
        # Pipeline mode: architect → code → security → ops
        stages = []
        
        # Stage 1: Architecture
        if "architect" in agent_types:
            stages.append([{
                "agent": "architect",
                "description": f"Design architecture for: {task}",
                "files": file_list
            }])
        
        # Stage 2: Implementation
        code_agents = []
        if "code" in agent_types:
            code_agents.append({
                "agent": "code",
                "description": f"Implement based on architecture: {task}",
                "files": file_list
            })
        if code_agents:
            stages.append(code_agents)
        
        # Stage 3: Review
        review_agents = []
        if "security" in agent_types:
            review_agents.append({
                "agent": "security",
                "description": f"Security review: {task}",
                "files": file_list
            })
        if review_agents:
            stages.append(review_agents)
        
        # Stage 4: DevOps
        if "ops" in agent_types:
            stages.append([{
                "agent": "ops",
                "description": f"Create deployment config for: {task}",
                "files": file_list
            }])
        
        console.print("[yellow]Running in PIPELINE mode[/yellow]\n")
        results = asyncio.run(orchestrator.run_pipeline(session.id, stages))
        
    else:
        # Parallel mode: all agents at once
        tasks = []
        for agent_type in agent_types:
            agent_config = registry.get_agent(f"{agent_type}-assistant") or registry.get_agent(f"{agent_type}-expert")
            if agent_config:
                tasks.append({
                    "agent": agent_type,
                    "description": f"{agent_config.name} working on: {task}",
                    "files": file_list
                })
        
        console.print("[yellow]Running in PARALLEL mode[/yellow]\n")
        results = asyncio.run(orchestrator.run_parallel(session.id, tasks))
    
    # Show results
    console.print("\n[bold]Results:[/bold]")
    status = orchestrator.get_session_status(session.id)
    
    table = Table(title=f"Session {session.id} Results")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Result Preview")
    
    for task_id, task_data in status["tasks"].items():
        status_color = {
            "completed": "green",
            "failed": "red",
            "running": "blue",
            "pending": "yellow"
        }.get(task_data["status"], "white")
        
        result_preview = task_data.get("result", "N/A")[:60] + "..." if task_data.get("result") else "N/A"
        
        table.add_row(
            task_data["agent_type"],
            f"[{status_color}]{task_data['status'].upper()}[/{status_color}]",
            result_preview
        )
    
    console.print(table)
    
    # Show shared context
    if status["shared_context"]:
        console.print("\n[bold]Shared Context:[/bold]")
        for key, value in status["shared_context"].items():
            console.print(f"  {key}: {str(value)[:100]}...")


@multi.command()
@click.argument('session_id')
def status(session_id):
    """Check status of a multi-agent session."""
    orchestrator = get_orchestrator()
    status = orchestrator.get_session_status(session_id)
    
    if "error" in status:
        console.print(f"[red]{status['error']}[/red]")
        return
    
    content = f"""
[bold cyan]Session:[/bold cyan] {status['name']}
[bold]ID:[/bold] {session_id}
[bold]Status:[/bold] {status['status']}
[bold]Agents:[/bold] {', '.join(status['agents'])}

[bold cyan]Tasks:[/bold cyan]
"""
    
    for task_id, task in status['tasks'].items():
        status_color = {
            "completed": "green",
            "failed": "red",
            "running": "blue",
            "pending": "yellow"
        }.get(task['status'], "white")
        
        content += f"\n  {task['agent_type']}: [{status_color}]{task['status'].upper()}[/{status_color}]"
        if task.get('error'):
            content += f" [red]({task['error']})[/red]"
    
    console.print(Panel(content, title=f"Session Status: {session_id}"))


@multi.command()
def list_sessions():
    """List all active multi-agent sessions."""
    orchestrator = get_orchestrator()
    
    if not orchestrator.sessions:
        console.print("[yellow]No active sessions.[/yellow]")
        return
    
    table = Table(title="Active Multi-Agent Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Agents")
    table.add_column("Tasks", justify="right")
    table.add_column("Status")
    
    for session_id, session in orchestrator.sessions.items():
        task_count = len(session.tasks)
        completed = sum(1 for t in session.tasks.values() if t.status == AgentStatus.COMPLETED)
        
        table.add_row(
            session_id,
            session.name,
            ", ".join(session.agents),
            f"{completed}/{task_count}",
            session.status
        )
    
    console.print(table)


@multi.command()
@click.argument('session_id')
@click.option('--message', '-m', required=True, help='Message to broadcast')
def broadcast(session_id, message):
    """Broadcast a message to all agents in a session."""
    orchestrator = get_orchestrator()
    orchestrator.broadcast_to_session(session_id, message, sender="user")
    console.print(f"[green]Broadcasted to session {session_id}:[/green] {message}")


@multi.command()
@click.option('--scenario', type=click.Choice(['code-review', 'feature-dev', 'security-audit', 'infra-setup']), 
              default='feature-dev', help='Example scenario to run')
def demo(scenario):
    """Run a demo multi-agent scenario."""
    scenarios = {
        'code-review': {
            'name': 'Code Review Session',
            'agents': ['code', 'security', 'architect'],
            'task': 'Review and improve the authentication module',
            'mode': 'parallel'
        },
        'feature-dev': {
            'name': 'Feature Development',
            'agents': ['architect', 'code', 'security', 'ops'],
            'task': 'Design and implement a new REST API endpoint with Docker deployment',
            'mode': 'pipeline'
        },
        'security-audit': {
            'name': 'Security Audit',
            'agents': ['security', 'code'],
            'task': 'Audit codebase for security vulnerabilities',
            'mode': 'parallel'
        },
        'infra-setup': {
            'name': 'Infrastructure Setup',
            'agents': ['architect', 'ops'],
            'task': 'Design and implement Kubernetes deployment configuration',
            'mode': 'pipeline'
        }
    }
    
    config = scenarios[scenario]
    
    console.print(f"[bold cyan]Running Demo Scenario:[/bold cyan] {scenario}")
    console.print(f"[dim]Description:[/dim] {config['name']}")
    console.print(f"[dim]Agents:[/dim] {', '.join(config['agents'])}")
    console.print(f"[dim]Mode:[/dim] {config['mode']}\n")
    
    # Run the scenario
    ctx = click.get_current_context()
    ctx.invoke(
        spawn,
        name=config['name'],
        agents=','.join(config['agents']),
        task=config['task'],
        pipeline=(config['mode'] == 'pipeline'),
        parallel=(config['mode'] == 'parallel')
    )
