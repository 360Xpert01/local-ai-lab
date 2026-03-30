"""Multi-Agent Orchestrator for parallel agent execution."""

import asyncio
import uuid
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os

from ..intelligence.code_generator import CodeGenerator, CodeGenerationResult


class AgentStatus(Enum):
    """Status of an agent worker."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentTask:
    """A task assigned to an agent."""
    id: str
    agent_type: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    files: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    generation_result: Optional[CodeGenerationResult] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "description": self.description,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "files_created": self.generation_result.files_created if self.generation_result else [],
            "files_updated": self.generation_result.files_updated if self.generation_result else [],
        }


@dataclass
class MultiAgentSession:
    """A session with multiple collaborating agents."""
    id: str
    name: str
    description: str
    agents: List[str]  # Agent types
    tasks: Dict[str, AgentTask] = field(default_factory=dict)
    shared_context: Dict[str, Any] = field(default_factory=dict)
    messages: List[Dict] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "active"
    output_dir: str = field(default=".")
    
    def add_message(self, agent: str, message: str, msg_type: str = "chat"):
        """Add a message to the shared conversation."""
        self.messages.append({
            "agent": agent,
            "message": message,
            "type": msg_type,
            "timestamp": datetime.now().isoformat()
        })
    
    def update_shared_context(self, key: str, value: Any):
        """Update shared context visible to all agents."""
        self.shared_context[key] = value


class MessageBus:
    """In-memory message bus for agent communication."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._global_subscribers: List[Callable] = []
        self._subscriber_id = 0
    
    def subscribe(self, event_type: str, callback: Callable) -> int:
        """Subscribe to a specific event type. Returns subscriber ID."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscriber_id += 1
        self._subscribers[event_type].append((self._subscriber_id, callback))
        return self._subscriber_id
    
    def subscribe_all(self, callback: Callable) -> int:
        """Subscribe to all events. Returns subscriber ID."""
        self._subscriber_id += 1
        self._global_subscribers.append((self._subscriber_id, callback))
        return self._subscriber_id
    
    def unsubscribe(self, subscriber_id: int):
        """Unsubscribe a callback by ID."""
        # Remove from specific subscribers
        for event_type in self._subscribers:
            self._subscribers[event_type] = [
                (sid, cb) for sid, cb in self._subscribers[event_type]
                if sid != subscriber_id
            ]
        # Remove from global subscribers
        self._global_subscribers = [
            (sid, cb) for sid, cb in self._global_subscribers
            if sid != subscriber_id
        ]
    
    def publish(self, event_type: str, data: Dict):
        """Publish an event to all subscribers."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Notify specific subscribers
        for sid, callback in self._subscribers.get(event_type, []):
            try:
                callback(event)
            except Exception as e:
                print(f"Error in subscriber: {e}")
        
        # Notify global subscribers
        for sid, callback in self._global_subscribers:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in global subscriber: {e}")


