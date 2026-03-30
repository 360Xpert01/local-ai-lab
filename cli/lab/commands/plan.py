"""Planning commands for creating project plans."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..intelligence.ollama_client import get_ollama_client
from ..intelligence.code_generator import CodeGenerator

console = Console()

# Default plans directory
PLANS_DIR = Path("plans")


@click.group()
def plan():
    """Create and manage project plans with AI assistance."""
    pass


@plan.command()
@click.argument('project_name')
@click.option('--description', '-d', help='Brief project description')
@click.option('--tech-stack', '-t', help='Technology stack (e.g., python,react,docker)')
@click.option('--output-dir', '-o', default='plans', help='Plans directory')
@click.option('--template', type=click.Choice(['basic', 'detailed', 'agile', 'architecture']), 
              default='detailed', help='Plan template type')
def create(project_name, description, tech_stack, output_dir, template):
    """Create a new project plan with AI discussion.
    
    Example:
        lab plan create my-app --description "A todo list app" --tech-stack python,react
    """
    plans_dir = Path(output_dir)
    plans_dir.mkdir(exist_ok=True)
    
    # Sanitize project name for filename
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name).lower()
    prefix = f"{safe_name}-"
    
    console.print(Panel.fit(
        f"[bold green]Project Planning Session[/bold green]\n\n"
        f"Project: [cyan]{project_name}[/cyan]\n"
        f"Template: [yellow]{template}[/yellow]\n"
        f"Output: [dim]{plans_dir}/{prefix}*.md[/dim]",
        title="🎯 Planning"
    ))
    
    # Check Ollama
    client = get_ollama_client()
    if not client.check_connection():
        console.print("[red]Ollama not running. Start with: ollama serve[/red]")
        return
    
    # Interactive planning discussion
    console.print("\n[bold cyan]Let's discuss your project...[/bold cyan]\n")
    
    # Gather information through interactive prompts
    plan_data = _gather_plan_info(project_name, description, tech_stack)
    
    # Generate plan using AI
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        progress.add_task("[cyan]AI is creating your plan...", total=None)
        
        plan_content = _generate_plan_with_ai(plan_data, template)
    
    # Save plan files
    saved_files = _save_plan_files(plans_dir, prefix, plan_content, template)
    
    # Display results
    console.print(f"\n[bold green]✓ Plan created successfully![/bold green]\n")
    console.print("[cyan]Generated files:[/cyan]")
    for f in saved_files:
        console.print(f"  [green]+[/green] {f}")
    
    # Show preview
    if saved_files:
        console.print(f"\n[bold]Preview of {Path(saved_files[0]).name}:[/bold]")
        console.print(Markdown(plan_content.get('main_plan', '')[:1000] + "..."))


@plan.command()
@click.option('--output-dir', '-o', default='plans', help='Plans directory')
def list(output_dir):
    """List all existing plans."""
    plans_dir = Path(output_dir)
    
    if not plans_dir.exists():
        console.print("[yellow]No plans directory found.[/yellow]")
        return
    
    plan_files = list(plans_dir.glob('*-plan.md'))
    
    if not plan_files:
        console.print("[yellow]No plans found. Create one with: lab plan create <name>[/yellow]")
        return
    
    console.print("\n[bold cyan]Existing Plans:[/bold cyan]\n")
    
    for f in sorted(plan_files):
        # Extract project name from filename
        project = f.name.replace('-plan.md', '')
        
        # Read first few lines for preview
        try:
            with open(f, 'r') as file:
                first_line = file.readline().strip('# \n')
                created = datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d')
        except:
            first_line = "No preview"
            created = "Unknown"
        
        console.print(f"  [cyan]{project}[/cyan]")
        console.print(f"    [dim]{first_line[:60]}...[/dim]")
        console.print(f"    [dim]Updated: {created}[/dim]\n")


@plan.command()
@click.argument('project_name')
@click.option('--output-dir', '-o', default='plans', help='Plans directory')
def show(project_name, output_dir):
    """Show a specific plan."""
    plans_dir = Path(output_dir)
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name).lower()
    plan_file = plans_dir / f"{safe_name}-plan.md"
    
    if not plan_file.exists():
        console.print(f"[red]Plan not found: {plan_file}[/red]")
        return
    
    with open(plan_file, 'r') as f:
        content = f.read()
    
    console.print(Markdown(content))


@plan.command()
@click.argument('project_name')
@click.option('--output-dir', '-o', default='plans', help='Plans directory')
def discuss(project_name, output_dir):
    """Continue discussion on an existing plan."""
    plans_dir = Path(output_dir)
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name).lower()
    plan_file = plans_dir / f"{safe_name}-plan.md"
    
    if not plan_file.exists():
        console.print(f"[red]Plan not found: {plan_file}[/red]")
        console.print("Create it first with: [cyan]lab plan create {project_name}[/cyan]")
        return
    
    # Load existing plan
    with open(plan_file, 'r') as f:
        existing_plan = f.read()
    
    console.print(Panel.fit(
        f"[bold green]Continuing Discussion: {project_name}[/bold green]",
        title="💬 Planning Session"
    ))
    
    console.print("\n[dim]Current plan loaded. Ask questions or suggest changes.[/dim]")
    console.print("[dim]Type 'save' to save changes, 'exit' to quit.\n[/dim]")
    
    # Interactive discussion
    client = get_ollama_client()
    conversation = [
        {"role": "system", "content": "You are a technical architect helping refine a project plan. Be concise and practical."},
        {"role": "user", "content": f"Here's my current plan:\n\n{existing_plan[:2000]}...\n\nLet's discuss improvements."}
    ]
    
    updated_plan = existing_plan
    
    while True:
        user_input = Prompt.ask("[bold green]You")
        
        if user_input.lower() in ['exit', 'quit']:
            break
        
        if user_input.lower() == 'save':
            # Save updated plan
            with open(plan_file, 'w') as f:
                f.write(updated_plan)
            console.print(f"[green]✓ Plan saved to {plan_file}[/green]")
            continue
        
        # Get AI response
        conversation.append({"role": "user", "content": user_input})
        
        try:
            response = client.chat(
                model="qwen2.5-coder:7b",
                messages=conversation,
                options={"temperature": 0.7}
            )
            
            ai_response = response.text
            conversation.append({"role": "assistant", "content": ai_response})
            
            console.print(Panel(ai_response, title="🤖 Architect", border_style="green"))
            
            # Check if user wants to apply changes to plan
            if any(kw in user_input.lower() for kw in ['update plan', 'add to plan', 'change plan']):
                # Generate updated plan
                console.print("[dim]Updating plan document...[/dim]")
                updated_plan = _generate_updated_plan(existing_plan, conversation)
                
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def _gather_plan_info(project_name: str, description: Optional[str], tech_stack: Optional[str]) -> dict:
    """Gather project information through interactive prompts or defaults."""
    
    # If not provided via CLI, ask interactively
    if not description:
        description = Prompt.ask("[cyan]Brief description", default="A new software project")
    
    console.print("\n[bold]Project Goals[/bold] (what problems does it solve?)")
    console.print("[dim]Press Enter to skip, type 'auto' for AI-generated goals[/dim]")
    goals = []
    
    # Check if we should auto-generate or skip interactive prompts
    first_goal = Prompt.ask(f"[cyan]Goal 1", default="")
    
    if first_goal.lower() == 'auto':
        # Auto-generate all content
        return {
            "project_name": project_name,
            "description": description,
            "goals": [],  # Will be AI-generated
            "tech_stack": [t.strip() for t in tech_stack.split(',')] if tech_stack else ["python"],
            "features": [],  # Will be AI-generated
            "constraints": [],
            "timeline": "1 month",
            "auto_generate": True,
            "created_at": datetime.now().isoformat()
        }
    
    if first_goal:
        goals.append(first_goal)
        # Continue gathering goals
        while True:
            goal = Prompt.ask(f"[cyan]Goal {len(goals) + 1}", default="")
            if not goal:
                break
            goals.append(goal)
            if len(goals) >= 5:
                break
    
    if not tech_stack:
        console.print("\n[bold]Technology Stack[/bold]")
        console.print("[dim]Examples: python,react,postgresql,docker[/dim]")
        tech_stack = Prompt.ask("[cyan]Tech stack", default="python")
    
    tech_list = [t.strip() for t in tech_stack.split(',')]
    
    # Key features
    console.print("\n[bold]Key Features[/bold]")
    features = []
    while True:
        feature = Prompt.ask(f"[cyan]Feature {len(features) + 1}", default="")
        if not feature:
            break
        features.append(feature)
        if len(features) >= 8:
            break
    
    # Constraints
    constraints = []
    if Confirm.ask("[cyan]Add constraints?", default=False):
        while True:
            constraint = Prompt.ask(f"[cyan]Constraint {len(constraints) + 1}", default="")
            if not constraint:
                break
            constraints.append(constraint)
    
    # Timeline estimate
    timeline = Prompt.ask(
        "[cyan]Expected timeline",
        choices=["1 week", "2 weeks", "1 month", "2-3 months", "6 months", "1 year"],
        default="1 month"
    )
    
    return {
        "project_name": project_name,
        "description": description,
        "goals": goals,
        "tech_stack": tech_list,
        "features": features,
        "constraints": constraints,
        "timeline": timeline,
        "auto_generate": False,
        "created_at": datetime.now().isoformat()
    }


def _generate_plan_with_ai(plan_data: dict, template: str) -> dict:
    """Generate plan content using AI."""
    client = get_ollama_client()
    
    # Build prompt based on template
    if template == 'architecture':
        system_prompt = """You are a senior system architect. Create detailed technical architecture plans.
