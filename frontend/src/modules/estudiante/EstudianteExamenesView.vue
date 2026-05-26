<script setup lang="ts">
import { formatFechaHoraCorta } from '../../shared/utils/dateUtils'
import { ref, shallowRef, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../../shared/services/api'
import { useTheme } from '../../shared/composables/useTheme'
import EstudianteNavbar from './components/EstudianteNavbar.vue'
import { isSidebarCollapsed } from './composables/useStudentLayout'
import { BookOpen, Loader2, Clock, CheckCircle2, AlertCircle, X, BookText, Calculator, ArrowRight, Zap, Target, ChevronLeft, ChevronRight } from 'lucide-vue-next'

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

type Tab = 'pendientes' | 'pasados'
const activeTab = shallowRef<Tab>('pendientes')

const puedeRendir = (e: AsignacionResumen) =>
  !e.completado || e.mis_intentos < e.intentos_permitidos

const examenesVisibles = computed(() =>
  activeTab.value === 'pendientes'
    ? examenes.value.filter(e => puedeRendir(e))
    : examenes.value.filter(e => !puedeRendir(e))
)

const countPendientes = computed(() => examenes.value.filter(e => puedeRendir(e)).length)
const countPasados   = computed(() => examenes.value.filter(e => !puedeRendir(e)).length)

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
  pre_inicio: 'text-red-500 bg-red-50 dark:bg-red-500/10 border-red-100 dark:border-red-500/20',
  inicio: 'text-orange-500 bg-orange-50 dark:bg-orange-500/10 border-orange-100 dark:border-orange-500/20',
  proceso: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-500/10 border-yellow-100 dark:border-yellow-500/20',
  satisfactorio: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10 border-emerald-100 dark:border-emerald-500/20',
  destacado: 'text-teal-500 bg-teal-50 dark:bg-emerald-500/10 border-teal-100 dark:border-emerald-500/20',
}

