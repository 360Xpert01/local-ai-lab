'use client';

import { useState, useEffect } from 'react';
import { Plus, Users, Play, Trash2 } from 'lucide-react';

interface Session {
  id: string;
  name: string;
  agents: string[];
  task_count: number;
  status: string;
}

const AGENT_TYPES = [
  { id: 'code', name: 'Code Assistant', color: 'bg-blue-500' },
  { id: 'security', name: 'Security Expert', color: 'bg-red-500' },
  { id: 'ops', name: 'DevOps Engineer', color: 'bg-green-500' },
  { id: 'architect', name: 'System Architect', color: 'bg-purple-500' },
];

export function SessionManager() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [showNewSession, setShowNewSession] = useState(false);
  const [newSessionName, setNewSessionName] = useState('');
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);

  useEffect(() => {
    fetchSessions();
    const interval = setInterval(fetchSessions, 2000);
    return () => clearInterval(interval);
  }, []);

  const fetchSessions = () => {
    fetch('http://localhost:8000/api/sessions')
      .then(res => res.json())
      .then(setSessions)
      .catch(console.error);
  };

  const createSession = async () => {
    if (!newSessionName || selectedAgents.length === 0) return;

    const res = await fetch('http://localhost:8000/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newSessionName,
        description: 'Multi-agent session',
        agents: selectedAgents
      })
    });

    if (res.ok) {
      setNewSessionName('');
      setSelectedAgents([]);
      setShowNewSession(false);
      fetchSessions();
    }
  };

  const runDemo = async (scenario: string) => {
    const scenarios: Record<string, { name: string; agents: string[] }> = {
      'feature-dev': {
        name: 'Feature Development',
        agents: ['architect', 'code', 'security', 'ops']
      },
      'code-review': {
        name: 'Code Review',
        agents: ['code', 'security']
      },
      'security-audit': {
        name: 'Security Audit',
        agents: ['security', 'code']
      }
    };

    const config = scenarios[scenario];
    
    const res = await fetch('http://localhost:8000/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: config.name,
        description: `Demo: ${scenario}`,
        agents: config.agents
      })
    });

    if (res.ok) {
      const session = await res.json();
      
      // Start parallel tasks
      await fetch(`http://localhost:8000/api/sessions/${session.session_id}/parallel`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(
          config.agents.map(agent => ({
            agent_type: agent,
            description: `Task for ${agent} agent`,
            files: []
          }))
        )
      });
      
      fetchSessions();
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 h-full">
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold flex items-center gap-2">
            <Users size={18} />
            Sessions
          </h2>
          <button
            onClick={() => setShowNewSession(true)}
            className="p-2 bg-blue-600 rounded-lg hover:bg-blue-500 transition-colors"
          >
            <Plus size={16} />
          </button>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* Quick Actions */}
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={() => runDemo('feature-dev')}
            className="px-3 py-2 bg-purple-900/50 text-purple-300 rounded text-sm hover:bg-purple-900 transition-colors flex items-center justify-center gap-2"
          >
            <Play size={14} />
            Feature Dev
          </button>
          <button
            onClick={() => runDemo('security-audit')}
            className="px-3 py-2 bg-red-900/50 text-red-300 rounded text-sm hover:bg-red-900 transition-colors flex items-center justify-center gap-2"
          >
            <Play size={14} />
            Security Audit
          </button>
        </div>

        {/* New Session Form */}
        {showNewSession && (
          <div className="bg-gray-700/50 rounded-lg p-3 space-y-3">
            <input
              type="text"
              placeholder="Session name"
              value={newSessionName}
              onChange={(e) => setNewSessionName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-800 rounded border border-gray-600 text-sm"
            />
            
            <div className="space-y-2">
              <span className="text-xs text-gray-400">Select Agents:</span>
              <div className="flex flex-wrap gap-2">
                {AGENT_TYPES.map(agent => (
                  <button
                    key={agent.id}
                    onClick={() => {
                      setSelectedAgents(prev =>
                        prev.includes(agent.id)
                          ? prev.filter(a => a !== agent.id)
                          : [...prev, agent.id]
                      );
                    }}
                    className={`px-2 py-1 rounded text-xs transition-colors ${
                      selectedAgents.includes(agent.id)
                        ? agent.color + ' text-white'
                        : 'bg-gray-700 text-gray-400'
                    }`}
                  >
                    {agent.name}
                  </button>
                ))}
              </div>
            </div>

            <div className="flex gap-2">
              <button
                onClick={createSession}
                className="flex-1 px-3 py-2 bg-blue-600 rounded text-sm hover:bg-blue-500"
              >
                Create
              </button>
              <button
                onClick={() => setShowNewSession(false)}
                className="px-3 py-2 bg-gray-600 rounded text-sm hover:bg-gray-500"
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* Session List */}
        <div className="space-y-2">
          {sessions.map(session => (
            <div
              key={session.id}
              className="bg-gray-700/50 rounded-lg p-3 hover:bg-gray-700 transition-colors"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-sm">{session.name}</div>
                  <div className="text-xs text-gray-400">
                    {session.agents.join(', ')} • {session.task_count} tasks
                  </div>
                </div>
                <span className={`text-xs px-2 py-1 rounded ${
                  session.status === 'active' ? 'bg-green-900/50 text-green-400' : 'bg-gray-600'
                }`}>
                  {session.status}
                </span>
              </div>
            </div>
          ))}
          
          {sessions.length === 0 && (
            <div className="text-center text-gray-500 text-sm py-8">
              No active sessions
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
