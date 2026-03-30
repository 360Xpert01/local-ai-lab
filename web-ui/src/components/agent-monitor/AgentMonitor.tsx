'use client';

import { useState, useEffect, useRef } from 'react';
import { Activity, Play, Square, RefreshCw, Cpu, Shield, Server, Layout } from 'lucide-react';

interface AgentStatus {
  id: string;
  name: string;
  type: string;
  status: 'idle' | 'running' | 'completed' | 'error';
  progress: number;
  currentTask?: string;
  lastActivity: string;
}

const AGENT_CONFIG: Record<string, { icon: any; color: string; bg: string }> = {
  code: { icon: Cpu, color: 'text-blue-400', bg: 'bg-blue-900/30' },
  security: { icon: Shield, color: 'text-red-400', bg: 'bg-red-900/30' },
  ops: { icon: Server, color: 'text-green-400', bg: 'bg-green-900/30' },
  architect: { icon: Layout, color: 'text-purple-400', bg: 'bg-purple-900/30' },
};

export function AgentMonitor() {
  const [agents, setAgents] = useState<AgentStatus[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // WebSocket connection for real-time updates
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      addLog('Connected to agent monitor');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      addLog('WebSocket error');
    };

    // Initial mock data
    setAgents([
      { id: 'code-1', name: 'Code Assistant', type: 'code', status: 'idle', progress: 0, lastActivity: '2 min ago' },
      { id: 'security-1', name: 'Security Expert', type: 'security', status: 'idle', progress: 0, lastActivity: '5 min ago' },
      { id: 'ops-1', name: 'DevOps Engineer', type: 'ops', status: 'idle', progress: 0, lastActivity: '10 min ago' },
      { id: 'architect-1', name: 'System Architect', type: 'architect', status: 'idle', progress: 0, lastActivity: '15 min ago' },
    ]);

    return () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const addLog = (message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-100), `[${timestamp}] ${message}`]);
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'agent.started':
        addLog(`Agent ${data.data.agent_type} started: ${data.data.description}`);
        updateAgentStatus(data.data.agent_type, 'running', data.data.description);
        break;
      case 'agent.completed':
        addLog(`Agent ${data.data.agent_type} completed`);
        updateAgentStatus(data.data.agent_type, 'completed');
        break;
      case 'agent.failed':
        addLog(`Agent ${data.data.agent_type} failed: ${data.data.error}`);
        updateAgentStatus(data.data.agent_type, 'error');
        break;
      case 'session.message':
        addLog(`Session: ${data.data.message}`);
        break;
    }
  };

  const updateAgentStatus = (type: string, status: AgentStatus['status'], task?: string) => {
    setAgents(prev => prev.map(agent => 
      agent.type === type 
        ? { ...agent, status, currentTask: task, lastActivity: 'now' }
        : agent
    ));
  };

  const spawnAgent = async (type: string) => {
    addLog(`Spawning ${type} agent...`);
    
    try {
      const res = await fetch('http://localhost:8000/api/sessions/default/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_type: type,
          description: `Task for ${type} agent`,
          files: []
        })
      });
      
      if (res.ok) {
        addLog(`${type} agent spawned successfully`);
        updateAgentStatus(type, 'running', 'Starting...');
      }
    } catch (error) {
      addLog(`Failed to spawn ${type} agent`);
    }
  };

  const getStatusColor = (status: AgentStatus['status']) => {
    switch (status) {
      case 'running': return 'bg-blue-500 animate-pulse';
      case 'completed': return 'bg-green-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold flex items-center gap-2">
            <Activity size={18} className="text-blue-400" />
            Agent Monitor
          </h2>
          <div className="flex gap-2">
            <button
              onClick={() => setLogs([])}
              className="p-1.5 hover:bg-gray-700 rounded transition-colors"
              title="Clear logs"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-hidden flex flex-col">
        {/* Agent Status */}
        <div className="p-4 space-y-3 overflow-y-auto">
          {agents.map(agent => {
            const config = AGENT_CONFIG[agent.type];
            const Icon = config.icon;
            
            return (
              <div
                key={agent.id}
                className={`${config.bg} rounded-lg p-3 border border-gray-700/50`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-gray-800 ${config.color}`}>
                      <Icon size={18} />
                    </div>
                    <div>
                      <div className="font-medium text-sm">{agent.name}</div>
                      <div className="text-xs text-gray-400">
                        {agent.status === 'running' && agent.currentTask
                          ? agent.currentTask.slice(0, 40) + '...'
                          : `Last activity: ${agent.lastActivity}`}
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${getStatusColor(agent.status)}`} />
                    <button
                      onClick={() => spawnAgent(agent.type)}
                      disabled={agent.status === 'running'}
                      className="p-1.5 hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
                    >
                      <Play size={14} />
                    </button>
                  </div>
                </div>

                {/* Progress bar */}
                {agent.status === 'running' && (
                  <div className="mt-3">
                    <div className="h-1 bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full ${config.color.replace('text', 'bg')} transition-all duration-500`}
                        style={{ width: `${agent.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Activity Logs */}
        <div className="flex-1 border-t border-gray-700 bg-gray-900/50">
          <div className="px-4 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wider">
            Activity Logs
          </div>
          <div className="px-4 pb-4 h-48 overflow-y-auto font-mono text-xs space-y-1">
            {logs.map((log, i) => (
              <div key={i} className="text-gray-300">
                {log}
              </div>
            ))}
            <div ref={logsEndRef} />
            {logs.length === 0 && (
              <div className="text-gray-500 italic">No activity yet...</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