const nivelLabels: Record<string, string> = {
  pre_inicio: 'Pre Inicio', inicio: 'Inicio', proceso: 'En Proceso',
  satisfactorio: 'Satisfactorio', destacado: 'Destacado',
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 transition-all duration-300 font-sans"
       :class="isSidebarCollapsed ? 'lg:pl-[84px]' : 'lg:pl-[280px]'">
    
    <!-- Premium Background Elements -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-teal-500/5 dark:bg-emerald-500/10 rounded-full blur-[120px]"></div>
      <div class="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-indigo-500/5 dark:bg-indigo-500/10 rounded-full blur-[100px]"></div>
    </div>

    <!-- Unified Student Navbar -->
    <EstudianteNavbar />

    <!-- Tabs -->
    <div class="sticky top-16 z-30 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 py-4 transition-all duration-300">
      <div class="max-w-4xl mx-auto px-4 sm:px-6">
        <div class="inline-flex p-1 bg-slate-100/80 dark:bg-slate-950/60 backdrop-blur-sm rounded-2xl border border-slate-200 dark:border-slate-800/80 relative w-full sm:w-auto shadow-inner">
          <button
            v-for="tab in [
              { id: 'pendientes' as Tab, label: 'Pendientes', count: countPendientes, icon: Zap },
              { id: 'pasados'    as Tab, label: 'Completados', count: countPasados, icon: CheckCircle2 },
            ]"
            :key="tab.id"
            @click="activeTab = tab.id"
            class="flex-1 sm:flex-initial flex items-center justify-center gap-1.5 sm:gap-2 px-3 py-2 sm:px-5 sm:py-2.5 rounded-xl text-xs sm:text-sm font-bold transition-all duration-300 cursor-pointer relative z-10 select-none"
            :class="activeTab === tab.id
              ? 'text-white shadow-md shadow-teal-500/20 bg-gradient-to-r from-teal-500 to-indigo-600 scale-[1.02] active:scale-[0.98]'
              : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 hover:bg-slate-200/50 dark:hover:bg-slate-800/40 active:scale-[0.98]'"
          >
            <component :is="tab.icon" class="w-3.5 h-3.5 sm:w-4 sm:h-4 transition-transform duration-300" :class="activeTab === tab.id ? 'rotate-12 scale-110' : ''" />
            <span>{{ tab.label }}</span>
            <span
              class="text-[9px] sm:text-[10px] font-black px-1.5 sm:px-2 py-0.5 rounded-full min-w-[18px] sm:min-w-[20px] text-center transition-all duration-300"
              :class="activeTab === tab.id
                ? 'bg-white/20 text-white backdrop-blur-sm'
                : 'bg-slate-200 dark:bg-slate-800/80 text-slate-500 dark:text-slate-400'"
            >{{ tab.count }}</span>
          </button>
        </div>
      </div>
    </div>

    <main class="max-w-4xl mx-auto px-4 sm:px-6 pt-8 pb-12 sm:pb-8 relative">
      <div v-if="loading" class="flex flex-col items-center justify-center py-20 gap-4">
        <Loader2 class="w-10 h-10 animate-spin text-teal-500" />
        <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Cargando exámenes...</p>
      </div>

      <div v-else-if="error" class="text-center py-20 bg-white dark:bg-slate-900 rounded-2xl border border-red-100 dark:border-red-900/30 shadow-xl flex flex-col items-center gap-4">
        <div class="w-16 h-16 rounded-full bg-red-50 dark:bg-red-500/10 flex items-center justify-center">
          <AlertCircle class="w-8 h-8 text-red-500" />
        </div>
        <p class="text-slate-800 dark:text-white font-bold">{{ error }}</p>
        <button @click="router.go(0)" class="text-teal-600 dark:text-emerald-400 font-bold text-sm hover:underline">Reintentar</button>
      </div>

      <!-- Empty state global (sin ningún examen) -->
      <div v-else-if="examenes.length === 0"
        class="text-center py-20 bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 shadow-xl">
        <div class="w-20 h-20 rounded-xl bg-slate-50 dark:bg-slate-800 flex items-center justify-center mx-auto mb-6">
          <BookOpen class="w-10 h-10 text-slate-300 dark:text-slate-600" />
        </div>
        <h3 class="text-xl font-bold text-slate-900 dark:text-white">Sin exámenes asignados</h3>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-2">Tu docente aún no ha publicado evaluaciones para ti.</p>
      </div>

      <template v-else>
        <!-- Empty state por tab -->
        <div v-if="examenesVisibles.length === 0"
          class="text-center py-20 bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 shadow-xl">
          <div class="w-20 h-20 rounded-xl bg-slate-50 dark:bg-slate-800 flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 v-if="activeTab === 'pendientes'" class="w-10 h-10 text-emerald-300 dark:text-emerald-700" />
            <BookOpen v-else class="w-10 h-10 text-slate-300 dark:text-slate-600" />
          </div>
          <h3 class="text-xl font-bold text-slate-900 dark:text-white">
            {{ activeTab === 'pendientes' ? '¡Todo al día!' : 'Aún no has completado exámenes' }}
          </h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-2">
            {{ activeTab === 'pendientes'
              ? 'No tienes evaluaciones pendientes por rendir.'
              : 'Tus exámenes completados aparecerán aquí.' }}
          </p>
        </div>

        <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div
            v-for="examen in examenesVisibles"
          :key="examen.id"
          class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 p-5 sm:p-6 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 flex flex-col group"
        >
          <div class="flex items-start gap-3 sm:gap-4 mb-4 sm:mb-6">
            <div :class="examen.tipo_examen === 'lectura'
              ? 'from-teal-400 to-emerald-500 shadow-teal-500/20'
              : 'from-indigo-400 to-purple-500 shadow-indigo-500/20'"
              class="w-12 h-12 sm:w-14 sm:h-14 rounded-xl bg-gradient-to-br flex items-center justify-center shadow-lg shrink-0 group-hover:scale-105 transition-transform">
              <BookOpen v-if="examen.tipo_examen === 'lectura'" class="w-6 h-6 sm:w-7 sm:h-7 text-white" />
              <Calculator v-else class="w-6 h-6 sm:w-7 sm:h-7 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2 mb-1">
                <span class="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full border border-slate-300 dark:border-slate-800 text-slate-400 dark:text-slate-500">
                  {{ examen.tipo_examen === 'lectura' ? 'Comunicación' : 'Matemática' }}
                </span>
                <span v-if="examen.duracion_minutos" class="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                  <Clock class="w-3 h-3" /> {{ examen.duracion_minutos }}'
                </span>
              </div>
              <h3 class="font-bold text-slate-900 dark:text-white text-base sm:text-lg leading-snug line-clamp-2">{{ examen.titulo }}</h3>
            </div>
          </div>

          <div class="flex-1 space-y-3 mb-6">
            <div class="flex items-center justify-between text-xs font-bold px-1">
              <span class="text-slate-400 dark:text-slate-500 uppercase tracking-widest">Estado</span>
              <div class="flex items-center gap-2">
                <span v-if="examen.completado && examen.nivel_logro"
                  :class="nivelColors[examen.nivel_logro] || 'text-slate-500 bg-slate-50'"
                  class="px-2.5 py-1 rounded-full text-[10px] font-bold border border-transparent uppercase tracking-wider">
                  {{ nivelLabels[examen.nivel_logro] ?? examen.nivel_logro }}
                </span>
                <span v-if="examen.completado"
                  class="inline-flex items-center gap-1 text-emerald-500 font-bold uppercase tracking-widest text-[10px]">
                  <CheckCircle2 class="w-3.5 h-3.5" />
                </span>
                <span v-else class="text-amber-500 font-bold uppercase tracking-widest text-[10px] flex items-center gap-1">
                  <Zap class="w-3.5 h-3.5 fill-amber-500" /> Pendiente
                </span>
              </div>
            </div>

            <div class="bg-slate-50 dark:bg-slate-800/50 rounded-xl p-3.5 sm:p-4 space-y-2">
              <div class="flex justify-between text-[11px] font-medium text-slate-500 dark:text-slate-400">
                <span>Vence:</span>
                <span class="font-bold text-slate-700 dark:text-slate-200">{{ examen.fecha_fin ? formatFechaHoraCorta(examen.fecha_fin) : 'Sin límite' }}</span>
              </div>
              <div class="flex justify-between text-[11px] font-medium text-slate-500 dark:text-slate-400">
                <span>Intentos:</span>
                <span class="font-bold text-slate-700 dark:text-slate-200">{{ examen.mis_intentos }} de {{ examen.intentos_permitidos }}</span>
              </div>
              <div v-if="examen.completado && examen.puntaje != null" class="flex justify-between text-[11px] font-medium text-slate-500 dark:text-slate-400 border-t border-slate-300/50 dark:border-slate-700/50 pt-2">
                <span>Puntaje:</span>
                <span class="font-black text-teal-600 dark:text-emerald-400 text-sm">{{ examen.puntaje.toFixed(1) }}%</span>
              </div>
            </div>
          </div>

          <div class="flex items-center gap-2 sm:gap-3">
            <button @click="abrirPreview(examen)"
              class="w-11 h-11 sm:w-12 sm:h-12 rounded-xl border border-slate-300 dark:border-slate-700 text-slate-400 hover:text-teal-500 hover:border-teal-500 dark:hover:border-emerald-500 transition-all flex items-center justify-center shrink-0"
              title="Previsualizar">
              <BookText class="w-5 h-5" />
            </button>
            <template v-if="!examen.completado || examen.mis_intentos < examen.intentos_permitidos">
              <button @click="router.push(`/estudiante/examen/${examen.id}`)"
                class="flex-1 h-11 sm:h-12 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold text-sm rounded-xl shadow-lg hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2">
                {{ examen.mis_intentos > 0 ? 'Reintentar' : 'Comenzar' }}
                <ArrowRight class="w-4 h-4" />
              </button>
            </template>
            <button v-else @click="router.push(`/estudiante/examen/${examen.id}?modo=resultados`)"
              class="flex-1 h-11 sm:h-12 bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 font-bold text-sm rounded-xl hover:bg-slate-200 dark:hover:bg-slate-700 transition-all flex items-center justify-center gap-2">
              <Target class="w-4 h-4" />
              Resultados
            </button>
          </div>
        </div>
        </div>
      </template>
    </main>

    <!-- Modal Preview Lectura -->
    <Teleport to="body">
      <Transition
        enter-active-class="transition duration-300 ease-out"
        enter-from-class="opacity-0 scale-[0.97]"
        enter-to-class="opacity-100 scale-100"
        leave-active-class="transition duration-200 ease-in"
        leave-from-class="opacity-100 scale-100"
        leave-to-class="opacity-0 scale-[0.97]"
      >
        <div v-if="showPreview" class="fixed inset-0 z-50 flex items-center justify-center p-0 sm:p-4 md:p-6">
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-slate-900/70 backdrop-blur-sm -z-10" @click="showPreview = false"></div>

          <!-- Contenedor modal: pantalla completa en mobile, modal grande en desktop -->
          <div class="bg-white dark:bg-slate-900 w-full h-full sm:h-auto sm:max-h-[90vh] sm:max-w-3xl md:max-w-4xl lg:max-w-5xl flex flex-col sm:rounded-2xl shadow-2xl overflow-hidden">

            <!-- Header -->
            <div class="flex items-center justify-between px-5 sm:px-8 pt-5 sm:pt-6 pb-4 sm:pb-5 border-b border-slate-200 dark:border-slate-800 shrink-0">
              <div class="flex items-center gap-3 sm:gap-4 min-w-0">
                <div class="w-10 h-10 sm:w-12 sm:h-12 rounded-xl flex items-center justify-center shrink-0 shadow-lg"
                  :class="previewData?.tipo_examen === 'matematica'
                    ? 'bg-gradient-to-br from-orange-400 to-amber-500'
                    : 'bg-gradient-to-br from-teal-500 to-indigo-600'">
                  <Calculator v-if="previewData?.tipo_examen === 'matematica'" class="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                  <BookText v-else class="w-5 h-5 sm:w-6 sm:h-6 text-white" />
                </div>
                <div class="min-w-0">
                  <h2 class="text-lg sm:text-xl font-bold text-slate-900 dark:text-white truncate">
                    {{ previewData?.titulo ?? 'Preparación' }}
                  </h2>
                  <p class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mt-0.5">
                    Vista previa
                    <template v-if="(previewData?.lecturas?.length ?? 0) > 1">
                      · {{ previewData!.lecturas.length }} textos
                    </template>
                  </p>
                </div>
              </div>
              <button @click="showPreview = false"
                class="w-9 h-9 sm:w-10 sm:h-10 flex items-center justify-center text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all shrink-0 ml-4">
                <X class="w-5 h-5 sm:w-6 sm:h-6" />
              </button>
            </div>

            <!-- Área principal: sidebar + contenido -->
            <div class="flex-1 min-h-0 flex overflow-hidden">

              <!-- Sidebar de lecturas (desktop, solo cuando hay múltiples) -->
              <div v-if="(previewData?.lecturas?.length ?? 0) > 1"
                class="hidden md:flex w-52 lg:w-60 border-r border-slate-200 dark:border-slate-800 flex-col shrink-0 bg-slate-50 dark:bg-slate-950">
                <p class="px-4 py-3 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest border-b border-slate-200 dark:border-slate-800">
                  Textos
                </p>
                <div class="flex-1 overflow-y-auto py-2">
                  <button
                    v-for="(lectura, i) in previewData!.lecturas"
                    :key="i"
                    @click="previewTabActiva = i"
                    class="w-full text-left px-4 py-3 flex items-start gap-3 transition-all group"
                    :class="previewTabActiva === i
                      ? 'bg-teal-500/10 dark:bg-emerald-500/10'
                      : 'hover:bg-slate-100 dark:hover:bg-slate-800/50'"
                  >
                    <span class="w-6 h-6 rounded-lg flex items-center justify-center text-[11px] font-black shrink-0 mt-0.5 transition-all"
                      :class="previewTabActiva === i
                        ? 'bg-teal-500 text-white'
                        : 'bg-slate-200 dark:bg-slate-700 text-slate-500 dark:text-slate-400 group-hover:bg-slate-300 dark:group-hover:bg-slate-600'">
                      {{ i + 1 }}
                    </span>
                    <span class="text-sm font-semibold leading-snug"
                      :class="previewTabActiva === i
                        ? 'text-teal-700 dark:text-emerald-400'
                        : 'text-slate-600 dark:text-slate-400 group-hover:text-slate-800 dark:group-hover:text-slate-200'">
                      {{ lectura.titulo || `Texto ${i + 1}` }}
                    </span>
                  </button>
                </div>
              </div>

              <!-- Panel derecho: toolbar + contenido scrollable -->
              <div class="flex-1 min-w-0 flex flex-col overflow-hidden">

                <!-- Tabs en mobile (solo cuando hay múltiples lecturas) -->
                <div v-if="(previewData?.lecturas?.length ?? 0) > 1"
                  class="md:hidden flex border-b border-slate-200 dark:border-slate-800 overflow-x-auto no-scrollbar shrink-0 bg-white dark:bg-slate-900">
                  <button v-for="(lectura, i) in previewData!.lecturas" :key="i"
                    @click="previewTabActiva = i"
                    class="flex-shrink-0 px-5 py-3.5 text-[10px] font-bold uppercase tracking-widest transition-all border-b-2"
                    :class="previewTabActiva === i
                      ? 'border-teal-500 text-teal-600 dark:text-emerald-400 bg-teal-500/5'
                      : 'border-transparent text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'">
                    {{ lectura.titulo || `Texto ${i + 1}` }}
                  </button>
                </div>

                <!-- Toolbar -->
                <div class="px-5 sm:px-6 py-2.5 bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-800 shrink-0 flex items-center gap-4 sm:gap-6 overflow-x-auto no-scrollbar">
                  <div class="flex items-center gap-2 shrink-0">
                    <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Tema</span>
                    <div class="flex items-center gap-1.5">
                      <button @click="readingTheme = 'claro'"
                        :class="readingTheme === 'claro' ? 'ring-2 ring-teal-500 scale-110' : 'hover:scale-105'"
                        class="w-5 h-5 rounded-full bg-white border border-slate-300 transition-all shadow-sm" />
                      <button @click="readingTheme = 'sepia'"
                        :class="readingTheme === 'sepia' ? 'ring-2 ring-amber-500 scale-110' : 'hover:scale-105'"
                        class="w-5 h-5 rounded-full bg-amber-50 border border-amber-200 transition-all shadow-sm" />
                      <button @click="readingTheme = 'oscuro'"
                        :class="readingTheme === 'oscuro' ? 'ring-2 ring-slate-400 scale-110' : 'hover:scale-105'"
                        class="w-5 h-5 rounded-full bg-slate-900 border border-slate-700 transition-all shadow-sm" />
                    </div>
                  </div>
                  <div class="w-px h-5 bg-slate-200 dark:bg-slate-700 shrink-0" />
                  <div class="flex items-center gap-2 shrink-0">
                    <span class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Fuente</span>
                    <div class="flex items-center gap-1">
                      <button @click="readingFont = 'sans'"
                        :class="readingFont === 'sans'
                          ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900'
                          : 'bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-300 dark:border-slate-700'"
                        class="px-2.5 py-1 rounded-lg text-xs font-bold transition-all">
                        Sans
                      </button>
                      <button @click="readingFont = 'serif'"
                        :class="readingFont === 'serif'
                          ? 'bg-slate-900 dark:bg-white text-white dark:text-slate-900'
                          : 'bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400 border border-slate-300 dark:border-slate-700'"
                        class="px-2.5 py-1 rounded-lg text-xs font-bold font-serif transition-all">
                        Serif
                      </button>
                    </div>
                  </div>
                  <!-- Dots indicador en mobile -->
                  <div v-if="(previewData?.lecturas?.length ?? 0) > 1" class="md:hidden ml-auto shrink-0 flex items-center gap-1.5">
                    <button v-for="(_, i) in previewData!.lecturas" :key="i"
                      @click="previewTabActiva = i"
                      class="transition-all rounded-full"
                      :class="previewTabActiva === i
                        ? 'w-5 h-2 bg-teal-500'
                        : 'w-2 h-2 bg-slate-300 dark:bg-slate-700 hover:bg-slate-400'" />
                  </div>
                </div>

                <!-- Contenido scrollable con transición entre lecturas -->
                <div class="flex-1 overflow-y-auto">
                  <div v-if="loadingPreview" class="flex flex-col items-center justify-center h-full gap-4 py-20">
                    <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
                    <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Cargando texto...</p>
                  </div>
                  <template v-else-if="previewData">
                    <Transition
                      enter-active-class="transition duration-200 ease-out"
                      enter-from-class="opacity-0 translate-y-2"
                      enter-to-class="opacity-100 translate-y-0"
                      leave-active-class="transition duration-150 ease-in"
                      leave-from-class="opacity-100"
                      leave-to-class="opacity-0"
                      mode="out-in"
                    >
                      <div :key="previewTabActiva" :class="[themeClasses[readingTheme], fontClasses[readingFont]]"
                        class="min-h-full px-5 sm:px-10 py-6 sm:py-10 transition-colors duration-200">
                        <div v-if="previewData.instrucciones" class="mb-6 p-4 sm:p-5 bg-black/5 dark:bg-white/5 rounded-xl border-l-4 border-teal-500">
                          <p class="text-[10px] font-bold uppercase tracking-widest mb-2 opacity-50">Instrucciones</p>
                          <p class="text-sm leading-relaxed">{{ previewData.instrucciones }}</p>
                        </div>
                        <h3 v-if="previewData.lecturas[previewTabActiva]?.titulo" class="text-xl font-bold mb-6">
                          {{ previewData.lecturas[previewTabActiva]?.titulo }}
                        </h3>
                        <div class="text-base leading-loose whitespace-pre-wrap">
                          {{ previewData.lecturas[previewTabActiva]?.texto || 'Sin texto disponible.' }}
                        </div>
                      </div>
                    </Transition>
                  </template>
                  <div v-else class="flex flex-col items-center justify-center h-full gap-4 py-20 text-center px-6">
                    <AlertCircle class="w-12 h-12 text-slate-200 dark:text-slate-700" />
                    <p class="text-sm font-bold text-slate-400">No se pudo cargar el contenido</p>
                  </div>
                </div>

              </div>
            </div>

            <!-- Footer -->
            <div class="px-5 sm:px-8 py-4 border-t border-slate-200 dark:border-slate-800 shrink-0 flex items-center justify-between bg-white dark:bg-slate-900">
              <!-- Navegación anterior/siguiente entre lecturas -->
              <div v-if="(previewData?.lecturas?.length ?? 0) > 1" class="flex items-center gap-2">
                <button
                  :disabled="previewTabActiva === 0"
                  @click="previewTabActiva = Math.max(0, previewTabActiva - 1)"
                  class="h-9 px-3 text-xs font-bold text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1">
                  <ChevronLeft class="w-4 h-4" />
                  <span class="hidden sm:inline">Anterior</span>
                </button>
                <span class="text-xs font-bold text-slate-400 dark:text-slate-500 tabular-nums">
                  {{ previewTabActiva + 1 }} / {{ previewData!.lecturas.length }}
                </span>
                <button
                  :disabled="previewTabActiva === (previewData!.lecturas.length - 1)"
                  @click="previewTabActiva = Math.min(previewData!.lecturas.length - 1, previewTabActiva + 1)"
                  class="h-9 px-3 text-xs font-bold text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-all disabled:opacity-30 disabled:cursor-not-allowed flex items-center gap-1">
                  <span class="hidden sm:inline">Siguiente</span>
                  <ChevronRight class="w-4 h-4" />
                </button>
              </div>
              <div v-else />
              <button @click="showPreview = false"
                class="h-9 px-5 text-sm font-bold text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all">
                Cerrar
              </button>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
.no-scrollbar::-webkit-scrollbar { display: none; }
.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
