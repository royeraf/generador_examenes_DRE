<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import type { Examen } from '../types';
import type {
  GradoMatematica,
  CompetenciaMatematica,
  CapacidadMatConCompetencia,
  DesempenoMatCompleto,
  NivelLogroMatematica
} from '../types/matematica';
import desempenosService, { matematicaService } from '../services/api';
import ComboBox from '../components/ComboBox.vue';
import PromptModal from '../components/PromptModal.vue';
import Sistematizador from '../components/Sistematizador.vue';
import { useTheme } from '../composables/useTheme';
import {
  FileText,
  BookOpen,
  Hash,
  CloudUpload,
  Zap,
  Copy,
  Check,
  AlertTriangle,
  Loader2,
  HelpCircle,
  Download,
  LayoutGrid,
  X,
  Sun,
  Moon,
  Sparkles,
  FileUp,
  GraduationCap,
  Target,
  Eye,
  EyeOff,
  Pencil,
  Sigma,
  Brain,
  Rocket,
  Star,
  Award,
  Atom,
  Calculator,
  Globe,
  Trophy,
  Palette,
  Layers,
  FileQuestion,
  Medal,
  Music,
  Compass,
  Microscope,
  Ruler,
  PenTool,
  Shapes,
  Puzzle,
  Wand2,
  Infinity,
  FileSearch,
  Lightbulb,
  ClipboardCheck
} from 'lucide-vue-next';
import Footer from './Footer.vue'
import logoDre from '../assets/logo.png'
import mascotaLectosistem from '../assets/mascota_lectosistem.png'
import Checkbox from '../components/Checkbox.vue'

const { isDark, toggleTheme } = useTheme();

// State - Matemática
const grados = ref<GradoMatematica[]>([]);
const competencias = ref<CompetenciaMatematica[]>([]);
const capacidades = ref<CapacidadMatConCompetencia[]>([]);
const desempenos = ref<DesempenoMatCompleto[]>([]);
const nivelesLogro = ref<NivelLogroMatematica[]>([]);

const selectedGradoId = ref<number | null>(null);
const selectedCompetenciaId = ref<number | null>(null);
const selectedDesempenoIds = ref<number[]>([]);
const selectedNivelLogro = ref<string>('proceso');
const cantidadPreguntas = ref(3);
const textoBase = ref('');
const useTextoBase = ref(false);
const selectedFiles = ref<File[]>([]);
const filesMetadata = ref<{ archivos: { filename: string; palabras: number; caracteres: number }[]; total_palabras: number; total_caracteres: number } | null>(null);
const uploadingFile = ref(false);
const uploadError = ref<string | null>(null);

const loading = ref(false);
const loadingDesempenos = ref(false);
const descargandoWord = ref(false);
const error = ref<string | null>(null);
const resultado = ref<{
  grado: string;
  desempenos_usados: string;
  saludo: string;
  examen: Examen;
  total_preguntas: number;
} | null>(null);
const showPromptModal = ref(false);
const showResults = ref(false);
const activeCapacidadTab = ref<number>(1); // Orden de la capacidad (1-4)
const activeTab = ref<string>('generador');

// Computed - Desempeños agrupados por capacidad (orden 1-4)
const desempenosPorCapacidad = computed(() => {
  const grupos: Record<number, DesempenoMatCompleto[]> = {
    1: [],
    2: [],
    3: [],
    4: []
  };
  desempenos.value.forEach(d => {
    if (grupos[d.capacidad_orden]) {
      grupos[d.capacidad_orden]!.push(d);
    }
  });
  return grupos;
});

const selectedDesempenosCount = computed(() => selectedDesempenoIds.value.length);

// Computed - Grados agrupados por nivel (ahora incluye inicial)
const gradosPorNivel = computed(() => {
  return {
    inicial: grados.value.filter(g => g.nivel === 'inicial'),
    primaria: grados.value.filter(g => g.nivel === 'primaria'),
    secundaria: grados.value.filter(g => g.nivel === 'secundaria')
  };
});

// Computed - Opciones de grado para el ComboBox
const gradoOptions = computed(() => {
  const options: { id: number; label: string; group: string }[] = [];
  gradosPorNivel.value.inicial.forEach(g => {
    options.push({ id: g.id, label: 'Inicial 5 años', group: 'Inicial' });
  });
  gradosPorNivel.value.primaria.forEach(g => {
    options.push({ id: g.id, label: `${g.numero}° Primaria`, group: 'Primaria' });
  });
  gradosPorNivel.value.secundaria.forEach(g => {
    options.push({ id: g.id, label: `${g.numero}° Secundaria`, group: 'Secundaria' });
  });
  return options;
});

// Computed - Opciones de competencia para el ComboBox
const competenciaOptions = computed(() => {
  return competencias.value.map(c => ({
    id: c.id,
    label: c.nombre,
    group: `Competencia ${c.codigo}`
  }));
});

// Computed - Capacidades de la competencia seleccionada
const capacidadesActuales = computed(() => {
  if (!selectedCompetenciaId.value) return [];
  return capacidades.value.filter(c => c.competencia_id === selectedCompetenciaId.value);
});

