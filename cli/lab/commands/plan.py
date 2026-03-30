"""Planning commands with conversational memory."""

import os
import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax

from ..intelligence.ollama_client import get_ollama_client

console = Console()

# Directories
PLANS_DIR = Path("plans")
MEMORY_DIR = PLANS_DIR / ".memory"


@dataclass
class MemoryEntry:
    """A single memory/conversation entry."""
    timestamp: str
    role: str  # 'user' or 'assistant'
    content: str
    project: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class ConversationMemory:
    """Manages conversational memory stored in markdown files."""
    
    def __init__(self, memory_dir: Path = MEMORY_DIR):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: List[MemoryEntry] = []
        self.project_context: Optional[str] = None
    
    def set_project(self, project_name: str):
        """Set current project context."""
        self.project_context = project_name
    
    def add(self, role: str, content: str, tags: List[str] = None):
        """Add a memory entry."""
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            project=self.project_context,
            tags=tags or []
        )
        self.current_session.append(entry)
        
        # Auto-save to session file
        self._append_to_session(entry)
    
    def _append_to_session(self, entry: MemoryEntry):
        """Append entry to current session file."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        session_file = self.memory_dir / f"session-{date_str}.md"
        
        # Format as markdown
        time_str = datetime.fromisoformat(entry.timestamp).strftime("%H:%M:%S")
        role_emoji = "👤" if entry.role == "user" else "🤖"
        project_tag = f" `[{entry.project}]`" if entry.project else ""
        
        content = f"\n## {role_emoji} {entry.role.upper()}{project_tag} *{time_str}*\n\n{entry.content}\n"
        
        # Append to file
        with open(session_file, 'a', encoding='utf-8') as f:
            f.write(content)
    
    def save_project_memory(self, project_name: str):
        """Save current session as project-specific memory."""
        if not self.current_session:
            return
        
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name).lower()
        memory_file = self.memory_dir / f"{safe_name}-memory.md"
        
        # Build markdown content
        lines = [
            f"# Memory: {project_name}",
            "",
            f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"**Entries:** {len(self.current_session)}",
            "",
            "---",
            ""
        ]
        
        for entry in self.current_session:
            time_str = datetime.fromisoformat(entry.timestamp).strftime("%H:%M:%S")
            role_emoji = "👤" if entry.role == "user" else "🤖"
            lines.extend([
                f"## {role_emoji} {entry.role.upper()} *{time_str}*",
                "",
                entry.content,
                "",
                "---",
                ""
            ])
        
        with open(memory_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return memory_file
    
    def load_project_memory(self, project_name: str) -> List[MemoryEntry]:
        """Load previous memory for a project."""
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name).lower()
        memory_file = self.memory_dir / f"{safe_name}-memory.md"
        
        if not memory_file.exists():
            return []
        
        # Parse markdown file
        entries = []
        with open(memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parsing - split by headers
        import re as regex
        pattern = r'## [👤🤖] (\w+) \*(\d{2}:\d{2}:\d{2})\*\n\n(.*?)(?=\n\n---|\Z)'
        matches = regex.findall(pattern, content, regex.DOTALL)
        
        for role, time_str, text in matches:
            entries.append(MemoryEntry(
                timestamp=f"{datetime.now().date()}T{time_str}",
                role=role.lower(),
                content=text.strip(),
                project=project_name
            ))
        
        return entries
    
    def search_memory(self, query: str) -> List[Dict]:
        """Search through all memory files."""
        results = []
        
        for memory_file in self.memory_dir.glob("*-memory.md"):
            with open(memory_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if query.lower() in content.lower():
                # Find relevant sections
                lines = content.split('\n')
                project_name = lines[0].replace('# Memory: ', '').strip()
                
                # Extract context around match
                for i, line in enumerate(lines):
                    if query.lower() in line.lower():
                        context = '\n'.join(lines[max(0, i-3):min(len(lines), i+4)])
                        results.append({
                            'project': project_name,
                            'file': str(memory_file),
                            'context': context
                        })
                        break
        
        return results
    
    def get_summary(self) -> str:
        """Get a summary of memory."""
        memory_files = list(self.memory_dir.glob("*-memory.md"))
        session_files = list(self.memory_dir.glob("session-*.md"))
        
        lines = [
            "# Memory Summary",
            "",
            f"**Total Projects:** {len(memory_files)}",
            f"**Session Files:** {len(session_files)}",
            "",
            "## Projects with Memory",
            ""
        ]
        
        for f in sorted(memory_files):
            project_name = f.name.replace('-memory.md', '')
            stats = f.stat()
            size_kb = stats.st_size / 1024
            modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d')
            lines.append(f"- `{project_name}` - {size_kb:.1f} KB (updated {modified})")
        
        return '\n'.join(lines)


@click.group()
def plan():
    """Create project plans with conversational AI memory."""
    pass


@plan.command()
@click.argument('project_name', required=False)
@click.option('--description', '-d', help='Project description (optional)')
@click.option('--tech-stack', '-t', help='Tech stack, comma-separated (optional)')
@click.option('--template', type=click.Choice(['basic', 'detailed', 'agile', 'architecture']), 
              default='detailed', help='Plan template')
def create(project_name, description, tech_stack, template):
    """Create a project plan through interactive chat with AI.
    
    Interactive mode (no flags needed):
        lab plan create
        lab plan create my-project
    
    Quick mode (with flags):
        lab plan create my-app -d "A todo app" -t python,react
    """
    # Initialize memory system
    memory = ConversationMemory()
    
    # Get project name interactively if not provided
    if not project_name:
        project_name = Prompt.ask("[bold cyan]Project name")
        if not project_name:
            console.print("[red]Project name is required[/red]")
            return
    
    # Set project context in memory
    memory.set_project(project_name)
    
    # Check for existing memory
    existing_memory = memory.load_project_memory(project_name)
    if existing_memory:
        console.print(Panel.fit(
            f"[yellow]Found existing memory for {project_name}[/yellow]\n"
            f"Previous conversations: {len(existing_memory)} entries",
            title="💾 Memory"
        ))
        if Confirm.ask("Load previous context?", default=True):
            console.print("[dim]Loaded previous context[/dim]\n")
    
    # Create plans directory
    PLANS_DIR.mkdir(exist_ok=True)
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name).lower()
    
    console.print(Panel.fit(
        f"[bold green]🎯 Planning Session: {project_name}[/bold green]\n\n"
        f"[dim]All conversations are saved to:[/dim]\n"
        f"  • plans/.memory/{safe_name}-memory.md\n"
        f"  • plans/.memory/session-YYYY-MM-DD.md\n\n"
        f"[yellow]Commands:[/yellow]\n"
        f"  [dim]save[/dim] - Save current plan\n"
        f"  [dim]show[/dim] - Show current plan draft\n"
        f"  [dim]memory[/dim] - Search memory\n"
        f"  [dim]exit[/dim] - End session",
        title="💬 Interactive Planning"
    ))
    
    # Check Ollama
    client = get_ollama_client()
    if not client.check_connection():
        console.print("[red]Ollama not running. Start with: ollama serve[/red]")
        return
    
    # Initialize conversation with system prompt
    conversation = [
        {"role": "system", "content": """You are a technical project planning assistant. 
