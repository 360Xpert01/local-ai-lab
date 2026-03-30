"""Ollama API client for code generation."""

import json
import requests
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass


@dataclass
class OllamaResponse:
    """Response from Ollama API."""
    text: str
    done: bool = True
    model: str = ""
    total_duration: Optional[int] = None
    load_duration: Optional[int] = None


class OllamaClient:
    """Client for Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.generate_url = f"{self.base_url}/api/generate"
        self.chat_url = f"{self.base_url}/api/chat"
        self.tags_url = f"{self.base_url}/api/tags"
    
    def check_connection(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(self.tags_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def list_models(self) -> List[str]:
        """List available models from Ollama."""
        try:
            response = requests.get(self.tags_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [m['name'] for m in data.get('models', [])]
        except Exception as e:
            print(f"Error listing models: {e}")
        return []
    
    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        stream: bool = False,
        options: Optional[Dict] = None
    ) -> OllamaResponse:
        """Generate text using Ollama."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream
        }
        
        if system:
            payload["system"] = system
        
        if options:
            payload["options"] = options
        
        try:
            response = requests.post(
                self.generate_url,
                json=payload,
                stream=stream,
                timeout=300
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_stream(response)
            else:
                data = response.json()
                return OllamaResponse(
                    text=data.get('response', ''),
                    done=data.get('done', True),
                    model=data.get('model', model),
                    total_duration=data.get('total_duration'),
                    load_duration=data.get('load_duration')
                )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    def generate_code(
        self,
        model: str,
        task: str,
        language: Optional[str] = None,
        context: Optional[str] = None,
        files: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """Generate code files based on a task.
        
        Returns a dict of filename -> content
        """
        system_prompt = """You are an expert software engineer. Generate complete, working code.

Respond in this JSON format:
```json
{
  "files": [
    {
      "path": "main.py",
      "content": "print('hello')"
    }
  ],
  "explanation": "brief explanation"
}
```

Rules:
1. Use the exact JSON format shown above
2. Wrap JSON in ```json and ``` markers
3. Generate COMPLETE files with all necessary code
4. Write clean, documented code"""

        user_prompt = f"Task: {task}\n\n"
        
        if language:
            user_prompt += f"Primary language: {language}\n\n"
        
        if context:
            user_prompt += f"Context:\n{context}\n\n"
        
        if files:
            user_prompt += f"Existing files to consider: {', '.join(files)}\n\n"
        
        user_prompt += "Generate the necessary code files."
        
        # Call Ollama
        response = self.generate(
            model=model,
            prompt=user_prompt,
            system=system_prompt,
            options={"temperature": 0.2, "num_predict": 4000}
        )
        
        # Parse the response
        return self._parse_code_response(response.text)
    
    def _parse_code_response(self, text: str) -> Dict[str, str]:
        """Parse code generation response - handles JSON and markdown code blocks."""
        files = {}
        explanation = ""
        
        # First, try to extract JSON from markdown code blocks
        json_match = None
        if "```json" in text:
            try:
                json_match = text.split("```json")[1].split("```")[0].strip()
            except IndexError:
                pass
        elif "```" in text and text.count("```") >= 2:
            # Try to find JSON inside any code block
            parts = text.split("```")
            for part in parts[1::2]:  # Every odd index is inside a code block
                part = part.strip()
                if part.startswith('{'):
                    json_match = part
                    break
        
        # Also try to find JSON directly in the text (not in code blocks)
        if not json_match:
            # Look for JSON object directly
            text_stripped = text.strip()
            if text_stripped.startswith('{'):
                json_match = text_stripped
            else:
                # Try to find JSON between braces
                start = text.find('{')
                end = text.rfind('}')
                if start != -1 and end != -1 and start < end:
                    json_match = text[start:end+1]
        
        # Try to parse JSON
        if json_match:
            try:
                data = json.loads(json_match)
                
                # Extract files
                for file_info in data.get("files", []):
                    path = file_info.get("path", "")
                    content = file_info.get("content", "")
                    if path and content:
                        files[path] = content
                
                explanation = data.get("explanation", "Code generated successfully")
                
                if files:
                    return {"files": files, "explanation": explanation}
                    
            except json.JSONDecodeError:
                pass  # Fall through to code block parsing
        
        # Fallback: Parse markdown code blocks as individual files
        # Look for patterns like: ```python or ``` with filename comments
        code_blocks = []
        lines = text.split('\n')
        current_block = None
        current_lang = None
        current_filename = None
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for code block start
            if line.strip().startswith('```'):
                if current_block is None:
                    # Starting a new block
                    current_block = []
                    current_lang = line.strip().replace('```', '').strip()
                    current_filename = None
                    
                    # Look for filename in previous line (comment or text)
                    if i > 0:
                        prev_line = lines[i-1].strip()
                        if '#' in prev_line and ('file' in prev_line.lower() or '.' in prev_line):
                            # Extract filename from comment
                            parts = prev_line.split('#')
                            if len(parts) > 1:
                                current_filename = parts[1].strip().replace('file:', '').strip()
                else:
                    # Ending a block
                    if current_block and current_filename:
                        files[current_filename] = '\n'.join(current_block)
                    elif current_block and current_lang:
                        # Guess filename from language
                        ext_map = {
                            'python': 'main.py', 'py': 'main.py',
                            'javascript': 'index.js', 'js': 'index.js',
                            'typescript': 'index.ts', 'ts': 'index.ts',
                            'go': 'main.go', 'rust': 'main.rs',
                            'java': 'Main.java', 'ruby': 'main.rb',
                            'yaml': 'config.yaml', 'yml': 'config.yml',
                            'dockerfile': 'Dockerfile', 'docker': 'Dockerfile'
                        }
                        filename = ext_map.get(current_lang, f'file.{current_lang}')
                        files[filename] = '\n'.join(current_block)
                    
                    current_block = None
                    current_lang = None
                    current_filename = None
            elif current_block is not None:
                # Check if first non-empty line contains filename
                if not current_block and not current_filename:
                    if '# file:' in line or '# File:' in line:
                        current_filename = line.split(':', 1)[1].strip()
                        continue
                current_block.append(line)
            
            i += 1
        
        # If we found files from code blocks, use those
        if files:
            explanation = "Code extracted from markdown code blocks"
            # Try to find explanation in the text
            if "explanation" in text.lower() or "summary" in text.lower():
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if line.lower().strip().startswith(('explanation', 'summary', 'this code')):
                        explanation = '\n'.join(lines[i:]).strip()
                        break
        else:
            explanation = f"Could not parse response into files. Raw output:\n{text[:500]}..."
        
        return {"files": files, "explanation": explanation}
        
        return {
            "files": files,
            "explanation": explanation
        }
    
    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        options: Optional[Dict] = None
    ) -> OllamaResponse:
        """Chat with Ollama."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream
        }
        
        if options:
            payload["options"] = options
        
        try:
            response = requests.post(
                self.chat_url,
                json=payload,
                stream=stream,
                timeout=300
            )
            response.raise_for_status()
            
            if stream:
                return self._handle_chat_stream(response)
            else:
                data = response.json()
                return OllamaResponse(
                    text=data.get('message', {}).get('content', ''),
                    done=data.get('done', True),
                    model=data.get('model', model)
                )
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    def _handle_stream(self, response) -> Iterator[str]:
        """Handle streaming response for generate."""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if 'response' in data:
                        yield data['response']
                    if data.get('done'):
                        break
                except json.JSONDecodeError:
                    continue
    
    def _handle_chat_stream(self, response) -> Iterator[str]:
        """Handle streaming response for chat."""
        for line in response.iter_lines():
            if line:
                try:
                    data = json.loads(line)
                    if 'message' in data and 'content' in data['message']:
                        yield data['message']['content']
                    if data.get('done'):
                        break
                except json.JSONDecodeError:
                    continue


# Global client instance
_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get global Ollama client."""
    global _client
    if _client is None:
        _client = OllamaClient()
    return _client
