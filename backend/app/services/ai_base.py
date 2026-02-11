from abc import ABC, abstractmethod
from typing import Any, Optional
import json
import re

class AIService(ABC):
    """Abstract base class for AI services."""
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the service is properly configured (e.g. API key)."""
        pass
        
    @abstractmethod
    async def generate_content(self, prompt: str) -> str:
        """Generate text content from a prompt."""
        pass
    
    @abstractmethod
    async def generar_preguntas(
        self,
        competencias: list[dict],
        cantidad: int = 5,
        tipo: str = "multiple",
        dificultad: str = "intermedio"
    ) -> list[Any]:
        """Generate questions (legacy method mainly used by preguntas.py)."""
        pass

    def clean_json_response(self, response_text: str) -> str:
        """Helper to clean JSON code blocks and recover JSON from text."""
        # 1. Basic markdown cleaning
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()

        # 2. Extract JSON if it's embedded in other text
        try:
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            if first_brace != -1 and last_brace != -1:
                response_text = response_text[first_brace:last_brace + 1]
        except:
            pass
            
        # 3. Last resort cleaning (remove comments and trailing commas)
        try:
            # Remove single-line comments // ...
            response_text = re.sub(r'^\s*//.*$', '', response_text, flags=re.MULTILINE)
            # Remove trailing commas: ,} -> } and ,] -> ]
            response_text = re.sub(r',\s*\}', '}', response_text)
            response_text = re.sub(r',\s*\]', ']', response_text)
        except:
            pass

        return response_text.strip()
