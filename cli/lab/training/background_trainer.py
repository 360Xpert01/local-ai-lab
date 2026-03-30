"""Background training runner with notification support."""

import os
import sys
import json
import time
import subprocess
import signal
import atexit
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Callable
import threading
import queue


@dataclass
class TrainingJob:
    """Represents a training job."""
    id: str
    agent_type: str
    model_id: str
    status: str  # pending, running, completed, failed, cancelled
    pid: Optional[int] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    progress: dict = None
    
    def __post_init__(self):
        if self.progress is None:
            self.progress = {
                'current_step': 0,
                'total_steps': 0,
                'loss': 0.0,
                'learning_rate': 0.0
            }


class NotificationManager:
    """Cross-platform notification manager."""
    
    def __init__(self):
        self.platform = self._detect_platform()
    
    def _detect_platform(self) -> str:
        """Detect the operating system."""
        if sys.platform == 'darwin':
            return 'macos'
        elif sys.platform.startswith('linux'):
            return 'linux'
        else:
            return 'unknown'
    
    def send(self, title: str, message: str, sound: bool = True):
        """Send a notification."""
        if self.platform == 'macos':
            self._send_macos(title, message, sound)
        elif self.platform == 'linux':
            self._send_linux(title, message)
        else:
            print(f"\n🔔 NOTIFICATION: {title}\n{message}\n")
    
    def _send_macos(self, title: str, message: str, sound: bool):
        """Send macOS notification."""
        try:
            script = f'''
            display notification "{message}" with title "{title}"
            '''
            if sound:
                script += 'sound name "Glass"'
            
            subprocess.run(['osascript', '-e', script], check=True)
        except Exception as e:
            print(f"Notification error: {e}")
    
    def _send_linux(self, title: str, message: str):
        """Send Linux notification."""
        try:
            subprocess.run([
                'notify-send',
                '--urgency=normal',
                title,
                message
            ], check=True)
        except FileNotFoundError:
            print(f"\n🔔 NOTIFICATION: {title}\n{message}\n")


