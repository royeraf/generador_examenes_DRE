from typing import Literal
from app.services.ai_base import AIService
from app.services.gemini_service import gemini_service
from app.services.chatgpt_service import chatgpt_service

class AIServiceFactory:
    """Factory for creating/retrieving AI services."""
    
    @staticmethod
    def get_service(service_name: str = "gemini") -> AIService:
        """
        Get an AI service instance by name.
        
        Args:
            service_name: 'gemini' or 'chatgpt'
            
        Returns:
            AIService implementation
        """
        if service_name == "gemini":
            return gemini_service
        elif service_name == "chatgpt":
            return chatgpt_service
        else:
            raise ValueError(f"Servicio de IA no soportado: {service_name}")
            
    @staticmethod
    def get_available_services() -> list[dict]:
        """Get list of available services and their status."""
        return [
            {
                "id": "gemini",
                "nombre": "Google Gemini",
                "descripcion": "Modelo Gemini 2.5 Flash (Standard)",
                "disponible": gemini_service.is_configured()
            },
            {
                "id": "chatgpt",
                "nombre": "OpenAI ChatGPT",
                "descripcion": "Modelo GPT-4o-mini de OpenAI",
                "disponible": chatgpt_service.is_configured()
            }
        ]

ai_factory = AIServiceFactory()
