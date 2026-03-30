"""Code generator that uses Ollama to create files."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .ollama_client import get_ollama_client


@dataclass
class CodeGenerationResult:
    """Result of code generation."""
    success: bool
    files_created: List[str]
    files_updated: List[str]
    errors: List[str]
    explanation: str


class CodeGenerator:
    """Generates code files using AI."""
    
    def __init__(self, output_dir: Optional[str] = None, model: str = "qwen2.5-coder:7b"):
        self.output_dir = Path(output_dir) if output_dir else Path.cwd()
        self.model = model
        self.client = get_ollama_client()
    
    def generate(
        self,
        task: str,
        language: Optional[str] = None,
        context: Optional[str] = None,
        existing_files: Optional[List[str]] = None
    ) -> CodeGenerationResult:
        """Generate code files for a task."""
        
        # Check Ollama connection
        if not self.client.check_connection():
            return CodeGenerationResult(
                success=False,
                files_created=[],
                files_updated=[],
                errors=["Ollama is not running. Please start it with: ollama serve"],
                explanation=""
            )
        
        try:
            # Generate code using Ollama
            result = self.client.generate_code(
                model=self.model,
                task=task,
                language=language,
                context=context,
                files=existing_files
            )
            
            files_dict = result.get("files", {})
            explanation = result.get("explanation", "")
            
            if not files_dict:
                return CodeGenerationResult(
                    success=False,
                    files_created=[],
                    files_updated=[],
                    errors=["No files were generated. The AI may not have returned valid JSON."],
                    explanation=explanation
                )
            
            # Write files to disk
            created = []
            updated = []
            errors = []
            
            for file_path, content in files_dict.items():
                try:
                    full_path = self._write_file(file_path, content)
                    if full_path:
                        if full_path in created:
                            continue
                        # Check if file was updated or created
                        rel_path = str(Path(file_path).relative_to(self.output_dir)) if self.output_dir in Path(file_path).parents else file_path
                        if rel_path in (existing_files or []):
                            updated.append(rel_path)
                        else:
                            created.append(rel_path)
                except Exception as e:
                    errors.append(f"Error writing {file_path}: {e}")
            
            return CodeGenerationResult(
                success=len(errors) == 0 or len(created) > 0 or len(updated) > 0,
                files_created=created,
                files_updated=updated,
                errors=errors,
                explanation=explanation
            )
            
        except Exception as e:
            return CodeGenerationResult(
                success=False,
                files_created=[],
                files_updated=[],
                errors=[f"Generation failed: {str(e)}"],
                explanation=""
            )
    
    def _write_file(self, file_path: str, content: str) -> Optional[str]:
        """Write a file to disk. Returns the relative path."""
        # Normalize path
        if os.path.isabs(file_path):
            target_path = Path(file_path)
        else:
            target_path = self.output_dir / file_path
        
        # Ensure parent directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        with open(target_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(target_path.relative_to(self.output_dir))
    
    def modify_file(
        self,
        file_path: str,
        modification: str,
        context: Optional[str] = None
    ) -> CodeGenerationResult:
        """Modify an existing file based on instructions."""
        
        full_path = self.output_dir / file_path
        
        if not full_path.exists():
            return CodeGenerationResult(
                success=False,
                files_created=[],
                files_updated=[],
                errors=[f"File not found: {file_path}"],
                explanation=""
            )
        
        # Read existing content
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                existing_content = f.read()
        except Exception as e:
            return CodeGenerationResult(
                success=False,
                files_created=[],
                files_updated=[],
                errors=[f"Error reading file: {e}"],
                explanation=""
            )
        
        # Build prompt for modification
        prompt = f"""Modify the following file according to these instructions:

Instructions: {modification}

Current file ({file_path}):
```
{existing_content}
```

Provide the complete updated file content."""

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                system="You are a code editor. Provide only the complete updated file content without explanations.",
                options={"temperature": 0.2}
            )
            
            new_content = response.text
            
            # Strip code blocks if present
            if "```" in new_content:
                lines = new_content.split('\n')
                # Find lines between code blocks
                in_code = False
                code_lines = []
                for line in lines:
                    if line.startswith('```'):
                        in_code = not in_code
                        continue
                    if in_code:
                        code_lines.append(line)
                new_content = '\n'.join(code_lines)
            
            # Write updated content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(new_content.strip())
            
            return CodeGenerationResult(
                success=True,
                files_created=[],
                files_updated=[file_path],
                errors=[],
                explanation=f"Successfully modified {file_path}"
            )
            
        except Exception as e:
            return CodeGenerationResult(
                success=False,
                files_created=[],
                files_updated=[],
                errors=[f"Modification failed: {e}"],
                explanation=""
            )


def generate_code(
    task: str,
    output_dir: Optional[str] = None,
    model: str = "qwen2.5-coder:7b",
    language: Optional[str] = None
) -> CodeGenerationResult:
    """Convenience function to generate code."""
    generator = CodeGenerator(output_dir=output_dir, model=model)
    return generator.generate(task=task, language=language)