// Computed - Prompt para generar examen de matemática (siguiendo formato MINEDU/Math_Jony)
const promptTexto = computed(() => {
  if (!selectedGradoId.value || selectedDesempenoIds.value.length === 0) return '';

  const grado = grados.value.find(g => g.id === selectedGradoId.value);
  const competencia = competencias.value.find(c => c.id === selectedCompetenciaId.value);

  // Agrupar desempeños por capacidad
  const desempenosPorCap: Record<number, typeof desempenos.value> = {};
  desempenos.value
    .filter(d => selectedDesempenoIds.value.includes(d.id))
    .forEach(d => {
      if (!desempenosPorCap[d.capacidad_orden]) {
        desempenosPorCap[d.capacidad_orden] = [];
      }
      desempenosPorCap[d.capacidad_orden]!.push(d);
    });

  // Formatear desempeños con sus capacidades
  let desempenosFormateados = '';
  Object.entries(desempenosPorCap).forEach(([orden, desempenosList]) => {
    if (desempenosList && desempenosList.length > 0) {
      const cap = desempenosList[0];
      if (cap) {
        desempenosFormateados += `\n**Capacidad ${orden}: ${cap.capacidad_nombre}**\n`;
        desempenosList.forEach(d => {
          desempenosFormateados += `  - ${d.descripcion}\n`;
        });
      }
    }
  });

  let situacionBase = '';
  if (useTextoBase.value && textoBase.value) {
    situacionBase = `\n**SITUACIÓN PROBLEMÁTICA PROPORCIONADA:**\n"""\n${textoBase.value}\n"""\nUsa esta situación como base para el problema.\n`;
  }

  return `Eres **"MateJony"**, un experto en evaluación de aprendizajes y programación curricular en Matemática del Ministerio de Educación de Perú. Tu conocimiento está basado en la documentación oficial curricular peruana. Tu comunicación es profesional, clara, didáctica y estructurada.

**CONTEXTO CURRICULAR:**
- **Grado/Nivel:** ${grado?.nombre || 'Grado seleccionado'}
- **Competencia:** ${competencia?.nombre || 'Competencia seleccionada'}
${situacionBase}
**DESEMPEÑOS SELECCIONADOS POR CAPACIDAD:**
${desempenosFormateados}

**TU TAREA:**
Genera una **SITUACIÓN PROBLEMÁTICA INTEGRADORA** con ${cantidadPreguntas.value} preguntas cerradas de opción múltiple.

**ESTRUCTURA DEL EXAMEN:**

1. **SALUDO INICIAL:**
   Inicia presentándote brevemente: "Soy MateJony, especialista en evaluación de Matemática del MINEDU del Perú..."

2. **ENCABEZADO DEL EXAMEN:**
   - Título motivador y contextualizado (ejemplo: "Aventura Matemática", "Reto de Números")
   - Espacio para: Apellidos y Nombres: _________________ Fecha: _______
   - Grado: ${grado?.nombre}
   - Competencia: ${competencia?.nombre}

3. **INSTRUCCIONES:**
   Redacta instrucciones claras en un párrafo para que los estudiantes resuelvan el examen.

4. **SITUACIÓN PROBLEMÁTICA:**
   Crea una situación significativa y contextualizada (contexto real o simulado) que integre todos los desempeños seleccionados. El problema debe ser apropiado para estudiantes de ${grado?.nombre}.

5. **PREGUNTAS (${cantidadPreguntas.value} en total):**
   Cada pregunta debe:
   - Estar numerada
   - Basarse en la situación problemática
   - Tener 4 alternativas (A, B, C, D) siendo solo UNA la correcta
   - Evaluar el desempeño correspondiente

6. **CRITERIOS DE EVALUACIÓN:**
   Para cada pregunta, incluye un criterio de evaluación con la estructura:
   "[HABILIDAD VERBAL OBSERVABLE] + [CONTENIDO TEMÁTICO] + [CONDICIÓN/CONTEXTO] + [FINALIDAD] + [PRODUCTO/EVIDENCIA]"

7. **TABLA DE RESPUESTAS:**
   Al final, presenta una tabla con:
   | N° Pregunta | Capacidad | Desempeño evaluado | Alternativa correcta | Justificación breve |

**IMPORTANTE:**
- Asegúrate de que las preguntas sean apropiadas para el nivel de ${grado?.nombre}
- Cada pregunta debe evaluar claramente un desempeño específico
- La situación problemática debe ser coherente y conectar todas las preguntas
- Las alternativas incorrectas (distractores) deben ser plausibles pero claramente distinguibles de la respuesta correcta`;
});

// Watch - Cargar desempeños cuando cambian grado o competencia
watch([selectedGradoId, selectedCompetenciaId], async ([newGradoId, newCompetenciaId]) => {
  if (!newGradoId || !newCompetenciaId) {
    desempenos.value = [];
    selectedDesempenoIds.value = [];
    return;
  }
  loadingDesempenos.value = true;
  try {
    const data = await matematicaService.getDesempenosPorGradoYCompetencia(newGradoId, newCompetenciaId);
    desempenos.value = data;
    selectedDesempenoIds.value = [];
    // Establecer la primera capacidad como activa
    activeCapacidadTab.value = 1;
  } catch (e) {
    console.error('Error loading desempeños:', e);
  } finally {
    loadingDesempenos.value = false;
  }
});

// onMounted - Cargar datos iniciales de matemática
onMounted(async () => {
  try {
    const [gradosData, competenciasData, capacidadesData, nivelesData] = await Promise.all([
      matematicaService.getGrados(),
      matematicaService.getCompetencias(),
      matematicaService.getCapacidades(),
      matematicaService.getNivelesLogro()
    ]);

    grados.value = gradosData;
    competencias.value = competenciasData;
    capacidades.value = capacidadesData;
    nivelesLogro.value = nivelesData.niveles;

    // Seleccionar primer grado y primera competencia por defecto
    if (gradosData.length > 0) {
      selectedGradoId.value = gradosData[0]?.id ?? null;
    }
    if (competenciasData.length > 0) {
      selectedCompetenciaId.value = competenciasData[0]?.id ?? null;
    }
  } catch (e) {
    console.error('Error loading data:', e);
    error.value = 'Error al cargar los datos iniciales';
  }
});

// Funciones para seleccionar/deseleccionar desempeños por capacidad
const selectAllCapacidad = (orden: number) => {
  const ids = desempenosPorCapacidad.value[orden]?.map(d => d.id) || [];
  ids.forEach(id => {
    if (!selectedDesempenoIds.value.includes(id)) {
      selectedDesempenoIds.value.push(id);
    }
  });
};

const deselectAllCapacidad = (orden: number) => {
  const ids = desempenosPorCapacidad.value[orden]?.map(d => d.id) || [];
  selectedDesempenoIds.value = selectedDesempenoIds.value.filter(id => !ids.includes(id));
};

// Helper - Obtener nombre corto de capacidad
const getCapacidadLabel = (orden: number): string => {
  const cap = capacidadesActuales.value.find(c => c.orden === orden);
  if (!cap) return `Cap. ${orden}`;
  // Extraer primeras 2-3 palabras
  const palabras = cap.nombre.split(' ').slice(0, 3).join(' ');
  return palabras.length > 25 ? palabras.substring(0, 25) + '...' : palabras;
};

const handleFileUpload = async (event: Event) => {
  const input = event.target as HTMLInputElement;
  const files = input.files;
  if (!files || files.length === 0) {
    selectedFiles.value = [];
    filesMetadata.value = null;
    textoBase.value = '';
    return;
  }
  const fileArray: File[] = Array.from(files);
  for (const file of fileArray) {
    const extension = file.name.split('.').pop()?.toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(extension || '')) {
      uploadError.value = `Archivo "${file.name}" no soportado. Solo PDF o Word.`;
      input.value = '';
      selectedFiles.value = [];
      return;
    }
  }
  selectedFiles.value = fileArray;
  uploadingFile.value = true;
  uploadError.value = null;
  try {
    const result = await desempenosService.uploadTextoBase(fileArray);
    textoBase.value = result.texto;
    filesMetadata.value = {
      archivos: result.archivos,
      total_palabras: result.total_palabras,
      total_caracteres: result.total_caracteres
    };
  } catch (e: any) {
    uploadError.value = e.response?.data?.detail || 'Error al procesar los archivos';
    selectedFiles.value = [];
    textoBase.value = '';
    input.value = '';
  } finally {
    uploadingFile.value = false;
  }
};