Help users create detailed project plans through conversation.

Guidelines:
- Ask clarifying questions to understand requirements
- Suggest technologies and architecture based on needs  
- Break down work into phases and tasks
- Identify risks and dependencies
- Be concise but thorough

When the user says 'save', summarize the plan into a structured markdown format."""}
    ]
    
    # Add existing memory to context
    for entry in existing_memory[-5:]:  # Last 5 entries for context
        conversation.append({"role": entry.role, "content": entry.content})
    
    # Initial user context
    initial_context = f"Project: {project_name}"
    if description:
        initial_context += f"\nDescription: {description}"
    if tech_stack:
        initial_context += f"\nTech Stack: {tech_stack}"
    
    initial_context += f"\n\nTemplate: {template}\n\nLet's create a project plan. What are the main goals of this project?"
    
    conversation.append({"role": "user", "content": initial_context})
    memory.add("user", initial_context, tags=["init", template])
    
    # Get initial AI response
    with console.status("[cyan]AI is thinking..."):
        response = client.chat(
            model="qwen2.5-coder:7b",
            messages=conversation,
            options={"temperature": 0.7}
        )
    
    ai_response = response.text
    conversation.append({"role": "assistant", "content": ai_response})
    memory.add("assistant", ai_response, tags=["response"])
    
    console.print(Panel(
        Markdown(ai_response),
        title="🤖 AI Architect",
        border_style="green"
    ))
    
    # Interactive conversation loop
    current_plan_draft = ""
    
    while True:
        user_input = Prompt.ask("\n[bold blue]You")
        
        if not user_input:
            continue
        
        command = user_input.lower().strip()
        
        if command == 'exit':
            if Confirm.ask("Save conversation to memory?", default=True):
                memory_file = memory.save_project_memory(project_name)
                console.print(f"[green]✓ Memory saved to {memory_file}[/green]")
            console.print("[dim]Goodbye![/dim]")
            break
        
        elif command == 'save':
            # Generate final plan
            with console.status("[cyan]Generating final plan..."):
                plan_content = _generate_final_plan(client, conversation, template)
                current_plan_draft = plan_content
            
            # Save plan files
            saved_files = _save_plan_files(plan_content, safe_name, template, memory)
            
            console.print(f"\n[bold green]✓ Plan saved![/bold green]")
            console.print("[cyan]Files created:[/cyan]")
            for f in saved_files:
                console.print(f"  [green]+[/green] {f}")
            
            # Also save memory
            memory_file = memory.save_project_memory(project_name)
            console.print(f"\n[dim]Memory saved to: {memory_file}[/dim]")
            continue
        
        elif command == 'show':
            if current_plan_draft:
                console.print(Panel(
                    Markdown(current_plan_draft[:2000] + "..."),
                    title="📋 Current Plan Draft",
                    border_style="blue"
                ))
            else:
                console.print("[yellow]No plan draft yet. Type 'save' to generate.[/yellow]")
            continue
        
        elif command == 'memory':
            search_query = Prompt.ask("[cyan]Search memory for")
            if search_query:
                results = memory.search_memory(search_query)
                if results:
                    console.print(f"\n[bold]Found {len(results)} matches:[/bold]")
                    for r in results[:3]:
                        console.print(Panel(
                            r['context'][:500],
                            title=f"📁 {r['project']}",
                            border_style="dim"
                        ))
                else:
                    console.print("[dim]No matches found[/dim]")
            continue
        
        elif command == 'summary':
            console.print(Markdown(memory.get_summary()))
            continue
        
        # Regular conversation
        conversation.append({"role": "user", "content": user_input})
        memory.add("user", user_input)
        
        with console.status("[cyan]AI is thinking..."):
            response = client.chat(
                model="qwen2.5-coder:7b",
                messages=conversation,
                options={"temperature": 0.7}
            )
        
        ai_response = response.text
        conversation.append({"role": "assistant", "content": ai_response})
        memory.add("assistant", ai_response)
        
        console.print(Panel(
            Markdown(ai_response),
            title="🤖 AI Architect",
            border_style="green"
        ))


@plan.command()
@click.argument('project_name')
def discuss(project_name):
    """Continue discussion on an existing plan with memory."""
    memory = ConversationMemory()
    memory.set_project(project_name)
    
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name).lower()
    plan_file = PLANS_DIR / f"{safe_name}-plan.md"
    
    if not plan_file.exists():
        console.print(f"[red]No plan found for '{project_name}'[/red]")
        console.print(f"Create one with: [cyan]lab plan create {project_name}[/cyan]")
        return
    
    # Load existing plan
    with open(plan_file, 'r') as f:
        plan_content = f.read()
    
    # Load memory
    existing_memory = memory.load_project_memory(project_name)
    
    console.print(Panel.fit(
        f"[bold green]💬 Continuing Discussion: {project_name}[/bold]\n\n"
        f"[dim]Loaded plan: {plan_file}[/dim]\n"
        f"[dim]Memory entries: {len(existing_memory)}[/dim]\n\n"
        f"[yellow]Commands:[/yellow] save, show, memory, exit",
        title="Planning Session"
    ))
    
    client = get_ollama_client()
    if not client.check_connection():
        console.print("[red]Ollama not running[/red]")
        return
    
    # Setup conversation
    conversation = [
        {"role": "system", "content": "You are reviewing and refining a project plan. Help improve it based on user questions."},
        {"role": "user", "content": f"Here's the current plan:\n\n{plan_content[:2000]}...\n\nLet's discuss improvements."}
    ]
    
    # Add memory context
    for entry in existing_memory[-5:]:
        conversation.append({"role": entry.role, "content": entry.content})
    
    # Interactive loop
    while True:
        user_input = Prompt.ask("\n[bold blue]You")
        
        if user_input.lower() in ['exit', 'quit']:
            if Confirm.ask("Save conversation?", default=True):
                memory.save_project_memory(project_name)
            break
        
        if user_input.lower() == 'save':
            # Regenerate plan
            with console.status("[cyan]Updating plan..."):
                new_plan = _generate_final_plan(client, conversation, 'detailed')
            
            with open(plan_file, 'w') as f:
                f.write(new_plan)
            
            console.print(f"[green]✓ Plan updated: {plan_file}[/green]")
            memory.save_project_memory(project_name)
            continue
        
        if user_input.lower() == 'show':
            console.print(Markdown(plan_content[:1500] + "..."))
            continue
        
        conversation.append({"role": "user", "content": user_input})
        memory.add("user", user_input)
        
        with console.status("[cyan]AI thinking..."):
            response = client.chat(
                model="qwen2.5-coder:7b",
                messages=conversation,
                options={"temperature": 0.7}
            )
        
        ai_response = response.text
        conversation.append({"role": "assistant", "content": ai_response})
        memory.add("assistant", ai_response)
        
        console.print(Panel(Markdown(ai_response), title="🤖 AI", border_style="green"))


@plan.command()
def list():
    """List all plans and memory."""
    if not PLANS_DIR.exists():
        console.print("[yellow]No plans directory found[/yellow]")
        return
    
    plan_files = list(PLANS_DIR.glob('*-plan.md'))
    
    console.print("\n[bold cyan]📁 Project Plans[/bold cyan]\n")
    
    if plan_files:
        for f in sorted(plan_files):
            project = f.name.replace('-plan.md', '')
            stats = f.stat()
            size = stats.st_size / 1024
            modified = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d')
            
            # Check for memory
            memory_file = MEMORY_DIR / f"{project}-memory.md"
            has_memory = memory_file.exists()
            memory_indicator = " 💾" if has_memory else ""
            
            console.print(f"  [cyan]{project}[/cyan]{memory_indicator}")
            console.print(f"    [dim]{size:.1f} KB • {modified}[/dim]")
    else:
        console.print("  [dim]No plans yet[/dim]")
    
    # Show memory summary
    if MEMORY_DIR.exists():
        console.print("\n[bold cyan]💾 Memory Storage[/bold cyan]\n")
        memory = ConversationMemory()
        console.print(Markdown(memory.get_summary()))


@plan.command()
@click.argument('project_name')
def show(project_name):
    """Show a specific plan."""
    safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-', project_name).lower()
    plan_file = PLANS_DIR / f"{safe_name}-plan.md"
    
    if not plan_file.exists():
        console.print(f"[red]Plan not found: {plan_file}[/red]")
        return
    
    with open(plan_file, 'r') as f:
        content = f.read()
    
    console.print(Markdown(content))
    
    # Show if has memory
    memory_file = MEMORY_DIR / f"{safe_name}-memory.md"
    if memory_file.exists():
        console.print(f"\n[dim]💾 Has conversation memory[/dim]")


@plan.command()
@click.argument('keyword')
def search(keyword):
    """Search through all plan memory."""
    memory = ConversationMemory()
    results = memory.search_memory(keyword)
    
    if results:
        console.print(f"\n[bold]Found {len(results)} matches for '{keyword}':[/bold]\n")
        for r in results:
            console.print(Panel(
                r['context'][:800],
                title=f"📁 {r['project']}",
                border_style="blue"
            ))
    else:
        console.print(f"[dim]No matches found for '{keyword}'[/dim]")


def _generate_final_plan(client, conversation: List[Dict], template: str) -> str:
    """Generate final plan from conversation."""
    
    # Add instruction to generate plan
    plan_prompt = """Based on our conversation, create a comprehensive project plan in markdown format.

