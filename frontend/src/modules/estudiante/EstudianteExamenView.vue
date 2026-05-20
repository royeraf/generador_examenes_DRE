<script setup lang="ts">
import { ref, shallowRef, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../../shared/services/api'
import {
  ChevronLeft, ChevronRight, Clock, AlertCircle, CheckCircle2,
  Loader2, BookOpen, ClipboardList,
  CheckCircle, XCircle, Lightbulb, Zap, Target, Trophy, ArrowLeft,
  X, ChevronDown
} from 'lucide-vue-next'
import ThinkingLoader from '../../shared/components/ThinkingLoader.vue'
import { useTheme } from '../../shared/composables/useTheme'

const route = useRoute()
const router = useRouter()
const { isDark } = useTheme()
const asignacionId = Number(route.params.id)

interface Opcion {
  letra: string
  valor?: string
  texto: string
}

interface Pregunta {
  numero: number
  enunciado: string
  opciones: Opcion[]
  nivel?: string
  desempeno_codigo?: string
}

interface TextoLectura {
  titulo: string
  texto: string
}

interface ExamenData {
  titulo: string
  instrucciones: string
  lectura?: string
  lecturas?: TextoLectura[]
  preguntas: Pregunta[]
  duracion_minutos: number | null
  intento_id: number
  tipo_examen: string
}

interface PreguntaRevision {
  numero: number
  enunciado: string
  opciones: { letra: string; texto: string }[]
  respuesta_correcta: string
  respuesta_dada: string
  es_correcta: boolean
  retroalimentacion_ia: string
  justificacion: string
  nivel: string
}

interface Revision {
  titulo: string
  puntaje_total: number
  preguntas_correctas: number
  preguntas_total: number
  nivel_logro: string
  preguntas: PreguntaRevision[]
}

const examen = ref<ExamenData | null>(null)
const loading = ref(true)
const error = ref('')
const enviando = ref(false)
const resultado = ref<any>(null)

// Revisión
const revision = ref<Revision | null>(null)
const loadingRevision = ref(false)
const intentoIdFinalizado = ref<number | null>(null)

const mostrarModalRevision = ref(false)
const preguntaRevisionActual = ref(0)

interface ConfettiParticle {
  id: number
  x: number
  color: string
  delay: number
  duration: number
  drift: number
}
const confettis = ref<ConfettiParticle[]>([])

function triggerConfetti() {
  if (!resultado.value || !['satisfactorio', 'destacado'].includes(resultado.value.nivel_logro)) {
    return
  }
  const colors = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#f43f5e', '#0ea5e9']
  const newConfettis: ConfettiParticle[] = []
  for (let i = 0; i < 120; i++) {
    newConfettis.push({
      id: i,
      x: Math.random() * 100,
      color: colors[Math.floor(Math.random() * colors.length)]!,
      delay: Math.random() * 2,
      duration: 2.5 + Math.random() * 2,
      drift: (Math.random() * 200 - 100)
    })
  }
  confettis.value = newConfettis
}

const lecturaTabActiva = shallowRef(0)
const lecturaAcordeonAbierto = ref<number | null>(0)

const toggleAcordeon = (idx: number) => {
  if (lecturaAcordeonAbierto.value === idx) {
    lecturaAcordeonAbierto.value = null
  } else {
    lecturaAcordeonAbierto.value = idx
    lecturaTabActiva.value = idx
  }
}

const lecturas = computed<TextoLectura[]>(() => {
  if (!examen.value) return []
  if (examen.value.lecturas?.length) return examen.value.lecturas
  return examen.value.lectura ? [{ titulo: '', texto: examen.value.lectura }] : []
})

const preguntaActual = ref(0)
const respuestas = ref<Record<number, string>>({})

const preguntaVisible = computed(() => examen.value?.preguntas[preguntaActual.value])
const preguntaRespondidaMap = computed(() => {
  const answered = new Set<number>()
  examen.value?.preguntas.forEach((pregunta) => {
    if (respuestas.value[pregunta.numero] !== undefined) {
      answered.add(pregunta.numero)
    }
  })
  return answered
})

// Timer
const tiempoRestante = ref(0)
let timerInterval: ReturnType<typeof setInterval> | null = null

const tiempoFormato = computed(() => {
  const mins = Math.floor(tiempoRestante.value / 60)
  const secs = tiempoRestante.value % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
})

const timerColor = computed(() => {
  if (tiempoRestante.value < 60) return 'text-red-500'
  if (tiempoRestante.value < 300) return 'text-orange-500'
  return 'text-slate-700 dark:text-slate-200'
})

const progreso = computed(() => {
  if (!examen.value) return 0
  return Math.round((Object.keys(respuestas.value).length / examen.value.preguntas.length) * 100)
})

const sinResponder = computed(() => {
  if (!examen.value) return []
  return examen.value.preguntas
    .filter(p => respuestas.value[p.numero] === undefined)
    .map(p => p.numero)
})

const todasRespondidas = computed(() => sinResponder.value.length === 0)

const intentoEnvioIncompleto = ref(false)

onMounted(async () => {
  try {
    const modo = route.query.modo
    if (modo === 'resultados') {
      const res = await apiClient.get(`/estudiante/examenes/${asignacionId}/resultado`)
      resultado.value = res.data
      triggerConfetti()
      return
    }

    const res = await apiClient.post(`/estudiante/examenes/${asignacionId}/iniciar`)
    const data = res.data
    examen.value = data

    if (data.duracion_minutos) {
      tiempoRestante.value = data.duracion_minutos * 60
      timerInterval = setInterval(() => {
        if (tiempoRestante.value > 0) {
          tiempoRestante.value--
        } else {
          finalizarPorTiempo()
        }
      }, 1000)
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al iniciar el examen'
  } finally {
    loading.value = false
  }
})

// Aviso del navegador al intentar cerrar/recargar mientras el examen está activo
function handleBeforeUnload(e: BeforeUnloadEvent) {
  if (!examen.value || resultado.value) return
  e.preventDefault()
  e.returnValue = ''
}

onMounted(() => {
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
  window.removeEventListener('beforeunload', handleBeforeUnload)
})

function seleccionar(preguntaNum: number, letra: string) {
  respuestas.value[preguntaNum] = letra
  if (intentoEnvioIncompleto.value && todasRespondidas.value) {
    intentoEnvioIncompleto.value = false
  }
}

function anterior() {
  if (preguntaActual.value > 0) preguntaActual.value--
}

function siguiente() {
  if (examen.value && preguntaActual.value < examen.value.preguntas.length - 1) {
    preguntaActual.value++
  }
}

async function _enviar() {
  if (timerInterval) clearInterval(timerInterval)
  if (!examen.value) return
  enviando.value = true
  try {
    const respuestasArray = Object.entries(respuestas.value).map(([num, letra]) => ({
      pregunta_numero: Number(num),
      respuesta: letra,
    }))
    const res = await apiClient.post(`/estudiante/intentos/${examen.value.intento_id}/finalizar`, {
      respuestas: respuestasArray,
    })
    resultado.value = res.data
    intentoIdFinalizado.value = examen.value.intento_id
    triggerConfetti()
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al enviar respuestas'
  } finally {
    enviando.value = false
  }
}

function finalizar() {
  if (!todasRespondidas.value) {
    intentoEnvioIncompleto.value = true
    const primera = sinResponder.value[0]
    const idx = examen.value?.preguntas.findIndex(p => p.numero === primera) ?? 0
    preguntaActual.value = idx
    return
  }
  _enviar()
}

function finalizarPorTiempo() {
  _enviar()
}

async function cargarRevision() {
  const intenId = intentoIdFinalizado.value
  if (!intenId && !route.query.intento_id) {
    loadingRevision.value = true
    try {
      const res = await apiClient.get(`/estudiante/examenes/${asignacionId}/revision`)
      revision.value = res.data
      preguntaRevisionActual.value = 0
      mostrarModalRevision.value = true
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Error al cargar revisión'
    } finally {
      loadingRevision.value = false
    }
    return
  }

  const id = intenId ?? Number(route.query.intento_id)
  loadingRevision.value = true
  try {
    const res = await apiClient.get(`/estudiante/intentos/${id}/revision`)
    revision.value = res.data
    preguntaRevisionActual.value = 0
    mostrarModalRevision.value = true
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar revisión'
  } finally {
    loadingRevision.value = false
  }
}

function anteriorRevision() {
  if (preguntaRevisionActual.value > 0) {
    preguntaRevisionActual.value--
  }
}

function siguienteRevision() {
  if (revision.value && preguntaRevisionActual.value < revision.value.preguntas.length - 1) {
    preguntaRevisionActual.value++
  } else {
    mostrarModalRevision.value = false
  }
}

const activeRevisionPregunta = computed(() => {
  return revision.value?.preguntas[preguntaRevisionActual.value] || null
})

const nivelColors: Record<string, string> = {
  pre_inicio: 'text-red-500 bg-red-50 dark:bg-red-500/10 border-red-100 dark:border-red-500/20',
  inicio: 'text-orange-500 bg-orange-50 dark:bg-orange-500/10 border-orange-100 dark:border-orange-500/20',
  proceso: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-500/10 border-yellow-100 dark:border-yellow-500/20',
  satisfactorio: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10 border-emerald-100 dark:border-emerald-500/20',
  destacado: 'text-teal-500 bg-teal-50 dark:bg-teal-500/10 border-teal-100 dark:border-teal-500/20',
}

const nivelLabels: Record<string, string> = {
  pre_inicio: 'Pre Inicio', inicio: 'Inicio', proceso: 'En Proceso',
  satisfactorio: 'Satisfactorio', destacado: 'Destacado',
}

const nivelMensaje: Record<string, string> = {
  pre_inicio: 'Sigue practicando, puedes mejorar.',
  inicio: 'Vas por buen camino, sigue adelante.',
  proceso: 'Buen esfuerzo, estás progresando.',
  satisfactorio: 'Muy bien, alcanzaste el nivel esperado.',
  destacado: '¡Excelente! Superaste las expectativas.',
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 transition-colors duration-500 font-sans selection:bg-teal-500/20">

    <!-- Confetti -->
    <div v-if="resultado && confettis.length > 0" class="fixed inset-0 pointer-events-none overflow-hidden z-[100]">
      <div v-for="c in confettis" :key="c.id"
           class="absolute top-[-5%] w-2.5 h-3.5 animate-confetti-fall opacity-0"
           :style="{
             left: c.x + '%',
             backgroundColor: c.color,
             animationDelay: c.delay + 's',
             animationDuration: c.duration + 's',
             '--drift': c.drift + 'px',
             borderRadius: c.id % 3 === 0 ? '50%' : '2px'
           }">
      </div>
    </div>

    <!-- Cargando -->
    <div v-if="loading" class="flex flex-col items-center justify-center min-h-screen gap-4">
      <Loader2 class="w-10 h-10 animate-spin text-teal-500" />
      <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Preparando examen...</p>
    </div>

    <!-- Error -->
    <div v-else-if="error && !examen && !resultado" class="flex flex-col items-center justify-center min-h-screen gap-6 px-6 text-center">
      <div class="w-20 h-20 rounded-2xl bg-red-50 dark:bg-red-500/10 flex items-center justify-center">
        <AlertCircle class="w-10 h-10 text-red-500" />
      </div>
      <div>
        <h1 class="text-xl font-bold text-slate-900 dark:text-white mb-2">¡Ups! Algo salió mal</h1>
        <p class="text-slate-500 dark:text-slate-400 max-w-xs">{{ error }}</p>
      </div>
      <button @click="router.push('/estudiante/examenes')"
        class="px-8 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-bold transition-transform active:scale-95 shadow-lg">
        Volver a la lista
      </button>
    </div>

    <!-- Resultado final -->
    <div v-else-if="resultado"
      class="min-h-screen flex flex-col items-center px-6 py-12 bg-slate-50 dark:bg-slate-950 relative overflow-y-auto">
      
      <!-- Background orbs -->
      <div class="fixed inset-0 pointer-events-none overflow-hidden">
        <div class="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-teal-500/5 dark:bg-teal-500/10 rounded-full blur-[120px]"></div>
        <div class="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-indigo-500/5 dark:bg-indigo-500/10 rounded-full blur-[100px]"></div>
      </div>

      <div class="w-full max-w-lg z-10">
        <!-- Success Card -->
        <div class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 shadow-2xl p-8 sm:p-10 mb-8 animate-slide-up-1 relative overflow-hidden">
          
          <div class="flex justify-center mb-8 animate-success-pop">
            <div class="w-24 h-24 rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-xl shadow-teal-500/20 rotate-12">
              <Trophy class="w-12 h-12 text-white -rotate-12" />
            </div>
          </div>

          <div class="text-center mb-10">
            <h1 class="text-3xl font-black text-slate-900 dark:text-white mb-2">¡Examen Terminado!</h1>
            <p class="text-slate-500 dark:text-slate-400 font-medium">
              {{ nivelMensaje[resultado.nivel_logro] ?? 'Has completado satisfactoriamente tu evaluación.' }}
            </p>
          </div>

          <div class="relative mb-10">
            <div class="text-center">
              <p class="text-7xl font-black tabular-nums leading-none mb-4" :class="resultado.puntaje_total >= 70 ? 'text-teal-500' : 'text-orange-500'">
                {{ resultado.puntaje_total?.toFixed(0) }}<span class="text-3xl font-bold opacity-50">%</span>
              </p>
              <div class="flex justify-center mb-6">
                <span :class="nivelColors[resultado.nivel_logro] || 'bg-slate-100 text-slate-600'"
                  class="px-5 py-1.5 rounded-full text-xs font-black uppercase tracking-[0.2em] border border-transparent">
                  {{ nivelLabels[resultado.nivel_logro] ?? resultado.nivel_logro ?? '—' }}
                </span>
              </div>
              <div class="h-3 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden mb-2">
                <div class="h-full rounded-full bg-gradient-to-r from-teal-500 to-indigo-600 transition-all duration-1000 ease-out"
                  :style="{ width: (resultado.puntaje_total ?? 0) + '%' }"></div>
              </div>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Progreso de logro obtenido</p>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-5 text-center group transition-colors hover:bg-emerald-50 dark:hover:bg-emerald-500/10">
              <div class="flex justify-center mb-2 text-emerald-500">
                <CheckCircle2 class="w-5 h-5" />
              </div>
              <p class="text-2xl font-black text-slate-900 dark:text-white">
                {{ resultado.preguntas_correctas }}
              </p>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Correctas</p>
            </div>
            <div class="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-5 text-center group transition-colors hover:bg-red-50 dark:hover:bg-red-500/10">
              <div class="flex justify-center mb-2 text-red-500">
                <XCircle class="w-5 h-5" />
              </div>
              <p class="text-2xl font-black text-slate-900 dark:text-white">
                {{ (resultado.preguntas_total ?? 0) - (resultado.preguntas_correctas ?? 0) }}
              </p>
              <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Incorrectas</p>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="flex flex-col gap-4 animate-slide-up-2">
          <button @click="cargarRevision" :disabled="loadingRevision"
            class="group w-full h-16 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold rounded-2xl shadow-xl transition-all active:scale-95 flex items-center justify-center gap-3">
            <ThinkingLoader v-if="loadingRevision" text="Analizando respuestas..." :variant="isDark ? 'purple' : 'teal'" />
            <template v-else>
              <ClipboardList class="w-5 h-5 group-hover:rotate-6 transition-transform" />
              <span>Ver Revisión con IA</span>
            </template>
          </button>

          <button @click="router.push('/estudiante/examenes')"
            class="w-full h-14 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 font-bold rounded-2xl border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-all active:scale-95 flex items-center justify-center gap-2">
            <ArrowLeft class="w-4 h-4" />
            <span>Volver a la lista</span>
          </button>
        </div>
      </div>

      <!-- Full-screen Practice-style Feedback Modal -->
      <Teleport to="body">
        <Transition
          enter-active-class="transition duration-300 ease-out"
          enter-from-class="opacity-0 translate-y-8"
          enter-to-class="opacity-100 translate-y-0"
          leave-active-class="transition duration-200 ease-in"
          leave-from-class="opacity-100 translate-y-0"
          leave-to-class="opacity-0 translate-y-8"
        >
          <div v-if="mostrarModalRevision && revision" class="fixed inset-0 z-50 bg-slate-50 dark:bg-slate-950 flex flex-col font-sans overflow-hidden">
            
            <!-- Premium Background Blurs -->
            <div class="absolute inset-0 pointer-events-none overflow-hidden -z-10">
              <div class="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-teal-500/5 dark:bg-teal-500/10 rounded-full blur-[120px]"></div>
              <div class="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-indigo-500/5 dark:bg-indigo-500/10 rounded-full blur-[100px]"></div>
            </div>

            <!-- Header -->
            <header class="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800/80 h-16 flex items-center shrink-0 px-6 justify-between relative z-10 shadow-sm">
              <div class="flex items-center gap-4 min-w-0">
                <button @click="mostrarModalRevision = false" 
                  class="w-10 h-10 rounded-xl flex items-center justify-center text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all border border-transparent hover:border-slate-300 dark:hover:border-slate-700 cursor-pointer">
                  <X class="w-5 h-5" />
                </button>
                <div class="min-w-0">
                  <h1 class="font-bold text-slate-900 dark:text-white text-base truncate leading-none mb-1">Revisión de Evaluación</h1>
                  <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest leading-none">
                    Práctica y retroalimentación inteligente
                  </p>
                </div>
              </div>

              <!-- Stats/Score Badge in Header -->
              <div class="flex items-center gap-3">
                <div class="hidden sm:flex flex-col items-end">
                  <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Logro obtenido</span>
                  <span class="text-sm font-black text-teal-600 dark:text-teal-400 leading-none mt-1">
                    {{ resultado?.puntaje_total?.toFixed(0) }}% ({{ resultado?.preguntas_correctas }}/{{ resultado?.preguntas_total }})
                  </span>
                </div>
                <div class="w-px h-8 bg-slate-200 dark:bg-slate-800 hidden sm:block"></div>
                <span :class="nivelColors[resultado?.nivel_logro || ''] || 'bg-slate-100 text-slate-600'"
                  class="px-3.5 py-1.5 rounded-full text-[10px] font-black uppercase tracking-wider border border-transparent">
                  {{ nivelLabels[resultado?.nivel_logro || ''] || '—' }}
                </span>
              </div>
            </header>

            <!-- Progress Bar under header -->
            <div class="h-1.5 bg-slate-100 dark:bg-slate-900 w-full relative">
              <div class="h-full bg-gradient-to-r from-teal-500 to-indigo-600 transition-all duration-300 ease-out"
                :style="{ width: ((preguntaRevisionActual + 1) / revision.preguntas.length) * 100 + '%' }"></div>
            </div>

            <!-- Main Scrollable Practice Area -->
            <div class="flex-1 overflow-y-auto px-4 py-8 md:py-12 flex flex-col items-center justify-start">
              <div class="w-full max-w-3xl flex flex-col gap-6 relative">
                
                <!-- Active Card with Vue transition -->
                <Transition name="card-fade" mode="out-in">
                  <div v-if="activeRevisionPregunta" :key="preguntaRevisionActual" class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 md:p-8 shadow-2xl relative flex flex-col w-full">
                    
                    <!-- Card Header: Number, Level, Correctness -->
                    <div class="flex flex-wrap items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-100 dark:border-slate-800/60">
                      <div class="flex items-center gap-3">
                        <span class="text-xs font-black uppercase tracking-widest text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-950/40 px-3 py-1.5 rounded-xl border border-indigo-100/50 dark:border-indigo-900/30">
                          Pregunta {{ activeRevisionPregunta.numero }} de {{ revision.preguntas.length }}
                        </span>
                        <span v-if="activeRevisionPregunta.nivel" class="text-[10px] font-black text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 px-2.5 py-1 rounded-full uppercase tracking-wider">
                          {{ activeRevisionPregunta.nivel }}
                        </span>
                      </div>

                      <div class="flex items-center gap-2">
                        <span v-if="activeRevisionPregunta.es_correcta" 
                          class="bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-100 dark:border-emerald-500/20 px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-wider flex items-center gap-1.5">
                          <CheckCircle class="w-3.5 h-3.5" /> Correcta
                        </span>
                        <span v-else 
                          class="bg-rose-50 dark:bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-100 dark:border-rose-500/20 px-3 py-1.5 rounded-full text-[10px] font-black uppercase tracking-wider flex items-center gap-1.5">
                          <XCircle class="w-3.5 h-3.5" /> Incorrecta
                        </span>
                      </div>
                    </div>

                    <!-- Question Text -->
                    <div class="mb-8">
                      <h3 class="text-lg md:text-xl font-bold text-slate-900 dark:text-white leading-relaxed">
                        {{ activeRevisionPregunta.enunciado }}
                      </h3>
                    </div>

                    <!-- Options Grid -->
                    <div class="space-y-3 mb-8">
                      <div v-for="opcion in activeRevisionPregunta.opciones" :key="opcion.letra"
                        class="flex items-center gap-4 px-5 py-4 rounded-xl border text-sm transition-all"
                        :class="
                          opcion.letra === activeRevisionPregunta.respuesta_correcta
                            ? 'bg-emerald-50 dark:bg-emerald-500/10 border-emerald-500 text-emerald-950 dark:text-emerald-300 font-bold shadow-sm shadow-emerald-500/5'
                            : opcion.letra === activeRevisionPregunta.respuesta_dada && !activeRevisionPregunta.es_correcta
                              ? 'bg-rose-50 dark:bg-rose-500/10 border-rose-500 text-rose-950 dark:text-rose-300 shadow-sm shadow-rose-500/5'
                              : 'bg-slate-50 dark:bg-slate-800/40 border-transparent text-slate-600 dark:text-slate-400 hover:bg-slate-100/50 dark:hover:bg-slate-800/70'
                        ">
                        <span class="w-8 h-8 rounded-xl flex items-center justify-center text-xs font-black shrink-0 shadow-sm transition-colors duration-300"
                          :class="
                            opcion.letra === activeRevisionPregunta.respuesta_correcta
                              ? 'bg-emerald-500 text-white'
                              : opcion.letra === activeRevisionPregunta.respuesta_dada && !activeRevisionPregunta.es_correcta
                                ? 'bg-rose-500 text-white'
                                : 'bg-white dark:bg-slate-700 text-slate-400 border border-slate-200 dark:border-slate-600'
                          ">{{ opcion.letra }}</span>
                        
                        <div class="flex-1 leading-snug">
                          <span class="block">{{ opcion.texto }}</span>
                          <span v-if="opcion.letra === activeRevisionPregunta.respuesta_correcta" class="inline-block text-[9px] font-black uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mt-1">
                            Respuesta Correcta
                          </span>
                          <span v-else-if="opcion.letra === activeRevisionPregunta.respuesta_dada && !activeRevisionPregunta.es_correcta" class="inline-block text-[9px] font-black uppercase tracking-wider text-rose-600 dark:text-rose-400 mt-1">
                            Tu Respuesta
                          </span>
                        </div>
                      </div>
                    </div>

                    <!-- AI Insight Container -->
                    <div class="bg-gradient-to-br from-indigo-50/60 to-purple-50/40 dark:from-indigo-950/30 dark:to-purple-950/20 rounded-xl p-6 border border-indigo-100/50 dark:border-indigo-500/10 relative overflow-hidden group">
                      <div class="absolute top-0 right-0 p-4 opacity-5 group-hover:scale-110 transition-transform">
                        <Lightbulb class="w-12 h-12 text-indigo-500" />
                      </div>
                      <div class="flex items-center justify-between mb-4">
                        <div class="flex items-center gap-2">
                          <div class="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                            <Zap class="w-4 h-4 text-white" />
                          </div>
                          <span class="text-[10px] font-black uppercase tracking-widest text-indigo-600 dark:text-indigo-400">Insight de Aprendizaje con IA</span>
                        </div>
                        <span class="text-[9px] font-bold text-slate-400 dark:text-slate-500 bg-slate-100 dark:bg-slate-800/80 px-2 py-0.5 rounded-md">Gemini AI</span>
                      </div>
                      <p class="text-sm text-indigo-900/90 dark:text-indigo-200/90 leading-relaxed font-medium">
                        {{ activeRevisionPregunta.retroalimentacion_ia }}
                      </p>
                    </div>

                  </div>
                </Transition>

              </div>
            </div>

            <!-- Footer Navigation Bar -->
            <footer class="bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800 py-6 px-6 shrink-0 relative z-10 shadow-lg">
              <div class="max-w-3xl mx-auto flex items-center justify-between gap-4">
                
                <!-- Previous Button -->
                <button @click="anteriorRevision" :disabled="preguntaRevisionActual === 0"
                  class="flex-1 sm:flex-initial h-12 px-6 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700 disabled:opacity-40 disabled:hover:bg-slate-100 dark:disabled:hover:bg-slate-800 font-bold text-sm rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer select-none">
                  <ChevronLeft class="w-4 h-4" />
                  <span>Anterior</span>
                </button>

                <!-- Progress Dots (Desktop only) -->
                <div class="hidden sm:flex items-center gap-1.5">
                  <button v-for="(p, idx) in revision.preguntas" :key="idx"
                    @click="preguntaRevisionActual = idx"
                    class="w-3 h-3 rounded-full transition-all duration-300 cursor-pointer"
                    :class="
                      idx === preguntaRevisionActual
                        ? 'bg-gradient-to-r from-teal-500 to-indigo-600 scale-125 w-6'
                        : p.es_correcta
                          ? 'bg-emerald-500/40 hover:bg-emerald-500/60'
                          : 'bg-rose-500/40 hover:bg-rose-500/60'
                    "
                    :title="'Ir a Pregunta ' + p.numero"
                  />
                </div>

                <!-- Next / Finish Button -->
                <button @click="siguienteRevision"
                  class="flex-1 sm:flex-initial h-12 px-6 bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:scale-[1.02] active:scale-[0.98] font-bold text-sm rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md shadow-slate-900/10 dark:shadow-white/5 select-none">
                  <span>{{ preguntaRevisionActual === revision.preguntas.length - 1 ? 'Finalizar Revisión' : 'Siguiente' }}</span>
                  <ChevronRight class="w-4 h-4" />
                </button>

              </div>
            </footer>

          </div>
        </Transition>
      </Teleport>
    </div>

    <!-- Examen en curso -->
    <div v-else-if="examen" class="w-full flex flex-col h-screen">
      <!-- Exam Header -->
      <header class="bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-300 dark:border-slate-800 h-16 flex items-center shrink-0 z-40 px-6">
        <div class="max-w-7xl mx-auto w-full flex items-center justify-between">
          <div class="flex items-center gap-4 min-w-0">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-teal-500/20 shrink-0">
              <BookOpen v-if="examen.tipo_examen !== 'matematica'" class="w-5 h-5 text-white" />
              <Target v-else class="w-5 h-5 text-white" />
            </div>
            <div class="min-w-0">
              <h1 class="font-bold text-slate-900 dark:text-white text-sm truncate leading-none mb-1">{{ examen.titulo }}</h1>
              <div class="flex items-center gap-2">
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{{ progreso }}% Completado</span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <div v-if="examen.duracion_minutos" :class="timerColor" class="flex items-center gap-2 px-4 py-2 bg-slate-50 dark:bg-slate-800 rounded-full font-mono font-black text-sm transition-colors border border-slate-300 dark:border-slate-700">
              <Clock class="w-4 h-4" />
              {{ tiempoFormato }}
            </div>
          </div>
        </div>
      </header>

      <!-- Progress Line -->
      <div class="h-1 bg-slate-100 dark:bg-slate-800 shrink-0">
        <div class="h-full bg-gradient-to-r from-teal-500 to-indigo-600 transition-all duration-700 ease-out"
          :style="{ width: progreso + '%' }"></div>
      </div>

      <!-- Main Content -->
      <main class="flex-1 overflow-hidden flex flex-col lg:flex-row relative">
        
        <!-- Background Orbs (taking) -->
        <div class="absolute inset-0 pointer-events-none overflow-hidden opacity-50">
          <div class="absolute top-[20%] left-[-5%] w-[400px] h-[400px] bg-teal-500/5 dark:bg-teal-500/10 rounded-full blur-[100px]"></div>
          <div class="absolute bottom-[20%] right-[-5%] w-[400px] h-[400px] bg-indigo-500/5 dark:bg-indigo-500/10 rounded-full blur-[100px]"></div>
        </div>

        <!-- Left: Reading Context (Responsive Accordion) -->
        <aside 
          v-if="lecturas.length" 
          :class="[
            'w-full lg:w-1/2 flex flex-col bg-white dark:bg-slate-900/50 z-10 relative transition-all duration-300 ease-in-out',
            lecturaAcordeonAbierto !== null 
              ? 'h-[40vh] sm:h-[45vh] lg:h-full border-b lg:border-b-0 lg:border-r border-slate-300 dark:border-slate-800' 
              : 'h-auto shrink-0 border-b border-slate-300 dark:border-slate-800'
          ]"
        >
          <!-- Single Lecture Accordion -->
          <template v-if="lecturas.length === 1">
            <!-- Accordion Header Button -->
            <button 
              @click="toggleAcordeon(0)"
              class="w-full px-6 py-5 sm:px-8 sm:py-6 flex items-center justify-between bg-slate-50/50 dark:bg-slate-800/10 hover:bg-slate-50 dark:hover:bg-slate-800/20 border-b border-slate-200 dark:border-slate-800/50 transition-all select-none text-left focus:outline-none"
            >
              <div class="flex items-center gap-3 min-w-0">
                <div :class="[
                  'w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors',
                  lecturaAcordeonAbierto === 0 ? 'bg-teal-500/10' : 'bg-slate-100 dark:bg-slate-800'
                ]">
                  <BookOpen :class="['w-4 h-4 transition-colors', lecturaAcordeonAbierto === 0 ? 'text-teal-500' : 'text-slate-400']" />
                </div>
                <div class="min-w-0">
                  <span class="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-0.5">Contexto de Lectura</span>
                  <h3 :class="['font-bold text-sm truncate leading-snug transition-colors', lecturaAcordeonAbierto === 0 ? 'text-teal-600 dark:text-teal-400' : 'text-slate-700 dark:text-slate-200']">
                  {{ lecturas[0]?.titulo || 'Texto Principal' }}
                  </h3>
                </div>
              </div>
              <ChevronDown 
                :class="[
                  'w-5 h-5 text-slate-400 transition-transform duration-300 shrink-0',
                  lecturaAcordeonAbierto === 0 ? 'rotate-180 text-teal-500' : ''
                ]" 
              />
            </button>

            <!-- Accordion Body Content -->
            <Transition
              enter-active-class="transition duration-300 ease-out"
              enter-from-class="opacity-0 max-h-0 scale-y-95 origin-top"
              enter-to-class="opacity-100 max-h-[800px] scale-y-100 origin-top"
              leave-active-class="transition duration-200 ease-in"
              leave-from-class="opacity-100 max-h-[800px] scale-y-100 origin-top"
              leave-to-class="opacity-0 max-h-0 scale-y-95 origin-top"
            >
              <div 
                v-show="lecturaAcordeonAbierto === 0"
                class="flex-1 overflow-y-auto p-6 sm:p-10 font-serif text-base sm:text-lg leading-relaxed text-slate-700 dark:text-slate-200 custom-scrollbar selection:bg-teal-500/20 bg-white dark:bg-slate-900"
              >
                <div class="max-w-2xl mx-auto whitespace-pre-wrap">
                  {{ lecturas[0]?.texto }}
                </div>
              </div>
            </Transition>
          </template>

          <!-- Multiple Lectures Accordion -->
          <template v-else>
            <!-- Label header (decorational, only on multiple) -->
            <div class="px-8 py-4 bg-slate-50/50 dark:bg-slate-800/10 border-b border-slate-200 dark:border-slate-800/50 flex items-center justify-between shrink-0">
              <div class="flex items-center gap-3">
                <div class="w-8 h-8 rounded-lg bg-teal-500/10 flex items-center justify-center shrink-0">
                  <BookOpen class="w-4 h-4 text-teal-500" />
                </div>
                <h2 class="text-xs font-black uppercase tracking-widest text-slate-400">Contexto de Lectura (Múltiple)</h2>
              </div>
            </div>

            <!-- Accordion Wrapper -->
            <div class="flex-1 flex flex-col overflow-y-auto custom-scrollbar">
              <div v-for="(t, i) in lecturas" :key="i" class="border-b border-slate-200 dark:border-slate-800 last:border-b-0 flex flex-col">
                <!-- Accordion Header -->
                <button 
                  @click="toggleAcordeon(i)"
                  class="w-full px-6 py-4 sm:px-8 sm:py-5 flex items-center justify-between bg-slate-50/20 dark:bg-slate-800/5 hover:bg-slate-50 dark:hover:bg-slate-800/20 transition-all select-none text-left focus:outline-none"
                >
                  <div class="flex items-center gap-3 min-w-0">
                    <div :class="[
                      'w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors',
                      lecturaAcordeonAbierto === i ? 'bg-teal-500/10' : 'bg-slate-100 dark:bg-slate-800'
                    ]">
                      <BookOpen :class="['w-4 h-4 transition-colors', lecturaAcordeonAbierto === i ? 'text-teal-500' : 'text-slate-400']" />
                    </div>
                    <div class="min-w-0">
                      <span class="text-[10px] font-black uppercase tracking-widest text-slate-400 block mb-0.5">Texto {{ i + 1 }}</span>
                      <h3 :class="['font-bold text-sm truncate leading-snug transition-colors', lecturaAcordeonAbierto === i ? 'text-teal-600 dark:text-teal-400' : 'text-slate-700 dark:text-slate-200']">
                        {{ t.titulo || `Lectura ${i + 1}` }}
                      </h3>
                    </div>
                  </div>
                  <ChevronDown 
                    :class="[
                      'w-5 h-5 text-slate-400 transition-transform duration-300 shrink-0',
                      lecturaAcordeonAbierto === i ? 'rotate-180 text-teal-500' : ''
                    ]" 
                  />
                </button>

                <!-- Accordion Content -->
                <Transition
                  enter-active-class="transition duration-300 ease-out"
                  enter-from-class="opacity-0 max-h-0 scale-y-95 origin-top"
                  enter-to-class="opacity-100 max-h-[800px] scale-y-100 origin-top"
                  leave-active-class="transition duration-200 ease-in"
                  leave-from-class="opacity-100 max-h-[800px] scale-y-100 origin-top"
                  leave-to-class="opacity-0 max-h-0 scale-y-95 origin-top"
                >
                  <div 
                    v-show="lecturaAcordeonAbierto === i"
                    class="overflow-y-auto p-6 sm:p-10 font-serif text-base sm:text-lg leading-relaxed text-slate-700 dark:text-slate-200 custom-scrollbar selection:bg-teal-500/20 bg-white dark:bg-slate-900 border-t border-slate-100 dark:border-slate-800/80"
                    :class="lecturas.length > 1 ? 'max-h-[300px] lg:max-h-none lg:flex-1' : 'flex-1'"
                  >
                    <div class="max-w-2xl mx-auto whitespace-pre-wrap">
                      {{ t.texto }}
                    </div>
                  </div>
                </Transition>
              </div>
            </div>
          </template>
        </aside>

        <!-- Right: Questions -->
        <section class="flex-1 min-h-0 lg:h-full flex flex-col z-20 bg-slate-50/30 dark:bg-slate-950/30">
          
          <!-- Question Nav -->
          <div class="px-8 py-6 flex flex-wrap gap-2 shrink-0">
            <button
              v-for="(_, idx) in examen.preguntas"
              :key="idx"
              @click="preguntaActual = idx; intentoEnvioIncompleto = false"
              :class="[
                'w-10 h-10 rounded-xl text-xs font-black transition-all transform active:scale-90',
                idx === preguntaActual
                  ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 shadow-lg ring-4 ring-indigo-500/20'
                  : (examen?.preguntas?.[idx] ? preguntaRespondidaMap.has(examen.preguntas[idx].numero) : false)
                    ? 'bg-teal-500 text-white shadow-md shadow-teal-500/20'
                    : intentoEnvioIncompleto && sinResponder.includes(examen.preguntas[idx]!.numero)
                      ? 'bg-red-500 text-white animate-pulse'
                      : 'bg-white dark:bg-slate-800 text-slate-400 border border-slate-300 dark:border-slate-700 hover:border-teal-400'
              ]"
            >
              {{ idx + 1 }}
            </button>
          </div>

          <!-- Active Question Area -->
          <div class="flex-1 overflow-y-auto px-8 py-4 custom-scrollbar">
            <div class="max-w-2xl mx-auto w-full">
              
              <!-- Incomplete warning -->
              <Transition
                enter-active-class="transition duration-300 ease-out"
                enter-from-class="opacity-0 -translate-y-4"
                enter-to-class="opacity-100 translate-y-0"
              >
                <div v-if="intentoEnvioIncompleto && sinResponder.length > 0"
                  class="mb-6 p-4 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-2xl flex items-center gap-4">
                  <div class="w-10 h-10 rounded-xl bg-red-500 flex items-center justify-center shrink-0 shadow-lg shadow-red-500/20">
                    <AlertCircle class="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <p class="text-sm font-bold text-red-600 dark:text-red-400">Preguntas pendientes</p>
                    <p class="text-xs text-red-500/80">{{ sinResponder.length === 1 ? 'Falta responder 1 pregunta.' : `Faltan ${sinResponder.length} preguntas.` }}</p>
                  </div>
                </div>
              </Transition>

              <!-- Question Card -->
              <div v-if="preguntaVisible" class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 p-8 sm:p-10 shadow-xl relative overflow-hidden group">
                <div class="absolute top-0 right-0 p-8 opacity-5 group-hover:scale-110 transition-transform">
                  <Zap class="w-20 h-20 text-indigo-500" />
                </div>

                <div class="relative">
                  <div class="flex items-center gap-4 mb-8">
                    <div class="w-12 h-12 rounded-2xl bg-indigo-500 flex items-center justify-center text-white font-black text-lg shadow-lg shadow-indigo-500/20">
                      {{ preguntaVisible.numero }}
                    </div>
                    <span class="text-[10px] font-black uppercase tracking-widest text-slate-400">Pregunta de Evaluación</span>
                  </div>

                  <h3 class="text-lg sm:text-xl font-bold text-slate-900 dark:text-white leading-relaxed mb-10">
                    {{ preguntaVisible.enunciado }}
                  </h3>

                  <div class="space-y-4">
                    <button
                      v-for="opcion in preguntaVisible.opciones"
                      :key="opcion.letra"
                      @click="seleccionar(preguntaVisible.numero, opcion.valor ?? opcion.letra)"
                      :class="[
                        'w-full text-left p-5 rounded-xl border-2 transition-all flex items-center gap-5 group/opt',
                        respuestas[preguntaVisible.numero] === (opcion.valor ?? opcion.letra)
                          ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-500/10 text-indigo-900 dark:text-indigo-300'
                          : 'border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:border-indigo-200 dark:hover:border-indigo-500/30 hover:bg-slate-50 dark:hover:bg-slate-800'
                      ]"
                    >
                      <div :class="[
                        'w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm transition-colors',
                        respuestas[preguntaVisible.numero] === (opcion.valor ?? opcion.letra)
                          ? 'bg-indigo-500 text-white'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-400 group-hover/opt:bg-indigo-100 dark:group-hover/opt:bg-slate-700'
                      ]">
                        {{ opcion.letra }}
                      </div>
                      <span class="flex-1 font-bold">{{ opcion.texto }}</span>
                      <div v-if="respuestas[preguntaVisible.numero] === (opcion.valor ?? opcion.letra)" class="w-6 h-6 rounded-full bg-indigo-500/20 flex items-center justify-center">
                        <CheckCircle2 class="w-4 h-4 text-indigo-500" />
                      </div>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Bottom Footer -->
          <footer class="px-8 py-6 bg-white dark:bg-slate-900 border-t border-slate-300 dark:border-slate-800 shrink-0">
            <div class="max-w-2xl mx-auto flex items-center justify-between gap-4">
              <button @click="anterior" :disabled="preguntaActual === 0"
                class="h-12 px-6 rounded-2xl border border-slate-300 dark:border-slate-700 font-bold text-sm text-slate-600 dark:text-slate-400 disabled:opacity-30 hover:bg-slate-50 dark:hover:bg-slate-800 transition-all flex items-center gap-2">
                <ChevronLeft class="w-4 h-4" />
                <span class="hidden sm:inline">Anterior</span>
              </button>

              <div class="flex-1 flex justify-center">
                <div class="px-4 py-2 bg-slate-50 dark:bg-slate-800 rounded-full text-[10px] font-black uppercase tracking-widest text-slate-400">
                  {{ preguntaActual + 1 }} de {{ examen.preguntas.length }}
                </div>
              </div>

              <button
                v-if="preguntaActual < examen.preguntas.length - 1"
                @click="siguiente"
                class="h-12 px-8 rounded-2xl bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold text-sm shadow-xl shadow-slate-900/10 hover:scale-[1.02] active:scale-95 transition-all flex items-center gap-2">
                <span>Siguiente</span>
                <ChevronRight class="w-4 h-4" />
              </button>

              <button
                v-else
                @click="finalizar"
                :disabled="enviando"
                class="h-12 px-8 rounded-2xl font-black text-sm shadow-xl transition-all active:scale-95 flex items-center gap-2"
                :class="todasRespondidas
                  ? 'bg-gradient-to-r from-teal-500 to-indigo-600 text-white shadow-teal-500/20'
                  : 'bg-red-500 text-white shadow-red-500/20'">
                <Loader2 v-if="enviando" class="w-4 h-4 animate-spin" />
                <template v-else>
                  <CheckCircle2 v-if="todasRespondidas" class="w-4 h-4" />
                  <AlertCircle v-else class="w-4 h-4" />
                  <span>{{ todasRespondidas ? 'Finalizar Examen' : 'Finalizar' }}</span>
                </template>
              </button>
            </div>
          </footer>
        </section>
      </main>
    </div>

  </div>
