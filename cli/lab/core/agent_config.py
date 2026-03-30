"""Agent configuration with dynamic model selection."""

import os
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from .model_info import ModelCapability, ModelInfo
from .registry import get_registry


class ModelSelectionConfig(BaseModel):
    """Model selection configuration for an agent."""
    default: str
    requires_capabilities: List[ModelCapability] = Field(default_factory=list)
    allow_user_override: bool = True


class PromptTemplate(BaseModel):
    """Prompt template configuration."""
    template: str
    variables: List[str] = Field(default_factory=list)


class TrainingConfig(BaseModel):
    """Training configuration for an agent."""
    datasets: List[str] = Field(default_factory=list)
    hyperparameters: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Complete agent configuration."""
    name: str
    description: str
    slug: str
    model: ModelSelectionConfig
    prompt: PromptTemplate
    tools: List[str] = Field(default_factory=list)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    
    def get_default_model(self) -> Optional[ModelInfo]:
        """Get the default model for this agent."""
        registry = get_registry()
        return registry.get_model(self.model.default)
    
    def get_compatible_models(self) -> List[ModelInfo]:
        """Get all models compatible with this agent."""
        registry = get_registry()
        return registry.get_compatible_models(
            self.model.requires_capabilities,
            require_fine_tunable=True
        )
    
    def is_model_compatible(self, model_id: str) -> bool:
        """Check if a model is compatible with this agent."""
        registry = get_registry()
        model = registry.get_model(model_id)
        if not model:
            return False
        
        return all(
            model.supports_capability(cap)
            for cap in self.model.requires_capabilities
        )
    
    def render_prompt(self, **kwargs) -> str:
        """Render the prompt template with variables."""
        template = self.prompt.template
        
        # Add model info to kwargs
        if 'model' not in kwargs:
            model = self.get_default_model()
            if model:
                kwargs['model'] = {
                    'name': model.name,
                    'family': model.family.value,
                    'parameters': model.parameters
                }
        
        # Simple template rendering
        result = template
        for key, value in kwargs.items():
            placeholder = f"{{{{ {key} }}}}"
            result = result.replace(placeholder, str(value))
        
        return result


# Default agent configurations
DEFAULT_AGENTS = {
    "code-assistant": {
        "name": "Code Assistant",
        "description": "General purpose coding agent for writing and refactoring code",
        "slug": "code",
        "model": {
            "default": "qwen2.5-coder-7b-instruct",
            "requires_capabilities": ["code"],
            "allow_user_override": True
        },
        "prompt": {
            "template": """You are an expert {{ model.family }} programmer and software engineer.
Model: {{ model.name }}

Your task: {{ task_context }}

Follow these principles:
- Write clean, maintainable, and efficient code
- Follow language-specific best practices and idioms
- Add appropriate error handling and edge case handling
- Include comments for complex logic
- Use descriptive variable and function names
- Consider performance implications

Respond with code and brief explanations.""",
            "variables": ["model", "task_context"]
        },
        "tools": ["file_read", "file_write", "file_edit", "shell_execute", "git_diff"],
        "training": {
            "datasets": ["commitpack_ft", "custom_snippets"],
            "hyperparameters": {
                "lora_r": 16,
                "lora_alpha": 16,
                "max_steps": 100,
                "learning_rate": 2e-4
            }
        }
    },
    "security-expert": {
        "name": "Security Expert",
        "description": "Security-focused agent for auditing and fixing vulnerabilities",
        "slug": "security",
        "model": {
            "default": "qwen2.5-coder-7b-instruct",
            "requires_capabilities": ["code", "reasoning"],
            "allow_user_override": True
        },
        "prompt": {
            "template": """You are a cybersecurity expert and code security auditor.
Model: {{ model.name }}

Your task: {{ task_context }}

Focus on:
- Identifying security vulnerabilities (OWASP Top 10, CWEs)
- Suggesting secure coding practices
- Reviewing authentication and authorization
- Checking for injection attacks, XSS, CSRF
- Analyzing dependency vulnerabilities
- Recommending fixes with code examples

