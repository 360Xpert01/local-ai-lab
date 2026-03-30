"""Intelligent prompt router that understands user intent and spawns appropriate agents."""

import re
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """Types of tasks the system can handle."""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    SECURITY_AUDIT = "security_audit"
    DEVOPS = "devops"
    ARCHITECTURE = "architecture"
    DATABASE_DESIGN = "database_design"
    API_DESIGN = "api_design"
    DEBUGGING = "debugging"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"


@dataclass
class ParsedIntent:
    """Parsed user intent from natural language."""
    task_type: TaskType
    primary_agent: str
    supporting_agents: List[str]
    task_description: str
    files_involved: List[str]
    technologies: List[str]
    urgency: str
    context: Dict[str, Any]


class PromptRouter:
    """Routes user prompts to appropriate agents using NLP."""
    
    TASK_PATTERNS = {
        TaskType.CODE_GENERATION: [
            r'create\s+(?:a|an)\s+(\w+)',
            r'generate\s+(?:a|an)\s+(\w+)',
            r'write\s+(?:a|an)\s+(\w+)',
            r'build\s+(?:a|an)\s+(\w+)',
            r'make\s+(?:a|an)\s+(\w+)',
            r'implement',
            r'develop',
            r'scaffold',
        ],
        TaskType.CODE_REVIEW: [
            r'review\s+(?:my|the)?\s*(?:code)?',
            r'check\s+(?:my|the)?\s*(?:code)?',
            r'analyze\s+(?:my|the)?\s*(?:code)?',
        ],
        TaskType.SECURITY_AUDIT: [
            r'security',
            r'vulnerabilit',
            r'audit',
        ],
        TaskType.DEVOPS: [
            r'docker',
            r'kubernetes',
            r'k8s',
            r'deploy',
            r'ci/cd',
            r'pipeline',
            r'terraform',
            r'infrastructure',
        ],
        TaskType.ARCHITECTURE: [
            r'architect',
            r'system\s+design',
            r'microservice',
        ],
        TaskType.DATABASE_DESIGN: [
            r'database',
            r'schema',
            r'erd',
        ],
        TaskType.API_DESIGN: [
            r'api',
            r'rest',
            r'graphql',
            r'endpoint',
        ],
        TaskType.DEBUGGING: [
            r'fix',
            r'debug',
            r'error',
            r'bug',
            r'not\s+working',
            r'broken',
        ],
        TaskType.REFACTORING: [
            r'refactor',
            r'rewrite',
            r'clean\s+up',
            r'optimize',
        ],
        TaskType.TESTING: [
            r'test',
            r'unit\s+test',
            r'integration\s+test',
        ],
        TaskType.DOCUMENTATION: [
            r'document',
            r'readme',
            r'explain',
        ],
    }
    
    TECH_PATTERNS = {
        'react': r'\breact\b',
        'vue': r'\bvue\.?js?\b',
        'angular': r'\bangular\b',
        'nextjs': r'\bnext\.?js\b',
        'typescript': r'\btypescript\b',
        'javascript': r'\bjavascript\b',
        'python': r'\bpython\b',
        'nodejs': r'\bnode\.?js\b',
        'nestjs': r'\bnest\.?js?\b',
        'express': r'\bexpress\b',
        'fastapi': r'\bfastapi\b',
        'django': r'\bdjango\b',
        'flask': r'\bflask\b',
        'docker': r'\bdocker\b',
        'kubernetes': r'\bkubernetes\b|\bk8s\b',
        'terraform': r'\bterraform\b',
        'aws': r'\baws\b',
        'postgresql': r'\bpostgres(?:ql)?\b',
        'mysql': r'\bmysql\b',
        'mongodb': r'\bmongo(?:db)?\b',
        'graphql': r'\bgraphql\b',
    }
    
    AGENT_MAP = {
        TaskType.CODE_GENERATION: ('code', ['architect']),
        TaskType.CODE_REVIEW: ('code', ['security']),
        TaskType.SECURITY_AUDIT: ('security', ['code']),
        TaskType.DEVOPS: ('ops', ['code']),
        TaskType.ARCHITECTURE: ('architect', ['code', 'ops']),
        TaskType.DATABASE_DESIGN: ('architect', ['code']),
        TaskType.API_DESIGN: ('architect', ['code']),
        TaskType.DEBUGGING: ('code', ['security']),
        TaskType.REFACTORING: ('code', []),
        TaskType.TESTING: ('code', []),
        TaskType.DOCUMENTATION: ('code', []),
        TaskType.UNKNOWN: ('code', []),
    }
    
    def parse_intent(self, prompt: str, context: Optional[Dict] = None) -> ParsedIntent:
        """Parse user intent from natural language prompt."""
        prompt_lower = prompt.lower()
        context = context or {}
        return self._rule_based_parse(prompt_lower, context)
    
    def _rule_based_parse(self, prompt: str, context: Dict) -> ParsedIntent:
        """Parse intent using rule-based patterns."""
        task_type = TaskType.UNKNOWN
        
        for task, patterns in self.TASK_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, prompt, re.IGNORECASE):
                    task_type = task
                    break
            if task_type != TaskType.UNKNOWN:
                break
        
        technologies = []
        for tech, pattern in self.TECH_PATTERNS.items():
            if re.search(pattern, prompt, re.IGNORECASE):
                technologies.append(tech)
        
        files = re.findall(r'[\w\-./]+\.(?:js|ts|jsx|tsx|py|go|rs|java|php|css|html|json|yaml|md)', prompt)
        
        urgency = 'medium'
        if re.search(r'urgent|asap|critical|broken', prompt, re.IGNORECASE):
            urgency = 'high'
        
        primary_agent, supporting_agents = self.AGENT_MAP.get(task_type, ('code', []))
        
        # Adjust based on tech
        if 'docker' in technologies or 'kubernetes' in technologies:
            if task_type == TaskType.CODE_GENERATION:
                primary_agent = 'ops'
                supporting_agents = ['code']
        
        return ParsedIntent(
            task_type=task_type,
            primary_agent=primary_agent,
            supporting_agents=supporting_agents,
            task_description=prompt,
            files_involved=files,
            technologies=technologies,
            urgency=urgency,
            context=context
        )
    
    def route_to_agents(self, prompt: str, context: Optional[Dict] = None) -> Dict:
        """Route a prompt to appropriate agents."""
        intent = self.parse_intent(prompt, context)
        
        return {
            'intent': intent,
            'execution_plan': self._create_execution_plan(intent),
            'explanation': self._explain_routing(intent)
        }
    
    def _create_execution_plan(self, intent: ParsedIntent) -> List[Dict]:
        """Create execution plan based on parsed intent."""
        plan = [{
            'agent': intent.primary_agent,
            'task': intent.task_description,
            'files': intent.files_involved
        }]
        
        for agent in intent.supporting_agents:
            plan.append({
                'agent': agent,
                'task': f"Support: {intent.task_description}",
                'files': intent.files_involved
            })
        
        return plan
    
    def _explain_routing(self, intent: ParsedIntent) -> str:
        """Generate explanation of routing decision."""
        agent_names = {
            'code': 'Code Assistant',
            'security': 'Security Expert',
            'ops': 'DevOps Engineer',
            'architect': 'System Architect'
        }
        
        explanation = f"Detected: {intent.task_type.value.replace('_', ' ').title()}\n"
        explanation += f"Primary: {agent_names.get(intent.primary_agent, intent.primary_agent)}\n"
        
        if intent.supporting_agents:
            supporting = [agent_names.get(a, a) for a in intent.supporting_agents]
            explanation += f"Supporting: {', '.join(supporting)}\n"
        
        if intent.technologies:
            explanation += f"Tech: {', '.join(intent.technologies)}\n"
        
        return explanation


_prompt_router: Optional[PromptRouter] = None


def get_prompt_router() -> PromptRouter:
    """Get singleton prompt router."""
    global _prompt_router
    if _prompt_router is None:
        _prompt_router = PromptRouter()
    return _prompt_router