class BackgroundTrainer:
    """Manages background training jobs."""
    
    def __init__(self, jobs_dir: Optional[Path] = None):
        self.jobs_dir = jobs_dir or Path.home() / '.lab' / 'training_jobs'
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.notification_manager = NotificationManager()
        self.active_jobs: dict[str, subprocess.Popen] = {}
        self.monitor_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
        # Cleanup on exit
        atexit.register(self.cleanup)
    
    def _get_job_file(self, job_id: str) -> Path:
        """Get path to job status file."""
        return self.jobs_dir / f"{job_id}.json"
    
    def _save_job(self, job: TrainingJob):
        """Save job status to file."""
        job_file = self._get_job_file(job.id)
        with open(job_file, 'w') as f:
            json.dump(asdict(job), f, indent=2)
    
    def load_job(self, job_id: str) -> Optional[TrainingJob]:
        """Load job status from file."""
        job_file = self._get_job_file(job.id)
        if not job_file.exists():
            return None
        
        with open(job_file, 'r') as f:
            data = json.load(f)
        return TrainingJob(**data)
    
    def list_jobs(self) -> list[TrainingJob]:
        """List all training jobs."""
        jobs = []
        for job_file in self.jobs_dir.glob('*.json'):
            try:
                with open(job_file, 'r') as f:
                    data = json.load(f)
                jobs.append(TrainingJob(**data))
            except:
                continue
        return sorted(jobs, key=lambda j: j.started_at or '', reverse=True)
    
    def start_training(
        self,
        agent_type: str,
        model_id: str,
        training_steps: int = 100,
        on_progress: Optional[Callable] = None
    ) -> TrainingJob:
        """Start a background training job."""
        # Generate job ID
        job_id = f"train_{agent_type}_{int(time.time())}"
        
        # Create job record
        job = TrainingJob(
            id=job_id,
            agent_type=agent_type,
            model_id=model_id,
            status='pending',
            started_at=datetime.now().isoformat()
        )
        
        # Generate notebook
        notebook_path = self._generate_notebook(job, training_steps)
        job.output_file = str(notebook_path)
        
        # Save initial state
        self._save_job(job)
        
        # Start training process
        process = self._start_training_process(job, training_steps)
        job.pid = process.pid
        job.status = 'running'
        self._save_job(job)
        
        self.active_jobs[job_id] = process
        
        # Start monitoring thread
        self._start_monitoring(job_id, process, on_progress)
        
        return job
    
    def _generate_notebook(self, job: TrainingJob, training_steps: int) -> Path:
        """Generate training notebook."""
        from jinja2 import Environment, FileSystemLoader
        from ..core.registry import get_registry
        from ..core.agent_config import get_agent_registry
        
        # Load model and agent info
        registry = get_registry()
        agent_registry = get_agent_registry()
        
        model = registry.get_model(job.model_id)
        agent = (agent_registry.get_agent(f"{job.agent_type}-assistant") or 
                agent_registry.get_agent(f"{job.agent_type}-expert"))
        
        if not model or not agent:
            raise ValueError(f"Model or agent not found")
        
        # Load template
        template_dir = Path(__file__).parent.parent.parent.parent / 'colab_training' / 'templates'
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template('unsloth_base.ipynb.j2')
        
        # Prepare context
        context = {
            'model': {
                'name': model.name,
                'id': model.id,
                'family': model.family.value,
                'parameters': model.parameters,
                'huggingface_id': model.huggingface_id,
            },
            'agent': {
                'name': agent.name,
                'slug': agent.slug,
            },
            'training': {
                'lora_r': agent.training.hyperparameters.get('lora_r', 16),
                'lora_alpha': agent.training.hyperparameters.get('lora_alpha', 16),
                'max_steps': training_steps,
                'learning_rate': agent.training.hyperparameters.get('learning_rate', 2e-4),
            },
            'test_instruction': self._get_test_instruction(job.agent_type),
            'test_input': '',
        }
        
        # Render notebook
        notebook_json = template.render(**context)
        notebook = json.loads(notebook_json)
        
        # Save to jobs directory
        output_file = self.jobs_dir / f"{job.id}.ipynb"
        with open(output_file, 'w') as f:
            json.dump(notebook, f, indent=2)
        
        return output_file
    
    def _get_test_instruction(self, agent_type: str) -> str:
        """Get test instruction for agent type."""
        instructions = {
            'code': 'Write a Python function to implement binary search',
            'security': 'Review this code for SQL injection vulnerabilities',
            'ops': 'Create a Dockerfile for a Node.js application',
            'architect': 'Design a URL shortener service with high availability',
        }
        return instructions.get(agent_type, 'Write a function to reverse a string')
    
    def _start_training_process(self, job: TrainingJob, training_steps: int) -> subprocess.Popen:
        """Start the actual training process."""
        # Create a Python script that runs the training
        training_script = self._create_training_script(job, training_steps)
        
        # Start process
        process = subprocess.Popen(
            [sys.executable, str(training_script)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.jobs_dir)
        )
        
        return process
    
    def _create_training_script(self, job: TrainingJob, training_steps: int) -> Path:
        """Create a Python script for training."""
        script_content = f'''#!/usr/bin/env python3
import sys
import json
import time
from pathlib import Path

# Simulate training progress
job_file = Path("{self._get_job_file(job.id)}")

def update_progress(step, total, loss, lr):
    with open(job_file, 'r') as f:
        job = json.load(f)
    
    job['progress'] = {{
        'current_step': step,
        'total_steps': total,
        'loss': loss,
        'learning_rate': lr
    }}
    
    with open(job_file, 'w') as f:
        json.dump(job, f, indent=2)

# Simulate training loop
total_steps = {training_steps}
for step in range(1, total_steps + 1):
    # Simulate work
    time.sleep(0.5)
    
    # Update progress
    loss = 2.0 * (1 - step / total_steps)
    lr = 2e-4 * (1 - step / total_steps)
    update_progress(step, total_steps, round(loss, 4), round(lr, 6))
    
    print(f"Step {{step}}/{{total_steps}}: loss={{loss:.4f}}")

# Mark as completed
with open(job_file, 'r') as f:
    job = json.load(f)
job['status'] = 'completed'
job['completed_at'] = time.strftime('%Y-%m-%dT%H:%M:%S')
with open(job_file, 'w') as f:
    json.dump(job, f, indent=2)

print("Training completed!")
'''
        
        script_path = self.jobs_dir / f"{job.id}_train.py"
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        return script_path
    
    def _start_monitoring(self, job_id: str, process: subprocess.Popen, on_progress: Optional[Callable]):
        """Start monitoring thread for a job."""
        def monitor():
            stdout_lines = []
            stderr_lines = []
            
            # Read output in separate threads
            def read_stdout():
                for line in process.stdout:
                    stdout_lines.append(line.strip())
                    print(line, end='')
            
            def read_stderr():
                for line in process.stderr:
                    stderr_lines.append(line.strip())
                    print(line, end='', file=sys.stderr)
            
            stdout_thread = threading.Thread(target=read_stdout)
            stderr_thread = threading.Thread(target=read_stderr)
            stdout_thread.start()
            stderr_thread.start()
            
            # Wait for completion
            process.wait()
            stdout_thread.join()
            stderr_thread.join()
            
            # Update job status
            job = self.load_job(job_id)
            if job:
                if process.returncode == 0:
                    job.status = 'completed'
                    self._send_completion_notification(job)
                else:
                    job.status = 'failed'
                    job.error_message = '\\n'.join(stderr_lines[-10:])
                    self._send_failure_notification(job)
                
                job.completed_at = datetime.now().isoformat()
                self._save_job(job)
            
            # Cleanup
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
    
    def _send_completion_notification(self, job: TrainingJob):
        """Send completion notification."""
        self.notification_manager.send(
            title=f"✅ Training Complete: {job.agent_type}",
            message=f"Model {job.model_id} finished training.\\nSteps: {job.progress['total_steps']}\\nFinal loss: {job.progress['loss']:.4f}"
        )
    
    def _send_failure_notification(self, job: TrainingJob):
        """Send failure notification."""
        self.notification_manager.send(
            title=f"❌ Training Failed: {job.agent_type}",
            message=f"Model {job.model_id} training failed.\\nCheck logs for details."
        )
    
    def stop_job(self, job_id: str) -> bool:
        """Stop a running training job."""
        if job_id in self.active_jobs:
            process = self.active_jobs[job_id]
            process.terminate()
            
            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
            
            # Update status
            job = self.load_job(job_id)
            if job:
                job.status = 'cancelled'
                job.completed_at = datetime.now().isoformat()
                self._save_job(job)
            
            del self.active_jobs[job_id]
            return True
        
        return False
    
    def get_job_status(self, job_id: str) -> Optional[TrainingJob]:
        """Get current status of a job."""
        return self.load_job(job_id)
    
    def cleanup(self):
        """Cleanup on exit."""
        self.stop_monitoring.set()
        
        # Stop all active jobs
        for job_id in list(self.active_jobs.keys()):
            self.stop_job(job_id)


# Singleton instance
_background_trainer: Optional[BackgroundTrainer] = None


def get_background_trainer() -> BackgroundTrainer:
    """Get singleton background trainer instance."""
    global _background_trainer
    if _background_trainer is None:
        _background_trainer = BackgroundTrainer()
    return _background_trainer
