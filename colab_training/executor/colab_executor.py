"""Execute training on Google Colab automatically."""

import os
import sys
import time
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from urllib.parse import urlencode


@dataclass
class ColabConfig:
    """Configuration for Colab execution."""
    notebook_path: Path
    training_data_path: Optional[Path] = None
    google_drive_folder: Optional[str] = None  # Folder ID to save results
    timeout_hours: int = 2


class ColabExecutor:
    """
    Execute training notebooks on Google Colab.
    
    Note: Full automation requires browser automation or Colab Pro API.
    This class provides helper methods and manual workflow assistance.
    """
    
    COLAB_BASE_URL = "https://colab.research.google.com"
    
    def __init__(self):
        self.config_dir = Path.home() / '.lab' / 'colab'
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_colab_link(self, notebook_path: Path) -> str:
        """Generate a direct Colab link for a local notebook."""
        # Convert to absolute path
        notebook_path = notebook_path.resolve()
        
        # For local files, we need to upload to GitHub/Gist or use the upload method
        # For now, provide instructions
        return {
            'method': 'upload',
            'colab_url': self.COLAB_BASE_URL,
            'instructions': [
                '1. Open https://colab.research.google.com',
                '2. Click "Upload" tab',
                f'3. Select: {notebook_path}',
                '4. Upload your training_data.jsonl file',
                '5. Runtime → Change runtime type → GPU',
                '6. Runtime → Run all',
            ]
        }
    
    def generate_github_upload_instructions(self, notebook_path: Path) -> str:
        """Generate instructions for uploading to GitHub for Colab access."""
        notebook_name = notebook_path.name
        
        instructions = f"""
📓 Google Colab - Manual Upload Instructions
============================================

Since Google Colab doesn't have a public API for automation,
you'll need to manually upload the notebook:

METHOD 1: Direct Upload (Easiest)
----------------------------------
1. Open: https://colab.research.google.com
2. Click "Upload" tab
3. Select this file: {notebook_path}
4. Click "Browse" and select your training_data.jsonl
5. Runtime → Change runtime type → GPU
6. Runtime → Run all (Ctrl+F9)

METHOD 2: GitHub Integration
---------------------------
1. Create a GitHub repository (or use existing)
2. Upload {notebook_path.name} to the repo
3. Open: https://colab.research.google.com/github/YOUR_USERNAME/YOUR_REPO/blob/main/{notebook_name}
4. Upload training_data.jsonl in the Files panel
5. Runtime → GPU → Run all

METHOD 3: Google Drive
---------------------
1. Open Google Drive
2. Right-click → More → Google Colaboratory
3. File → Upload notebook → Select {notebook_path}
4. Upload training_data.jsonl
5. Runtime → GPU → Run all

TIPS FOR SUCCESS
----------------
✓ Use Chrome or Firefox (best Colab support)
✓ Keep the browser tab active (don't switch away for long)
✓ Use Colab Keep-Alive extension if needed
✓ Save to Google Drive periodically: Files → Save a copy in Drive
✓ Enable notifications: Tools → Settings → Site → Notifications

EXPECTED OUTPUT
---------------
After training completes, you'll see:
- A download prompt for the .gguf file
- Or check Files panel on the left for the model folder

IMPORT TO LOCAL
---------------
Once downloaded, import to Ollama:
    lab train import ~/Downloads/unsloth.Q4_K_M.gguf --agent-type <agent>

AUTOMATION LIMITATIONS
---------------------
Google Colab doesn't provide a public API for:
- Automated notebook execution
- File uploads
- Runtime management

This is by design to prevent abuse of free resources.

For fully automated training, consider:
- Local training: lab train local --agent <type>
- Kaggle Notebooks (better API support)
- RunPod.io or Lambda Labs (paid GPU)
"""
        return instructions
    
    def check_colab_keep_alive(self) -> Dict[str, Any]:
        """Check and provide Colab keep-alive tips."""
        return {
            'browser_tips': [
                'Keep the Colab tab visible (not minimized)',
                'Don\'t switch away for more than 10-15 minutes',
                'Use a separate browser window for other tasks',
            ],
            'extensions': {
                'chrome': 'Colab Auto Reconnect (unofficial extensions exist)',
                'firefox': 'Auto Reload Tab extensions',
            },
            'script': '''
# Run this in browser console (F12) to keep alive:
function clickConnect(){
    console.log("Clicking connect button");
    document.querySelector("colab-connect-button").click();
}
setInterval(clickConnect, 60000);  // Click every minute
'''
        }
    
    def generate_upload_script(self, notebook_path: Path) -> Path:
        """Generate a helper script for Colab upload."""
        script_content = f'''#!/bin/bash
# Colab Upload Helper
# Generated by Local AI Lab

echo "🚀 Colab Training Helper"
echo "======================="
echo ""

NOTEBOOK="{notebook_path}"

echo "Notebook: $NOTEBOOK"
echo ""

# Check if file exists
if [ ! -f "$NOTEBOOK" ]; then
    echo "❌ Notebook not found: $NOTEBOOK"
    exit 1
fi

# Open Colab in browser
echo "Opening Google Colab..."
open "https://colab.research.google.com" 2>/dev/null || \
xdg-open "https://colab.research.google.com" 2>/dev/null || \
echo "Please manually open: https://colab.research.google.com"

echo ""
echo "Next steps:"
echo "1. Click 'Upload' in Colab"
echo "2. Select: $NOTEBOOK"
echo "3. Upload your training_data.jsonl"
echo "4. Runtime → Change runtime type → GPU"
echo "5. Runtime → Run all"
echo ""

# Copy notebook path to clipboard if available
if command -v pbcopy &> /dev/null; then
    echo "$NOTEBOOK" | pbcopy
    echo "📋 Notebook path copied to clipboard!"
elif command -v xclip &> /dev/null; then
    echo "$NOTEBOOK" | xclip -selection clipboard
    echo "📋 Notebook path copied to clipboard!"
fi
'''
        
        script_path = self.config_dir / 'upload_to_colab.sh'
        script_path.write_text(script_content)
        script_path.chmod(0o755)
        
        return script_path
    
    def monitor_colab_session(self, session_url: str) -> Dict[str, Any]:
        """
        Attempt to monitor a Colab session.
        Note: Limited without authentication token.
        """
        return {
            'status': 'manual_monitoring_required',
            'message': 'Colab sessions require manual monitoring',
            'monitoring_tips': [
                'Watch the training cell output',
                'Check for "Training completed!" message',
                'Download the GGUF file when prompted',
                'If disconnected, check if checkpoint was saved',
            ]
        }
    
    def create_kaggle_version(self, notebook_path: Path) -> Dict[str, Any]:
        """Create Kaggle-compatible version (better API support)."""
        # Kaggle has better API support than Colab
        instructions = f"""
📓 Kaggle Alternative (Better for Automation)
============================================

Kaggle Notebooks offer similar free GPU access with better API support:

BENEFITS OVER COLAB:
- 30 hours GPU/week (vs Colab's variable limits)
- Better API for dataset management
- More reliable for long-running jobs
- No keep-alive needed

STEPS:
1. Go to https://www.kaggle.com/code
2. Click "New Notebook"
3. File → Upload notebook → Select {notebook_path.name}
4. Add your training_data.jsonl as a dataset
5. Settings → Accelerator → GPU T4x2
6. Run all

API ACCESS:
Kaggle offers a Python API for automation:
    pip install kaggle

UPLOAD DATASET:
    kaggle datasets init -p ./training_data
    kaggle datasets create -p ./training_data

RUN NOTEBOOK:
    kaggle kernels push -p ./notebook_folder

See: https://www.kaggle.com/docs/api
"""
        return {
            'instructions': instructions,
            'url': 'https://www.kaggle.com/code',
            'api_available': True
        }


