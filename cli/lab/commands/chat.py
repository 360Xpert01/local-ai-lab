"""Chat commands for interacting with agents."""

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


@click.command()
@click.option('--agent', '-a', default='code', help='Agent to chat with')
@click.option('--model', '-m', help='Model to use (overrides agent default)')
@click.option('--multi', is_flag=True, help='Chat with multiple agents simultaneously')
@click.option('--context', '-c', help='Context directory or files')
def chat(agent, model, multi, context):
    """Interactive chat with AI agents."""
    
    if multi:
        # Multi-agent chat mode
        console.print(Panel.fit(
            "[bold green]Multi-Agent Chat Mode[/bold green]\n"
            "Chatting with: code, security, ops, architect agents",
            title="Multi-Agent"
        ))
        agents = ['code', 'security', 'ops', 'architect']
    else:
        # Single agent chat
        console.print(Panel.fit(
            f"[bold green]Chat Mode: {agent}[/bold green]\n"
            f"Model: {model or 'agent default'}\n"
            f"Context: {context or 'none'}",
            title="Chat"
        ))
        agents = [agent]
    
    console.print("\n[cyan]Commands:[/cyan]")
    console.print("  [bold]/agents[/bold]  - List active agents")
    console.print("  [bold]/switch[/bold] - Switch primary agent")
    console.print("  [bold]/file[/bold]   - Include file in context")
    console.print("  [bold]/clear[/bold]  - Clear conversation")
    console.print("  [bold]/quit[/bold]   - Exit chat\n")
    
    conversation_history = []
    
    while True:
        try:
            # Get user input
            user_input = console.input("[bold green]You>[/bold green] ")
            
            # Handle commands
            if user_input.startswith('/'):
                cmd = user_input[1:].lower()
                
                if cmd == 'quit' or cmd == 'q':
                    break
                elif cmd == 'agents':
                    console.print(f"[cyan]Active agents:[/cyan] {', '.join(agents)}")
                    continue
                elif cmd == 'clear':
                    conversation_history = []
                    console.print("[dim]Conversation cleared.[/dim]")
                    continue
                else:
                    console.print(f"[yellow]Unknown command: {cmd}[/yellow]")
                    continue
            
            if not user_input.strip():
                continue
            
            # Add to history
            conversation_history.append({"role": "user", "content": user_input})
            
            # Simulate agent response
            if multi:
                # In multi-agent mode, all agents respond
                for ag in agents:
                    console.print(f"\n[bold blue]{ag}>[/bold blue] thinking...")
                    # In real implementation, this would query Ollama
                    response = f"[This would be {ag}'s response to: {user_input[:30]}...]"
                    console.print(f"{ag}: {response}\n")
                    conversation_history.append({"role": "assistant", "agent": ag, "content": response})
            else:
                console.print(f"\n[bold blue]{agent}>[/bold blue] thinking...")
                # In real implementation, this would query Ollama
                response = f"[This would be {agent}'s response using model {model or 'default'}]"
                console.print(Markdown(response))
                conversation_history.append({"role": "assistant", "content": response})
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use /quit to exit.[/yellow]")
        except EOFError:
            break
    
    console.print("\n[dim]Chat ended.[/dim]")
