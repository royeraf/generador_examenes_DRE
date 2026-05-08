import { ref, shallowRef, computed } from 'vue';
import type { Examen } from '../types';
import type { NivelDificultad } from '../constants/niveles';
import desempenosService from '../services/api';

export interface BaseResultado {
  grado: string;
  desempenos_usados: string;
  saludo: string;
  examen: Examen;
  total_preguntas: number;
}

export function useBaseExam() {
  const selectedGradoId = shallowRef<number | null>(null);
  const selectedDesempenoIds = ref<number[]>([]);
  const selectedNivelDificultad = shallowRef<NivelDificultad>('intermedio');
  const cantidadPreguntas = shallowRef(3);

  const loading = shallowRef(false);
  const loadingDesempenos = shallowRef(false);
  const loadingGrados = shallowRef(true);
  const descargandoWord = shallowRef(false);
  const error = shallowRef<string | null>(null);
  const showResults = shallowRef(false);
  const activeTab = shallowRef<string>('generador');

  const selectedDesempenosCount = computed(() => selectedDesempenoIds.value.length);

  // descargarExamenWord se define aquí para reutilizar descargandoWord y error,
  // pero necesita acceso al resultado específico de cada módulo vía ref de cierre.
  function makeDescargarWord<T extends BaseResultado>(resultadoRef: { value: T | null }) {
    return async () => {
      if (!resultadoRef.value?.examen) return;
      descargandoWord.value = true;
      try {
        await desempenosService.descargarWord(resultadoRef.value.examen, resultadoRef.value.grado);
      } catch {
        error.value = 'Error al descargar el documento Word';
      } finally {
        descargandoWord.value = false;
      }
    };
  }

  return {
    selectedGradoId,
    selectedDesempenoIds,
    selectedNivelDificultad,
    cantidadPreguntas,
    loading,
    loadingDesempenos,
    loadingGrados,
    descargandoWord,
    error,
    showResults,
    activeTab,
    selectedDesempenosCount,
    makeDescargarWord,
  };
}
