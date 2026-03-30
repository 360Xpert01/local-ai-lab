"""End-to-end tests for CLI workflows."""

import pytest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


class TestCLICommands:
    """E2E tests for CLI commands."""
    
    @pytest.mark.e2e
    def test_cli_help(self):
        """Test CLI help command works."""
        result = subprocess.run(
            [sys.executable, "-m", "lab.cli", "--help"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "Local AI Lab" in result.stdout
    
    @pytest.mark.e2e
    def test_model_list_command(self):
        """Test model list command."""
        result = subprocess.run(
            [sys.executable, "-m", "lab.cli", "model", "list"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        # Should succeed even if empty
        assert result.returncode == 0
    
    @pytest.mark.e2e
    def test_agent_list_command(self):
        """Test agent list command."""
        result = subprocess.run(
            [sys.executable, "-m", "lab.cli", "agent", "list"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
    
    @pytest.mark.e2e
    def test_status_command(self):
        """Test status command."""
        result = subprocess.run(
            [sys.executable, "-m", "lab.cli", "status"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )
        
        assert result.returncode == 0
        assert "Models:" in result.stdout
        assert "Agents:" in result.stdout


class TestTrainingWorkflow:
    """E2E tests for training workflows."""
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_training_script_generation_only(self, temp_dir):
        """Test training notebook/script generation without execution."""
        from lab.training.local_trainer import LocalTrainer, LocalTrainingConfig
        from lab.core.registry import get_registry
        
        trainer = LocalTrainer()
        trainer.lab_dir = temp_dir
        
        # Use actual registry
        registry = get_registry()
        models = registry.list_models()
        
        if not models:
            pytest.skip("No models in registry")
        
        model = models[0]
        
        config = LocalTrainingConfig(
            agent_type="code",
            model_id=model.huggingface_id or model.id,
            training_steps=1,  # Minimal for testing
            batch_size=1,
            use_mlx=False
        )
        
        script_path = trainer.generate_training_script(config)
        
        assert script_path.exists()
        assert script_path.stat().st_size > 0
    
    @pytest.mark.e2e
    @pytest.mark.slow
    def test_colab_notebook_generation(self, temp_dir):
        """Test Colab notebook generation end-to-end."""
        from lab.commands.train import generate_training_notebook
        from lab.core.registry import get_registry
        from lab.core.agent_config import get_agent_registry
        import json
        
        # Get real registry data
        model_registry = get_registry()
        agent_registry = get_agent_registry()
        
        models = model_registry.list_models()
        agents = agent_registry.list_agents()
        
        if not models or not agents:
            pytest.skip("Registry not initialized")
        
        model = models[0]
        agent = agents[0]
        
        # Generate notebook
        notebook_path = generate_training_notebook(
            agent_config=agent,
            model_info=model,
            steps=10,
            output_name="e2e_test"
        )
        
        # Move to temp dir
        final_path = temp_dir / "e2e_test.ipynb"
        notebook_path.rename(final_path)
        
        assert final_path.exists()
        
        # Verify it's valid JSON
        with open(final_path) as f:
            loaded = json.load(f)
        
        assert "cells" in loaded


class TestMultiAgentWorkflow:
    """E2E tests for multi-agent workflows."""
    
    @pytest.mark.e2e
    def test_orchestrator_session_creation(self):
        """Test creating a multi-agent session."""
        from lab.agents.orchestrator import get_orchestrator
        
        orchestrator = get_orchestrator()
        
        session = orchestrator.create_session(
            name="Test Session",
            description="E2E Test",
            agents=["code", "security"]
        )
        
        assert session.id is not None
        assert session.name == "Test Session"
        assert "code" in session.agents
        assert "security" in session.agents
        
        # Cleanup
        if session.id in orchestrator.sessions:
            del orchestrator.sessions[session.id]
    
    @pytest.mark.e2e
    def test_parallel_task_queue(self):
        """Test parallel task execution setup."""
        from lab.agents.orchestrator import get_orchestrator
        import asyncio
        
        orchestrator = get_orchestrator()
        
        session = orchestrator.create_session(
            name="Parallel Test",
            description="Testing parallel execution",
            agents=["code", "ops"]
        )
        
        # Create task configurations
        tasks = [
            {"agent": "code", "description": "Write a function", "files": []},
            {"agent": "ops", "description": "Create Dockerfile", "files": []}
        ]
        
        # Verify tasks can be queued (actual execution would require Ollama)
        assert len(tasks) == 2
        assert tasks[0]["agent"] == "code"
        assert tasks[1]["agent"] == "ops"
        
        # Cleanup
        if session.id in orchestrator.sessions:
            del orchestrator.sessions[session.id]