Focus on: system components, data flow, API design, scalability, and technology choices."""
    elif template == 'agile':
        system_prompt = """You are an agile product owner. Create user stories, sprints, and backlog items.
Focus on: user stories, acceptance criteria, story points, and sprint planning."""
    else:
        system_prompt = """You are a technical project manager. Create comprehensive project plans.
Focus on: clear structure, actionable tasks, timelines, and dependencies."""
    
    # Build prompt dynamically based on available data
    prompt_parts = [
        f"Create a detailed {template} plan for the following project:",
        "",
        f"Project Name: {plan_data['project_name']}",
        f"Description: {plan_data['description']}",
    ]
    
    if plan_data.get('goals'):
        prompt_parts.extend(["", "Goals:", chr(10).join(f'- {g}' for g in plan_data['goals'])])
    
    prompt_parts.extend([
        "",
        f"Technology Stack: {', '.join(plan_data['tech_stack'])}",
    ])
    
    if plan_data.get('features'):
        prompt_parts.extend(["", "Key Features:", chr(10).join(f'- {f}' for f in plan_data['features'])])
    
    prompt_parts.extend([
        "",
        f"Timeline: {plan_data['timeline']}",
        "",
    ])
    
    if plan_data.get('auto_generate'):
        prompt_parts.append("Please also suggest appropriate goals and key features based on the project description and tech stack.")
    
    prompt_parts.extend([
        "Create a comprehensive plan with:",
        "1. Executive Summary",
        "2. Architecture/Design Overview", 
        "3. Detailed Implementation Plan with phases",
        "4. Task breakdown with estimated effort",
        "5. Technology decisions and rationale",
        "6. Risk assessment",
        "7. Next steps",
        "",
        "Format as Markdown with clear sections."
    ])
    
    prompt = "\n".join(prompt_parts)
    
    try:
        response = client.generate(
            model="qwen2.5-coder:7b",
            prompt=prompt,
            system=system_prompt,
            options={"temperature": 0.4, "num_predict": 4000}
        )
        
        main_plan = response.text
        
        # Also generate a task checklist
        checklist_prompt = f"""Based on this plan, create a simple task checklist:

