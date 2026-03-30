'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { AgentMonitor } from '@/components/agent-monitor/AgentMonitor';
import { ModelSelector } from '@/components/ModelSelector';
import { SessionManager } from '@/components/SessionManager';

// Dynamically import TerminalWidget with SSR disabled (xterm requires browser)
const TerminalWidget = dynamic(
  () => import('@/components/terminal/TerminalWidget').then(mod => mod.TerminalWidget),
  { ssr: false }
);

export default function Dashboard() {
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    // Check API health
    fetch('http://localhost:8000/api/health')
      .then(() => setApiStatus('connected'))
      .catch(() => setApiStatus('disconnected'));
  }, []);

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Local AI Lab
            </h1>
            <span className="text-gray-400 text-sm">
              Dynamic Model-Agnostic AI Development Environment
            </span>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${apiStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className="text-sm text-gray-400">
                API {apiStatus}
              </span>
            </div>
            <ModelSelector />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-120px)]">
          {/* Left Column - Session Manager */}
          <div className="lg:col-span-1 space-y-6">
            <SessionManager />
          </div>

          {/* Middle Column - Terminal */}
          <div className="lg:col-span-1">
            <TerminalWidget />
          </div>

          {/* Right Column - Agent Monitor */}
          <div className="lg:col-span-1">
            <AgentMonitor />
          </div>
        </div>
      </main>
    </div>
  );
}
