<script setup lang="ts">
import { ref, shallowRef, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../../shared/services/api'
import {
  ChevronLeft, ChevronRight, Clock, AlertCircle, CheckCircle2,
  Loader2, BookOpen, ClipboardList, ChevronDown, ChevronUp,
  CheckCircle, XCircle, Lightbulb, X
} from 'lucide-vue-next'
import ThinkingLoader from '../../shared/components/ThinkingLoader.vue'

const route = useRoute()
const router = useRouter()
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
const mostrarRevision = ref(false)
const preguntaRevisionAbierta = ref<number | null>(null)
const intentoIdFinalizado = ref<number | null>(null)

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

const showLecturaModal = ref(false)
const lecturaTabActiva = shallowRef(0)
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

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval)
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
    // Ir a la primera pregunta sin responder
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
  // Buscar el intento_id: puede venir del flujo de envío o hay que buscarlo del resultado
  const intenId = intentoIdFinalizado.value
  if (!intenId && !route.query.intento_id) {
    // modo=resultados: buscar último intento desde el resultado de la asignacion
    // usamos el endpoint de revision vía asignacion
    loadingRevision.value = true
    mostrarRevision.value = true
    try {
      const res = await apiClient.get(`/estudiante/examenes/${asignacionId}/revision`)
      revision.value = res.data
    } catch (e: any) {
      error.value = e.response?.data?.detail ?? 'Error al cargar revisión'
    } finally {
      loadingRevision.value = false
    }
    return
  }

  const id = intenId ?? Number(route.query.intento_id)
  loadingRevision.value = true
  mostrarRevision.value = true
  try {
    const res = await apiClient.get(`/estudiante/intentos/${id}/revision`)
    revision.value = res.data
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar revisión'
  } finally {
    loadingRevision.value = false
  }
}

function togglePreguntaRevision(num: number) {
  preguntaRevisionAbierta.value = preguntaRevisionAbierta.value === num ? null : num
}