Include:
1. Executive Summary
2. Project Goals
3. Technology Stack
4. Architecture Overview
5. Implementation Phases with tasks
6. Timeline and Milestones
7. Risk Assessment
8. Next Steps

Use proper markdown with headers, lists, and code blocks where appropriate."""
    
    final_conversation = conversation + [{"role": "user", "content": plan_prompt}]
    
    response = client.chat(
        model="qwen2.5-coder:7b",
        messages=final_conversation,
        options={"temperature": 0.4}
    )
    
    return response.text


def _save_plan_files(plan_content: str, safe_name: str, template: str, memory: ConversationMemory) -> List[str]:
    """Save plan to files."""
    saved = []
    
    # Main plan
    plan_file = PLANS_DIR / f"{safe_name}-plan.md"
    with open(plan_file, 'w') as f:
        f.write(plan_content)
    saved.append(str(plan_file))
    
    # Extract checklist from plan
    checklist = _extract_checklist(plan_content)
    if checklist:
        checklist_file = PLANS_DIR / f"{safe_name}-checklist.md"
        with open(checklist_file, 'w') as f:
            f.write(checklist)
        saved.append(str(checklist_file))
    
    # Save metadata
    metadata = {
        "project": safe_name,
        "template": template,
        "created": datetime.now().isoformat(),
        "conversation_entries": len(memory.current_session)
    }
    
    import json
    meta_file = PLANS_DIR / f"{safe_name}-metadata.json"
    with open(meta_file, 'w') as f:
        json.dump(metadata, f, indent=2)
    saved.append(str(meta_file))
    
    return saved


def _extract_checklist(plan_content: str) -> str:
    """Extract tasks from plan into a checklist."""
    lines = plan_content.split('\n')
    checklist_lines = ["# Task Checklist\n"]
    
    in_task_section = False
    for line in lines:
        # Detect task sections
        if any(kw in line.lower() for kw in ['task', 'phase', 'milestone', 'implementation']):
            if line.startswith('#'):
                in_task_section = True
                checklist_lines.append(f"\n{line}\n")
        elif line.startswith('#') and in_task_section:
            in_task_section = False
        
        # Convert list items to checkboxes
        if in_task_section and line.strip().startswith('- '):
            checklist_lines.append(f"- [ ] {line.strip()[2:]}")
        elif in_task_section and line.strip():
            checklist_lines.append(line)
    
    return '\n'.join(checklist_lines) if len(checklist_lines) > 2 else ""