class ColabProAutomation:
    """
    For Colab Pro users with API access (if available).
    Note: Colab Pro doesn't currently have a public automation API.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('COLAB_PRO_API_KEY')
    
    def is_available(self) -> bool:
        """Check if Colab Pro automation is available."""
        # Currently, Colab doesn't offer public automation API
        return False
    
    def execute_notebook(self, notebook_path: Path) -> Dict[str, Any]:
        """Execute notebook (placeholder for future API)."""
        return {
            'status': 'not_available',
            'message': 'Colab Pro does not currently offer automation API',
            'alternatives': [
                'Use Kaggle API for automation',
                'Use local training: lab train local',
                'Use RunPod.io API',
            ]
        }


# Singleton
_colab_executor: Optional[ColabExecutor] = None


def get_colab_executor() -> ColabExecutor:
    """Get singleton Colab executor."""
    global _colab_executor
    if _colab_executor is None:
        _colab_executor = ColabExecutor()
    return _colab_executor


def print_colab_instructions(notebook_path: Path):
    """Print clear instructions for manual Colab upload."""
    executor = get_colab_executor()
    
    print("=" * 70)
    print("📓 GOOGLE COLAB TRAINING - MANUAL UPLOAD REQUIRED")
    print("=" * 70)
    print()
    print(f"Notebook generated: {notebook_path}")
    print()
    print("Google Colab doesn't have a public API for automation.")
    print("Please follow these steps to run your training:")
    print()
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ STEP 1: Open Google Colab                                           │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print("   URL: https://colab.research.google.com")
    print()
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ STEP 2: Upload Notebook                                             │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print("   1. Click 'Upload' tab")
    print(f"   2. Select: {notebook_path}")
    print("   3. Wait for notebook to load")
    print()
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ STEP 3: Upload Training Data                                        │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print("   1. Look for 'Files' panel on the left")
    print("   2. Click 'Upload to session storage'")
    print("   3. Select your training_data.jsonl file")
    print()
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ STEP 4: Configure Runtime                                           │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print("   1. Runtime → Change runtime type")
    print("   2. Hardware accelerator: GPU")
    print("   3. GPU type: T4 (free tier)")
    print("   4. Click Save")
    print()
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ STEP 5: Run Training                                                │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print("   1. Runtime → Run all (Ctrl+F9)")
    print("   2. Wait for training to complete (~10-30 minutes)")
    print("   3. Keep browser tab active (don't minimize)")
    print()
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ STEP 6: Download Model                                              │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print("   1. A download will start automatically")
    print("   2. Or check Files panel for the model folder")
    print("   3. Download the .gguf file to your computer")
    print()
    print("┌─────────────────────────────────────────────────────────────────────┐")
    print("│ STEP 7: Import to Ollama                                            │")
    print("└─────────────────────────────────────────────────────────────────────┘")
    print("   lab train import ~/Downloads/unsloth.Q4_K_M.gguf --agent-type code")
    print()
    print("=" * 70)
    print()
    print("💡 PRO TIPS:")
    print("   • Keep the browser tab visible (Colab disconnects inactive tabs)")
    print("   • Training takes ~10-30 minutes on T4 GPU")
    print("   • If disconnected, re-run from the beginning (checkpoints auto-save)")
    print()
    print("🔄 AUTOMATION ALTERNATIVES:")
    print("   • Local training: lab train local --agent code")
    print("   • Kaggle (better API): See FINETUNING_GUIDE.md")
    print("   • Paid GPU: RunPod.io or Lambda Labs")
    print()
    print("=" * 70)