</template>

<style scoped>
@keyframes success-pop {
  0% { transform: scale(0.5) rotate(0deg); opacity: 0; }
  60% { transform: scale(1.1) rotate(15deg); opacity: 1; }
  100% { transform: scale(1) rotate(12deg); opacity: 1; }
}

@keyframes slide-up-fade {
  0% { transform: translateY(30px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}

.animate-success-pop {
  animation: success-pop 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-slide-up-1 {
  opacity: 0;
  animation: slide-up-fade 0.6s ease-out 0.2s forwards;
}

.animate-slide-up-2 {
  opacity: 0;
  animation: slide-up-fade 0.6s ease-out 0.4s forwards;
}

@keyframes confetti-fall {
  0% { transform: translate3d(0, 0, 0) rotateX(0deg) rotateY(0deg) rotateZ(0deg); opacity: 1; }
  100% { transform: translate3d(var(--drift), 110vh, 0) rotateX(720deg) rotateY(360deg) rotateZ(360deg); opacity: 0; }
}

.animate-confetti-fall {
  animation: confetti-fall linear forwards;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}

.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.4);
}

.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }

.card-fade-enter-active,
.card-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.card-fade-enter-from {
  opacity: 0;
  transform: translateY(12px) scale(0.98);
}
.card-fade-leave-to {
  opacity: 0;
  transform: translateY(-12px) scale(0.98);
}
</style>
