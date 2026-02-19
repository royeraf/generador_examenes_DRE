import { ref } from 'vue';
import type { ExamenHistoryEntry, GenerarExamenResponse } from '../types';
import { examenesService } from '../services/api';

// Module-level shared state (singleton)
const history = ref<ExamenHistoryEntry[]>([]);
const loadingHistory = ref(false);
const loadingDelete = ref<string | null>(null);

export function useMatSistemHistory() {

    async function fetchHistory() {
        loadingHistory.value = true;
        try {
            const data = await examenesService.getExamenesMatematica();
            history.value = data.map((ex: any) => ({
                id: ex.id.toString(),
                fechaCreacion: ex.fecha_creacion,
                gradoLabel: ex.grado_nombre || 'Grado no especificado',
                resultado: {
                    grado: ex.grado_nombre,
                    total_preguntas: ex.total_preguntas,
                    examen: {
                        titulo: ex.titulo,
                        grado: ex.grado_nombre,
                    }
                } as any
            }));
        } catch (error) {
            console.error('Error fetching math history:', error);
        } finally {
            loadingHistory.value = false;
        }
    }

    async function saveExam(resultado: GenerarExamenResponse, gradoLabel: string, params?: any): Promise<void> {
        try {
            const payload = {
                grado_id: params?.grado_id || null,
                competencia_id: params?.competencia_id || null,
                titulo: resultado.examen.titulo,
                grado_nombre: gradoLabel,
                nivel_dificultad: params?.nivel_dificultad || 'intermedio',
                modelo_ia: params?.modelo || 'gemini',
                saludo: resultado.saludo,
                situacion_problematica: (resultado.examen as any).situacion_problematica,
                preguntas: resultado.examen.preguntas,
                tabla_respuestas: resultado.examen.tabla_respuestas,
                desempenos_usados: resultado.desempenos_usados
            };

            await examenesService.saveExamenMatematica(payload);
            await fetchHistory();
        } catch (error) {
            console.error('Error saving math exam:', error);
        }
    }

    async function getFullExam(id: string): Promise<ExamenHistoryEntry | null> {
        try {
            const ex = await examenesService.getExamenMatematica(parseInt(id));
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
                        situacion_problematica: ex.situacion_problematica,
                        preguntas: ex.preguntas,
                        tabla_respuestas: ex.tabla_respuestas
                    } as any
                }
            };
        } catch (error) {
            console.error('Error fetching full math exam:', error);
            return null;
        }
    }

    async function removeExam(id: string) {
        loadingDelete.value = id;
        try {
            await examenesService.deleteExamenMatematica(parseInt(id));
            history.value = history.value.filter(e => e.id !== id);
        } catch (error) {
            console.error('Error removing math exam:', error);
        } finally {
            loadingDelete.value = null;
        }
    }

    function clearHistory() {
        history.value = [];
    }

    return { history, loadingHistory, loadingDelete, fetchHistory, saveExam, getFullExam, removeExam, clearHistory };
}
