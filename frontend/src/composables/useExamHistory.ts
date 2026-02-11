import { ref } from 'vue';
import type { ExamenHistoryEntry, GenerarExamenResponse, FilaTablaRespuestas, PreguntaConfig, DesempenoItem } from '../types';

const STORAGE_KEY = 'lectosistem_examHistory';
const MAX_ENTRIES = 20;

// Module-level shared state (singleton)
const history = ref<ExamenHistoryEntry[]>(loadFromStorage());

function loadFromStorage(): ExamenHistoryEntry[] {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
}

function persist() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(history.value));
}

export function useExamHistory() {

    function saveExam(resultado: GenerarExamenResponse, gradoLabel: string): ExamenHistoryEntry {
        const entry: ExamenHistoryEntry = {
            id: Date.now().toString(),
            fechaCreacion: new Date().toISOString(),
            gradoLabel,
            resultado,
        };

        history.value.unshift(entry);

        // Keep max entries
        if (history.value.length > MAX_ENTRIES) {
            history.value = history.value.slice(0, MAX_ENTRIES);
        }

        persist();
        return entry;
    }

    function removeExam(id: string) {
        history.value = history.value.filter(e => e.id !== id);
        persist();
    }

    function clearHistory() {
        history.value = [];
        persist();
    }

    return { history, saveExam, removeExam, clearHistory };
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

        result[targetLevel].push({
            descripcion: matched?.descripcion || fila.desempeno,
            desempenoId: matched?.id ?? null,
            clave: fila.respuesta_correcta,
        });
    }

    return result;
}
