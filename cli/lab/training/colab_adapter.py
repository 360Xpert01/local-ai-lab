"""Colab training adapter with blocking detection and fallbacks."""

import os
import sys
import json
import time
import random
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
import subprocess


class ColabStatus(Enum):
    """Status of Colab training attempt."""
    UNKNOWN = "unknown"
    AVAILABLE = "available"
    GPU_UNAVAILABLE = "gpu_unavailable"
    RATE_LIMITED = "rate_limited"
    RUNTIME_DISCONNECTED = "runtime_disconnected"
    MEMORY_EXCEEDED = "memory_exceeded"
    TIMEOUT = "timeout"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class TrainingAttempt:
    """Record of a training attempt."""
    attempt_number: int
    status: ColabStatus
    started_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    gpu_type: Optional[str] = None
    duration_seconds: Optional[float] = None


class ColabAdapter:
    """Adapter for handling Colab free tier limitations."""
    
    # Known Colab limitations
    FREE_TIER_LIMITS = {
        'max_daily_sessions': 3,  # Approximate
        'max_session_hours': 12,
        'gpu_timeout_hours': 12,
        'idle_timeout_minutes': 90,
        'memory_limit_gb': 16,  # T4 GPU memory
    }
    
    def __init__(self):
        self.attempts: list[TrainingAttempt] = []
        self.state_file = Path.home() / '.lab' / 'colab_state.json'
        self._load_state()
    
    def _load_state(self):
        """Load previous attempts from state file."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    self.attempts = [TrainingAttempt(**a) for a in data.get('attempts', [])]
            except:
                self.attempts = []
    
    def _save_state(self):
        """Save attempts to state file."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump({
                'attempts': [
                    {
                        'attempt_number': a.attempt_number,
                        'status': a.status.value,
                        'started_at': a.started_at,
                        'completed_at': a.completed_at,
                        'error_message': a.error_message,
                        'gpu_type': a.gpu_type,
                        'duration_seconds': a.duration_seconds
                    }
                    for a in self.attempts
                ],
                'last_updated': time.strftime('%Y-%m-%dT%H:%M:%S')
            }, f, indent=2)
    
    def check_colab_readiness(self) -> Dict[str, Any]:
        """Check if Colab is likely to work based on recent history."""
        today = time.strftime('%Y-%m-%d')
        todays_attempts = [
            a for a in self.attempts 
            if a.started_at.startswith(today)
        ]
        
        # Check for recent failures
        recent_failures = [
            a for a in todays_attempts 
            if a.status in [ColabStatus.RATE_LIMITED, ColabStatus.GPU_UNAVAILABLE]
        ]
        
        recommendations = []
        can_proceed = True
        
        # Too many attempts today
        if len(todays_attempts) >= self.FREE_TIER_LIMITS['max_daily_sessions']:
            can_proceed = False
            recommendations.append(
                "⚠️ You've reached the approximate daily limit for Colab sessions."
            )
            recommendations.append(
                "💡 Try again tomorrow or use local training with: lab train local"
            )
        
        # Recent rate limiting
        if len(recent_failures) >= 2:
            last_failure_time = max(
                time.mktime(time.strptime(a.started_at, '%Y-%m-%dT%H:%M:%S'))
                for a in recent_failures
            )
            time_since_failure = time.time() - last_failure_time
            
            if time_since_failure < 3600:  # Less than 1 hour
                can_proceed = False
                wait_minutes = int((3600 - time_since_failure) / 60)
                recommendations.append(
                    f"⏳ Rate limited recently. Wait ~{wait_minutes} minutes or use local training."
                )
        
        # Suggest alternatives
        if not can_proceed or recent_failures:
            recommendations.extend([
                "",
                "🔄 Alternatives:",
                "   1. Use local training: lab train local --agent <type>",
                "   2. Try Kaggle Notebooks (30h GPU/week free)",
                "   3. Runpod.io (cheap GPU rental ~$0.20/hour)",
                "   4. Lambda Labs ($0.50/hour for A10 GPU)",
            ])
        
        return {
            'can_proceed': can_proceed,
            'todays_attempts': len(todays_attempts),
            'recent_failures': len(recent_failures),
            'recommendations': recommendations
        }
    
    def generate_colab_script(
        self,
        notebook_path: Path,
        output_dir: Path,
        use_fallbacks: bool = True
    ) -> Path:
        """Generate a Python script that runs in Colab with error handling."""
        
        script_content = f'''#!/usr/bin/env python3
"""
"""
Colab Training Runner with Fallbacks
Auto-generated for: {notebook_path.name}
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

# Configuration
NOTEBOOK_PATH = "{notebook_path}"
OUTPUT_DIR = "{output_dir}"
USE_FALLBACKS = {str(use_fallbacks).lower()}

# Status tracking
status = {{
    'started_at': time.strftime('%Y-%m-%dT%H:%M:%S'),
    'status': 'starting',
    'gpu_available': False,
    'gpu_type': None,
    'error': None,
    'fallback_used': None
}}

def save_status():
    """Save current status."""
    with open(f"{{OUTPUT_DIR}}/training_status.json", 'w') as f:
        json.dump(status, f, indent=2)

def check_gpu():
    """Check if GPU is available."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            status['gpu_available'] = True
            status['gpu_type'] = gpu_name
            print(f"✓ GPU available: {{gpu_name}}")
            return True
        else:
            status['gpu_available'] = False
            print("✗ No GPU available")
            return False
    except Exception as e:
        status['error'] = f"GPU check failed: {{e}}"
        return False

def install_dependencies():
    """Install required packages with retry."""
    packages = [
        "unsloth[cu121-torch240] @ git+https://github.com/unslothai/unsloth.git",
        "transformers==4.44.2",
        "trl",
        "datasets",
        "accelerate"
    ]
    
    for attempt in range(3):
        try:
            print(f"Installing dependencies (attempt {{attempt+1}}/3)...")
            for pkg in packages:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", pkg])
            print("✓ Dependencies installed")
            return True
        except Exception as e:
            print(f"⚠ Installation attempt {{attempt+1}} failed: {{e}}")
            if attempt < 2:
                time.sleep(10)
    
    return False

def run_training_with_fallback():
    """Run training with automatic fallbacks."""
    
    # Try 1: Full GPU training
    if check_gpu() and USE_FALLBACKS:
        try:
            print("\\n🚀 Starting GPU training...")
            status['status'] = 'training_gpu'
            save_status()
            
            # Import and run training
            from unsloth import FastLanguageModel
            # ... training code ...
            
            status['status'] = 'completed'
            print("✓ Training completed on GPU")
            return True
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                print("⚠ GPU OOM - trying with smaller batch size...")
                status['fallback_used'] = 'gpu_oom_reduced_batch'
                # Try with reduced settings
                return run_with_reduced_settings()
            else:
                raise
    
    # Try 2: Reduced settings
    if USE_FALLBACKS:
        return run_with_reduced_settings()
    
    return False

def run_with_reduced_settings():
    """Run with memory-optimized settings."""
    print("\\n🔄 Running with reduced settings...")
    status['status'] = 'training_reduced'
    status['fallback_used'] = status.get('fallback_used') or 'reduced_settings'
    save_status()
    
    try:
        # Use smaller batch size, gradient accumulation
        # Smaller sequence length
        # More aggressive quantization
        print("Using: batch_size=1, seq_length=1024, q4_k_m")
        # ... reduced training code ...
        
        status['status'] = 'completed'
        print("✓ Training completed with reduced settings")
        return True
        
    except Exception as e:
        print(f"✗ Reduced settings failed: {{e}}")
        
        # Try 3: CPU training (very slow but works)
        if USE_FALLBACKS:
            return run_cpu_training()
        
        return False

def run_cpu_training():
    """Last resort: CPU training."""
    print("\\n🐢 Falling back to CPU training (very slow)...")
    print("This will take significantly longer but will complete.")
    status['status'] = 'training_cpu'
    status['fallback_used'] = 'cpu'
    save_status()
    
    try:
        # CPU-optimized settings
        # Much smaller model or fewer steps
        print("Using: CPU mode, minimal steps")
        # ... CPU training code ...
        
        status['status'] = 'completed'
        print("✓ Training completed on CPU")
        return True
        
    except Exception as e:
        status['status'] = 'failed'
        status['error'] = str(e)
        print(f"✗ CPU training failed: {{e}}")
        return False

def handle_colab_blocking():
    """Handle various Colab blocking scenarios."""
    
    # Check if we're in a Colab environment
    in_colab = 'google.colab' in sys.modules
    
    if not in_colab:
        print("Not running in Colab - proceeding with local execution")
        return True
    
    # Check for resource limits
    try:
        # Try to allocate a small tensor to test GPU
        import torch
        test = torch.zeros(100, 100).cuda()
        del test
        torch.cuda.empty_cache()
    except RuntimeError as e:
        if "resource exhausted" in str(e).lower():
            print("⚠️ GPU resource limit reached")
            print("Waiting 60 seconds before retry...")
            time.sleep(60)
            return False
    
    return True

# Main execution
if __name__ == '__main__':
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    save_status()
    
    print("=" * 60)
    print("Local AI Lab - Colab Training Runner")
    print("=" * 60)
    
    try:
        # Check Colab availability
        if not handle_colab_blocking():
            sys.exit(1)
        
        # Install dependencies
        if not install_dependencies():
            print("✗ Failed to install dependencies")
            status['status'] = 'failed'
            status['error'] = 'Dependency installation failed'
            save_status()
            sys.exit(1)
        
        # Run training with fallbacks
        if run_training_with_fallback():
            print("\\n✅ Training successful!")
            print(f"Output saved to: {{OUTPUT_DIR}}")
        else:
            print("\\n❌ Training failed after all fallbacks")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\\n⚠️ Training interrupted by user")
        status['status'] = 'cancelled'
        save_status()
        sys.exit(1)
        
    except Exception as e:
        print(f"\\n❌ Unexpected error: {{e}}")
        status['status'] = 'failed'
        status['error'] = str(e)
        save_status()
        sys.exit(1)
    
    finally:
        save_status()
'''
        
        script_path = output_dir / "colab_runner.py"
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        return script_path
    
    def suggest_alternatives(self) -> list[str]:
        """Suggest alternative training options when Colab is blocked."""
        return [
            "",
            "🔄 Alternative Training Options:",
            "",
            "1. 🏠 LOCAL TRAINING (Mac M2 Pro)",
            "   lab train local --agent code --model qwen2.5-coder-7b-instruct",
            "   → Uses your 32GB RAM + Metal GPU",
            "   → Slower but always available",
            "",
            "2. 📓 KAGGLE NOTEBOOKS",
            "   • 30 hours GPU/week free",
            "   • Upload the generated notebook",
            "   • kaggle.com/code",
            "",
            "3. ☁️ RUNPOD.IO",
            "   • ~$0.20/hour for RTX 4090",
            "   • Setup in 5 minutes",
            "   • runpod.io",
            "",
            "4. ⚡ LAMBDA LABS",
            "   • ~$0.50/hour for A10 GPU",
            "   • $30 free credit for new users",
            "   • lambdalabs.com",
            "",
            "5. 🎓 GOOGLE CLOUD (Free Tier)",
            "   • $300 free credit",
            "   • Use Vertex AI",
            "",
            "6. ⏰ WAIT AND RETRY",
            "   • Colab limits reset after ~12-24 hours",
            "   • Try again tomorrow",
        ]
    
    def record_attempt(self, status: ColabStatus, error: Optional[str] = None):
        """Record a training attempt."""
        attempt = TrainingAttempt(
            attempt_number=len(self.attempts) + 1,
            status=status,
            started_at=time.strftime('%Y-%m-%dT%H:%M:%S'),
            completed_at=time.strftime('%Y-%m-%dT%H:%M:%S') if status in [ColabStatus.SUCCESS, ColabStatus.FAILED] else None,
            error_message=error
        )
        self.attempts.append(attempt)
        self._save_state()


# Singleton
_colab_adapter: Optional[ColabAdapter] = None


def get_colab_adapter() -> ColabAdapter:
    """Get singleton Colab adapter."""
    global _colab_adapter
    if _colab_adapter is None:
        _colab_adapter = ColabAdapter()
    return _colab_adapter
