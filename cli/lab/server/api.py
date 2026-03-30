"""FastAPI server for Web UI integration."""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio

from ..core.registry import get_registry
from ..core.agent_config import get_agent_registry
from ..agents.orchestrator import get_orchestrator

app = FastAPI(title="Local AI Lab API", version="0.1.0")

# CORS for Web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class ModelInfoResponse(BaseModel):
    id: str
    name: str
    family: str
    parameters: str
    context_length: int
    capabilities: List[str]
    fine_tunable: bool


class AgentInfoResponse(BaseModel):
    slug: str
    name: str
    description: str
    default_model: str
    compatible_models: List[str]
    tools: List[str]


class SpawnAgentRequest(BaseModel):
    agent_type: str
    model: Optional[str] = None
    task: str
    files: List[str] = []


class CreateSessionRequest(BaseModel):
    name: str
    description: str
    agents: List[str]


class TaskRequest(BaseModel):
    agent_type: str
    description: str
    files: List[str] = []


# Endpoints
@app.get("/api/models", response_model=List[ModelInfoResponse])
async def list_models():
    """List all available models."""
    registry = get_registry()
    models = registry.list_models()
    
    return [
        ModelInfoResponse(
            id=m.id,
            name=m.name,
            family=m.family.value,
            parameters=m.parameters,
            context_length=m.context_length,
            capabilities=[c.value for c in m.capabilities],
            fine_tunable=m.is_fine_tunable()
        )
        for m in models
    ]


@app.get("/api/models/{model_id}")
async def get_model(model_id: str):
    """Get detailed model information."""
    registry = get_registry()
    model = registry.get_model(model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "provider": model.provider,
        "ollama_name": model.ollama_name,
        "huggingface_id": model.huggingface_id,
        "family": model.family.value,
        "parameters": model.parameters,
        "context_length": model.context_length,
        "capabilities": [c.value for c in model.capabilities],
        "fine_tuning": {
            "supported": model.is_fine_tunable(),
            "trainer": model.fine_tuning.trainer if model.is_fine_tunable() else None,
            "quantizations": model.fine_tuning.quantizations if model.is_fine_tunable() else []
        }
    }


@app.get("/api/agents", response_model=List[AgentInfoResponse])
async def list_agents():
    """List all available agents."""
    registry = get_agent_registry()
    agents = registry.list_agents()
    
    return [
        AgentInfoResponse(
            slug=a.slug,
            name=a.name,
            description=a.description,
            default_model=a.model.default,
            compatible_models=[m.id for m in a.get_compatible_models()],
            tools=a.tools
        )
        for a in agents
    ]


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """Get detailed agent information."""
    registry = get_agent_registry()
    
    agent = (registry.get_agent(f"{agent_id}-assistant") or 
            registry.get_agent(f"{agent_id}-expert") or
            registry.get_agent(agent_id))
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "slug": agent.slug,
        "name": agent.name,
        "description": agent.description,
        "default_model": agent.model.default,
        "compatible_models": [m.id for m in agent.get_compatible_models()],
        "tools": agent.tools,
        "prompt_template": agent.prompt.template[:200] + "..."
    }


@app.post("/api/sessions")
async def create_session(request: CreateSessionRequest):
    """Create a new multi-agent session."""
    orchestrator = get_orchestrator()
    session = orchestrator.create_session(
        name=request.name,
        description=request.description,
        agents=request.agents
    )
    
    return {
        "session_id": session.id,
        "name": session.name,
        "agents": session.agents,
        "status": "created"
    }


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session status."""
    orchestrator = get_orchestrator()
    status = orchestrator.get_session_status(session_id)
    
    if "error" in status:
        raise HTTPException(status_code=404, detail=status["error"])
    
    return status


@app.post("/api/sessions/{session_id}/tasks")
async def spawn_task(session_id: str, request: TaskRequest, background_tasks: BackgroundTasks):
    """Spawn a task in a session."""
    orchestrator = get_orchestrator()
    
    # Run in background
    async def run_task():
        await orchestrator.spawn_agent_task(
            session_id=session_id,
            agent_type=request.agent_type,
            task_description=request.description,
            files=request.files
        )
    
    background_tasks.add_task(run_task)
    
    return {"status": "spawned", "session_id": session_id}


@app.post("/api/sessions/{session_id}/parallel")
async def run_parallel(session_id: str, tasks: List[TaskRequest], background_tasks: BackgroundTasks):
    """Run multiple tasks in parallel."""
    orchestrator = get_orchestrator()
    
    task_configs = [
        {
            "agent": t.agent_type,
            "description": t.description,
            "files": t.files
        }
        for t in tasks
    ]
    
    async def run_parallel_tasks():
        await orchestrator.run_parallel(session_id, task_configs)
    
    background_tasks.add_task(run_parallel_tasks)
    
    return {"status": "started", "session_id": session_id, "task_count": len(tasks)}


@app.get("/api/sessions")
async def list_sessions():
    """List all active sessions."""
    orchestrator = get_orchestrator()
    
    return [
        {
            "id": sid,
            "name": s.name,
            "agents": s.agents,
            "task_count": len(s.tasks),
            "status": s.status
        }
        for sid, s in orchestrator.sessions.items()
    ]


# WebSocket for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time agent updates."""
    await websocket.accept()
    
    orchestrator = get_orchestrator()
    connected = True
    
    # Subscribe to events
    async def event_handler(event):
        nonlocal connected
        if connected:
            try:
                await websocket.send_json(event)
            except Exception:
                connected = False
    
    def sync_handler(event):
        if connected:
            asyncio.create_task(event_handler(event))
    
    handler_id = orchestrator.message_bus.subscribe_all(sync_handler)
    
    try:
        while connected:
            try:
                # Keep connection alive, handle client messages
                data = await websocket.receive_json()
                
                if data.get("action") == "broadcast":
                    session_id = data.get("session_id")
                    message = data.get("message")
                    if session_id and message:
                        orchestrator.broadcast_to_session(session_id, message, "user")
                        await websocket.send_json({"status": "broadcast_sent"})
            except Exception:
                break
    
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        connected = False
        orchestrator.message_bus.unsubscribe(handler_id)
        try:
            await websocket.close()
        except Exception:
            pass  # Already closed


# Health check
@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "models": len(get_registry().list_models()),
        "agents": len(get_agent_registry().list_agents()),
        "sessions": len(get_orchestrator().sessions)
    }