const nivelColors: Record<string, string> = {
  pre_inicio: 'text-red-500',
  inicio: 'text-orange-500',
  proceso: 'text-yellow-600',
  satisfactorio: 'text-green-600',
  destacado: 'text-teal-600',
}
const nivelLabels: Record<string, string> = {
  pre_inicio: 'Pre Inicio', inicio: 'Inicio', proceso: 'En Proceso',
  satisfactorio: 'Satisfactorio', destacado: 'Destacado',
}
const nivelBadge: Record<string, string> = {
  pre_inicio: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  inicio: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  proceso: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  satisfactorio: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
  destacado: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
}
const nivelMensaje: Record<string, string> = {
  pre_inicio: 'Sigue practicando, puedes mejorar.',
  inicio: 'Vas por buen camino, sigue adelante.',
  proceso: 'Buen esfuerzo, estás progresando.',
  satisfactorio: 'Muy bien, alcanzaste el nivel esperado.',
  destacado: 'Excelente, superaste las expectativas.',
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900 relative overflow-x-hidden w-full">

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
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <Loader2 class="w-10 h-10 animate-spin text-teal-500" />
    </div>

    <!-- Error -->
    <div v-else-if="error && !examen && !resultado" class="flex flex-col items-center justify-center min-h-screen gap-4">
      <AlertCircle class="w-10 h-10 text-red-500" />
      <p class="text-slate-700 dark:text-slate-200">{{ error }}</p>
      <button @click="router.push('/estudiante/examenes')"
        class="px-4 py-2 bg-teal-500 text-white rounded-xl font-semibold">Volver</button>
    </div>

    <!-- Resultado final -->
    <div v-else-if="resultado"
      class="min-h-screen flex flex-col items-center px-4 py-10 bg-gradient-to-br from-slate-50 via-teal-50/20 to-indigo-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">

      <!-- ── Tarjeta de resultado ── -->
      <div class="w-full max-w-sm mb-8">

        <div class="flex justify-center mb-6 animate-success-pop">
          <div class="w-20 h-20 rounded-full bg-gradient-to-br from-teal-400 to-indigo-500 flex items-center justify-center shadow-lg shadow-teal-500/25">
            <CheckCircle2 class="w-10 h-10 text-white" />
          </div>
        </div>

        <div class="text-center mb-7 animate-slide-up-1">
          <h1 class="text-2xl font-black text-slate-800 dark:text-white">Examen completado</h1>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            {{ nivelMensaje[resultado.nivel_logro] ?? 'Has terminado el examen.' }}
          </p>
        </div>

        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-6 mb-3 animate-slide-up-2">
          <div class="text-center">
            <p class="text-6xl font-black tabular-nums leading-none" :class="nivelColors[resultado.nivel_logro] ?? 'text-teal-600 dark:text-teal-400'">
              {{ resultado.puntaje_total?.toFixed(0) }}<span class="text-2xl font-semibold text-slate-400 dark:text-slate-500">%</span>
            </p>
            <p class="text-xs text-slate-400 dark:text-slate-500 mt-1 mb-3">Puntaje obtenido</p>
            <div class="h-2.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
              <div class="h-full rounded-full bg-gradient-to-r from-teal-500 to-indigo-500 transition-all duration-700"
                :style="{ width: (resultado.puntaje_total ?? 0) + '%' }"></div>
            </div>
          </div>
          <div class="flex justify-center mt-4">
            <span :class="nivelBadge[resultado.nivel_logro] ?? 'bg-slate-100 text-slate-600'"
              class="px-4 py-1 rounded-full text-sm font-bold">
              {{ nivelLabels[resultado.nivel_logro] ?? resultado.nivel_logro ?? '—' }}
            </span>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-3 mb-4 animate-slide-up-3">
          <div class="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-4 text-center shadow-sm">
            <p class="text-2xl font-black text-emerald-600 dark:text-emerald-400">
              {{ resultado.preguntas_correctas }}
              <span class="text-sm font-medium text-slate-400">/{{ resultado.preguntas_total }}</span>
            </p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Correctas</p>
          </div>
          <div class="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 p-4 text-center shadow-sm">
            <p class="text-2xl font-black text-red-500 dark:text-red-400">
              {{ (resultado.preguntas_total ?? 0) - (resultado.preguntas_correctas ?? 0) }}
              <span class="text-sm font-medium text-slate-400">/{{ resultado.preguntas_total }}</span>
            </p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Incorrectas</p>
          </div>
        </div>

        <!-- Botón Revisión -->
        <button @click="cargarRevision" :disabled="loadingRevision"
          class="w-full py-3.5 mb-3 font-bold rounded-xl shadow transition-all text-sm flex items-center justify-center gap-2 animate-slide-up-3"
          :class="loadingRevision
            ? 'bg-white dark:bg-slate-900 border-2 border-slate-200 dark:border-slate-700 cursor-wait'
            : 'bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 text-white'">
          <ThinkingLoader v-if="loadingRevision" text="Generando retroalimentación" variant="purple" />
          <template v-else>
            <ClipboardList class="w-4 h-4" />
            Ver revisión detallada
          </template>
        </button>

        <button @click="router.push('/estudiante/examenes')"
          class="w-full py-3 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 font-semibold rounded-xl transition-all text-sm animate-slide-up-4">
          Volver a mis exámenes
        </button>
      </div>

      <!-- ── Revisión detallada ── -->
      <div v-if="mostrarRevision" class="w-full max-w-2xl">

        <!-- Loading revisión -->
        <div v-if="loadingRevision" class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-10 flex flex-col items-center shadow-sm">
          <ThinkingLoader text="Generando retroalimentación" variant="purple" />
          <p class="text-xs text-slate-400 dark:text-slate-500 mt-4">Esto puede tomar unos segundos</p>
        </div>

        <!-- Lista de preguntas revisadas -->
        <div v-else-if="revision" class="space-y-3">
          <div class="flex items-center gap-2 mb-4">
            <ClipboardList class="w-5 h-5 text-violet-500" />
            <h2 class="text-base font-bold text-slate-800 dark:text-white">Revisión detallada</h2>
            <span class="ml-auto text-xs text-slate-400">{{ revision.preguntas_correctas }}/{{ revision.preguntas_total }} correctas</span>
          </div>

          <div v-for="preg in revision.preguntas" :key="preg.numero"
            class="bg-white dark:bg-slate-800 rounded-xl border-2 overflow-hidden shadow-sm transition-all"
            :class="preg.es_correcta
              ? 'border-emerald-200 dark:border-emerald-800'
              : 'border-red-200 dark:border-red-900'">

            <!-- Cabecera de pregunta (clic para expandir) -->
            <button @click="togglePreguntaRevision(preg.numero)"
              class="w-full flex items-center gap-3 p-4 text-left hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors">
              <!-- Icono correcto/incorrecto -->
              <div class="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                :class="preg.es_correcta
                  ? 'bg-emerald-100 dark:bg-emerald-900/40'
                  : 'bg-red-100 dark:bg-red-900/30'">
                <CheckCircle v-if="preg.es_correcta" class="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                <XCircle v-else class="w-4 h-4 text-red-500 dark:text-red-400" />
              </div>
              <div class="flex-1 min-w-0">
                <span class="text-[10px] font-bold uppercase tracking-wide"
                  :class="preg.es_correcta ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-500 dark:text-red-400'">
                  Pregunta {{ preg.numero }} · {{ preg.es_correcta ? 'Correcta' : 'Incorrecta' }}
                </span>
                <p class="text-sm text-slate-700 dark:text-slate-200 font-medium truncate mt-0.5">{{ preg.enunciado }}</p>
              </div>
              <ChevronDown v-if="preguntaRevisionAbierta !== preg.numero" class="w-4 h-4 text-slate-400 shrink-0" />
              <ChevronUp v-else class="w-4 h-4 text-slate-400 shrink-0" />
            </button>

            <!-- Contenido expandido -->
            <div v-if="preguntaRevisionAbierta === preg.numero" class="border-t border-slate-100 dark:border-slate-700 px-4 pb-4 pt-3 space-y-3">

              <!-- Opciones con colores -->
              <div class="space-y-1.5">
                <div v-for="opcion in preg.opciones" :key="opcion.letra"
                  class="flex items-center gap-2.5 px-3 py-2.5 rounded-lg border text-sm transition-all"
                  :class="
                    opcion.letra === preg.respuesta_correcta && opcion.letra === preg.respuesta_dada
                      ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-400 dark:border-emerald-600 text-emerald-800 dark:text-emerald-300 font-semibold'
                      : opcion.letra === preg.respuesta_correcta
                        ? 'bg-emerald-50 dark:bg-emerald-900/30 border-emerald-400 dark:border-emerald-600 text-emerald-800 dark:text-emerald-300 font-semibold'
                        : opcion.letra === preg.respuesta_dada && !preg.es_correcta
                          ? 'bg-red-50 dark:bg-red-900/20 border-red-400 dark:border-red-700 text-red-700 dark:text-red-400'
                          : 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400'
                  ">
                  <span class="w-6 h-6 rounded-md flex items-center justify-center text-xs font-bold shrink-0"
                    :class="
                      opcion.letra === preg.respuesta_correcta
                        ? 'bg-emerald-500 text-white'
                        : opcion.letra === preg.respuesta_dada && !preg.es_correcta
                          ? 'bg-red-500 text-white'
                          : 'bg-slate-200 dark:bg-slate-700 text-slate-500'
                    ">{{ opcion.letra }}</span>
                  <span class="flex-1">{{ opcion.texto }}</span>
                  <CheckCircle v-if="opcion.letra === preg.respuesta_correcta" class="w-4 h-4 text-emerald-500 shrink-0" />
                  <XCircle v-else-if="opcion.letra === preg.respuesta_dada && !preg.es_correcta" class="w-4 h-4 text-red-500 shrink-0" />
                </div>
              </div>

              <!-- Leyenda -->
              <div class="flex items-center gap-4 text-[11px] text-slate-400">
                <span class="flex items-center gap-1"><CheckCircle class="w-3 h-3 text-emerald-500" /> Respuesta correcta</span>
                <span v-if="!preg.es_correcta" class="flex items-center gap-1"><XCircle class="w-3 h-3 text-red-500" /> Tu respuesta</span>
              </div>

              <!-- Retroalimentación IA -->
              <div v-if="preg.retroalimentacion_ia"
                class="rounded-xl p-3.5 border flex gap-3"
                :class="preg.es_correcta
                  ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800'
                  : 'bg-violet-50 dark:bg-violet-900/20 border-violet-200 dark:border-violet-800'">
                <Lightbulb class="w-4 h-4 shrink-0 mt-0.5"
                  :class="preg.es_correcta ? 'text-emerald-500' : 'text-violet-500'" />
                <p class="text-sm leading-relaxed"
                  :class="preg.es_correcta
                    ? 'text-emerald-800 dark:text-emerald-300'
                    : 'text-violet-800 dark:text-violet-300'">
                  {{ preg.retroalimentacion_ia }}
                </p>
              </div>
            </div>
          </div>

          <!-- Footer revisión -->
          <div class="pt-2 pb-8">
            <button @click="router.push('/estudiante/examenes')"
              class="w-full py-3.5 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold rounded-xl shadow transition-all text-sm">
              Volver a mis exámenes
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Examen en curso -->
    <div v-else-if="examen" class="w-full max-w-full">
      <div class="bg-white dark:bg-slate-800 border-b border-slate-100 dark:border-slate-700 sticky top-0 z-40 w-full">
        <div class="max-w-4xl mx-auto px-2 sm:px-4 h-14 flex items-center justify-between gap-2">
          <div class="flex items-center gap-2 min-w-0">
            <BookOpen class="w-5 h-5 text-teal-500 shrink-0" />
            <span class="font-bold text-slate-800 dark:text-white text-sm truncate">{{ examen.titulo }}</span>
          </div>
          <div class="flex items-center gap-2 sm:gap-4 shrink-0">
            <div v-if="examen.duracion_minutos" :class="timerColor" class="flex items-center gap-1 font-mono font-bold text-xs sm:text-sm">
              <Clock class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
              {{ tiempoFormato }}
            </div>
            <span class="text-[10px] sm:text-xs text-slate-500 whitespace-nowrap">{{ progreso }}% resp.</span>
          </div>
        </div>
        <div class="h-1 bg-slate-100 dark:bg-slate-700">
          <div class="h-full bg-gradient-to-r from-teal-500 to-indigo-600 transition-all duration-300"
            :style="{ width: progreso + '%' }"></div>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-4 py-6">
        <!-- Botón Ver Lectura -->
        <button v-if="lecturas.length" @click="showLecturaModal = true"
          class="w-full flex items-center justify-between p-4 mb-6 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm hover:border-teal-300 dark:hover:border-teal-700 hover:shadow-md transition-all group">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-xl bg-teal-50 dark:bg-teal-900/30 flex items-center justify-center group-hover:scale-105 transition-transform">
              <BookOpen class="w-6 h-6 text-teal-600 dark:text-teal-400" />
            </div>
            <div class="text-left">
              <h3 class="text-base font-bold text-slate-800 dark:text-white">Textos de Lectura</h3>
              <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Presiona para leer {{ lecturas.length > 1 ? 'los textos base' : 'el texto base' }}</p>
            </div>
          </div>
          <ChevronRight class="w-5 h-5 text-slate-400 group-hover:translate-x-1 transition-transform" />
        </button>

        <!-- Navegación rápida -->
        <div class="flex flex-wrap gap-2 mb-3">
          <button
            v-for="(_, idx) in examen.preguntas"
            :key="idx"
            @click="preguntaActual = idx; intentoEnvioIncompleto = false"
            :class="[
              'w-8 h-8 rounded-lg text-xs font-bold transition-all',
              idx === preguntaActual
                ? 'bg-indigo-600 text-white'
                : examen.preguntas[idx] && preguntaRespondidaMap.has(examen.preguntas[idx].numero)
                  ? 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400'
                  : intentoEnvioIncompleto && sinResponder.includes(examen.preguntas[idx]!.numero)
                    ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400 ring-2 ring-red-400 animate-pulse'
                    : 'bg-white dark:bg-slate-700 text-slate-500 border border-slate-200 dark:border-slate-600'
            ]"
          >
            {{ idx + 1 }}
          </button>
        </div>

        <!-- Advertencia preguntas sin responder -->
        <div v-if="intentoEnvioIncompleto && sinResponder.length > 0"
          class="flex items-center gap-2 mb-4 px-3 py-2.5 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl text-sm text-red-600 dark:text-red-400">
          <AlertCircle class="w-4 h-4 shrink-0" />
          <span class="font-medium">
            {{ sinResponder.length === 1
              ? `Falta responder la pregunta ${sinResponder[0]}.`
              : `Faltan ${sinResponder.length} preguntas sin responder.` }}
            Responde todas antes de enviar.
          </span>
        </div>

        <!-- Pregunta actual -->
        <div v-if="preguntaVisible" class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm">
          <div class="flex items-start gap-3 mb-5">
            <span class="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 font-bold text-sm flex items-center justify-center shrink-0">
              {{ preguntaVisible.numero }}
            </span>
            <p class="text-slate-800 dark:text-white font-medium leading-relaxed">
              {{ preguntaVisible.enunciado }}
            </p>
          </div>

          <div class="space-y-2.5">
            <button
              v-for="opcion in preguntaVisible.opciones"
              :key="opcion.letra"
              @click="seleccionar(preguntaVisible.numero, opcion.valor ?? opcion.letra)"
              :class="[
                'w-full text-left p-3.5 rounded-xl border-2 transition-all text-sm',
                respuestas[preguntaVisible.numero] === (opcion.valor ?? opcion.letra)
                  ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 font-medium'
                  : 'border-slate-200 dark:border-slate-600 text-slate-700 dark:text-slate-200 hover:border-indigo-300 hover:bg-indigo-50/50 dark:hover:bg-slate-700/50'
              ]"
            >
              <span class="font-bold mr-2">{{ opcion.letra }}.</span> {{ opcion.texto }}
            </button>
          </div>
        </div>

        <!-- Navegación inferior -->
        <div class="flex items-center justify-between mt-6">
          <button @click="anterior" :disabled="preguntaActual === 0"
            class="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 text-sm font-medium text-slate-600 dark:text-slate-300 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-600 transition-colors">
            <ChevronLeft class="w-4 h-4" /> Anterior
          </button>

          <button
            v-if="preguntaActual < examen.preguntas.length - 1"
            @click="siguiente"
            class="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm transition-all">
            Siguiente <ChevronRight class="w-4 h-4" />
          </button>

          <button
            v-else
            @click="finalizar"
            :disabled="enviando"
            class="flex items-center gap-1.5 px-6 py-2.5 rounded-xl font-bold text-sm transition-all disabled:opacity-70"
            :class="todasRespondidas
              ? 'bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white'
              : 'bg-gradient-to-r from-red-400 to-orange-500 hover:from-red-500 hover:to-orange-600 text-white'">
            <Loader2 v-if="enviando" class="w-4 h-4 animate-spin" />
            <AlertCircle v-else-if="!todasRespondidas" class="w-4 h-4" />
            <CheckCircle2 v-else class="w-4 h-4" />
            {{ todasRespondidas ? 'Finalizar examen' : `${sinResponder.length} sin responder` }}
          </button>
        </div>
      </div>
    </div>

  </div>

  <!-- Modal/Bottom Sheet Lectura -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 translate-y-8 sm:translate-y-0 sm:scale-95"
      enter-to-class="opacity-100 translate-y-0 sm:scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0 sm:scale-100"
      leave-to-class="opacity-0 translate-y-8 sm:translate-y-0 sm:scale-95"
    >
      <div v-if="showLecturaModal" class="fixed inset-0 z-[100] flex items-end sm:items-center justify-center p-0 sm:p-4">
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-slate-900/60 backdrop-blur-sm -z-10" @click="showLecturaModal = false"></div>
        
        <!-- Modal content -->
        <div class="bg-white dark:bg-slate-800 w-full max-w-3xl sm:rounded-2xl rounded-t-2xl sm:rounded-b-2xl shadow-2xl flex flex-col max-h-[90vh] sm:max-h-[85vh] relative">
          <!-- Drag handle (mobile only) -->
          <div class="w-full h-8 flex justify-center items-center sm:hidden shrink-0 absolute top-0" @click="showLecturaModal = false">
            <div class="w-12 h-1.5 bg-slate-200 dark:bg-slate-600 rounded-full"></div>
          </div>

          <!-- Header -->
          <div class="px-5 pt-8 sm:pt-5 pb-4 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between shrink-0">
            <h2 class="text-lg font-bold text-slate-800 dark:text-white flex items-center gap-2">
              <BookOpen class="w-5 h-5 text-teal-500" /> Textos de Lectura
            </h2>
            <button @click="showLecturaModal = false" class="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 transition-colors">
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Body -->
          <div class="overflow-y-auto p-0 flex-1 custom-scrollbar bg-slate-50 dark:bg-slate-900 sm:rounded-b-2xl">
            <div v-if="lecturas.length > 1" class="flex border-b border-slate-200 dark:border-slate-700 overflow-x-auto bg-white dark:bg-slate-800 sticky top-0 z-10 shadow-sm">
              <button v-for="(t, i) in lecturas" :key="i"
                @click="lecturaTabActiva = i"
                :class="[
                  'flex-shrink-0 px-5 py-3 text-sm font-semibold transition-colors border-b-2 -mb-px',
                  lecturaTabActiva === i
                    ? 'border-teal-500 text-teal-600 dark:text-teal-400 bg-teal-50/50 dark:bg-teal-900/10'
                    : 'border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                ]">
                {{ t.titulo || `Texto ${i + 1}` }}
              </button>
            </div>
            <div class="p-5 sm:p-8 text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-wrap sm:text-lg text-base font-serif">
              {{ lecturas[lecturaTabActiva]?.texto }}
            </div>
          </div>
          
          <!-- Safe area bottom mobile -->
          <div class="h-6 bg-slate-50 dark:bg-slate-900 sm:hidden"></div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