class MultiAgentOrchestrator:
    """Orchestrates multiple agents working in parallel."""
    
    def __init__(self):
        self.sessions: Dict[str, MultiAgentSession] = {}
        self.message_bus = MessageBus()
        self._workers: Dict[str, asyncio.Task] = {}
        self._code_generator: Optional[CodeGenerator] = None
    
    def _get_code_generator(self, output_dir: str = ".") -> CodeGenerator:
        """Get or create code generator."""
        if self._code_generator is None:
            self._code_generator = CodeGenerator(output_dir=output_dir)
        return self._code_generator
    
    def create_session(
        self,
        name: str,
        description: str,
        agents: List[str],
        output_dir: str = "."
    ) -> MultiAgentSession:
        """Create a new multi-agent session."""
        session_id = str(uuid.uuid4())[:8]
        session = MultiAgentSession(
            id=session_id,
            name=name,
            description=description,
            agents=agents,
            output_dir=output_dir
        )
        self.sessions[session_id] = session
        return session
    
    async def spawn_agent_task(
        self,
        session_id: str,
        agent_type: str,
        task_description: str,
        files: List[str] = None,
        depends_on: List[str] = None,
        output_dir: str = "."
    ) -> AgentTask:
        """Spawn an agent task, optionally waiting for dependencies."""
        session = self.sessions.get(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        task_id = f"{agent_type}-{str(uuid.uuid4())[:6]}"
        task = AgentTask(
            id=task_id,
            agent_type=agent_type,
            description=task_description,
            files=files or []
        )
        
        session.tasks[task_id] = task
        
        # Start worker
        worker = asyncio.create_task(
            self._run_agent_worker(session_id, task_id, agent_type, task_description, output_dir)
        )
        self._workers[task_id] = worker
        
        return task
    
    async def _run_agent_worker(
        self,
        session_id: str,
        task_id: str,
        agent_type: str,
        task_description: str,
        output_dir: str = "."
    ):
        """Run an agent worker with real code generation."""
        session = self.sessions[session_id]
        task = session.tasks[task_id]
        
        task.status = AgentStatus.RUNNING
        task.started_at = datetime.now()
        
        # Publish start event
        self.message_bus.publish("agent.started", {
            "session_id": session_id,
            "task_id": task_id,
            "agent_type": agent_type,
            "description": task_description
        })
        
        try:
            # Determine task type and execute accordingly
            if self._is_code_generation_task(task_description):
                # Use real code generation
                generator = self._get_code_generator(output_dir)
                
                # Determine language from description
                language = self._detect_language(task_description)
                
                result = generator.generate(
                    task=task_description,
                    language=language,
                    existing_files=task.files
                )
                
                task.generation_result = result
                
                if result.success:
                    task.status = AgentStatus.COMPLETED
                    task.result = f"Generated {len(result.files_created)} new file(s), updated {len(result.files_updated)} file(s).\n\n{result.explanation}"
                    
                    # Update shared context with created files
                    all_files = result.files_created + result.files_updated
                    if all_files:
                        existing = session.shared_context.get("generated_files", [])
                        session.shared_context["generated_files"] = list(set(existing + all_files))
                else:
                    task.status = AgentStatus.FAILED
                    task.error = "\n".join(result.errors) if result.errors else "Unknown error"
                    task.result = result.explanation
                    
            elif self._is_security_audit_task(task_description):
                # Security audit task - analyze files
                result = await self._run_security_audit(task_description, task.files, output_dir)
                task.status = AgentStatus.COMPLETED
                task.result = result
                
            elif self._is_devops_task(task_description):
                # DevOps task - create configs
                generator = self._get_code_generator(output_dir)
                result = generator.generate(
                    task=f"Create DevOps configuration: {task_description}",
                    language="yaml"
                )
                task.generation_result = result
                task.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED
                task.result = result.explanation if result.success else "\n".join(result.errors)
                
            else:
                # General task - provide guidance
                result = await self._run_general_task(agent_type, task_description)
                task.status = AgentStatus.COMPLETED
                task.result = result
            
            # Publish completion event
            if task.status == AgentStatus.COMPLETED:
                self.message_bus.publish("agent.completed", {
                    "session_id": session_id,
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "result": task.result
                })
            else:
                self.message_bus.publish("agent.failed", {
                    "session_id": session_id,
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "error": task.error or "Task failed"
                })
            
        except Exception as e:
            task.error = str(e)
            task.status = AgentStatus.FAILED
            
            self.message_bus.publish("agent.failed", {
                "session_id": session_id,
                "task_id": task_id,
                "agent_type": agent_type,
                "error": str(e)
            })
        
        finally:
            task.completed_at = datetime.now()
    
    def _is_code_generation_task(self, description: str) -> bool:
        """Check if task is code generation."""
        keywords = [
            'create', 'generate', 'write', 'build', 'implement', 'code',
            'develop', 'make', 'app', 'application', 'website', 'api',
            'script', 'program', 'function', 'class', 'module'
        ]
        desc_lower = description.lower()
        return any(kw in desc_lower for kw in keywords)
    
    def _is_security_audit_task(self, description: str) -> bool:
        """Check if task is security audit."""
        keywords = ['security', 'audit', 'vulnerability', 'scan', 'check security']
        desc_lower = description.lower()
        return any(kw in desc_lower for kw in keywords)
    
    def _is_devops_task(self, description: str) -> bool:
        """Check if task is DevOps."""
        keywords = ['docker', 'kubernetes', 'k8s', 'deploy', 'ci/cd', 'pipeline', 'infrastructure']
        desc_lower = description.lower()
        return any(kw in desc_lower for kw in keywords)
    
    def _detect_language(self, description: str) -> Optional[str]:
        """Detect programming language from description."""
        lang_map = {
            'python': ['python', 'flask', 'django', 'fastapi', '.py'],
            'javascript': ['javascript', 'js', 'node', 'nodejs', 'express', 'react'],
            'typescript': ['typescript', 'ts', 'angular', 'nestjs'],
            'go': ['golang', 'go ', '.go'],
            'rust': ['rust', 'cargo', '.rs'],
            'java': ['java', 'spring', '.java'],
            'ruby': ['ruby', 'rails', '.rb'],
            'php': ['php', 'laravel', '.php'],
            'html': ['html', 'web page', 'website'],
            'css': ['css', 'stylesheet', 'styling'],
        }
        
        desc_lower = description.lower()
        for lang, keywords in lang_map.items():
            if any(kw in desc_lower for kw in keywords):
                return lang
        return None
    
    async def _run_security_audit(self, description: str, files: List[str], output_dir: str) -> str:
        """Run security audit on files."""
        from ..intelligence.ollama_client import get_ollama_client
        
        client = get_ollama_client()
        
        # Read files if they exist
        file_contents = []
        for f in (files or []):
            file_path = os.path.join(output_dir, f)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as file:
                        content = file.read()
                        file_contents.append(f"=== {f} ===\n{content[:2000]}...")
                except:
                    pass
        
        prompt = f"""Analyze the following code for security vulnerabilities:

Task: {description}

Files to analyze:
{chr(10).join(file_contents) if file_contents else 'No files provided'}

Provide a security analysis with:
1. Summary of findings
2. Critical issues (if any)
3. Recommendations for fixes"""

        try:
            response = client.generate(
                model="qwen2.5-coder:7b",
                prompt=prompt,
                system="You are a security expert. Analyze code for OWASP Top 10 vulnerabilities and common security issues.",
                options={"temperature": 0.3}
            )
            return response.text
        except Exception as e:
            return f"Security audit failed: {e}"
    
    async def _run_general_task(self, agent_type: str, description: str) -> str:
        """Run a general task."""
        from ..intelligence.ollama_client import get_ollama_client
        
        client = get_ollama_client()
        
        system_prompts = {
            'architect': "You are a system architect. Provide clear, structured technical guidance.",
            'code': "You are a coding assistant. Provide helpful, practical code advice.",
            'ops': "You are a DevOps engineer. Provide infrastructure and deployment guidance.",
        }
        
        system = system_prompts.get(agent_type, "You are a helpful AI assistant.")
        
        try:
            response = client.generate(
                model="qwen2.5-coder:7b",
                prompt=description,
                system=system,
                options={"temperature": 0.4}
            )
            return response.text
        except Exception as e:
            return f"Task execution failed: {e}"
    
    async def run_parallel(
        self,
        session_id: str,
        tasks: List[Dict[str, Any]]
    ) -> List[AgentTask]:
        """Run multiple agent tasks in parallel."""
        spawned_tasks = []
        
        for task_config in tasks:
            task = await self.spawn_agent_task(
                session_id=session_id,
                agent_type=task_config["agent"],
                task_description=task_config["description"],
                files=task_config.get("files", []),
                output_dir=task_config.get("output_dir", ".")
            )
            spawned_tasks.append(task)
        
        # Wait for all tasks to complete
        await asyncio.gather(
            *self._workers.values(),
            return_exceptions=True
        )
        
        return spawned_tasks
    
    async def run_pipeline(
        self,
        session_id: str,
        stages: List[List[Dict[str, Any]]]
    ) -> Dict[str, List[AgentTask]]:
        """Run tasks in pipeline stages (sequential stages, parallel within stage)."""
        results = {}
        
        for i, stage in enumerate(stages):
            stage_name = f"stage_{i+1}"
            print(f"\n[Pipeline] Running {stage_name}...")
            
            # Run all tasks in this stage in parallel
            tasks = await self.run_parallel(session_id, stage)
            results[stage_name] = tasks
            
            # Check for failures
            failed = [t for t in tasks if t.status == AgentStatus.FAILED]
            if failed:
                print(f"[Pipeline] Stage {stage_name} had {len(failed)} failures")
        
        return results
    
    def get_session_status(self, session_id: str) -> Dict:
        """Get status of all tasks in a session."""
        session = self.sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        
        return {
            "session_id": session_id,
            "name": session.name,
            "status": session.status,
            "agents": session.agents,
            "tasks": {tid: t.to_dict() for tid, t in session.tasks.items()},
            "shared_context": session.shared_context,
            "messages": session.messages
        }
    
    def broadcast_to_session(self, session_id: str, message: str, sender: str = "system"):
        """Broadcast a message to all agents in a session."""
        session = self.sessions.get(session_id)
        if session:
            session.add_message(sender, message, "broadcast")
            self.message_bus.publish("session.message", {
                "session_id": session_id,
                "sender": sender,
                "message": message
            })


# Global orchestrator instance
_orchestrator: Optional[MultiAgentOrchestrator] = None


def get_orchestrator() -> MultiAgentOrchestrator:
    """Get global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = MultiAgentOrchestrator()
    return _orchestrator
