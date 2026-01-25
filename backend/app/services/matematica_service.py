"""
Servicio para gestionar evaluaciones de Matemática (MatSistem).
Genera situaciones problemáticas y preguntas siguiendo el modelo MINEDU.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
import json

from app.models.db_models import (
    Grado,
    CompetenciaMatematica,
    CapacidadMatematica,
    DesempenoMatematica,
    EstandarMatematica
)
from app.config import get_settings
from app.services.ai_factory import ai_factory

settings = get_settings()


class MatematicaService:
    """Servicio para generar evaluaciones de matemática."""
    
    def __init__(self):
        pass
    
    def _build_prompt_matematica(
        self,
        grado_nombre: str,
        competencia_nombre: str,
        capacidades_desempenos: dict,
        cantidad: int,
        situacion_base: Optional[str] = None
    ) -> str:
        """
        Construye el prompt para generar un examen de matemática
        siguiendo el formato oficial del MINEDU (MateJony).
        """
        
        # Formatear desempeños por capacidad
        desempenos_formateados = ""
        for orden, data in capacidades_desempenos.items():
            desempenos_formateados += f"\n**Capacidad {orden}: {data['nombre']}**\n"
            for des in data['desempenos']:
                desempenos_formateados += f"  - {des['codigo']}: {des['descripcion']}\n"
        
        situacion_texto = ""
        if situacion_base:
            situacion_texto = f"""
**SITUACIÓN PROBLEMÁTICA PROPORCIONADA:**
\"\"\"
{situacion_base}
\"\"\"
Usa esta situación como base para el problema.
"""
        
        prompt = f"""Eres **"MateJony"**, un experto en evaluación de aprendizajes y programación curricular en Matemática del Ministerio de Educación de Perú. Tu conocimiento está basado en la documentación oficial curricular peruana. Tu comunicación es profesional, clara, didáctica y estructurada.

**CONTEXTO CURRICULAR:**
- **Grado/Nivel:** {grado_nombre}
- **Competencia:** {competencia_nombre}
{situacion_texto}
**DESEMPEÑOS SELECCIONADOS POR CAPACIDAD:**
{desempenos_formateados}

**TU TAREA:**
Genera una **SITUACIÓN PROBLEMÁTICA INTEGRADORA** con exactamente {cantidad} preguntas cerradas de opción múltiple.

**ESTRUCTURA DEL EXAMEN:**

1. **SALUDO INICIAL:**
   Preséntate brevemente: "Soy MateJony, especialista en evaluación de Matemática del MINEDU del Perú..."

2. **ENCABEZADO DEL EXAMEN:**
   - Título motivador y contextualizado (ejemplo: "Aventura Matemática", "Reto de Números", "Desafío con Figuras")
   - Espacio para: Apellidos y Nombres / Fecha
   - Grado: {grado_nombre}
   - Competencia: {competencia_nombre}

3. **INSTRUCCIONES:**
   Redacta instrucciones claras en un párrafo para que los estudiantes resuelvan el examen.

4. **SITUACIÓN PROBLEMÁTICA:**
   Crea una SITUACIÓN SIGNIFICATIVA y CONTEXTUALIZADA (contexto real o simulado) apropiada para estudiantes de {grado_nombre}. 
   La situación debe integrar todos los desempeños seleccionados de forma coherente.
   NO ES UN TEXTO DE LECTURA - es un PROBLEMA MATEMÁTICO contextualizado.

5. **PREGUNTAS ({cantidad} en total):**
   Cada pregunta debe:
   - Estar numerada
   - Basarse en la situación problemática
   - Tener 4 alternativas (A, B, C, D) siendo solo UNA la correcta
   - Evaluar un desempeño específico de los seleccionados
   - Requerir razonamiento matemático, no solo memorización

6. **CRITERIO DE EVALUACIÓN POR PREGUNTA:**
   Para cada pregunta, incluye el criterio de evaluación con estructura:
   "[HABILIDAD VERBAL OBSERVABLE] + [CONTENIDO TEMÁTICO] + [CONDICIÓN/CONTEXTO] + [FINALIDAD]"

7. **TABLA DE RESPUESTAS:**
   Al final tabla con: N° Pregunta | Capacidad | Desempeño | Alternativa correcta | Justificación breve