@keyframes success-pop {
  0% { transform: scale(0.5); opacity: 0; }
  60% { transform: scale(1.1); opacity: 1; }
  100% { transform: scale(1); opacity: 1; }
}

@keyframes slide-up-fade {
  0% { transform: translateY(20px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}

.animate-success-pop {
  animation: success-pop 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}

.animate-slide-up-1 {
  opacity: 0;
  animation: slide-up-fade 0.5s ease-out 0.1s forwards;
}

.animate-slide-up-2 {
  opacity: 0;
  animation: slide-up-fade 0.5s ease-out 0.2s forwards;
}

.animate-slide-up-3 {
  opacity: 0;
  animation: slide-up-fade 0.5s ease-out 0.3s forwards;
}

.animate-slide-up-4 {
  opacity: 0;
  animation: slide-up-fade 0.5s ease-out 0.4s forwards;
}

@keyframes confetti-fall {
  0% { transform: translate3d(0, 0, 0) rotateX(0deg) rotateY(0deg) rotateZ(0deg); opacity: 1; }
  100% { transform: translate3d(var(--drift), 110vh, 0) rotateX(720deg) rotateY(360deg) rotateZ(360deg); opacity: 0; }
}

.animate-confetti-fall {
  animation: confetti-fall linear forwards;
}
</style>
