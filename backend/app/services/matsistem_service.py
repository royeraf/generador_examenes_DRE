"""
Servicio para gestionar evaluaciones de Matemática (MatSistem).
Genera situaciones problemáticas y preguntas siguiendo el modelo MINEDU.
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import json

from app.models.db_models import (
    Grado,
    CompetenciaMatematica,
    CapacidadMatematica,
    DesempenoMatematica,
    EstandarMatematica
)
from app.core.config import get_settings
from app.services.ai_factory import ai_factory

settings = get_settings()


class MatSistemService:
    """Servicio para generar evaluaciones de matemática."""
    
    def __init__(self):
        pass
    
    def _build_prompt_matematica(
        self,
        grado_nombre: str,
        competencia_nombre: str,
        capacidades_desempenos: dict,
        cantidad: int,
        situacion_base: Optional[str] = None,
        nivel_dificultad: str = "intermedio"
    ) -> str:
        """
        Construye el prompt para generar un examen de matemática
        siguiendo el formato oficial del MINEDU (MateJony).
        
        Args:
            nivel_dificultad: 'basico', 'intermedio', o 'avanzado'
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
        
        # Instrucciones según nivel de dificultad para matemática
        dificultad_instrucciones = {
            "basico": """
**NIVEL DE DIFICULTAD: BÁSICO (Simple y sencillo)**
- Crear una situación problemática SENCILLA y fácil de comprender
- Usar NÚMEROS PEQUEÑOS y operaciones directas
- Los problemas deben resolverse en 1-2 pasos como máximo
- Evitar múltiples operaciones o procesos complejos
- Las alternativas incorrectas deben ser claramente distinguibles
- Usar contextos cotidianos y familiares para el estudiante
- Los datos deben estar explícitos y fáciles de identificar
- Priorizar ejercicios de aplicación directa de conceptos""",
            "intermedio": """
**NIVEL DE DIFICULTAD: INTERMEDIO (Demanda cognitiva media)**
- La situación problemática debe tener complejidad moderada
- Pueden requerirse 2-3 pasos para resolver los problemas
- Incluir problemas que requieran identificar datos relevantes
- Las alternativas incorrectas deben ser plausibles
- Combinar diferentes operaciones o conceptos relacionados
- Requerir que el estudiante organice información antes de resolver
- Equilibrar problemas de diferentes niveles de complejidad""",
            "avanzado": """
**NIVEL DE DIFICULTAD: AVANZADO (Alta demanda cognitiva)**
- La situación problemática debe ser COMPLEJA y desafiante
- Los problemas pueden requerir MÚLTIPLES PASOS (3 o más)
- Incluir problemas que requieran RAZONAMIENTO y ESTRATEGIA
- Las alternativas incorrectas deben ser MUY PLAUSIBLES (distractores bien elaborados)
- Requerir análisis de datos, identificación de patrones o relaciones
- Incluir problemas no rutinarios que desafíen al estudiante
- Pueden requerirse conceptos combinados de diferentes capacidades
- Incluir problemas que admitan diferentes estrategias de solución
- Requerir que el estudiante justifique o argumente su respuesta"""
        }
        
        instruccion_dificultad = dificultad_instrucciones.get(
            nivel_dificultad.lower(), 
            dificultad_instrucciones["intermedio"]
        )
        
        prompt = f"""Eres **"MateJony"**, especialista pedagógico en Matemática del MINEDU (Perú). Tu enfoque es la Resolución de Problemas y el Pensamiento Crítico.
Diseña una **Situación Significativa de Aprendizaje** para estudiantes de **{grado_nombre}**.

**PARÁMETROS CURRICULARES:**
- **Competencia:** {competencia_nombre}
- **Grado:** {grado_nombre}
- **Nivel de Dificultad:** {nivel_dificultad.upper()}
- **Contexto:** Regional Peruano (mercados locales, ferias, turismo, geografía, biodiversidad del Perú).

**INSUMO BASE:**
{situacion_texto if situacion_base else "CREA UNA SITUACIÓN ORIGINAL basada en un contexto real y motivador para la edad del estudiante."}

**DESEMPEÑOS A EVALUAR (Tus preguntas deben alinearse a estos):**
{desempenos_formateados}

{instruccion_dificultad}

**REQUERIMIENTOS DEL ENTREGABLE:**
Genera un examen completo en formato JSON con la siguiente estructura.
1. La **Situación Problemática** debe ser un texto narrativo breve (y datos numéricos/gráficos si aplica) que plantee un reto. NO puede ser solo una operación matemática suelta.
2. Genera **{cantidad} preguntas** de opción múltiple.
3. Cada pregunta debe estar vinculada a uno de los desempeños listados.

**FORMATO JSON OBLIGATORIO:**
Responde ÚNICAMENTE con este JSON válido:

{{
    "saludo": "¡Hola! Soy MateJony. He preparado este desafío matemático contextualizado para tus estudiantes...",
    "examen": {{
        "titulo": "Título motivador (ej: 'Nuestra Feria Gastronómica', 'Calculando distancias en los Andes')",
        "grado": "{grado_nombre}",
        "competencia": "{competencia_nombre}",
        "instrucciones": "Lee atentamente la situación y resuelve los problemas planteados.",
        "situacion_problematica": "Texto completo de la situación significativa...",
        "preguntas": [
            {{
                "numero": 1,
                "enunciado": "¿Enunciado del problema matemático?",
                "opciones": [
                    {{"letra": "A", "texto": "Respuesta 1", "es_correcta": false}},
                    {{"letra": "B", "texto": "Respuesta 2 (Correcta)", "es_correcta": true}},
                    {{"letra": "C", "texto": "Respuesta 3", "es_correcta": false}},
                    {{"letra": "D", "texto": "Respuesta 4", "es_correcta": false}}
                ],
                "capacidad": "Nombre de la capacidad asociada",
                "desempeno_codigo": "Código del desempeño evaluado",
                "criterio_evaluacion": "Criterio específico: [Habilidad] + [Contenido] + [Condición]"
            }}
        ],
        "tabla_respuestas": [
            {{
                "pregunta": 1,
                "capacidad": "Capacidad",
                "desempeno": "Desempeño resumido",
                "respuesta_correcta": "B",
                "justificacion": "Explicación paso a paso de la resolución"
            }}
        ]
    }}
}}
"""
        return prompt

    async def generar_examen_matematica(
        self,
        db: AsyncSession,
        grado_id: int,
        competencia_id: int,
        desempeno_ids: List[int],
        cantidad: int = 3,
        situacion_base: Optional[str] = None,
        modelo: str = "gemini",
        nivel_dificultad: str = "intermedio"
    ) -> dict:
        """
        Genera un examen de matemática basado en desempeños específicos.
        
        Args:
            nivel_dificultad: 'basico' (simple), 'intermedio' (demanda media), 'avanzado' (alta demanda cognitiva)
        """
        ai_service = ai_factory.get_service(modelo)
        
        if not ai_service.is_configured():
            raise ValueError(f"Configuración de API para {modelo} incompleta")
        
        if not desempeno_ids:
            raise ValueError("Debe seleccionar al menos un desempeño")
        
        # Obtener grado
        result_grado = await db.execute(select(Grado).where(Grado.id == grado_id))
        grado = result_grado.scalars().first()
        if not grado:
            raise ValueError(f"Grado con id {grado_id} no encontrado")
        
        # Obtener competencia
        result_comp = await db.execute(select(CompetenciaMatematica).where(CompetenciaMatematica.id == competencia_id))
        competencia = result_comp.scalars().first()
        if not competencia:
            raise ValueError(f"Competencia con id {competencia_id} no encontrada")
        
        # Obtener desempeños seleccionados con sus capacidades
        result_desempenos = await db.execute(
            select(DesempenoMatematica)
            .where(DesempenoMatematica.id.in_(desempeno_ids))
            .options(selectinload(DesempenoMatematica.capacidad))
        )
        desempenos = result_desempenos.scalars().all()
        
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
            situacion_base=situacion_base,
            nivel_dificultad=nivel_dificultad
        )
        
        try:
            response_text = await ai_service.generate_content(prompt)
            response_text = ai_service.clean_json_response(response_text)
            
            data = json.loads(response_text)
            
            # Construir texto de desempeños usados
            # d.capacidad ya está cargado gracias a selectinload
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
matsistem_service = MatSistemService()
