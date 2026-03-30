"""Training and fine-tuning commands with background execution."""

import click
import sys
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import time
from pathlib import Path

from ..core.agent_config import get_agent_registry
from ..core.registry import get_registry

console = Console()


@click.group()
def train():
    """Fine-tune models locally or via Google Colab."""
    pass


@train.command()
@click.option('--agent', '-a', required=True, help='Agent type to train (code, security, ops, architect)')
@click.option('--base-model', '-m', help='Base model ID (overrides agent default)')
@click.option('--steps', '-s', default=100, help='Training steps (default: 100)')
@click.option('--background', '-b', is_flag=True, help='Run training in background')
@click.option('--notify', '-n', is_flag=True, help='Send notification when complete')
def start(agent, base_model, steps, background, notify):
    """Start fine-tuning (Colab or prepare for upload)."""
    agent_registry = get_agent_registry()
    model_registry = get_registry()
    
    # Get agent config
    agent_config = (agent_registry.get_agent(f"{agent}-assistant") or 
                   agent_registry.get_agent(f"{agent}-expert"))
    
    if not agent_config:
        console.print(f"[red]Unknown agent type: {agent}[/red]")
        return
    
    # Determine base model
    if not base_model:
        base_model = agent_config.model.default
    
    model_info = model_registry.get_model(base_model)
    if not model_info:
        console.print(f"[red]Unknown model: {base_model}[/red]")
        return
    
    if not model_info.is_fine_tunable():
        console.print(f"[red]Model {base_model} does not support fine-tuning[/red]")
        return
    
    # Check Colab readiness
    from ..training.colab_adapter import get_colab_adapter
    
    colab_adapter = get_colab_adapter()
    readiness = colab_adapter.check_colab_readiness()
    
    # Display info
    console.print(Panel.fit(
        f"[bold cyan]Training Configuration[/bold cyan]\n\n"
        f"[bold]Agent:[/bold] {agent_config.name}\n"
        f"[bold]Base Model:[/bold] {model_info.name}\n"
        f"[bold]Steps:[/bold] {steps}\n"
        f"[bold]Output:[/bold] lab-{agent}-{model_info.family.value}\n\n"
        f"[yellow]⚠️ Note:[/yellow] Google Colab requires manual upload.\n"
        f"The notebook will be generated for you to upload.",
        title="Fine-tuning Setup"
    ))
    
    # Show warnings if any
    if readiness['recent_failures'] > 0:
        console.print(f"\n[yellow]⚠️ You've had {readiness['recent_failures']} failed Colab attempts today[/yellow]")
    
    if not readiness['can_proceed']:
        console.print("\n[red]⚠️ Colab rate limit likely[/red]")
        for rec in readiness['recommendations']:
            console.print(rec)
        
        # Offer local training
        if click.confirm("\nWould you like to train locally instead?"):
            ctx = click.get_current_context()
            ctx.invoke(local, agent=agent, steps=steps, background=background, notify=notify)
            return
    
    # Generate notebook
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating notebook...", total=None)
        
        try:
            notebook_path = generate_training_notebook(
                agent_config=agent_config,
                model_info=model_info,
                steps=steps,
                output_name=f"lab-{agent}-{model_info.family.value}"
            )
        except Exception as e:
            console.print(f"[red]Error generating notebook: {e}[/red]")
            console.print("[yellow]Try using local training instead:[/yellow]")
            console.print(f"  lab train local --agent {agent} --steps {steps}")
            return
        progress.update(task, completed=True)
    
    console.print(f"\n[green]✓ Notebook generated:[/green] {notebook_path}")
    
    # Print detailed Colab instructions
    console.print()
    console.print("=" * 70)
    console.print("📓 GOOGLE COLAB TRAINING - MANUAL UPLOAD REQUIRED")
    console.print("=" * 70)
    console.print()
    console.print("[yellow]Google Colab doesn't have a public API for automation.[/yellow]")
    console.print("You'll need to manually upload and run the notebook.")
    console.print()
    console.print("┌─────────────────────────────────────────────────────────────────────┐")
    console.print("│ QUICK START - 3 EASY STEPS                                          │")
    console.print("└─────────────────────────────────────────────────────────────────────┘")
    console.print()
    console.print(f"1. [bold]Open Colab:[/bold]  https://colab.research.google.com")
    console.print(f"2. [bold]Upload:[/bold]     Click 'Upload' → Select: {notebook_path}")
    console.print(f"3. [bold]Upload Data:[/bold] Upload training_data.jsonl in Files panel")
    console.print(f"4. [bold]Set GPU:[/bold]    Runtime → Change runtime → GPU")
    console.print(f"5. [bold]Run:[/bold]        Runtime → Run all (Ctrl+F9)")
    console.print()
    console.print("[dim]Training takes ~10-30 minutes. Keep the browser tab active![/dim]")
    console.print()
    console.print("=" * 70)
    
    if background:
        # Start background training preparation
        console.print("\n[cyan]Starting background training preparation...[/cyan]")
        
        from ..training.background_trainer import get_background_trainer
        trainer = get_background_trainer()
        
        job = trainer.start_training(
            agent_type=agent,
            model_id=base_model,
            training_steps=steps,
            on_progress=lambda p: console.print(f"Progress: {p}")
        )
        
        console.print(f"\n[green]✓ Background job started:[/green] {job.id}")
        console.print(f"PID: {job.pid}")
        console.print(f"\nMonitor with: [cyan]lab train status {job.id}[/cyan]")
        
        if notify:
            console.print("[dim]You'll receive a notification when complete[/dim]")
    else:
        console.print("\n[bold]Next steps:[/bold]")
        console.print("1. Open the notebook in Google Colab")
        console.print("2. Upload your training_data.jsonl file")
        console.print("3. Run all cells")
        console.print("4. Download the .gguf file when training completes")
        console.print("\nOr run in background:")
        console.print(f"  [cyan]lab train start --agent {agent} --background --notify[/cyan]")