Be thorough and specific in your security analysis.""",
            "variables": ["model", "task_context"]
        },
        "tools": ["file_read", "file_write", "file_edit", "security_scan", "dependency_check"],
        "training": {
            "datasets": ["secure_code", "vulnerability_fixes"],
            "hyperparameters": {
                "lora_r": 32,
                "lora_alpha": 32,
                "max_steps": 150,
                "learning_rate": 1e-4
            }
        }
    },
    "ops-engineer": {
        "name": "DevOps Engineer",
        "description": "DevOps-focused agent for infrastructure and deployment",
        "slug": "ops",
        "model": {
            "default": "llama-3.1-8b-instruct",
            "requires_capabilities": ["code", "reasoning"],
            "allow_user_override": True
        },
        "prompt": {
            "template": """You are a DevOps engineer and infrastructure expert.
Model: {{ model.name }}

Your task: {{ task_context }}

Expertise areas:
- Docker and containerization
- Kubernetes manifests and deployments
- Terraform and infrastructure as code
- CI/CD pipelines (GitHub Actions, GitLab CI)
- Cloud platforms (AWS, GCP, Azure basics)
- Monitoring and observability
- Shell scripting and automation

Provide production-ready configurations with best practices.""",
            "variables": ["model", "task_context"]
        },
        "tools": ["file_read", "file_write", "docker_build", "k8s_apply", "terraform_plan"],
        "training": {
            "datasets": ["docker_examples", "k8s_manifests", "terraform_examples"],
            "hyperparameters": {
                "lora_r": 16,
                "lora_alpha": 16,
                "max_steps": 100,
                "learning_rate": 2e-4
            }
        }
    },
    "architect": {
        "name": "System Architect",
        "description": "Architecture-focused agent for system design and patterns",
        "slug": "architect",
        "model": {
            "default": "llama-3.1-8b-instruct",
            "requires_capabilities": ["code", "reasoning", "long_context"],
            "allow_user_override": True
        },
        "prompt": {
            "template": """You are a senior system architect and technical leader.
Model: {{ model.name }}

Your task: {{ task_context }}

Architecture expertise:
- System design patterns and trade-offs
- API design (REST, GraphQL, gRPC)
- Database schema design
- Microservices architecture
- Scalability and performance
- Technical decision documentation
- Mermaid/PlantUML diagrams

Think holistically about the system and provide well-reasoned recommendations.""",
            "variables": ["model", "task_context"]
        },
        "tools": ["file_read", "file_write", "diagram_generate", "design_doc_create"],
        "training": {
            "datasets": ["design_patterns", "system_design", "api_design"],
            "hyperparameters": {
                "lora_r": 32,
                "lora_alpha": 32,
                "max_steps": 120,
                "learning_rate": 1.5e-4
            }
        }
    }
}


class AgentRegistry:
    """Registry for agent configurations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / ".lab" / "config"
        self.agents_dir = self.config_dir / "agents"
        self._agents: Dict[str, AgentConfig] = {}
        self._load_agents()
    
    def _load_agents(self) -> None:
        """Load agent configurations."""
        # Create default agents if not exists or directory is empty
        if not self.agents_dir.exists() or not any(self.agents_dir.glob("*.yaml")):
            self._create_default_agents()
        
        # Load all agent configs
        for config_file in self.agents_dir.glob("*.yaml"):
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f)
                agent_id = config_file.stem
                self._agents[agent_id] = AgentConfig(**data)
    
    def _create_default_agents(self) -> None:
        """Create default agent configuration files."""
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        for agent_id, config in DEFAULT_AGENTS.items():
            config_file = self.agents_dir / f"{agent_id}.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """Get agent configuration by ID."""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[AgentConfig]:
        """List all available agents."""
        return list(self._agents.values())
    
    def create_agent(
        self,
        agent_id: str,
        name: str,
        description: str,
        model_id: str,
        prompt_template: str,
        tools: List[str] = None
    ) -> AgentConfig:
        """Create a new custom agent."""
        config = AgentConfig(
            name=name,
            description=description,
            slug=agent_id,
            model=ModelSelectionConfig(
                default=model_id,
                requires_capabilities=[ModelCapability.CODE],
                allow_user_override=True
            ),
            prompt=PromptTemplate(
                template=prompt_template,
                variables=["model", "task_context"]
            ),
            tools=tools or ["file_read", "file_write"],
            training=TrainingConfig()
        )
        
        # Save to file
        config_file = self.agents_dir / f"{agent_id}.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(config.model_dump(), f, default_flow_style=False, sort_keys=False)
        
        self._agents[agent_id] = config
        return config


# Global agent registry
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get global agent registry instance."""
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry
