<script setup lang="ts">
import { ref, shallowRef, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../../shared/services/api'
import { useTheme } from '../../shared/composables/useTheme'
import { BookOpen, GraduationCap, ChevronLeft, Loader2, Clock, CheckCircle2, AlertCircle, X, BookText, Calculator } from 'lucide-vue-next'

const router = useRouter()
useTheme()

interface AsignacionResumen {
  id: number
  tipo_examen: string
  titulo: string
  fecha_inicio: string | null
  fecha_fin: string | null
  duracion_minutos: number | null
  intentos_permitidos: number
  mis_intentos: number
  completado: boolean
  puntaje?: number | null
  nivel_logro?: string | null
}

const examenes = ref<AsignacionResumen[]>([])
const loading = ref(true)
const error = ref('')

// Modal preview lectura
interface PreviewLectura { titulo: string; texto: string }
interface Preview {
  titulo: string
  tipo_examen: string
  lecturas: PreviewLectura[]
  instrucciones: string
}
const showPreview = shallowRef(false)
const previewAsignacionId = shallowRef<number | null>(null)
const previewData = ref<Preview | null>(null)
const loadingPreview = shallowRef(false)
const previewTabActiva = shallowRef(0)

type ReadingTheme = 'claro' | 'sepia' | 'oscuro'
type ReadingFont  = 'sans' | 'serif'
const readingTheme = shallowRef<ReadingTheme>('claro')
const readingFont  = shallowRef<ReadingFont>('sans')

const themeClasses: Record<ReadingTheme, string> = {
  claro:  'bg-white text-slate-800',
  sepia:  'bg-amber-50 text-amber-950',
  oscuro: 'bg-slate-900 text-slate-100',
}
const fontClasses: Record<ReadingFont, string> = {
  sans:  'font-sans',
  serif: 'font-serif',
}

async function abrirPreview(examen: AsignacionResumen) {
  previewAsignacionId.value = examen.id
  previewData.value = null
  previewTabActiva.value = 0
  showPreview.value = true
  loadingPreview.value = true
  try {
    const res = await apiClient.get(`/estudiante/examenes/${examen.id}/preview`)
    previewData.value = res.data
  } catch {
    previewData.value = null
  } finally {
    loadingPreview.value = false
  }
}

function irAlExamen() {
  if (previewAsignacionId.value === null) return
  showPreview.value = false
  router.push(`/estudiante/examen/${previewAsignacionId.value}`)
}

onMounted(async () => {
  try {
    const res = await apiClient.get('/estudiante/examenes')
    examenes.value = res.data
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar exámenes'
  } finally {
    loading.value = false
  }
})

const nivelColors: Record<string, string> = {
  pre_inicio: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  inicio: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  proceso: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  satisfactorio: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  destacado: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
}

const nivelLabels: Record<string, string> = {
  pre_inicio: 'Pre Inicio', inicio: 'Inicio', proceso: 'En Proceso',
  satisfactorio: 'Satisfactorio', destacado: 'Destacado',
}

function formatFecha(fecha: string | null) {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleDateString('es-PE', { day: '2-digit', month: 'short' })
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-teal-50 to-indigo-50 dark:from-slate-900 dark:to-slate-800">
    <header class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-700 sticky top-0 z-40">
      <div class="max-w-4xl mx-auto px-4 h-14 flex items-center gap-3">
        <button @click="router.push('/estudiante')" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
          <ChevronLeft class="w-5 h-5" />
        </button>
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center">
            <GraduationCap class="w-4 h-4 text-white" />
          </div>
          <span class="font-bold text-slate-800 dark:text-white text-sm">Mis Exámenes</span>
        </div>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8">
      <div v-if="loading" class="flex justify-center py-16">
        <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
      </div>

      <div v-else-if="error" class="text-center py-16 text-red-500 flex flex-col items-center gap-3">
        <AlertCircle class="w-8 h-8" />
        <p>{{ error }}</p>
      </div>

      <div v-else-if="examenes.length === 0"
        class="text-center py-16 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700">
        <BookOpen class="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p class="text-slate-500 dark:text-slate-400 font-medium">No tienes exámenes asignados</p>
        <p class="text-sm text-slate-400 dark:text-slate-500 mt-1">Tu docente aún no ha asignado exámenes</p>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="examen in examenes"
          :key="examen.id"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-5 shadow-sm hover:shadow-md transition-all"
        >
          <div class="flex items-start gap-4">
            <div :class="examen.tipo_examen === 'lectura'
              ? 'from-teal-500 to-indigo-600'
              : 'from-orange-500 to-amber-500'"
              class="w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center shrink-0">
              <BookOpen class="w-5 h-5 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2 flex-wrap">
                <div>
                  <h3 class="font-bold text-slate-800 dark:text-white">{{ examen.titulo }}</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {{ examen.tipo_examen === 'lectura' ? 'Comunicación' : 'Matemática' }}
                    <span v-if="examen.duracion_minutos" class="ml-2 flex items-center gap-0.5 inline-flex">
                      <Clock class="w-3 h-3" /> {{ examen.duracion_minutos }} min
                    </span>
                  </p>
                </div>
                <div class="flex items-center gap-2 flex-wrap">
                  <span v-if="examen.completado && examen.nivel_logro"
                    :class="nivelColors[examen.nivel_logro] || 'bg-slate-100 text-slate-700'"
                    class="px-2.5 py-0.5 rounded-full text-xs font-bold">
                    {{ nivelLabels[examen.nivel_logro] ?? examen.nivel_logro }}
                  </span>
                  <span v-if="examen.completado"
                    class="inline-flex items-center gap-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2.5 py-0.5 rounded-full text-xs font-bold">
                    <CheckCircle2 class="w-3 h-3" /> Completado
                  </span>
                </div>
              </div>

              <div class="flex items-center gap-4 mt-3 text-xs text-slate-500 dark:text-slate-400">
                <span v-if="examen.fecha_inicio">Desde: {{ formatFecha(examen.fecha_inicio) }}</span>
                <span v-if="examen.fecha_fin">Hasta: {{ formatFecha(examen.fecha_fin) }}</span>
                <span>Intento {{ examen.mis_intentos }}/{{ examen.intentos_permitidos }}</span>
                <span v-if="examen.completado && examen.puntaje != null">
                  Puntaje: <span class="font-semibold text-teal-600 dark:text-teal-400">{{ examen.puntaje.toFixed(1) }}%</span>
                </span>
              </div>
            </div>
          </div>

          <div class="mt-4 flex items-center justify-end gap-2">
            <template v-if="!examen.completado || examen.mis_intentos < examen.intentos_permitidos">
              <button @click="abrirPreview(examen)"
                class="p-2 rounded-xl border border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-teal-400 hover:text-teal-600 dark:hover:text-teal-400 transition-all"
                title="Ver lectura">
                <BookText class="w-4 h-4" />
              </button>
              <button @click="router.push(`/estudiante/examen/${examen.id}`)"
                class="px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all">
                {{ examen.mis_intentos > 0 ? 'Reintentar' : 'Comenzar' }}
              </button>
            </template>
            <button v-else @click="router.push(`/estudiante/examen/${examen.id}?modo=resultados`)"
              class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold text-sm rounded-xl transition-all">
              Ver resultados
            </button>
          </div>
        </div>
      </div>
    </main>
    <!-- Modal Preview Lectura -->
    <Teleport to="body">
      <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0"
        enter-to-class="opacity-100" leave-active-class="transition duration-150"
        leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="showPreview"
          class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          @click.self="showPreview = false">
          <div class="bg-white dark:bg-slate-800 w-full max-w-xl max-h-[88vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden">

            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <div class="flex items-center gap-3 min-w-0">
                <div class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
                  :class="previewData?.tipo_examen === 'matematica'
                    ? 'bg-gradient-to-br from-orange-400 to-amber-500'
                    : 'bg-gradient-to-br from-teal-500 to-indigo-600'">
                  <Calculator v-if="previewData?.tipo_examen === 'matematica'" class="w-4 h-4 text-white" />
                  <BookText v-else class="w-4 h-4 text-white" />
                </div>
                <div class="min-w-0">
                  <h2 class="text-sm font-bold text-slate-800 dark:text-white truncate">
                    {{ previewData?.titulo ?? 'Preparación' }}
                  </h2>
                  <p class="text-xs text-slate-400 dark:text-slate-500">
                    Lee con atención antes de comenzar
                  </p>
                </div>
              </div>
              <button @click="showPreview = false"
                class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl transition-colors shrink-0">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Toolbar de lectura -->
            <div class="px-5 py-2.5 border-b border-slate-100 dark:border-slate-700 shrink-0 flex items-center gap-4 flex-wrap">
              <!-- Tema -->
              <div class="flex items-center gap-1.5">
                <span class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mr-0.5">Tema</span>
                <button @click="readingTheme = 'claro'" title="Claro"
                  :class="readingTheme === 'claro' ? 'ring-2 ring-offset-1 ring-slate-400' : 'hover:scale-110'"
                  class="w-5 h-5 rounded-full bg-white border border-slate-300 transition-all" />
                <button @click="readingTheme = 'sepia'" title="Sepia"
                  :class="readingTheme === 'sepia' ? 'ring-2 ring-offset-1 ring-amber-400' : 'hover:scale-110'"
                  class="w-5 h-5 rounded-full bg-amber-50 border border-amber-300 transition-all" />
                <button @click="readingTheme = 'oscuro'" title="Oscuro"
                  :class="readingTheme === 'oscuro' ? 'ring-2 ring-offset-1 ring-slate-500' : 'hover:scale-110'"
                  class="w-5 h-5 rounded-full bg-slate-900 border border-slate-600 transition-all" />
              </div>

              <div class="w-px h-4 bg-slate-200 dark:bg-slate-700" />

              <!-- Tipografía -->
              <div class="flex items-center gap-1.5">
                <span class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide mr-0.5">Fuente</span>
                <button @click="readingFont = 'sans'"
                  :class="readingFont === 'sans'
                    ? 'border-teal-400 bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300'
                    : 'border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-slate-300'"
                  class="px-2.5 py-0.5 rounded-lg border text-xs font-semibold font-sans transition-all">
                  Aa
                </button>
                <button @click="readingFont = 'serif'"
                  :class="readingFont === 'serif'
                    ? 'border-teal-400 bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300'
                    : 'border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-slate-300'"
                  class="px-2.5 py-0.5 rounded-lg border text-xs font-semibold font-serif transition-all">
                  Aa
                </button>
              </div>
            </div>

            <!-- Body -->
            <div class="flex-1 min-h-0 overflow-y-auto">
              <div v-if="loadingPreview" class="flex justify-center py-12">
                <Loader2 class="w-6 h-6 animate-spin text-teal-500" />
              </div>
              <template v-else-if="previewData">
                <!-- Tabs si hay múltiples textos -->
                <div v-if="previewData.lecturas.length > 1"
                  class="flex border-b border-slate-200 dark:border-slate-700 overflow-x-auto shrink-0 bg-white dark:bg-slate-800">
                  <button v-for="(t, i) in previewData.lecturas" :key="i"
                    @click="previewTabActiva = i"
                    :class="[
                      'flex-shrink-0 px-4 py-2.5 text-xs font-semibold transition-colors border-b-2 -mb-px',
                      previewTabActiva === i
                        ? 'border-teal-500 text-teal-600 dark:text-teal-400'
                        : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-200'
                    ]">
                    {{ t.titulo || `Texto ${i + 1}` }}
                  </button>
                </div>
                <div :class="[themeClasses[readingTheme], fontClasses[readingFont]]"
                  class="min-h-full px-5 py-4 transition-colors duration-200">
                  <p v-if="previewData.instrucciones"
                    class="text-xs font-semibold uppercase tracking-wider opacity-50 mb-2">
                    Instrucciones
                  </p>
                  <p v-if="previewData.instrucciones" class="text-sm leading-relaxed opacity-80 mb-5">
                    {{ previewData.instrucciones }}
                  </p>
                  <p v-if="previewData.lecturas[previewTabActiva]?.titulo"
                    class="text-xs font-semibold uppercase tracking-wider opacity-50 mb-3">
                    {{ previewData.lecturas[previewTabActiva]?.titulo }}
                  </p>
                  <p v-else class="text-xs font-semibold uppercase tracking-wider opacity-50 mb-3">
                    {{ previewData.tipo_examen === 'matematica' ? 'Situación problemática' : 'Texto de lectura' }}
                  </p>
                  <p class="text-sm leading-relaxed whitespace-pre-wrap">
                    {{ previewData.lecturas[previewTabActiva]?.texto || 'Sin texto disponible.' }}
                  </p>
                </div>
              </template>
              <div v-else class="flex flex-col items-center justify-center py-12 gap-2 text-center">
                <AlertCircle class="w-8 h-8 text-slate-300 dark:text-slate-600" />
                <p class="text-sm text-slate-400 dark:text-slate-500">No se pudo cargar la vista previa</p>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-5 py-4 border-t border-slate-100 dark:border-slate-700 shrink-0 flex items-center justify-between gap-3">
              <button @click="showPreview = false"
                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
                Cancelar
              </button>
              <button @click="irAlExamen"
                class="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all">
                <BookOpen class="w-4 h-4" />
                Comenzar examen
              </button>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>
