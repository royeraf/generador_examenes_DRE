<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '../../services/api'
import { ChevronLeft, ChevronRight, Clock, AlertCircle, CheckCircle2, Loader2, BookOpen } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const asignacionId = Number(route.params.id)

interface Opcion {
  letra: string
  texto: string
}

interface Pregunta {
  numero: number
  enunciado: string
  opciones: Opcion[]
  nivel?: string
  desempeno_codigo?: string
}

interface ExamenData {
  titulo: string
  instrucciones: string
  lectura?: string
  preguntas: Pregunta[]
  duracion_minutos: number | null
  intento_id: number
}

const examen = ref<ExamenData | null>(null)
const loading = ref(true)
const error = ref('')
const enviando = ref(false)
const resultado = ref<any>(null)

const preguntaActual = ref(0)
const respuestas = ref<Record<number, string>>({})

const preguntaVisible = computed(() => examen.value?.preguntas[preguntaActual.value])

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

onMounted(async () => {
  try {
    // Iniciar el intento
    const res = await apiClient.post(`/estudiante/examenes/${asignacionId}/iniciar`)
    const data = res.data
    examen.value = data

    if (data.duracion_minutos) {
      tiempoRestante.value = data.duracion_minutos * 60
      timerInterval = setInterval(() => {
        if (tiempoRestante.value > 0) {
          tiempoRestante.value--
        } else {
          finalizar()
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
}

function anterior() {
  if (preguntaActual.value > 0) preguntaActual.value--
}

function siguiente() {
  if (examen.value && preguntaActual.value < examen.value.preguntas.length - 1) {
    preguntaActual.value++
  }
}

async function finalizar() {
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
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al enviar respuestas'
  } finally {
    enviando.value = false
  }
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
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-900">

    <!-- Cargando -->
    <div v-if="loading" class="flex items-center justify-center min-h-screen">
      <Loader2 class="w-10 h-10 animate-spin text-teal-500" />
    </div>

    <!-- Error -->
    <div v-else-if="error && !examen" class="flex flex-col items-center justify-center min-h-screen gap-4">
      <AlertCircle class="w-10 h-10 text-red-500" />
      <p class="text-slate-700 dark:text-slate-200">{{ error }}</p>
      <button @click="router.push('/estudiante/examenes')"
        class="px-4 py-2 bg-teal-500 text-white rounded-xl font-semibold">Volver</button>
    </div>

    <!-- Resultado final -->
    <div v-else-if="resultado" class="max-w-2xl mx-auto px-4 py-12">
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-8 text-center shadow-sm">
        <div class="w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto mb-5">
          <CheckCircle2 class="w-10 h-10 text-green-500" />
        </div>
        <h2 class="text-2xl font-bold text-slate-800 dark:text-white">Examen completado</h2>
        <p class="text-slate-500 dark:text-slate-400 mt-2">Has terminado el examen</p>

        <div class="mt-6 grid grid-cols-2 gap-4">
          <div class="bg-slate-50 dark:bg-slate-700 rounded-xl p-4">
            <p class="text-3xl font-bold text-teal-600 dark:text-teal-400">{{ resultado.puntaje_total?.toFixed(1) }}%</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Puntaje</p>
          </div>
          <div class="bg-slate-50 dark:bg-slate-700 rounded-xl p-4">
            <p :class="nivelColors[resultado.nivel_logro] || 'text-slate-600'"
              class="text-xl font-bold">
              {{ nivelLabels[resultado.nivel_logro] ?? resultado.nivel_logro ?? '—' }}
            </p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Nivel de logro</p>
          </div>
          <div class="bg-slate-50 dark:bg-slate-700 rounded-xl p-4">
            <p class="text-2xl font-bold text-slate-700 dark:text-slate-200">{{ resultado.preguntas_correctas }}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Correctas</p>
          </div>
          <div class="bg-slate-50 dark:bg-slate-700 rounded-xl p-4">
            <p class="text-2xl font-bold text-slate-700 dark:text-slate-200">{{ resultado.preguntas_total }}</p>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Total preguntas</p>
          </div>
        </div>

        <button @click="router.push('/estudiante/examenes')"
          class="mt-6 w-full py-3 bg-gradient-to-r from-teal-500 to-indigo-600 text-white font-bold rounded-xl">
          Volver a mis exámenes
        </button>
      </div>
    </div>

    <!-- Examen en curso -->
    <div v-else-if="examen">
      <!-- Header del examen -->
      <div class="bg-white dark:bg-slate-800 border-b border-slate-100 dark:border-slate-700 sticky top-0 z-40">
        <div class="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <div class="flex items-center gap-3">
            <BookOpen class="w-5 h-5 text-teal-500" />
            <span class="font-bold text-slate-800 dark:text-white text-sm truncate max-w-[200px]">{{ examen.titulo }}</span>
          </div>
          <div class="flex items-center gap-4">
            <div v-if="examen.duracion_minutos" :class="timerColor" class="flex items-center gap-1.5 font-mono font-bold text-sm">
              <Clock class="w-4 h-4" />
              {{ tiempoFormato }}
            </div>
            <span class="text-xs text-slate-500">{{ progreso }}% respondido</span>
          </div>
        </div>
        <!-- Barra de progreso -->
        <div class="h-1 bg-slate-100 dark:bg-slate-700">
          <div class="h-full bg-gradient-to-r from-teal-500 to-indigo-600 transition-all duration-300"
            :style="{ width: progreso + '%' }"></div>
        </div>
      </div>

      <div class="max-w-4xl mx-auto px-4 py-6">
        <!-- Lectura base (si hay) -->
        <div v-if="examen.lectura" class="mb-6 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-5 shadow-sm">
          <p class="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">Texto Base</p>
          <div class="text-sm text-slate-700 dark:text-slate-200 leading-relaxed whitespace-pre-wrap">{{ examen.lectura }}</div>
        </div>

        <!-- Navegación rápida -->
        <div class="flex flex-wrap gap-2 mb-5">
          <button
            v-for="(_, idx) in examen.preguntas"
            :key="idx"
            @click="preguntaActual = idx"
            :class="[
              'w-8 h-8 rounded-lg text-xs font-bold transition-all',
              idx === preguntaActual
                ? 'bg-indigo-600 text-white'
                : respuestas[(idx + 1)] !== undefined
                  ? 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400'
                  : 'bg-white dark:bg-slate-700 text-slate-500 border border-slate-200 dark:border-slate-600'
            ]"
          >
            {{ idx + 1 }}
          </button>
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
              @click="seleccionar(preguntaVisible.numero, opcion.letra)"
              :class="[
                'w-full text-left p-3.5 rounded-xl border-2 transition-all text-sm',
                respuestas[preguntaVisible.numero] === opcion.letra
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
            class="flex items-center gap-1.5 px-6 py-2.5 rounded-xl bg-gradient-to-r from-green-500 to-teal-600 hover:from-green-600 hover:to-teal-700 text-white font-bold text-sm transition-all disabled:opacity-70">
            <Loader2 v-if="enviando" class="w-4 h-4 animate-spin" />
            <CheckCircle2 v-else class="w-4 h-4" />
            Finalizar examen
          </button>
        </div>
      </div>
    </div>

  </div>
</template>