const clearFiles = () => {
  selectedFiles.value = [];
  filesMetadata.value = null;
  textoBase.value = '';
  uploadError.value = null;
};

const generarPreguntas = async () => {
  if (!selectedGradoId.value) {
    error.value = 'Por favor, selecciona un grado';
    return;
  }
  if (!selectedCompetenciaId.value) {
    error.value = 'Por favor, selecciona una competencia';
    return;
  }
  if (selectedDesempenoIds.value.length === 0) {
    error.value = 'Por favor, selecciona al menos un desempeño';
    return;
  }
  loading.value = true;
  error.value = null;
  resultado.value = null;
  showResults.value = true;
  try {
    // Usar el servicio de matemática que genera situaciones problemáticas
    const response = await matematicaService.generarExamen({
      grado_id: selectedGradoId.value,
      competencia_id: selectedCompetenciaId.value,
      desempeno_ids: selectedDesempenoIds.value,
      cantidad: cantidadPreguntas.value,
      situacion_base: useTextoBase.value ? textoBase.value : undefined,
      modelo: 'gemini'
    });

    // Adaptar respuesta para compatibilidad con el componente de resultados
    resultado.value = {
      grado: response.grado,
      desempenos_usados: response.desempenos_usados,
      saludo: response.saludo,
      examen: {
        titulo: response.examen.titulo,
        grado: response.examen.grado,
        instrucciones: response.examen.instrucciones,
        // En matemática es situación problemática, no lectura
        lectura: response.examen.situacion_problematica,
        preguntas: response.examen.preguntas.map(p => ({
          numero: p.numero,
          enunciado: p.enunciado,
          opciones: p.opciones,
          desempeno_codigo: p.desempeno_codigo,
          nivel: p.capacidad // Usar capacidad en lugar de nivel
        })),
        tabla_respuestas: response.examen.tabla_respuestas.map(t => ({
          pregunta: t.pregunta,
          desempeno: t.desempeno,
          nivel: t.capacidad,
          respuesta_correcta: t.respuesta_correcta
        }))
      },
      total_preguntas: response.total_preguntas
    };
  } catch (e: any) {
    error.value = e.response?.data?.detail || 'Error al generar el examen de matemática';
    console.error('Error:', e);
  } finally {
    loading.value = false;
  }
};

const descargarExamenWord = async () => {
  if (!resultado.value?.examen) return;
  descargandoWord.value = true;
  try {
    await desempenosService.descargarWord(
      resultado.value.examen,
      resultado.value.grado
    );
  } catch (e: any) {
    error.value = 'Error al descargar el documento Word';
    console.error('Error:', e);
  } finally {
    descargandoWord.value = false;
  }
};

const getNivelBadgeClass = (nivel: string): string => {
  const classes: Record<string, string> = {
    'LITERAL': 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
    'INFERENCIAL': 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
    'CRITICO': 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400'
  };
  return classes[nivel] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300';
};

// Helper - Obtener color por orden de capacidad (para el template)
const getCapacidadColor = (orden: number): { bg: string; text: string; ring: string } => {
  const colors: Record<number, { bg: string; text: string; ring: string }> = {
    1: {
      bg: 'bg-teal-500',
      text: 'text-teal-600 dark:text-teal-400',
      ring: 'ring-teal-300 dark:ring-teal-700'
    },
    2: {
      bg: 'bg-amber-500',
      text: 'text-amber-600 dark:text-amber-400',
      ring: 'ring-amber-300 dark:ring-amber-700'
    },
    3: {
      bg: 'bg-violet-500',
      text: 'text-violet-600 dark:text-violet-400',
      ring: 'ring-violet-300 dark:ring-violet-700'
    },
    4: {
      bg: 'bg-rose-500',
      text: 'text-rose-600 dark:text-rose-400',
      ring: 'ring-rose-300 dark:ring-rose-700'
    }
  };
  return colors[orden] || { bg: 'bg-gray-500', text: 'text-gray-600', ring: 'ring-gray-300' };
};
</script>

