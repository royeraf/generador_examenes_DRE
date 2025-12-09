from abc import ABC, abstractmethod
from typing import Any, Optional
import json

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
        """Helper to clean JSON code blocks from response."""
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        return response_text.strip()