{main_plan[:1000]}

Create a markdown checklist of actionable tasks organized by priority (P0, P1, P2)."""
        
        checklist_response = client.generate(
            model="qwen2.5-coder:7b",
            prompt=checklist_prompt,
            options={"temperature": 0.3, "num_predict": 2000}
        )
        
        return {
            "main_plan": main_plan,
            "checklist": checklist_response.text,
            "metadata": plan_data
        }
        
    except Exception as e:
        console.print(f"[red]Error generating plan: {e}[/red]")
        return _generate_fallback_plan(plan_data)


def _generate_fallback_plan(plan_data: dict) -> dict:
    """Generate a basic plan without AI (fallback)."""
    
    main_plan = f"""# {plan_data['project_name']} - Project Plan

## Executive Summary
{plan_data['description']}

## Goals
{chr(10).join(f'- {g}' for g in plan_data['goals'])}

## Technology Stack
{chr(10).join(f'- {t}' for t in plan_data['tech_stack'])}

## Key Features
{chr(10).join(f'- {f}' for f in plan_data['features'])}

## Timeline
{plan_data['timeline']}

## Phases

### Phase 1: Setup & Foundation
- [ ] Project setup
- [ ] Repository initialization
- [ ] Development environment setup
- [ ] CI/CD pipeline setup