@train.command()
@click.option('--agent', '-a', required=True, help='Agent type to train')
@click.option('--model', '-m', help='Base model (default: agent default)')
@click.option('--steps', '-s', default=100, help='Training steps')
@click.option('--batch-size', '-b', default=1, help='Batch size (default: 1 for M2)')
@click.option('--background', '-bg', is_flag=True, help='Run in background')
@click.option('--notify', '-n', is_flag=True, help='Notify when complete')
@click.option('--use-mlx', is_flag=True, default=True, help='Use Apple MLX framework')
def local(agent, model, steps, batch_size, background, notify, use_mlx):
    """Train locally on your Mac (no Colab needed)."""
    from ..training.local_trainer import get_local_trainer, LocalTrainingConfig
    
    trainer = get_local_trainer()
    
    # Check readiness
    readiness = trainer.check_readiness()
    
    # Show unsloth status
    if not readiness.get('has_unsloth', False):
        console.print("[yellow]⚠️  Note: Unsloth not available on this platform[/yellow]")
        console.print("[dim]Unsloth requires NVIDIA/AMD GPU. Using standard PyTorch instead.[/dim]")
        console.print("[dim]For faster training, consider using Google Colab:[/dim]")
        console.print("[dim]  lab train start --agent code --steps 100[/dim]")
        console.print()
    
    if not readiness['ready']:
        console.print("[red]⚠️ Issues detected:[/red]")
        for issue in readiness['issues']:
            console.print(f"  • {issue}")
        console.print("\n[yellow]Recommendations:[/yellow]")
        for rec in readiness['recommendations']:
            console.print(f"  • {rec}")
        
        if not click.confirm("\nContinue anyway?"):
            return
    
    # Get proper model ID for display
    display_model = model
    if not display_model:
        agent_registry = get_agent_registry()
        agent_config = (agent_registry.get_agent(f"{agent}-assistant") or 
                       agent_registry.get_agent(f"{agent}-expert"))
        display_model = agent_config.model.default if agent_config else 'qwen2.5-coder-7b-instruct'
    
    # Show device info
    device = readiness['device']
    content = f"""
[bold cyan]Local Training Setup[/bold cyan]

[bold]Device:[/bold] {device['platform']}
[bold]MLX Available:[/bold] {'✓' if device['has_mlx'] else '✗'}
[bold]MPS Available:[/bold] {'✓' if device['has_mps'] else '✗'}
[bold]Memory:[/bold] {device['memory_gb']:.1f} GB
[bold]Free Space:[/bold] {readiness['free_space_gb']:.1f} GB
[bold]Unsloth:[/bold] {'✓ Available' if readiness.get('has_unsloth') else '✗ Using PyTorch'}

[bold cyan]Configuration:[/bold cyan]
[bold]Agent:[/bold] {agent}
[bold]Model:[/bold] {display_model}
[bold]Steps:[/bold] {steps}
[bold]Batch Size:[/bold] {batch_size}
[bold]Estimated Time:[/bold] {trainer.get_estimated_time(steps)}
"""
    
    console.print(Panel(content))
    
    if not click.confirm("\nStart local training?"):
        return
    
    # Get proper model ID and HF ID
    model_registry = get_registry()
    agent_registry = get_agent_registry()
    
    if not model:
        # Get agent's default model
        agent_config = (agent_registry.get_agent(f"{agent}-assistant") or 
                       agent_registry.get_agent(f"{agent}-expert"))
        if agent_config:
            model = agent_config.model.default
        else:
            model = 'qwen2.5-coder-7b-instruct'  # Fallback default
    
    # Get the HuggingFace model ID
    model_info = model_registry.get_model(model)
    if model_info and model_info.huggingface_id:
        hf_model_id = model_info.huggingface_id
    else:
        hf_model_id = 'Qwen/Qwen2.5-Coder-7B-Instruct'  # Fallback
    
    # Create config
    config = LocalTrainingConfig(
        agent_type=agent,
        model_id=hf_model_id,  # Use HF ID for training
        training_steps=steps,
        batch_size=batch_size,
        use_mlx=use_mlx
    )
    
    # Generate script
    script_path = trainer.generate_training_script(config)
    console.print(f"\n[cyan]Training script generated:[/cyan] {script_path}")
    
    if background:
        # Run in background
        import subprocess
        
        console.print("\n[cyan]Starting background training...[/cyan]")
        
        # Start process
        process = subprocess.Popen(
            [sys.executable, str(script_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        console.print(f"[green]✓ Started with PID: {process.pid}[/green]")
        console.print(f"\nMonitor with: [cyan]ps aux | grep {process.pid}[/cyan]")
        console.print(f"Progress file: {trainer.output_dir}/progress_{agent}.json")
        
        if notify:
            # Start notification watcher
            console.print("[dim]Notification will be sent when complete[/dim]")
    else:
        # Run in foreground
        console.print("\n[cyan]Starting training (Ctrl+C to stop)...[/cyan]\n")
        
        import subprocess
        try:
            result = subprocess.run(
                [sys.executable, str(script_path)],
                check=True
            )
            console.print("\n[green]✅ Training completed![/green]")
            
            if notify:
                from ..training.background_trainer import NotificationManager
                NotificationManager().send(
                    "Training Complete",
                    f"Local training for {agent} agent finished!"
                )
                
        except subprocess.CalledProcessError as e:
            console.print(f"\n[red]✗ Training failed: {e}[/red]")


@train.command()
@click.argument('job_id', required=False)
def status(job_id):
    """Check training job status."""
    from ..training.background_trainer import get_background_trainer
    
    trainer = get_background_trainer()
    
    if job_id:
        # Show specific job
        job = trainer.get_job_status(job_id)
        if not job:
            console.print(f"[red]Job {job_id} not found[/red]")
            return
        
        content = f"""
[bold]Job ID:[/bold] {job.id}
[bold]Agent:[/bold] {job.agent_type}
[bold]Model:[/bold] {job.model_id}
[bold]Status:[/bold] [{get_status_color(job.status)}]{job.status.upper()}[/{get_status_color(job.status)}]
[bold]Started:[/bold] {job.started_at}
"""
        
        if job.completed_at:
            content += f"[bold]Completed:[/bold] {job.completed_at}\n"
        
        if job.progress['total_steps'] > 0:
            progress_pct = (job.progress['current_step'] / job.progress['total_steps']) * 100
            content += f"\n[bold]Progress:[/bold] {job.progress['current_step']}/{job.progress['total_steps']} ({progress_pct:.1f}%)"
            content += f"\n[bold]Loss:[/bold] {job.progress['loss']:.4f}"
        
        if job.error_message:
            content += f"\n[bold red]Error:[/bold red] {job.error_message}"
        
        console.print(Panel(content, title=f"Job Status: {job_id}"))
    else:
        # List all jobs
        jobs = trainer.list_jobs()
        
        if not jobs:
            console.print("[yellow]No training jobs found[/yellow]")
            return
        
        table = Table(title="Training Jobs")
        table.add_column("ID", style="cyan")
        table.add_column("Agent")
        table.add_column("Model")
        table.add_column("Status", style="bold")
        table.add_column("Progress")
        
        for job in jobs[:10]:  # Show last 10
            status_color = get_status_color(job.status)
            
            if job.progress['total_steps'] > 0:
                progress = f"{job.progress['current_step']}/{job.progress['total_steps']}"
            else:
                progress = "-"
            
            table.add_row(
                job.id[:20],
                job.agent_type,
                job.model_id,
                f"[{status_color}]{job.status}[/{status_color}]",
                progress
            )
        
        console.print(table)


@train.command()
@click.argument('job_id')
def stop(job_id):
    """Stop a running training job."""
    from ..training.background_trainer import get_background_trainer
    
    trainer = get_background_trainer()
    
    if trainer.stop_job(job_id):
        console.print(f"[green]✓ Job {job_id} stopped[/green]")
    else:
        console.print(f"[red]Job {job_id} not found or not running[/red]")


@train.command()
@click.argument('gguf_path')
@click.option('--name', '-n', help='Model name in Ollama')
@click.option('--agent-type', '-a', help='Agent type for system prompt')
def import_model(gguf_path, name, agent_type):
    """Import a trained GGUF model into Ollama."""
    import subprocess
    from pathlib import Path
    
    gguf = Path(gguf_path)
    if not gguf.exists():
        console.print(f"[red]File not found: {gguf_path}[/red]")
        return
    
    model_name = name or f"lab-{gguf.stem}"
    
    # Get system prompt if agent type specified
    system_prompt = "You are a helpful AI assistant."
    if agent_type:
        prompts = {
            'code': "You are an expert software engineer and coding assistant.",
            'security': "You are a cybersecurity expert and code auditor.",
            'ops': "You are a DevOps engineer and infrastructure expert.",
            'architect': "You are a senior system architect."
        }
        system_prompt = prompts.get(agent_type, system_prompt)
    
    # Create Modelfile
    modelfile_content = f"""FROM ./{gguf.name}

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER stop "<|endoftext|>"
PARAMETER stop "<|im_end|>"

SYSTEM {system_prompt}
"""
    
    import_dir = gguf.parent / f"import_{model_name}"
    import_dir.mkdir(exist_ok=True)
    
    modelfile_path = import_dir / "Modelfile"
    modelfile_path.write_text(modelfile_content)
    
    # Copy GGUF
    import_gguf = import_dir / gguf.name
    if not import_gguf.exists():
        import_gguf.write_bytes(gguf.read_bytes())
    
    console.print(f"[cyan]Importing to Ollama as '{model_name}'...[/cyan]")
    
    try:
        result = subprocess.run(
            ['ollama', 'create', model_name, '-f', 'Modelfile'],
            cwd=import_dir,
            capture_output=True,
            text=True,
            check=True
        )
        console.print(f"[green]✓ Model imported successfully![/green]")
        console.print(f"\nTest with: [cyan]ollama run {model_name}[/cyan]")
        
        # Cleanup
        import shutil
        shutil.rmtree(import_dir)
        
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Import failed:[/red]")
        console.print(e.stderr)


@train.command(name='list-datasets')
def list_datasets():
    """List available training datasets."""
    table = Table(title="Training Datasets")
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    table.add_column("Agent Types")
    
    datasets = [
        ("alpaca_code", "General programming examples", "code"),
        ("commitpack", "Code refactoring examples", "code"),
        ("secure_code", "Security patterns and fixes", "security"),
        ("docker_examples", "Docker configurations", "ops"),
        ("k8s_manifests", "Kubernetes deployments", "ops"),
        ("terraform_examples", "Infrastructure as code", "ops"),
        ("system_design", "System architecture examples", "architect"),
    ]
    
    for name, desc, agents in datasets:
        table.add_row(name, desc, agents)
    
    console.print(table)


def generate_training_notebook(agent_config, model_info, steps, output_name):
    """Generate a Jupyter notebook for Colab training."""
    import json
    from pathlib import Path
    
    notebook = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {"provenance": [], "gpuType": "T4"},
            "kernelspec": {"name": "python3", "display_name": "Python 3"},
            "language_info": {"name": "python"},
            "accelerator": "GPU"
        },
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# Fine-tuning: {model_info.name}\n",
                    f"\n",
                    f"**Agent Type:** {agent_config.name}\n",
                    f"\n",
                    f"**Base Model:** {model_info.name} ({model_info.parameters})\n",
                    f"\n",
                    f"**Training Config:**\n",
                    f"- LoRA r: {agent_config.training.hyperparameters.get('lora_r', 16)}\n",
                    f"- Max Steps: {steps}\n",
                    f"- Learning Rate: {agent_config.training.hyperparameters.get('learning_rate', 2e-4)}\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Install dependencies\n",
                    "!pip install \"unsloth[cu121-torch240] @ git+https://github.com/unslothai/unsloth.git\" --quiet\n",
                    "!pip install transformers==4.44.2 trl datasets accelerate --quiet\n",
                    "print('✓ Dependencies installed')"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "import torch\n",
                    "from unsloth import FastLanguageModel\n",
                    "\n",
                    "max_seq_length = 2048\n",
                    "dtype = None\n",
                    "load_in_4bit = True\n",
                    "\n",
                    f'model, tokenizer = FastLanguageModel.from_pretrained(\n',
                    f'    model_name="{model_info.huggingface_id}",\n',
                    "    max_seq_length=max_seq_length,\n",
                    "    dtype=dtype,\n",
                    "    load_in_4bit=load_in_4bit\n",
                    ")\n",
                    "\n",
                    f"print(f'✓ Loaded model: {model_info.name}')"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Setup LoRA\n",
                    "model = FastLanguageModel.get_peft_model(\n",
                    f"    model, r={agent_config.training.hyperparameters.get('lora_r', 16)},\n",
                    "    target_modules=[\"q_proj\", \"k_proj\", \"v_proj\", \"o_proj\",\n",
                    "                    \"gate_proj\", \"up_proj\", \"down_proj\"],\n",
                    f"    lora_alpha={agent_config.training.hyperparameters.get('lora_alpha', 16)},\n",
                    "    lora_dropout=0,\n",
                    "    bias=\"none\",\n",
                    "    use_gradient_checkpointing=\"unsloth\"\n",
                    ")\n",
                    "print('✓ LoRA configured')"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "from datasets import load_dataset\n",
                    "\n",
                    "# Load training data\n",
                    "dataset = load_dataset(\"json\", data_files=\"training_data.jsonl\", split=\"train\")\n",
                    "\n",
                    "# Format prompts\n",
                    "alpaca_prompt = '''### Instruction:\n",
                    "{}\n",
                    "\n",
                    "### Input:\n",
                    "{}\n",
                    "\n",
                    "### Response:\n",
                    "{}'''\n",
                    "\n",
                    "EOS_TOKEN = tokenizer.eos_token\n",
                    "\n",
                    "def formatting_prompts_func(examples):\n",
                    "    texts = []\n",
                    "    for inst, inp, out in zip(examples[\"instruction\"], examples[\"input\"], examples[\"output\"]):\n",
                    "        text = alpaca_prompt.format(inst, inp, out) + EOS_TOKEN\n",
                    "        texts.append(text)\n",
                    "    return {\"text\": texts}\n",
                    "\n",
                    "dataset = dataset.map(formatting_prompts_func, batched=True)\n",
                    "print(f'✓ Loaded {len(dataset)} training examples')"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "from trl import SFTTrainer\n",
                    "from transformers import TrainingArguments\n",
                    "\n",
                    "trainer = SFTTrainer(\n",
                    "    model=model,\n",
                    "    tokenizer=tokenizer,\n",
                    "    train_dataset=dataset,\n",
                    "    dataset_text_field=\"text\",\n",
                    "    max_seq_length=2048,\n",
                    "    dataset_num_proc=2,\n",
                    "    args=TrainingArguments(\n",
                    "        per_device_train_batch_size=2,\n",
                    "        gradient_accumulation_steps=4,\n",
                    "        warmup_steps=5,\n",
                    f"        max_steps={steps},\n",
                    f"        learning_rate={agent_config.training.hyperparameters.get('learning_rate', 2e-4)},\n",
                    "        logging_steps=1,\n",
                    "        optim=\"adamw_8bit\",\n",
                    "        weight_decay=0.01,\n",
                    "        lr_scheduler_type=\"linear\",\n",
                    "        seed=3407,\n",
                    "        output_dir=\"outputs\",\n",
                    "    ),\n",
                    ")\n",
                    "\n",
                    "print('✓ Training configured')"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    "# Train!\n",
                    "print('Starting training...')\n",
                    "trainer_stats = trainer.train()\n",
                    "\n",
                    f"print(f'\\n✓ Training completed!')\n",
                    "print(f\"Time: {trainer_stats.metrics.get('train_runtime', 0):.2f}s\")"
                ],
                "outputs": []
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "source": [
                    f'# Save to GGUF\n',
                    f'model.save_pretrained_gguf(\"{output_name}\", tokenizer, quantization_method=\"q4_k_m\")\n',
                    "\n",
                    "# Download\n",
                    "from google.colab import files\n",
                    f'files.download(\"{output_name}/unsloth.Q4_K_M.gguf\")\n',
                    "\n",
                    "print('✓ Model ready for download!')"
                ],
                "outputs": []
            }
        ]
    }
    
    output_path = Path.home() / '.lab' / 'training_jobs' / f"train_{agent_config.slug}_{model_info.family.value}.ipynb"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(notebook, f, indent=2)
    
    return output_path


def get_status_color(status: str) -> str:
    """Get color for status."""
    colors = {
        'completed': 'green',
        'running': 'blue',
        'pending': 'yellow',
        'failed': 'red',
        'cancelled': 'red'
    }
    return colors.get(status, 'white')
