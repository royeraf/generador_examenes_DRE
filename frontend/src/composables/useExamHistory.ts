import { ref } from 'vue';
import type { ExamenHistoryEntry, GenerarExamenResponse, FilaTablaRespuestas, PreguntaConfig, DesempenoItem } from '../types';
import { examenesService } from '../services/api';

// Module-level shared state (singleton)
const history = ref<ExamenHistoryEntry[]>([]);
const loadingHistory = ref(false);
const loadingDelete = ref<string | null>(null);

export function useExamHistory() {

    async function fetchHistory() {
        loadingHistory.value = true;
        try {
            const data = await examenesService.getExamenesLectura();
            // Map backend summary to frontend history entry
            history.value = data.map((ex: any) => ({
                id: ex.id.toString(),
                fechaCreacion: ex.fecha_creacion,
                gradoLabel: ex.grado_nombre || 'Grado no especificado',
                // For the list we store a partial result, full fetch happens on demand if needed
                // or we can store what we have.
                resultado: {
                    grado: ex.grado_nombre,
                    total_preguntas: ex.total_preguntas,
                    examen: {
                        titulo: ex.titulo,
                        grado: ex.grado_nombre,
                        // Full content will be loaded on demand in the view
                    }
                } as any
            }));
        } catch (error) {
            console.error('Error fetching history:', error);
        } finally {
            loadingHistory.value = false;
        }
    }

    async function saveExam(resultado: GenerarExamenResponse, gradoLabel: string, params?: any): Promise<void> {
        try {
            const payload = {
                grado_id: params?.grado_id || null,
                titulo: resultado.examen.titulo,
                grado_nombre: gradoLabel,
                nivel_dificultad: params?.nivel_dificultad || 'intermedio',
                modelo_ia: params?.modelo || 'gemini',
                saludo: resultado.saludo,
                instrucciones: resultado.examen.instrucciones,
                lectura: resultado.examen.lectura,
                preguntas: resultado.examen.preguntas,
                tabla_respuestas: resultado.examen.tabla_respuestas,
                desempenos_usados: resultado.desempenos_usados
            };

            await examenesService.saveExamenLectura(payload);
            await fetchHistory(); // Refresh
        } catch (error) {
            console.error('Error saving exam:', error);
        }
    }

    async function getFullExam(id: string): Promise<ExamenHistoryEntry | null> {
        try {
            const ex = await examenesService.getExamenLectura(parseInt(id));
            return {
                id: ex.id.toString(),
                fechaCreacion: ex.fecha_creacion,
                gradoLabel: ex.grado_nombre,
                resultado: {
                    grado: ex.grado_nombre,
                    desempenos_usados: ex.desempenos_usados,
                    saludo: ex.saludo,
                    total_preguntas: ex.preguntas?.length || 0,
                    examen: {
                        titulo: ex.titulo,
                        grado: ex.grado_nombre,
                        instrucciones: ex.instrucciones,
                        lectura: ex.lectura,
                        preguntas: ex.preguntas,
                        tabla_respuestas: ex.tabla_respuestas
                    }
                }
            };
        } catch (error) {
            console.error('Error fetching full exam:', error);
            return null;
        }
    }

    async function removeExam(id: string) {
        loadingDelete.value = id;
        try {
            await examenesService.deleteExamenLectura(parseInt(id));
            history.value = history.value.filter(e => e.id !== id);
        } catch (error) {
            console.error('Error removing exam:', error);
        } finally {
            loadingDelete.value = null;
        }
    }

    function clearHistory() {
        // Not implemented on backend yet or usually not desired to clear all
        history.value = [];
    }

    return { history, loadingHistory, loadingDelete, fetchHistory, saveExam, getFullExam, removeExam, clearHistory };
}

/**
 * Maps exam answer table to Sistematizador level structure.
 * LITERAL → inicio, INFERENCIAL → proceso, CRÍTICO → satisfactorio
 */
export function mapExamToNiveles(
    tablaRespuestas: FilaTablaRespuestas[],
    availableDesempenos: DesempenoItem[]
): Record<string, PreguntaConfig[]> {
    const nivelMapping: Record<string, string> = {
        'LITERAL': 'inicio',
        'INFERENCIAL': 'proceso',
        'CRITICO': 'satisfactorio',
        'CRÍTICO': 'satisfactorio',
    };

    const result: Record<string, PreguntaConfig[]> = {
        'pre-inicio': [],
        'inicio': [],
        'proceso': [],
        'satisfactorio': [],
        'destacado': [],
    };

    for (const fila of tablaRespuestas) {
        const targetLevel = nivelMapping[fila.nivel.toUpperCase()] || 'inicio';

        const matched = availableDesempenos.find(d => d.codigo === fila.desempeno);

        const container = result[targetLevel];
        if (container) {
            container.push({
                descripcion: matched?.descripcion || fila.desempeno,
                desempenoId: matched?.id ?? null,
                clave: fila.respuesta_correcta,
            });
        }
    }

    return result;
}