IMPORTANTE: Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
    "saludo": "texto del saludo de MateJony",
    "examen": {{
        "titulo": "título motivador del examen de matemática",
        "grado": "{grado_nombre}",
        "competencia": "{competencia_nombre}",
        "instrucciones": "instrucciones precisas para resolver el examen",
        "situacion_problematica": "descripción del contexto/problema matemático (NO es un texto de lectura, es una SITUACIÓN con datos numéricos, figuras, patrones, etc.)",
        "preguntas": [
            {{
                "numero": 1,
                "enunciado": "texto de la pregunta matemática",
                "opciones": [
                    {{"letra": "A", "texto": "opción a", "es_correcta": false}},
                    {{"letra": "B", "texto": "opción b", "es_correcta": true}},
                    {{"letra": "C", "texto": "opción c", "es_correcta": false}},
                    {{"letra": "D", "texto": "opción d", "es_correcta": false}}
                ],
                "capacidad": "nombre de la capacidad evaluada",
                "desempeno_codigo": "código del desempeño",
                "criterio_evaluacion": "criterio de evaluación para esta pregunta"
            }}
        ],
        "tabla_respuestas": [
            {{
                "pregunta": 1,
                "capacidad": "nombre de la capacidad",
                "desempeno": "descripción breve del desempeño",
                "respuesta_correcta": "A|B|C|D",
                "justificacion": "explicación breve de por qué es correcta"
            }}
        ]
    }}
}}
"""
        return prompt

    async def generar_examen_matematica(
        self,
        db: Session,
        grado_id: int,
        competencia_id: int,
        desempeno_ids: List[int],
        cantidad: int = 3,
        situacion_base: Optional[str] = None,
        modelo: str = "gemini"
    ) -> dict:
        """
        Genera un examen de matemática basado en desempeños específicos.
        """
        ai_service = ai_factory.get_service(modelo)
        
        if not ai_service.is_configured():
            raise ValueError(f"Configuración de API para {modelo} incompleta")
        
        if not desempeno_ids:
            raise ValueError("Debe seleccionar al menos un desempeño")
        
        # Obtener grado
        grado = db.query(Grado).filter(Grado.id == grado_id).first()
        if not grado:
            raise ValueError(f"Grado con id {grado_id} no encontrado")
        
        # Obtener competencia
        competencia = db.query(CompetenciaMatematica).filter(
            CompetenciaMatematica.id == competencia_id
        ).first()
        if not competencia:
            raise ValueError(f"Competencia con id {competencia_id} no encontrada")
        
        # Obtener desempeños seleccionados con sus capacidades
        desempenos = db.query(DesempenoMatematica).filter(
            DesempenoMatematica.id.in_(desempeno_ids)
        ).all()
        
        if not desempenos:
            raise ValueError("No se encontraron los desempeños seleccionados")
        
        # Organizar desempeños por capacidad
        capacidades_desempenos = {}
        for d in desempenos:
            cap = d.capacidad
            if cap.orden not in capacidades_desempenos:
                capacidades_desempenos[cap.orden] = {
                    'nombre': cap.nombre,
                    'desempenos': []
                }
            capacidades_desempenos[cap.orden]['desempenos'].append({
                'codigo': d.codigo,
                'descripcion': d.descripcion
            })
        
        # Construir prompt
        prompt = self._build_prompt_matematica(
            grado_nombre=grado.nombre,
            competencia_nombre=competencia.nombre,
            capacidades_desempenos=capacidades_desempenos,
            cantidad=cantidad,
            situacion_base=situacion_base
        )
        
        try:
            response_text = await ai_service.generate_content(prompt)
            response_text = ai_service.clean_json_response(response_text)
            
            data = json.loads(response_text)
            
            # Construir texto de desempeños usados
            desempenos_texto = "\n".join([
                f"{d.codigo}. {d.descripcion} (Cap: {d.capacidad.nombre})"
                for d in desempenos
            ])
            
            return {
                "grado": grado.nombre,
                "competencia": competencia.nombre,
                "desempenos_usados": desempenos_texto,
                "saludo": data.get("saludo", ""),
                "examen": data.get("examen", {}),
                "total_preguntas": len(data.get("examen", {}).get("preguntas", []))
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al parsear respuesta de {modelo}: {e}")
        except Exception as e:
            raise ValueError(f"Error al generar examen de matemática: {e}")


# Singleton instance
matematica_service = MatematicaService()