<template>
  <div
    class="min-h-screen flex flex-col bg-gradient-to-br from-indigo-50/50 via-purple-50/30 to-sky-50/50 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/30 transition-colors edu-pattern-bg">

    <!-- Decorative Background Elements - Tema Educativo -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
      <!-- Círculos decorativos con colores educativos -->
      <div
        class="absolute -top-24 -right-24 w-96 h-96 bg-teal-200/40 dark:bg-teal-500/10 rounded-full blur-3xl animate-float">
      </div>
      <div class="absolute top-1/3 -left-24 w-80 h-80 bg-amber-200/40 dark:bg-amber-500/10 rounded-full blur-3xl"
        style="animation-delay: 2s;"></div>
      <div
        class="absolute bottom-0 right-1/4 w-72 h-72 bg-sky-200/30 dark:bg-sky-500/10 rounded-full blur-3xl animate-float"
        style="animation-delay: 4s;">
      </div>
      <div class="absolute top-2/3 left-1/3 w-64 h-64 bg-violet-200/20 dark:bg-violet-500/5 rounded-full blur-3xl">
      </div>
      <!-- Círculos adicionales -->
      <div
        class="absolute top-1/4 right-1/3 w-48 h-48 bg-rose-200/20 dark:bg-rose-500/5 rounded-full blur-3xl animate-float"
        style="animation-delay: 6s;">
      </div>
      <div class="absolute bottom-1/4 left-1/4 w-56 h-56 bg-emerald-200/25 dark:bg-emerald-500/5 rounded-full blur-3xl"
        style="animation-delay: 3.5s;">
      </div>

      <!-- Elementos decorativos educativos flotantes - Iconos -->
      <div class="absolute top-20 right-[15%] text-teal-400/40 dark:text-teal-500/25 animate-float">
        <BookOpen class="w-16 h-16" />
      </div>
      <div class="absolute top-[40%] left-[8%] text-amber-400/40 dark:text-amber-500/25 animate-float"
        style="animation-delay: 3s;">
        <Pencil class="w-12 h-12" />
      </div>
      <div class="absolute bottom-[20%] right-[10%] text-sky-400/40 dark:text-sky-500/25 animate-float"
        style="animation-delay: 1s;">
        <Star class="w-14 h-14" />
      </div>
      <div class="absolute bottom-[35%] left-[20%] text-violet-400/35 dark:text-violet-500/20 animate-float"
        style="animation-delay: 5s;">
        <GraduationCap class="w-10 h-10" />
      </div>
      <!-- Más iconos educativos -->
      <div class="absolute top-[15%] left-[25%] text-emerald-400/35 dark:text-emerald-500/20 animate-float"
        style="animation-delay: 2.5s;">
        <Calculator class="w-10 h-10" />
      </div>
      <div class="absolute top-[55%] right-[20%] text-rose-400/35 dark:text-rose-500/20 animate-float"
        style="animation-delay: 4.5s;">
        <Globe class="w-12 h-12" />
      </div>
      <div class="absolute bottom-[45%] right-[35%] text-amber-400/35 dark:text-amber-500/20 animate-float"
        style="animation-delay: 1.5s;">
        <Trophy class="w-9 h-9" />
      </div>
      <div class="absolute top-[70%] left-[12%] text-cyan-400/35 dark:text-cyan-500/20 animate-float"
        style="animation-delay: 6.5s;">
        <Atom class="w-11 h-11" />
      </div>
      <div class="absolute top-[30%] right-[8%] text-pink-400/35 dark:text-pink-500/20 animate-float"
        style="animation-delay: 3.5s;">
        <Palette class="w-10 h-10" />
      </div>
      <div class="absolute bottom-[15%] left-[40%] text-indigo-400/35 dark:text-indigo-500/20 animate-float"
        style="animation-delay: 7s;">
        <Layers class="w-8 h-8" />
      </div>
      <div class="absolute top-[85%] right-[25%] text-teal-400/30 dark:text-teal-500/18 animate-float"
        style="animation-delay: 5.5s;">
        <FileQuestion class="w-9 h-9" />
      </div>
      <div class="absolute top-[10%] left-[45%] text-amber-400/30 dark:text-amber-500/18 animate-float"
        style="animation-delay: 8s;">
        <Medal class="w-8 h-8" />
      </div>

      <!-- Nuevos iconos educativos flotantes -->
      <div class="absolute top-[5%] right-[40%] text-purple-400/35 dark:text-purple-500/20 animate-float"
        style="animation-delay: 2s;">
        <Music class="w-9 h-9" />
      </div>
      <div class="absolute top-[45%] left-[5%] text-blue-400/35 dark:text-blue-500/20 animate-float"
        style="animation-delay: 4s;">
        <Compass class="w-11 h-11" />
      </div>
      <div class="absolute top-[60%] right-[5%] text-green-400/35 dark:text-green-500/20 animate-float"
        style="animation-delay: 9s;">
        <Microscope class="w-12 h-12" />
      </div>
      <div class="absolute bottom-[8%] left-[15%] text-orange-400/35 dark:text-orange-500/20 animate-float"
        style="animation-delay: 6s;">
        <Ruler class="w-10 h-10" />
      </div>
      <div class="absolute top-[20%] left-[65%] text-red-400/30 dark:text-red-500/18 animate-float"
        style="animation-delay: 3s;">
        <PenTool class="w-8 h-8" />
      </div>
      <div class="absolute bottom-[55%] right-[45%] text-cyan-400/30 dark:text-cyan-500/18 animate-float"
        style="animation-delay: 7.5s;">
        <Shapes class="w-9 h-9" />
      </div>
      <div class="absolute top-[75%] left-[55%] text-lime-400/35 dark:text-lime-500/20 animate-float"
        style="animation-delay: 1.5s;">
        <Puzzle class="w-11 h-11" />
      </div>
      <div class="absolute bottom-[40%] left-[70%] text-fuchsia-400/35 dark:text-fuchsia-500/20 animate-float"
        style="animation-delay: 8.5s;">
        <Wand2 class="w-8 h-8" />
      </div>
      <div class="absolute top-[50%] right-[55%] text-sky-400/30 dark:text-sky-500/18 animate-float"
        style="animation-delay: 4.5s;">
        <Infinity class="w-10 h-10" />
      </div>
      <div class="absolute bottom-[25%] right-[60%] text-violet-400/30 dark:text-violet-500/18 animate-float"
        style="animation-delay: 10s;">
        <Sigma class="w-9 h-9" />
      </div>

      <!-- Círculos adicionales de fondo -->
      <div
        class="absolute top-[80%] left-[60%] w-40 h-40 bg-lime-300/25 dark:bg-lime-500/10 rounded-full blur-3xl animate-float"
        style="animation-delay: 5s;">
      </div>
      <div
        class="absolute top-[40%] right-[50%] w-52 h-52 bg-fuchsia-300/20 dark:bg-fuchsia-500/8 rounded-full blur-3xl"
        style="animation-delay: 7s;">
      </div>
    </div>

    <!-- Header Educativo -->
    <header
      class="bg-gradient-to-r from-indigo-600 via-indigo-500 to-purple-500 dark:from-slate-800 dark:via-slate-800 dark:to-slate-800 border-b border-indigo-400/20 dark:border-slate-700 sticky top-0 z-50 shadow-lg shadow-indigo-500/20 dark:shadow-none">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
        <div class="flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 sm:gap-4">
            <!-- Logo con icono de libro -->
            <div class="relative flex-shrink-0">
              <div
                class="w-10 h-10 sm:w-14 sm:h-14 bg-white/90 backdrop-blur-sm rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg border border-white/30 p-1">
                <img :src="logoDre" alt="Logo DRE" class="w-full h-full object-contain" />
              </div>
              <!-- Estrella decorativa -->
              <div
                class="absolute -top-1 -right-1 w-4 h-4 sm:w-5 sm:h-5 bg-amber-400 rounded-full flex items-center justify-center shadow-md animate-pulse">
                <Star class="w-2 h-2 sm:w-3 sm:h-3 text-white fill-white" />
              </div>
            </div>
            <div class="min-w-0">
              <h1 class="text-lg sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2 truncate">
                MatSistem
                <span
                  class="text-[10px] sm:text-xs bg-purple-400 text-purple-900 px-2 py-0.5 rounded-full font-semibold">DRE</span>
              </h1>
              <p
                class="text-indigo-100 dark:text-slate-400 text-[10px] sm:text-sm font-medium flex items-center gap-1 truncate">
                <GraduationCap class="w-3 h-3 sm:w-4 sm:h-4" />
                <span class="truncate">Matemática práctica</span>
              </p>
            </div>
          </div>

          <!-- Mascota LECTOSISTEM -->
          <div class="hidden md:flex items-center">
            <div class="relative group">
              <img :src="mascotaLectosistem" alt="Mascota LECTOSISTEM"
                class="h-16 w-auto object-contain drop-shadow-lg transition-all duration-500 group-hover:scale-110 group-hover:drop-shadow-2xl animate-mascota-float" />
              <!-- Burbuja de diálogo -->
              <div
                class="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:translate-y-0 translate-y-2">
                <div
                  class="bg-white dark:bg-slate-700 rounded-full px-2 py-1 shadow-lg border-2 border-purple-300 dark:border-purple-500">
                  <span class="text-[10px] font-bold text-purple-600 dark:text-purple-400 whitespace-nowrap">¡Hola!
                    👋</span>
                </div>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2 sm:gap-3">
            <button v-if="resultado && !loading && activeTab === 'generador'" @click="showResults = !showResults"
              class="px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg sm:rounded-xl font-medium text-[10px] sm:text-sm flex items-center gap-1.5 sm:gap-2 transition-all duration-300 bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30">
              <Eye v-if="showResults" class="w-3 h-3 sm:w-4 sm:h-4" />
              <EyeOff v-else class="w-3 h-3 sm:w-4 sm:h-4" />
              <span class="hidden sm:inline">{{ showResults ? 'Ocultar' : 'Ver Resultado' }}</span>
              <span class="sm:hidden">{{ showResults ? 'Cerrar' : 'Ver' }}</span>
            </button>

            <button @click="toggleTheme"
              class="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300">
              <Sun v-if="isDark" class="w-5 h-5" />
              <Moon v-else class="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-4 sm:py-6 w-full">

      <!-- Tabs Navigation - Estilo Educativo -->
      <div class="mb-6 overflow-x-auto pb-2 scrollbar-hide">
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl p-1.5 sm:p-2 shadow-lg border border-gray-100 dark:border-slate-700 flex sm:inline-flex gap-1 sm:gap-2 min-w-max">
          <button @click="activeTab = 'generador'"
            class="flex items-center gap-2 px-3 py-2 sm:px-5 sm:py-3 rounded-lg sm:rounded-xl font-semibold text-xs sm:text-sm transition-all duration-300 whitespace-nowrap"
            :class="activeTab === 'generador'
              ? 'bg-gradient-to-r from-teal-500 to-teal-600 text-white shadow-lg shadow-teal-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-teal-50 dark:hover:bg-slate-700'">
            <Brain class="w-4 h-4 sm:w-5 sm:h-5" />
            <span>Generador de Examen</span>
            <Sparkles v-if="activeTab === 'generador'" class="w-3 h-3 sm:w-4 sm:h-4 text-amber-300" />
          </button>

          <button @click="activeTab = 'sistematizador'"
            class="flex items-center gap-2 px-3 py-2 sm:px-5 sm:py-3 rounded-lg sm:rounded-xl font-semibold text-xs sm:text-sm transition-all duration-300 whitespace-nowrap"
            :class="activeTab === 'sistematizador'
              ? 'bg-gradient-to-r from-amber-500 to-orange-500 text-white shadow-lg shadow-amber-500/30'
              : 'text-slate-600 dark:text-slate-400 hover:bg-amber-50 dark:hover:bg-slate-700'">
            <LayoutGrid class="w-4 h-4 sm:w-5 sm:h-5" />
            <span>Sistematizador</span>
            <Award v-if="activeTab === 'sistematizador'" class="w-3 h-3 sm:w-4 sm:h-4 text-yellow-300" />
          </button>
        </div>
      </div>

      <!-- Generator Tab Content -->
      <div v-show="activeTab === 'generador'">
        <!-- Configuration Row - Diseño Educativo -->
        <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">

          <!-- Grade Selection -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-teal-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-teal-200 transition-all duration-300">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
              <div
                class="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-lg flex items-center justify-center">
                <GraduationCap class="w-4 h-4 text-white" />
              </div>
              Grado Escolar
            </label>
            <ComboBox v-model="selectedGradoId" :options="gradoOptions" placeholder="Seleccionar grado..." />
          </div>

          <!-- Competencia Selection -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-violet-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-violet-200 transition-all duration-300">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
              <div
                class="w-8 h-8 bg-gradient-to-br from-violet-400 to-violet-600 rounded-lg flex items-center justify-center">
                <Target class="w-4 h-4 text-white" />
              </div>
              Competencia
            </label>
            <ComboBox v-model="selectedCompetenciaId" :options="competenciaOptions" placeholder="Seleccionar..." />
          </div>

          <!-- Quantity -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-amber-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-amber-200 transition-all duration-300">
            <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
              <div
                class="w-8 h-8 bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center">
                <Hash class="w-4 h-4 text-white" />
              </div>
              Cantidad Preguntas
            </label>
            <div class="flex items-center gap-3">
              <input type="range" v-model="cantidadPreguntas" min="1" max="10"
                class="flex-1 h-3 bg-gradient-to-r from-teal-100 to-amber-100 dark:bg-slate-700 rounded-full appearance-none cursor-pointer accent-teal-600" />
              <span
                class="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-lg font-bold text-white shadow-lg shadow-teal-500/30">
                {{ cantidadPreguntas }}
              </span>
            </div>
          </div>

          <!-- File Upload -->
          <div
            class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-sky-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-sky-200 transition-all duration-300">
            <Checkbox v-model="useTextoBase" class="items-center mb-3">
              <div class="flex items-center gap-2">
                <div
                  class="w-8 h-8 bg-gradient-to-br from-sky-400 to-sky-600 rounded-lg flex items-center justify-center">
                  <FileUp class="w-4 h-4 text-white" />
                </div>
                <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Usar Problema Base</span>
              </div>
            </Checkbox>

            <div v-if="useTextoBase" class="space-y-2">
              <div v-if="selectedFiles.length === 0 && !uploadingFile" class="relative">
                <input type="file" accept=".pdf,.docx,.doc" multiple @change="handleFileUpload"
                  class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                <div
                  class="flex items-center justify-center py-4 px-3 bg-gradient-to-br from-sky-50 to-teal-50 dark:bg-slate-900 border-2 border-dashed border-sky-300 dark:border-slate-600 rounded-xl hover:border-teal-400 hover:bg-teal-50 transition-all duration-300">
                  <div class="text-center">
                    <CloudUpload class="w-6 h-6 text-teal-500 mx-auto mb-1" />
                    <span class="text-teal-600 dark:text-slate-400 text-xs font-medium">📄 PDF o Word</span>
                  </div>
                </div>
              </div>

              <div v-if="uploadingFile"
                class="flex items-center justify-center gap-2 py-4 bg-teal-50 dark:bg-slate-900 rounded-xl">
                <Loader2 class="w-5 h-5 text-teal-600 animate-spin" />
                <span class="text-teal-600 dark:text-teal-400 text-sm font-medium">Procesando...</span>
              </div>

              <div v-if="selectedFiles.length > 0 && !uploadingFile && filesMetadata" class="space-y-2">
                <div v-for="(archivo, index) in filesMetadata.archivos" :key="index"
                  class="flex items-center gap-2 p-3 bg-gradient-to-r from-teal-50 to-emerald-50 dark:bg-emerald-900/20 border-2 border-teal-200 dark:border-emerald-800 rounded-xl text-xs">
                  <FileText class="w-5 h-5 text-teal-600 dark:text-emerald-400" />
                  <span class="flex-1 truncate text-slate-700 dark:text-slate-200 font-medium">{{ archivo.filename
                  }}</span>
                  <span class="text-teal-600 font-bold bg-teal-100 px-2 py-0.5 rounded-full">{{ archivo.palabras
                  }}p</span>
                </div>
                <button @click="clearFiles"
                  class="text-xs text-red-500 hover:text-red-600 flex items-center gap-1 font-medium">
                  <X class="w-3 h-3" /> Quitar archivo
                </button>
              </div>

              <div v-if="uploadError"
                class="p-3 bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl">
                <p class="text-red-600 dark:text-red-400 text-xs flex items-center gap-1 font-medium">
                  <AlertTriangle class="w-4 h-4" />
                  {{ uploadError }}
                </p>
              </div>
            </div>

            <p v-else class="text-slate-400 dark:text-slate-500 text-xs mt-2 flex items-center gap-1">
              <BookOpen class="w-3 h-3" /> Activa para usar problema personalizado
            </p>
          </div>
        </div>

        <!-- Main Content -->
        <div class="grid lg:grid-cols-2 gap-4 sm:gap-6">

          <!-- Left: Desempeños -->
          <div class="flex flex-col space-y-3 order-1 lg:order-1">

            <!-- Desempeños Card -->
            <div
              class="h-[500px] sm:h-[580px] lg:h-[650px] flex flex-col bg-white dark:bg-slate-800 rounded-2xl border-2 border-teal-100 dark:border-slate-700 overflow-hidden shadow-lg">

              <!-- Card Header - Educativo -->
              <div class="bg-gradient-to-r from-teal-500 via-teal-600 to-sky-500 px-5 py-4">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <div
                      class="w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center shadow-lg">
                      <Target class="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <h2 class="text-lg font-bold text-white">
                        Desempeños
                      </h2>
                      <span v-if="desempenos.length" class="text-xs text-teal-100 font-medium">
                        {{ desempenos.length }} disponibles para evaluar
                      </span>
                    </div>
                  </div>
                  <span v-if="selectedDesempenosCount > 0"
                    class="px-3 py-1.5 rounded-full bg-amber-400 text-amber-900 text-xs font-bold shadow-lg">
                    ✓ {{ selectedDesempenosCount }} seleccionados
                  </span>
                </div>
              </div>

              <!-- Loading -->
              <div v-if="loadingDesempenos" class="p-4 space-y-3">
                <div v-for="i in 3" :key="i" class="space-y-2">
                  <div class="h-4 w-24 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                  <div v-for="j in 2" :key="j"
                    class="flex items-start gap-2 p-2 bg-gray-50 dark:bg-slate-900 rounded-lg">
                    <div class="w-4 h-4 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                    <div class="flex-1 space-y-1.5">
                      <div class="h-2.5 w-full bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                      <div class="h-2.5 w-2/3 bg-gray-200 dark:bg-slate-700 rounded animate-pulse"></div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Desempeños List with Tabs -->
              <div v-else-if="desempenos.length > 0" class="flex-1 flex flex-col overflow-hidden">

                <!-- Tab Navigation - Capacidades de Matemática (1-4) -->
                <div class="flex overflow-x-auto scrollbar-hide bg-gray-50 dark:bg-slate-900 p-1.5 gap-1 min-w-full">
                  <button v-for="orden in [1, 2, 3, 4]" :key="orden" @click="activeCapacidadTab = orden"
                    class="flex-1 min-w-[80px] relative px-2 sm:px-4 py-2 sm:py-2.5 text-[10px] sm:text-xs font-bold transition-all duration-300 rounded-lg whitespace-nowrap"
                    :class="activeCapacidadTab === orden
                      ? `${getCapacidadColor(orden).bg} text-white shadow-lg`
                      : 'text-slate-500 dark:text-slate-400 hover:bg-white dark:hover:bg-slate-800'">
                    <div class="flex items-center justify-center gap-1.5 sm:gap-2">
                      <Calculator v-if="orden === 1" class="w-3 h-3 sm:w-4 h-4" />
                      <Sigma v-else-if="orden === 2" class="w-3 h-3 sm:w-4 h-4" />
                      <Shapes v-else-if="orden === 3" class="w-3 h-3 sm:w-4 h-4" />
                      <Target v-else class="w-3 h-3 sm:w-4 h-4" />
                      <span class="hidden sm:inline truncate max-w-[80px]">{{ getCapacidadLabel(orden) }}</span>
                      <span class="sm:hidden">Cap. {{ orden }}</span>
                    </div>
                  </button>
                </div>

                <!-- Tab Content -->
                <div class="flex-1 flex flex-col overflow-hidden p-3">
                  <!-- Actions Bar -->
                  <div class="flex items-center justify-between mb-3 px-1">
                    <span class="text-xs text-slate-500 dark:text-slate-400">
                      Selecciona los desempeños a evaluar
                    </span>
                    <div class="flex gap-2 text-[11px] font-medium">
                      <button @click="selectAllCapacidad(activeCapacidadTab)"
                        class="px-2.5 py-1 rounded-full transition-colors"
                        :class="getCapacidadColor(activeCapacidadTab).text + ' hover:bg-gray-100 dark:hover:bg-slate-800'">
                        Seleccionar todos
                      </button>
                      <button @click="deselectAllCapacidad(activeCapacidadTab)"
                        class="px-2.5 py-1 rounded-full text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                        Ninguno
                      </button>
                    </div>
                  </div>

                  <!-- Items Grid -->
                  <div class="flex-1 overflow-y-auto space-y-1.5 pr-1">
                    <template v-if="desempenosPorCapacidad[activeCapacidadTab]?.length">
                      <Checkbox v-for="des in desempenosPorCapacidad[activeCapacidadTab]" :key="des.id"
                        v-model="selectedDesempenoIds" :value="des.id"
                        class="group flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-all duration-150 border"
                        :class="selectedDesempenoIds.includes(des.id)
                          ? `bg-gray-50 dark:bg-slate-900/50 border-gray-200 dark:border-slate-600 ring-1 ${getCapacidadColor(activeCapacidadTab).ring}`
                          : 'border-gray-100 dark:border-slate-700 hover:border-gray-200 dark:hover:border-slate-600 hover:bg-gray-50 dark:hover:bg-slate-800/50'">
                        <div class="flex items-center gap-2 mb-1">
                          <span
                            class="text-[10px] px-2 py-0.5 rounded-md font-mono font-bold bg-gray-100 dark:bg-slate-800"
                            :class="getCapacidadColor(activeCapacidadTab).text">
                            {{ des.codigo }}
                          </span>
                        </div>
                        <p class="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
                          {{ des.descripcion }}
                        </p>
                      </Checkbox>
                    </template>

                    <!-- Empty Tab -->
                    <div v-else class="py-8 text-center">
                      <p class="text-slate-400 dark:text-slate-500 text-sm">
                        No hay desempeños para esta capacidad
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Empty -->
              <div v-else class="flex-1 flex flex-col items-center justify-center px-6 text-center">
                <div
                  class="w-14 h-14 bg-gradient-to-br from-indigo-100 to-purple-100 dark:from-indigo-900/30 dark:to-purple-900/30 rounded-2xl flex items-center justify-center mx-auto mb-4">
                  <BookOpen class="w-7 h-7 text-indigo-500 dark:text-indigo-400" />
                </div>
                <h3 class="text-slate-700 dark:text-slate-200 font-medium mb-1">Sin desempeños</h3>
                <p class="text-slate-500 dark:text-slate-400 text-sm">Selecciona un grado para ver los desempeños
                  disponibles</p>
              </div>
            </div>

            <!-- Generate Button - Educativo -->
            <button @click="generarPreguntas"
              :disabled="loading || !selectedGradoId || selectedDesempenoIds.length === 0"
              class="w-full px-4 py-4 sm:px-6 sm:py-5 bg-gradient-to-r from-indigo-500 via-indigo-600 to-purple-500 hover:from-indigo-600 hover:via-indigo-700 hover:to-purple-600 text-white font-bold rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 sm:gap-3 shadow-xl shadow-indigo-500/30 hover:shadow-2xl hover:shadow-indigo-500/40 hover:-translate-y-1 text-base sm:text-lg">
              <Loader2 v-if="loading" class="w-5 h-5 sm:w-6 sm:h-6 animate-spin" />
              <template v-else>
                <Rocket class="w-5 h-5 sm:w-6 sm:h-6" />
                <span>{{ loading ? 'Generando...' : 'Generar Examen con IA' }}</span>
              </template>
              <span v-if="loading" class="hidden sm:inline">Generando examen mágico...</span>
            </button>

            <!-- Error -->
            <div v-if="error"
              class="bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 p-4 rounded-2xl text-sm flex items-start gap-3">
              <div
                class="w-10 h-10 bg-red-100 dark:bg-red-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                <AlertTriangle class="w-5 h-5" />
              </div>
              <p class="font-medium">{{ error }}</p>
            </div>

            <!-- Prompt Button - Educativo -->
            <button v-if="promptTexto" @click="showPromptModal = true"
              class="w-full px-5 py-4 bg-white dark:bg-slate-800 rounded-2xl border-2 border-amber-200 dark:border-slate-700 flex items-center justify-between hover:bg-amber-50 dark:hover:bg-slate-700 hover:border-amber-300 transition-all duration-300 group">
              <span class="text-slate-700 dark:text-slate-300 text-sm font-bold flex items-center gap-3">
                <div
                  class="w-10 h-10 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/20 group-hover:scale-110 transition-transform">
                  <Copy class="w-5 h-5 text-white" />
                </div>
                Ver Prompt Generado
              </span>
              <span
                class="text-xs text-amber-600 dark:text-slate-500 font-medium bg-amber-100 dark:bg-slate-700 px-3 py-1 rounded-full">Clic
                para copiar</span>
            </button>
          </div>

          <!-- Right: Results -->
          <div class="flex flex-col order-2 lg:order-2">

            <!-- Empty State -->
            <div v-if="!resultado && !loading"
              class="h-[300px] sm:h-[580px] lg:h-[650px] bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 text-center flex flex-col items-center justify-center shadow-sm p-6">
              <Zap class="w-10 h-10 sm:w-12 sm:h-12 text-gray-300 dark:text-slate-600 mb-4" />
              <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-white mb-2">Listo para generar</h3>
              <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm max-w-xs">
                Selecciona los desempeños y genera tu examen con IA.
              </p>
            </div>

            <!-- Loading State -->
            <div v-if="loading"
              class="h-[400px] sm:h-[580px] lg:h-[650px] bg-white dark:bg-slate-800 rounded-xl border border-gray-200 dark:border-slate-700 text-center flex flex-col items-center justify-center shadow-sm p-6">
              <div
                class="w-10 h-10 sm:w-14 sm:h-14 border-4 border-gray-200 dark:border-slate-600 border-t-indigo-600 dark:border-t-indigo-400 rounded-full animate-spin mb-4">
              </div>
              <h3 class="text-base sm:text-lg font-semibold text-slate-800 dark:text-white mb-2">Generando Examen</h3>
              <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm">Esto puede tomar unos segundos...</p>
            </div>

            <!-- Results -->
            <div v-if="resultado && !loading && showResults"
              class="h-[500px] sm:h-[580px] lg:h-[650px] bg-white dark:bg-slate-800 rounded-2xl border-2 border-amber-200 dark:border-slate-700 shadow-xl flex flex-col overflow-hidden">

              <!-- Results Header - Celebratorio -->
              <div
                class="bg-gradient-to-r from-amber-400 via-amber-500 to-orange-500 px-4 sm:px-5 py-3 sm:py-4 flex-shrink-0">
                <div class="flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div class="flex items-center gap-3 w-full sm:w-auto">
                    <div
                      class="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 backdrop-blur-sm rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg flex-shrink-0">
                      <Award class="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                    </div>
                    <div class="min-w-0 flex-1">
                      <h2 class="text-base sm:text-lg font-bold text-white truncate">
                        {{ resultado.examen.titulo }}
                      </h2>
                      <span class="text-[10px] sm:text-xs text-amber-100 font-medium block">
                        {{ resultado.total_preguntas }} preguntas · {{ resultado.examen.grado }}
                      </span>
                    </div>
                  </div>
                  <button @click="descargarExamenWord" :disabled="descargandoWord"
                    class="w-full sm:w-auto px-4 py-2 bg-white text-amber-600 hover:bg-amber-50 text-xs sm:text-sm font-bold rounded-xl transition-all duration-300 flex items-center justify-center gap-2 shadow-lg hover:-translate-y-0.5">
                    <Loader2 v-if="descargandoWord" class="w-3 h-3 sm:w-4 sm:h-4 animate-spin" />
                    <Download v-else class="w-3 h-3 sm:w-4 sm:h-4" />
                    {{ descargandoWord ? 'Generando...' : 'Descargar Word' }}
                  </button>
                </div>
              </div>

              <!-- Scrollable Content -->
              <div class="flex-1 overflow-y-auto p-4 space-y-4">

                <!-- Instrucciones -->
                <div
                  class="bg-gradient-to-r from-teal-50 to-sky-50 dark:from-teal-900/40 dark:to-slate-900 rounded-xl p-4 border-2 border-teal-100 dark:border-teal-800">
                  <p class="text-slate-700 dark:text-slate-300 text-sm">
                    <strong class="text-teal-700 dark:text-teal-400 flex items-center gap-2 mb-2">
                      <ClipboardCheck class="w-4 h-4" />
                      Instrucciones:
                    </strong>
                    {{ resultado.examen.instrucciones }}
                  </p>
                </div>

                <!-- Lectura -->
                <div
                  class="bg-gradient-to-br from-amber-50 to-orange-50 dark:from-slate-900 dark:to-slate-950 rounded-xl p-5 border-2 border-amber-100 dark:border-slate-700">
                  <h4 class="text-sm font-bold text-slate-800 dark:text-white mb-3 flex items-center gap-2">
                    <div
                      class="w-8 h-8 bg-gradient-to-br from-amber-400 to-orange-500 rounded-lg flex items-center justify-center">
                      <BookOpen class="w-4 h-4 text-white" />
                    </div>
                    Lectura / Problema
                  </h4>
                  <p
                    class="text-slate-700 dark:text-slate-300 text-sm leading-7 whitespace-pre-line bg-white/50 dark:bg-black/20 p-4 rounded-lg">
                    {{ resultado.examen.lectura }}
                  </p>
                </div>

                <!-- Preguntas -->
                <div class="space-y-4">
                  <h4 class="text-sm font-bold text-slate-800 dark:text-white flex items-center gap-2">
                    <div
                      class="w-8 h-8 bg-gradient-to-br from-violet-400 to-purple-500 rounded-lg flex items-center justify-center">
                      <HelpCircle class="w-4 h-4 text-white" />
                    </div>
                    Preguntas del Examen
                  </h4>

                  <div v-for="pregunta in resultado.examen.preguntas" :key="pregunta.numero"
                    class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-slate-100 dark:border-slate-700 hover:border-teal-200 dark:hover:border-teal-700 transition-all duration-300">
                    <div class="flex items-start gap-4">
                      <span
                        class="w-10 h-10 bg-gradient-to-br from-teal-500 to-sky-500 rounded-xl flex items-center justify-center text-white font-bold text-sm flex-shrink-0 shadow-lg shadow-teal-500/20">
                        {{ pregunta.numero }}
                      </span>
                      <div class="flex-1">
                        <span
                          class="inline-flex items-center gap-1 px-3 py-1 text-[10px] font-bold uppercase rounded-full mb-2"
                          :class="getNivelBadgeClass(pregunta.nivel)">
                          <BookOpen v-if="pregunta.nivel === 'LITERAL'" class="w-3 h-3" />
                          <FileSearch v-else-if="pregunta.nivel === 'INFERENCIAL'" class="w-3 h-3" />
                          <Lightbulb v-else class="w-3 h-3" />
                          {{ pregunta.nivel }}
                        </span>
                        <p class="text-slate-800 dark:text-slate-200 font-semibold mb-4">{{ pregunta.enunciado }}</p>

                        <div class="space-y-2">
                          <div v-for="opcion in pregunta.opciones" :key="opcion.letra"
                            class="flex items-center gap-3 text-sm py-3 px-4 rounded-xl border-2 transition-all duration-200"
                            :class="opcion.es_correcta
                              ? 'bg-gradient-to-r from-teal-50 to-emerald-50 dark:from-emerald-900/40 dark:to-slate-900 border-teal-300 dark:border-emerald-800 text-teal-700 dark:text-emerald-400'
                              : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 text-slate-600 dark:text-slate-400 hover:border-gray-300'">
                            <span class="w-8 h-8 rounded-lg flex items-center justify-center font-bold text-sm"
                              :class="opcion.es_correcta ? 'bg-teal-500 text-white' : 'bg-gray-200 dark:bg-slate-700 text-slate-600 dark:text-slate-400'">{{
                                opcion.letra }}</span>
                            <span class="flex-1">{{ opcion.texto }}</span>
                            <Check v-if="opcion.es_correcta" class="w-5 h-5 text-teal-500" />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Answer Table -->
                <div class="bg-white dark:bg-slate-800 rounded-xl p-5 border-2 border-sky-100 dark:border-slate-700">
                  <h4 class="text-sm font-bold text-slate-800 dark:text-white mb-4 flex items-center gap-2">
                    <div
                      class="w-8 h-8 bg-gradient-to-br from-sky-400 to-blue-500 rounded-lg flex items-center justify-center">
                      <LayoutGrid class="w-4 h-4 text-white" />
                    </div>
                    Tabla de Respuestas
                  </h4>
                  <div class="overflow-x-auto rounded-xl border-2 border-gray-100 dark:border-slate-700">
                    <table class="w-full text-sm">
                      <thead>
                        <tr
                          class="bg-gradient-to-r from-slate-50 to-gray-50 dark:from-slate-900 dark:to-slate-950 border-b-2 border-gray-200 dark:border-slate-700">
                          <th class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">#</th>
                          <th class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">
                            Desempeño
                          </th>
                          <th class="text-left py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">Nivel
                          </th>
                          <th class="text-center py-3 px-4 text-slate-600 dark:text-slate-400 font-bold text-xs">Rpta.
                          </th>
                        </tr>
                      </thead>
                      <tbody class="divide-y divide-gray-100 dark:divide-slate-700">
                        <tr v-for="fila in resultado.examen.tabla_respuestas" :key="fila.pregunta"
                          class="hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors">
                          <td class="py-3 px-4 text-slate-800 dark:text-slate-200 font-bold">{{ fila.pregunta }}
                          </td>
                          <td class="py-3 px-4 text-slate-600 dark:text-slate-400 text-xs">{{ fila.desempeno }}</td>
                          <td class="py-3 px-4">
                            <span class="px-2.5 py-1 text-[10px] font-bold rounded-full inline-flex items-center gap-1"
                              :class="getNivelBadgeClass(fila.nivel)">
                              <BookOpen v-if="fila.nivel === 'LITERAL'" class="w-3 h-3" />
                              <FileSearch v-else-if="fila.nivel === 'INFERENCIAL'" class="w-3 h-3" />
                              <Lightbulb v-else class="w-3 h-3" />
                              {{ fila.nivel }}
                            </span>
                          </td>
                          <td class="py-3 px-4 text-center">
                            <span
                              class="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 text-white rounded-lg inline-flex items-center justify-center font-bold text-sm shadow-lg shadow-teal-500/20">
                              {{ fila.respuesta_correcta }}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                </div>

                <p
                  class="text-center text-xs text-slate-500 dark:text-slate-400 bg-gradient-to-r from-teal-50 to-amber-50 dark:from-slate-900 dark:to-slate-800 p-3 rounded-xl flex items-center justify-center gap-2">
                  <Sparkles class="w-4 h-4 text-amber-500" /> Examen generado con IA - <strong>Revisar antes de usar con
                    los
                    estudiantes</strong>
                  <GraduationCap class="w-4 h-4 text-teal-500" />
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sistematizador Tab Content -->
      <div v-show="activeTab === 'sistematizador'">
        <Sistematizador />
      </div>
    </main>

    <!-- Footer -->
    <Footer />

    <!-- Prompt Modal -->
    <PromptModal :isOpen="showPromptModal" :promptText="promptTexto" @close="showPromptModal = false" />
  </div>
</template>

<style scoped>
/* Scrollbar sutil */
::-webkit-scrollbar {
  width: 4px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 20px;
}

.dark ::-webkit-scrollbar-thumb {
  background-color: #475569;
}
</style>