### Phase 2: Core Development
- [ ] Implement core features
- [ ] Database design
- [ ] API development
- [ ] Frontend implementation

### Phase 3: Testing & Quality
- [ ] Unit tests
- [ ] Integration tests
- [ ] Security audit
- [ ] Performance testing

### Phase 4: Deployment
- [ ] Production setup
- [ ] Monitoring setup
- [ ] Documentation
- [ ] Launch

## Next Steps
1. Review and refine this plan
2. Set up project repository
3. Begin Phase 1

---
Created: {plan_data['created_at']}
"""
    
    checklist = f"""# {plan_data['project_name']} - Task Checklist

## P0 (Critical)
- [ ] Project setup and planning
- [ ] Core architecture decisions
- [ ] Development environment ready

## P1 (High Priority)
{chr(10).join(f'- [ ] Implement: {f}' for f in plan_data['features'][:3])}

## P2 (Medium Priority)
{chr(10).join(f'- [ ] Implement: {f}' for f in plan_data['features'][3:])}
"""
    
    return {
        "main_plan": main_plan,
        "checklist": checklist,
        "metadata": plan_data
    }


def _save_plan_files(plans_dir: Path, prefix: str, plan_content: dict, template: str) -> list:
    """Save plan files to disk."""
    saved = []
    
    # Main plan file
    plan_file = plans_dir / f"{prefix}plan.md"
    with open(plan_file, 'w') as f:
        f.write(plan_content['main_plan'])
    saved.append(str(plan_file))
    
    # Checklist file
    checklist_file = plans_dir / f"{prefix}checklist.md"
    with open(checklist_file, 'w') as f:
        f.write(plan_content['checklist'])
    saved.append(str(checklist_file))
    
    # Metadata file (JSON)
    import json
    metadata_file = plans_dir / f"{prefix}metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(plan_content['metadata'], f, indent=2)
    saved.append(str(metadata_file))
    
    # Architecture diagram placeholder (if architecture template)
    if template == 'architecture':
        arch_file = plans_dir / f"{prefix}architecture.md"
        with open(arch_file, 'w') as f:
            f.write(f"""# {plan_content['metadata']['project_name']} - Architecture

## System Diagram
```
[TODO: Add system architecture diagram]

You can use:
- Mermaid: https://mermaid.live
- Draw.io: https://draw.io
- Excalidraw: https://excalidraw.com
```

## Component Overview
{chr(10).join(f'- **{t}**: Description here' for t in plan_content['metadata']['tech_stack'])}

## Data Flow
1. User request → API Gateway
2. Authentication/Authorization
3. Business logic processing
4. Database operations
5. Response to user

## API Design
[TODO: Document key API endpoints]
""")
        saved.append(str(arch_file))
    
    return saved


def _generate_updated_plan(existing_plan: str, conversation: list) -> str:
    """Generate updated plan based on discussion."""
    client = get_ollama_client()
    
    prompt = f"""Based on our discussion, update the following project plan:

Current Plan:
{existing_plan}

Discussion Summary:
{chr(10).join(f"{m['role']}: {m['content'][:200]}" for m in conversation[-4:])}

Please provide the complete updated plan incorporating our discussion points."""
    
    try:
        response = client.generate(
            model="qwen2.5-coder:7b",
            prompt=prompt,
            options={"temperature": 0.4, "num_predict": 4000}
        )
        return response.text
    except:
        return existing_plan
