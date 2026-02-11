import { ref } from 'vue';
import type { ExamenHistoryEntry, GenerarExamenResponse } from '../types';

const STORAGE_KEY = 'matsistem_examHistory';
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

export function useMatSistemHistory() {

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
