'use client';

import { useEffect, useRef, useState } from 'react';
import { Terminal } from 'xterm';
import { FitAddon } from 'xterm-addon-fit';
import 'xterm/css/xterm.css';
import { Maximize2, Minimize2, Trash } from 'lucide-react';

export function TerminalWidget() {
  const terminalRef = useRef<HTMLDivElement>(null);
  const term = useRef<Terminal | null>(null);
  const fitAddon = useRef<FitAddon | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (!terminalRef.current) return;

    // Create terminal
    term.current = new Terminal({
      theme: {
        background: '#1f2937',
        foreground: '#e5e7eb',
        cursor: '#3b82f6',
        selectionBackground: '#3b82f6',
        black: '#1f2937',
        red: '#ef4444',
        green: '#10b981',
        yellow: '#f59e0b',
        blue: '#3b82f6',
        magenta: '#8b5cf6',
        cyan: '#06b6d4',
        white: '#e5e7eb',
      },
      fontSize: 14,
      fontFamily: 'Menlo, Monaco, "Courier New", monospace',
      cursorBlink: true,
      cursorStyle: 'block',
    });

    fitAddon.current = new FitAddon();
    term.current.loadAddon(fitAddon.current);
    term.current.open(terminalRef.current);
    fitAddon.current.fit();

    // Welcome message
    term.current.writeln('\x1b[1;34m╔══════════════════════════════════════════╗\x1b[0m');
    term.current.writeln('\x1b[1;34m║      Local AI Lab Terminal v0.1.0        ║\x1b[0m');
    term.current.writeln('\x1b[1;34m╚══════════════════════════════════════════╝\x1b[0m');
    term.current.writeln('');
    term.current.writeln('\x1b[32mWelcome! Type commands to interact with agents.\x1b[0m');
    term.current.writeln('');
    term.current.writeln('Available commands:');
    term.current.writeln('  \x1b[36mlab agent spawn <type>\x1b[0m  - Spawn an agent');
    term.current.writeln('  \x1b[36mlab multi spawn\x1b[0m         - Multi-agent mode');
    term.current.writeln('  \x1b[36mlab model list\x1b[0m          - List models');
    term.current.writeln('  \x1b[36mlab train start\x1b[0m         - Start training');
    term.current.writeln('  \x1b[36mhelp\x1b[0m                    - Show help');
    term.current.writeln('');
    prompt();

    // Handle input
    let currentLine = '';
    
    term.current.onData((data) => {
      const code = data.charCodeAt(0);
      
      if (code === 13) { // Enter
        term.current?.writeln('');
        handleCommand(currentLine);
        currentLine = '';
        prompt();
      } else if (code === 127) { // Backspace
        if (currentLine.length > 0) {
          currentLine = currentLine.slice(0, -1);
          term.current?.write('\b \b');
        }
      } else if (code >= 32 && code <= 126) {
        currentLine += data;
        term.current?.write(data);
      }
    });

    // Handle resize
    const handleResize = () => {
      fitAddon.current?.fit();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      term.current?.dispose();
    };
  }, []);

  const prompt = () => {
    term.current?.write('\x1b[32mlab\x1b[0m:\x1b[34m~\x1b[0m$ ');
  };

  // Intelligent routing logic
  const detectIntent = (input: string) => {
    const lower = input.toLowerCase();
    
    // Detect task type
    const patterns: Record<string, RegExp[]> = {
      code_generation: [/create\s+(?:a|an)/i, /generate/i, /build/i, /make\s+(?:a|an)/i, /implement/i],
      security_audit: [/security/i, /vulnerabilit/i, /audit/i, /hack/i, /exploit/i],
      devops: [/docker/i, /kubernetes/i, /k8s/i, /deploy/i, /pipeline/i, /terraform/i, /infrastructure/i],
      architecture: [/architect/i, /design\s+the\s+system/i, /microservice/i],
      database: [/database/i, /schema/i, /erd/i, /sql/i],
      api_design: [/api/i, /rest/i, /graphql/i, /endpoint/i],
      debugging: [/fix/i, /debug/i, /error/i, /bug/i, /broken/i, /not\s+working/i],
      testing: [/test/i, /jest/i, /pytest/i, /unit\s+test/i],
    };
    
    for (const [task, regexes] of Object.entries(patterns)) {
      for (const regex of regexes) {
        if (regex.test(lower)) return task;
      }
    }
    return 'general';
  };

  const detectTech = (input: string): string[] => {
    const lower = input.toLowerCase();
    const techs: string[] = [];
    const techPatterns: Record<string, RegExp> = {
      react: /\breact\b/i,
      vue: /\bvue\.?js?\b/i,
      angular: /\bangular\b/i,
      nextjs: /\bnext\.?js\b/i,
      typescript: /\btypescript\b/i,
      javascript: /\bjavascript\b|\bjs\b/i,
      python: /\bpython\b/i,
      nodejs: /\bnode\.?js\b/i,
      nestjs: /\bnest\.?js?\b/i,
      django: /\bdjango\b/i,
      flask: /\bflask\b/i,
      docker: /\bdocker\b/i,
      kubernetes: /\bkubernetes\b|\bk8s\b/i,
      postgresql: /\bpostgres(?:ql)?\b/i,
      mongodb: /\bmongo(?:db)?\b/i,
    };
    
    for (const [tech, pattern] of Object.entries(techPatterns)) {
      if (pattern.test(lower)) techs.push(tech);
    }
    return techs;
  };

  const routeToAgent = (input: string) => {
    const taskType = detectIntent(input);
    const techs = detectTech(input);
    
    const agentMap: Record<string, { primary: string; supporting: string[]; icon: string }> = {
      code_generation: { primary: 'Code Assistant', supporting: ['System Architect'], icon: '💻' },
      security_audit: { primary: 'Security Expert', supporting: ['Code Assistant'], icon: '🔒' },
      devops: { primary: 'DevOps Engineer', supporting: ['Code Assistant'], icon: '⚙️' },
      architecture: { primary: 'System Architect', supporting: ['Code Assistant', 'DevOps Engineer'], icon: '🏗️' },
      database: { primary: 'System Architect', supporting: ['Code Assistant'], icon: '🗄️' },
      api_design: { primary: 'System Architect', supporting: ['Code Assistant'], icon: '🔌' },
      debugging: { primary: 'Code Assistant', supporting: ['Security Expert'], icon: '🐛' },
      testing: { primary: 'Code Assistant', supporting: [], icon: '🧪' },
      general: { primary: 'Code Assistant', supporting: [], icon: '🤖' },
    };
    
    // Adjust for tech
    let route = agentMap[taskType] || agentMap.general;
    if (techs.includes('docker') || techs.includes('kubernetes')) {
      if (taskType === 'code_generation') {
        route = { primary: 'DevOps Engineer', supporting: ['Code Assistant'], icon: '⚙️' };
      }
    }
    
    return { ...route, taskType, techs };
  };

  const handleCommand = (cmd: string) => {
    const trimmed = cmd.trim();
    const lower = trimmed.toLowerCase();
    
    if (lower === 'help') {
      term.current?.writeln('\x1b[1;36mLocal AI Lab - Intelligent Commands:\x1b[0m');
      term.current?.writeln('');
      term.current?.writeln('\x1b[33mJust type what you want to do!\x1b[0m');
      term.current?.writeln('');
      term.current?.writeln('Examples:');
      term.current?.writeln('  \x1b[32mcreate a calculator web app\x1b[0m');
      term.current?.writeln('  \x1b[32mset up docker for my nodejs app\x1b[0m');
      term.current?.writeln('  \x1b[32mreview my code for security issues\x1b[0m');
      term.current?.writeln('  \x1b[32mdesign a database schema for e-commerce\x1b[0m');
      term.current?.writeln('  \x1b[32mfix the bug in authentication.js\x1b[0m');
      term.current?.writeln('');
      term.current?.writeln('The AI will automatically route to the right expert!');
      term.current?.writeln('');
      term.current?.writeln('Traditional commands:');
      term.current?.writeln('  \x1b[36magent list\x1b[0m - List all agents');
      term.current?.writeln('  \x1b[36mmodel list\x1b[0m - List available models');
      term.current?.writeln('  \x1b[36mtrain start --agent code\x1b[0m - Start training');
      term.current?.writeln('  \x1b[36mclear\x1b[0m - Clear terminal');
    } else if (lower === 'clear') {
      term.current?.clear();
    } else if (lower.startsWith('lab ') || lower.startsWith('agent ') || lower.startsWith('model ') || lower.startsWith('train ')) {
      // Traditional CLI commands
      term.current?.writeln(`\x1b[33mUse CLI for: ${cmd}\x1b[0m`);
      term.current?.writeln('  Run this in your system terminal.');
    } else if (trimmed) {
      // Intelligent routing for natural language
      const route = routeToAgent(trimmed);
      
      term.current?.writeln('');
      term.current?.writeln(`\x1b[1;34m🧠 Analyzing your request...\x1b[0m`);
      term.current?.writeln('');
      
      setTimeout(() => {
        term.current?.writeln(`\x1b[36mTask Type:\x1b[0m ${route.taskType.replace('_', ' ').toUpperCase()}`);
        if (route.techs.length > 0) {
          term.current?.writeln(`\x1b[36mTechnologies:\x1b[0m ${route.techs.join(', ')}`);
        }
        term.current?.writeln('');
        term.current?.writeln(`\x1b[1;32m${route.icon} Primary Agent:\x1b[0m ${route.primary}`);
        if (route.supporting.length > 0) {
          term.current?.writeln(`\x1b[90m  Supporting: ${route.supporting.join(', ')}\x1b[0m`);
        }
        term.current?.writeln('');
        
        // Simulate agent response
        term.current?.writeln('\x1b[90m─────────────────────────────────────────\x1b[0m');
        
        if (route.taskType === 'code_generation') {
          term.current?.writeln(`\x1b[32mI'll create this for you!\x1b[0m`);
          term.current?.writeln('');
          term.current?.writeln('Plan:');
          term.current?.writeln('  1. Create project structure');
          term.current?.writeln('  2. Generate source files');
          term.current?.writeln('  3. Add configuration files');
          if (route.supporting.includes('System Architect')) {
            term.current?.writeln('  4. Review architecture with System Architect');
          }
        } else if (route.taskType === 'security_audit') {
          term.current?.writeln(`\x1b[32mI'll audit your code for security issues.\x1b[0m`);
          term.current?.writeln('');
          term.current?.writeln('I will check for:');
          term.current?.writeln('  • OWASP Top 10 vulnerabilities');
          term.current?.writeln('  • Injection attacks');
          term.current?.writeln('  • Authentication flaws');
          term.current?.writeln('  • Insecure dependencies');
        } else if (route.taskType === 'devops') {
          term.current?.writeln(`\x1b[32mI'll set up the DevOps infrastructure.\x1b[0m`);
          term.current?.writeln('');
          term.current?.writeln('I will create:');
          term.current?.writeln('  • Dockerfile for containerization');
          term.current?.writeln('  • Docker Compose for local dev');
          term.current?.writeln('  • CI/CD pipeline configuration');
        } else if (route.taskType === 'debugging') {
          term.current?.writeln(`\x1b[32mI'll help you debug this issue.\x1b[0m`);
          term.current?.writeln('');
          term.current?.writeln('Steps:');
          term.current?.writeln('  1. Analyze the error');
          term.current?.writeln('  2. Identify root cause');
          term.current?.writeln('  3. Provide fix with explanation');
        } else {
          term.current?.writeln(`\x1b[32mI'll help with this task!\x1b[0m`);
          term.current?.writeln(`\x1b[90m(Connect Ollama for real AI processing)\x1b[0m`);
        }
        
        term.current?.writeln('\x1b[90m─────────────────────────────────────────\x1b[0m');
        term.current?.writeln('');
        term.current?.writeln('\x1b[33m💡 Connect Ollama for real AI code generation:\x1b[0m');
        term.current?.writeln('   ollama pull qwen2.5-coder:7b');
        term.current?.writeln('   ollama serve');
        term.current?.writeln('');
      }, 300);
    }
  };

  const clearTerminal = () => {
    term.current?.clear();
    term.current?.writeln('\x1b[1;34m╔══════════════════════════════════════════╗\x1b[0m');
    term.current?.writeln('\x1b[1;34m║      Local AI Lab Terminal v0.1.0        ║\x1b[0m');
    term.current?.writeln('\x1b[1;34m╚══════════════════════════════════════════╝\x1b[0m');
    term.current?.writeln('');
    prompt();
  };

  return (
    <div className={`bg-gray-800 rounded-lg border border-gray-700 flex flex-col ${
      isExpanded ? 'fixed inset-4 z-50' : 'h-full'
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700 bg-gray-800 rounded-t-lg">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500" />
            <div className="w-3 h-3 rounded-full bg-yellow-500" />
            <div className="w-3 h-3 rounded-full bg-green-500" />
          </div>
          <span className="text-sm text-gray-400 ml-2">Terminal</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearTerminal}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
            title="Clear"
          >
            <Trash size={14} />
          </button>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1.5 hover:bg-gray-700 rounded transition-colors"
            title={isExpanded ? 'Minimize' : 'Maximize'}
          >
            {isExpanded ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
          </button>
        </div>
      </div>

      {/* Terminal */}
      <div 
        ref={terminalRef} 
        className="flex-1 p-2 overflow-hidden"
        style={{ background: '#1f2937' }}
      />
    </div>
  );
}
