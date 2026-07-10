<script setup lang="ts">
import { construirFechaISO, extraerFechaHora, formatFechaHora } from '../../shared/utils/dateUtils'
import { ref, shallowRef, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient, asignacionesService, examenesService, organizacionService, codigosClaseService } from '../../shared/services/api'
import type { UpdateAsignacionPayload, CodigoClase } from '../../shared/services/api'
import Header from '../../shared/components/Header.vue'
import Footer from '../../shared/components/Footer.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import Swal from 'sweetalert2'
import { Toast } from '../../shared/utils/swal'
import {
  ClipboardList, BookOpen, Calculator,
  Loader2, Users, ChevronDown,
  Clock, AlertCircle, Plus, X, BookMarked, Save, User, Pencil,
  RefreshCw, TrendingUp, GraduationCap, Calendar, ShieldCheck, Hash, Check,
  LayoutGrid, LayoutList
} from 'lucide-vue-next'
import type { Grado } from '../../shared/types'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const vistaIE = computed(() => auth.isDirector || auth.isAuxiliar)
const vistaUGEL = computed(() => auth.isResponsableUGEL)
const headerTitle = computed(() => {
  if (vistaIE.value) return 'Asignaciones de la Institución'
  if (vistaUGEL.value) return 'Asignaciones de la UGEL'
  return 'Mis Asignaciones'
})

interface Asignacion {
  id: number
  tipo_examen: 'lectura' | 'matematica'
  titulo: string | null
  grado_id: number
  grado_nombre: string | null
  seccion: string | null
  fecha_inicio: string | null
  fecha_fin: string | null
  duracion_minutos: number | null
  intentos_permitidos: number
  mezclar_preguntas: boolean
  mezclar_alternativas: boolean
  is_active: boolean
  completados: number
  fecha_creacion: string | null
  asignado_por_id: number | null
  asignado_por_nombre: string | null
  puede_eliminar: boolean
}

interface Resultado {
  estudiante: string
  codigo: string | null
  estado: string
  puntaje: number | null
  nivel_logro: string | null
  correctas: number | null
  total: number | null
  fecha: string | null
}

interface ExamenItem {
  id: number
  titulo: string | null
  grado_nombre: string | null
  fecha_creacion: string
}

const asignaciones = ref<Asignacion[]>([])
const loading = ref(true)
const error = ref('')
const resultados = ref<Record<number, Resultado[]>>({})
const loadingToggle = ref<number | null>(null)
const viewMode = ref<'cards' | 'table'>(
  (localStorage.getItem('asignaciones_view') as 'cards' | 'table') ?? 'cards'
)
function setViewMode(mode: 'cards' | 'table') {
  viewMode.value = mode
  localStorage.setItem('asignaciones_view', mode)
}

// Modal resultados
const showResultados = shallowRef(false)
const resultadosAsig = ref<Asignacion | null>(null)
const loadingResultados = shallowRef(false)
const editingId = shallowRef<number | null>(null)
const isEditing = computed(() => editingId.value !== null)

// Modal nueva asignación
const showModal = ref(false)
const saving = ref(false)
const modalError = ref('')

// Datos para el formulario
const tipoExamen = ref<'lectura' | 'matematica'>('lectura')
const examenesLectura = ref<ExamenItem[]>([])
const examenesMatematica = ref<ExamenItem[]>([])
const grados = ref<Grado[]>([])
const codigosClase = ref<CodigoClase[]>([])
const loadingExamenes = ref(false)

const examenSeleccionadoId = ref<number | null>(null)
const examenDropdownOpen = shallowRef(false)
const examenSeleccionado = computed(() =>
  examenesActuales.value.find(ex => ex.id === examenSeleccionadoId.value) ?? null
)
const codigoClaseId = ref<number | null>(null)
const claseDropdownOpen = shallowRef(false)
const gradoSeleccionadoId = ref<number | null>(null)
const gradoDropdownOpen = shallowRef(false)
const seccion = ref('')
const seccionDropdownOpen = shallowRef(false)

// Para docentes: usa codigos_clase; para roles superiores: usa grado+sección libres
const usarCodigosClase = computed(() => auth.isDocente || auth.isAuxiliar)
const codigoClaseSeleccionado = computed(() =>
  codigosClase.value.find(c => c.id === codigoClaseId.value) ?? null
)
const gradoSeleccionado = computed(() =>
  grados.value.find(g => g.id === gradoSeleccionadoId.value) ?? null
)
const fechaAplicacion = ref('')
const horaInicio = ref('')
const horaFin = ref('')
const intentosPermitidos = ref(1)
const mezclarPreguntas = ref(true)
const mezclarAlternativas = ref(true)

const examenesActuales = computed(() =>
  tipoExamen.value === 'lectura' ? examenesLectura.value : examenesMatematica.value
)

const duracionVentanaMinutos = computed(() => {
  if (!horaInicio.value || !horaFin.value) return null
  const [h1, m1] = horaInicio.value.split(':').map(Number) as [number, number]
  const [h2, m2] = horaFin.value.split(':').map(Number) as [number, number]
  let minutos = (h2 * 60 + m2) - (h1 * 60 + m1)
  if (minutos < 0) minutos += 24 * 60
  return minutos
})

const duracionVentanaTexto = computed(() => {
  const min = duracionVentanaMinutos.value
  if (min === null) return null
  const horas = Math.floor(min / 60)
  const mins = min % 60
  if (horas === 0) return `${mins} min`
  if (mins === 0) return `${horas} h`
  return `${horas} h ${mins} min`
})

async function fetchAsignaciones() {
  loading.value = true
  error.value = ''
  try {
    const res = await apiClient.get('/examenes/asignaciones')
    asignaciones.value = res.data
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar asignaciones'
  } finally {
    loading.value = false
  }
}

function closeModal() {
  showModal.value = false
  editingId.value = null
  examenDropdownOpen.value = false
  claseDropdownOpen.value = false
  gradoDropdownOpen.value = false
  seccionDropdownOpen.value = false
}

// extraerFechaHora importado de shared/utils/dateUtils

function openEditModal(asig: Asignacion) {
  editingId.value = asig.id
  modalError.value = ''
  const inicio = extraerFechaHora(asig.fecha_inicio)
  const fin = extraerFechaHora(asig.fecha_fin)
  fechaAplicacion.value = inicio.date
  horaInicio.value = inicio.time
  horaFin.value = fin.time
  intentosPermitidos.value = asig.intentos_permitidos
  mezclarPreguntas.value = asig.mezclar_preguntas
  mezclarAlternativas.value = asig.mezclar_alternativas
  showModal.value = true
}

async function openModal() {
  editingId.value = null
  modalError.value = ''
  examenSeleccionadoId.value = null
  codigoClaseId.value = null
  gradoSeleccionadoId.value = null
  seccion.value = ''
  fechaAplicacion.value = ''
  horaInicio.value = ''
  horaFin.value = ''
  intentosPermitidos.value = 1
  mezclarPreguntas.value = true
  mezclarAlternativas.value = true
  tipoExamen.value = 'lectura'

  showModal.value = true
  loadingExamenes.value = true
  try {
    const fetches: Promise<any>[] = [
      examenesService.getExamenesLectura(),
      examenesService.getExamenesMatematica(),
    ]
    if (usarCodigosClase.value) {
      fetches.push(codigosClaseService.getAll())
    } else {
      fetches.push(organizacionService.getGrados())
    }
    const [lec, mat, extra] = await Promise.all(fetches)
    examenesLectura.value = lec
    examenesMatematica.value = mat
    if (usarCodigosClase.value) {
      codigosClase.value = (extra as CodigoClase[]).filter(c => c.is_active)
    } else {
      grados.value = extra
    }
  } catch {
    modalError.value = 'Error al cargar datos'
  } finally {
    loadingExamenes.value = false
  }
}

// construirFechaISO importado de shared/utils/dateUtils

async function guardar() {
  modalError.value = ''
  if ((fechaAplicacion.value || horaInicio.value || horaFin.value)
    && (!fechaAplicacion.value || !horaInicio.value || !horaFin.value)) {
    modalError.value = 'Completa el día, la hora de inicio y la hora de fin'
    return
  }

  if (isEditing.value) {
    saving.value = true
    try {
      await asignacionesService.updateAsignacion(editingId.value!, {
        fecha_inicio: construirFechaISO(fechaAplicacion.value, horaInicio.value),
        fecha_fin: construirFechaISO(fechaAplicacion.value, horaFin.value),
        intentos_permitidos: intentosPermitidos.value,
        mezclar_preguntas: mezclarPreguntas.value,
        mezclar_alternativas: mezclarAlternativas.value,
        is_active: true,
      } satisfies UpdateAsignacionPayload)
      closeModal()
      await fetchAsignaciones()
      Toast.fire({ icon: 'success', title: 'Asignación actualizada' })
    } catch (e: any) {
      modalError.value = e.response?.data?.detail ?? 'Error al actualizar'
    } finally {
      saving.value = false
    }
    return
  }

  if (!examenSeleccionadoId.value) {
    modalError.value = 'Selecciona un examen'
    return
  }
  saving.value = true
  try {
    const payload: any = {
      tipo_examen: tipoExamen.value,
      examen_id: examenSeleccionadoId.value,
      fecha_inicio: construirFechaISO(fechaAplicacion.value, horaInicio.value),
      fecha_fin: construirFechaISO(fechaAplicacion.value, horaFin.value),
      intentos_permitidos: intentosPermitidos.value,
      mezclar_preguntas: mezclarPreguntas.value,
      mezclar_alternativas: mezclarAlternativas.value,
    }
    if (usarCodigosClase.value) {
      payload.codigo_clase_id = codigoClaseId.value
    } else {
      payload.grado_id = gradoSeleccionadoId.value ?? undefined
      payload.seccion = seccion.value.trim() || null
    }
    await asignacionesService.asignar(payload)
    closeModal()
    await fetchAsignaciones()
    Toast.fire({ icon: 'success', title: 'Examen asignado correctamente' })
  } catch (e: any) {
    modalError.value = e.response?.data?.detail ?? 'Error al asignar'
  } finally {
    saving.value = false
  }
}

async function openResultados(asig: Asignacion) {
  resultadosAsig.value = asig
  showResultados.value = true
  if (!resultados.value[asig.id]) {
    loadingResultados.value = true
    try {
      const data = await asignacionesService.getResultados(asig.id)
      resultados.value[asig.id] = data
    } catch {
      resultados.value[asig.id] = []
    } finally {
      loadingResultados.value = false
    }
  }
}

async function toggle(asig: Asignacion) {
  const accion = asig.is_active ? 'desactivar' : 'activar'
  const result = await Swal.fire({
    title: asig.is_active ? '¿Desactivar asignación?' : '¿Activar asignación?',
    html: asig.is_active
      ? 'Los estudiantes no podrán iniciar ni continuar este examen.'
      : 'Los estudiantes podrán acceder nuevamente a este examen.',
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: asig.is_active ? '#64748b' : '#7c3aed',
    confirmButtonText: asig.is_active ? 'Desactivar' : 'Activar',
    cancelButtonText: 'Cancelar',
  })
  if (!result.isConfirmed) return
  loadingToggle.value = asig.id
  try {
    const { is_active } = await asignacionesService.toggleActive(asig.id)
    asig.is_active = is_active
  } catch (e: any) {
    Toast.fire({ icon: 'error', title: e.response?.data?.detail ?? `Error al ${accion}` })
  } finally {
    loadingToggle.value = null
  }
}

onMounted(fetchAsignaciones)

// formatFechaHora importado de shared/utils/dateUtils

const nivelColors: Record<string, string> = {
  pre_inicio: 'text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400',
  inicio: 'text-orange-600 bg-orange-50 dark:bg-orange-900/20 dark:text-orange-400',
  proceso: 'text-yellow-700 bg-yellow-50 dark:bg-yellow-900/20 dark:text-yellow-400',
  satisfactorio: 'text-green-600 bg-green-50 dark:bg-green-900/20 dark:text-green-400',
  destacado: 'text-teal-600 bg-teal-50 dark:bg-teal-900/20 dark:text-teal-400',
}
const nivelLabels: Record<string, string> = {
  pre_inicio: 'Pre Inicio', inicio: 'Inicio', proceso: 'En Proceso',
  satisfactorio: 'Satisfactorio', destacado: 'Destacado',
}

const estadoLabels: Record<string, string> = {
  sin_intento: 'Sin intento',
  en_progreso: 'En progreso',
  completado: 'Completado',
}

const estadoColors: Record<string, string> = {
  sin_intento: 'text-slate-600 bg-slate-100 dark:bg-slate-700 dark:text-slate-300',
  en_progreso: 'text-amber-700 bg-amber-50 dark:bg-amber-900/20 dark:text-amber-300',
  completado: 'text-emerald-700 bg-emerald-50 dark:bg-emerald-900/20 dark:text-emerald-300',
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-violet-50/20 to-indigo-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-colors">
    <EduBackground />
    <Header :title="headerTitle" subtitle="Exámenes asignados a estudiantes" :show-home="true" />

    <main class="flex-1 w-full max-w-6xl mx-auto px-4 sm:px-6 py-6 md:py-10 space-y-6 md:space-y-10 relative z-10">

      <!-- Header & Welcome -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <div class="flex items-center gap-2 text-violet-600 dark:text-violet-400 font-bold text-sm tracking-wider uppercase">
            <ClipboardList class="w-4 h-4" />
            <span>Gestión de Evaluaciones</span>
          </div>
          <h2 class="text-3xl md:text-4xl font-black text-slate-800 dark:text-white tracking-tight">
            {{ headerTitle }}
          </h2>
          <p class="text-slate-500 dark:text-slate-400 text-sm md:text-base max-w-2xl">
            {{ asignaciones.length }} asignación(es) activas en el sistema.
          </p>
        </div>
        <div class="flex items-center gap-3">
          <div class="flex items-center bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-2xl p-1 shadow-sm">
            <button @click="setViewMode('cards')" title="Vista cards"
              class="p-2.5 rounded-xl transition-all"
              :class="viewMode === 'cards' ? 'bg-violet-100 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'">
              <LayoutGrid class="w-4 h-4" />
            </button>
            <button @click="setViewMode('table')" title="Vista tabla"
              class="p-2.5 rounded-xl transition-all"
              :class="viewMode === 'table' ? 'bg-violet-100 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400' : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-300'">
              <LayoutList class="w-4 h-4" />
            </button>
          </div>
          <button @click="openModal"
            class="group flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-violet-600 to-indigo-700 hover:from-violet-700 hover:to-indigo-800 text-white font-bold text-sm rounded-2xl shadow-xl shadow-violet-500/20 hover:-translate-y-0.5 transition-all active:scale-95 cursor-pointer">
            <Plus class="w-5 h-5 group-hover:rotate-90 transition-transform duration-300" />
            <span>Nueva Asignación</span>
          </button>
        </div>
      </div>

      <!-- Error -->
      <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="transform -translate-y-4 opacity-0" enter-to-class="transform translate-y-0 opacity-100">
        <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-2xl p-5 text-red-600 dark:text-red-400 text-sm flex items-center justify-between shadow-lg">
          <span class="flex items-center gap-3 font-medium">
            <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div> 
            {{ error }}
          </span>
          <button @click="fetchAsignaciones" class="px-4 py-1.5 bg-red-100 dark:bg-red-500/20 rounded-xl font-bold hover:bg-red-200 dark:hover:bg-red-500/30 transition-colors cursor-pointer">
            Reintentar
          </button>
        </div>
      </Transition>

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-24">
        <div class="relative w-16 h-16">
          <div class="absolute inset-0 rounded-full border-4 border-slate-300 dark:border-slate-800"></div>
          <div class="absolute inset-0 rounded-full border-4 border-violet-500 border-t-transparent animate-spin"></div>
        </div>
        <p class="mt-4 text-sm font-bold text-slate-400 dark:text-slate-500 tracking-widest uppercase">Sincronizando Asignaciones</p>
      </div>

      <!-- Empty -->
      <div v-else-if="asignaciones.length === 0"
        class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 p-12 text-center shadow-sm group">
        <div class="w-24 h-24 bg-slate-50 dark:bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-500">
           <ClipboardList class="w-12 h-12 text-slate-300 dark:text-slate-600" />
        </div>
        <h3 class="text-2xl font-black text-slate-800 dark:text-white mb-2 tracking-tight">Sin asignaciones aún</h3>
        <p class="text-sm text-slate-500 dark:text-slate-400 mb-8 max-w-sm mx-auto">
          Comienza asignando uno de tus exámenes generados a un grado o sección específica.
        </p>
        <button @click="openModal"
          class="inline-flex items-center gap-2 px-8 py-4 bg-gradient-to-r from-violet-500 to-indigo-600 text-white font-black text-sm rounded-2xl shadow-xl shadow-violet-500/20 hover:from-violet-600 hover:to-indigo-700 transition-all active:scale-95 cursor-pointer">
          <Plus class="w-5 h-5" />
          <span>Crear Primera Asignación</span>
        </button>
      </div>

      <!-- Cards -->
      <div v-else-if="viewMode === 'cards'" class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
        <div v-for="asig in asignaciones" :key="asig.id"
          class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 p-5 shadow-sm hover:shadow-xl hover:shadow-violet-500/5 transition-all duration-300 relative group overflow-hidden flex flex-col"
          :class="!asig.is_active ? 'opacity-50' : ''">

          <div class="absolute -right-6 -top-6 w-24 h-24 bg-violet-500/5 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700"></div>

          <!-- Top: icon + badges -->
          <div class="flex items-center gap-3 mb-4 relative z-10">
            <div :class="asig.tipo_examen === 'lectura'
              ? 'bg-teal-50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400'
              : 'bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400'"
              class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 group-hover:rotate-6 transition-transform shadow-inner">
              <BookOpen v-if="asig.tipo_examen === 'lectura'" class="w-6 h-6" />
              <Calculator v-else class="w-6 h-6" />
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span :class="asig.tipo_examen === 'lectura' ? 'text-teal-500 bg-teal-500/10' : 'text-indigo-500 bg-indigo-500/10'"
                class="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded-full">
                {{ asig.tipo_examen === 'lectura' ? 'LectoSistem' : 'MatSistem' }}
              </span>
              <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest bg-slate-100 dark:bg-slate-800 px-2 py-0.5 rounded-full">
                {{ asig.completados }} rindiendo
              </span>
            </div>
          </div>

          <!-- Title -->
          <h3 class="text-base font-black text-slate-800 dark:text-white leading-tight mb-1.5 line-clamp-2 relative z-10">
            {{ asig.titulo ?? (asig.tipo_examen === 'lectura' ? 'Examen de Comunicación' : 'Examen de Matemática') }}
          </h3>

          <!-- Grade/Section -->
          <div class="flex items-center gap-1.5 text-sm font-bold mb-3 relative z-10">
            <span class="text-violet-600 dark:text-violet-400">{{ asig.grado_nombre ?? `Grado ${asig.grado_id}` }}</span>
            <span v-if="asig.seccion" class="text-slate-400">· Secc. {{ asig.seccion }}</span>
          </div>

          <!-- Metadata -->
          <div class="space-y-1.5 flex-1 relative z-10">
            <div v-if="asig.duracion_minutos" class="flex items-center gap-2 text-xs font-bold text-slate-400">
              <Clock class="w-3.5 h-3.5 text-violet-400 shrink-0" />
              <span>{{ asig.duracion_minutos }} min.</span>
            </div>
            <div v-if="asig.fecha_fin" class="flex items-center gap-2 text-xs font-bold text-slate-400">
              <AlertCircle class="w-3.5 h-3.5 text-amber-400 shrink-0" />
              <span class="truncate">{{ formatFechaHora(asig.fecha_inicio) }} – {{ formatFechaHora(asig.fecha_fin) }}</span>
            </div>
            <div v-if="asig.asignado_por_nombre" class="flex items-center gap-2 text-xs font-bold text-slate-400">
              <User class="w-3.5 h-3.5 text-indigo-400 shrink-0" />
              <span class="truncate">{{ asig.asignado_por_nombre }}</span>
            </div>
          </div>

          <!-- Actions -->
          <div class="flex items-center gap-2 pt-4 mt-4 border-t border-slate-100 dark:border-slate-800 relative z-10">
            <button @click="openResultados(asig)"
              class="flex-1 flex items-center justify-center gap-2 px-3 py-2.5 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold text-xs rounded-xl transition-all active:scale-95 border border-slate-200 dark:border-slate-700 cursor-pointer">
              <Users class="w-4 h-4" />
              <span>Reporte</span>
            </button>
            <button v-if="asig.puede_eliminar" @click="openEditModal(asig)"
              class="p-2.5 bg-violet-50 dark:bg-violet-950/40 text-violet-600 dark:text-violet-400 rounded-xl hover:bg-violet-600 hover:text-white transition-all active:scale-95 border border-violet-100 dark:border-violet-900/50 cursor-pointer"
              title="Editar">
              <Pencil class="w-4 h-4" />
            </button>
            <button v-if="asig.puede_eliminar" @click="toggle(asig)" :disabled="loadingToggle === asig.id"
              title="Activar / Desactivar"
              class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none disabled:opacity-40"
              :class="asig.is_active ? 'bg-violet-500' : 'bg-slate-300 dark:bg-slate-600'">
              <Loader2 v-if="loadingToggle === asig.id" class="w-3 h-3 text-white absolute left-1/2 -translate-x-1/2 animate-spin" />
              <span v-else class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200"
                :class="asig.is_active ? 'translate-x-6' : 'translate-x-1'" />
            </button>
          </div>
        </div>
      </div>

      <!-- Table -->
      <div v-else-if="viewMode === 'table'" class="bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 shadow-sm overflow-hidden">
          <table class="w-full border-collapse text-sm table-fixed">
            <colgroup>
              <col class="w-[33%]" />
              <col class="w-[15%]" />
              <col class="w-[26%]" />
              <col class="w-[10%]" />
              <col class="w-[16%]" />
            </colgroup>
            <thead>
              <tr class="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-700">
                <th class="px-4 py-3 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Examen</th>
                <th class="px-4 py-3 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Destino</th>
                <th class="px-4 py-3 text-left text-[10px] font-black text-slate-400 uppercase tracking-widest">Horario</th>
                <th class="px-4 py-3 text-center text-[10px] font-black text-slate-400 uppercase tracking-widest">Estado</th>
                <th class="px-4 py-3 text-right text-[10px] font-black text-slate-400 uppercase tracking-widest">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
              <tr v-for="asig in asignaciones" :key="asig.id"
                class="hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                :class="!asig.is_active ? 'opacity-50' : ''">
                <td class="px-4 py-3">
                  <div class="flex items-center gap-2.5 min-w-0">
                    <div :class="asig.tipo_examen === 'lectura' ? 'bg-teal-50 dark:bg-teal-900/30 text-teal-600' : 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600'"
                      class="w-7 h-7 rounded-lg flex items-center justify-center shrink-0">
                      <BookOpen v-if="asig.tipo_examen === 'lectura'" class="w-3.5 h-3.5" />
                      <Calculator v-else class="w-3.5 h-3.5" />
                    </div>
                    <div class="min-w-0">
                      <p class="font-black text-slate-800 dark:text-white truncate text-xs leading-tight">
                        {{ asig.titulo ?? (asig.tipo_examen === 'lectura' ? 'Examen de Comunicación' : 'Examen de Matemática') }}
                      </p>
                      <span :class="asig.tipo_examen === 'lectura' ? 'text-teal-500' : 'text-indigo-500'"
                        class="text-[9px] font-black uppercase tracking-widest">
                        {{ asig.tipo_examen === 'lectura' ? 'LectoSistem' : 'MatSistem' }}
                      </span>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <p class="font-bold text-xs text-violet-600 dark:text-violet-400 truncate">{{ asig.grado_nombre ?? `Grado ${asig.grado_id}` }}</p>
                  <p v-if="asig.seccion" class="text-[10px] font-bold text-slate-400">Secc. {{ asig.seccion }}</p>
                </td>
                <td class="px-4 py-3">
                  <span v-if="asig.fecha_inicio" class="text-[10px] font-bold text-slate-500 dark:text-slate-400 leading-relaxed">
                    {{ formatFechaHora(asig.fecha_inicio) }}<br/>{{ formatFechaHora(asig.fecha_fin) }}
                  </span>
                  <span v-else class="text-xs text-slate-400">—</span>
                </td>
                <td class="px-4 py-3 text-center">
                  <span :class="asig.is_active ? 'bg-emerald-50 dark:bg-emerald-900/20 text-emerald-700 dark:text-emerald-400' : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'"
                    class="text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded-full whitespace-nowrap">
                    {{ asig.is_active ? 'Activa' : 'Inactiva' }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <div class="flex items-center justify-end gap-1.5">
                    <button @click="openResultados(asig)" title="Ver resultados"
                      class="p-1.5 rounded-lg text-slate-400 hover:text-violet-600 hover:bg-violet-50 dark:hover:bg-violet-900/20 transition-all">
                      <Users class="w-4 h-4" />
                    </button>
                    <button v-if="asig.puede_eliminar" @click="openEditModal(asig)" title="Editar"
                      class="p-1.5 rounded-lg text-slate-400 hover:text-violet-600 hover:bg-violet-50 dark:hover:bg-violet-900/20 transition-all">
                      <Pencil class="w-4 h-4" />
                    </button>
                    <button v-if="asig.puede_eliminar" @click="toggle(asig)" :disabled="loadingToggle === asig.id"
                      title="Activar / Desactivar"
                      class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 focus:outline-none disabled:opacity-40 shrink-0"
                      :class="asig.is_active ? 'bg-violet-500' : 'bg-slate-300 dark:bg-slate-600'">
                      <Loader2 v-if="loadingToggle === asig.id" class="w-3 h-3 text-white absolute left-1/2 -translate-x-1/2 animate-spin" />
                      <span v-else class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200"
                        :class="asig.is_active ? 'translate-x-6' : 'translate-x-1'" />
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
      </div>

    </main>

    <Footer />

    <!-- Modal Nueva Asignación: Premium Bottom Sheet pattern -->
    <Teleport to="body">
      <Transition name="details-modal">
        <div v-if="showModal"
          class="fixed inset-0 z-[120] flex items-end sm:items-center justify-center sm:p-4">
          
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm transition-opacity cursor-pointer" @click="closeModal()"></div>

          <div class="relative bg-white dark:bg-slate-900 w-full sm:max-w-2xl max-h-[94dvh] sm:max-h-[85vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10 animate-slide-up">
            
            <!-- Drag handle mobile -->
            <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0 cursor-pointer" @click="closeModal()">
                <div class="w-10 h-1.5 rounded-full bg-slate-200 dark:bg-slate-800"></div>
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between px-8 py-6 border-b border-slate-300 dark:border-slate-800 shrink-0">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-violet-500/20">
                  <BookMarked class="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 class="text-xl font-black text-slate-800 dark:text-white tracking-tight">
                    {{ isEditing ? 'Ajustar Evaluación' : 'Asignar Nueva Evaluación' }}
                  </h2>
                  <p class="text-xs font-bold text-slate-500 dark:text-slate-400">Configuración de acceso y aleatoriedad</p>
                </div>
              </div>
              <button @click="closeModal()" class="p-3 bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-2xl transition-all cursor-pointer">
                <X class="w-6 h-6" />
              </button>
            </div>

            <!-- Body -->
            <div class="flex-1 min-h-0 overflow-y-auto p-0 custom-scrollbar bg-slate-50/30 dark:bg-slate-900/10">

              <div class="p-8 space-y-10">

                <!-- SECCIÓN 1: EVALUACIÓN (Solo en creación) -->
                <section v-if="!isEditing" class="space-y-6">
                  <div class="flex items-center gap-3 mb-2">
                    <div class="w-8 h-8 rounded-lg bg-violet-100 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400 flex items-center justify-center">
                      <BookMarked class="w-4 h-4" />
                    </div>
                    <h3 class="text-sm font-black text-slate-800 dark:text-white uppercase tracking-wider">Detalles de la Evaluación</h3>
                  </div>

                  <div class="space-y-4">
                    <!-- Área -->
                    <div class="space-y-3">
                      <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Área Académica</label>
                      <div class="flex gap-2">
                        <button type="button" @click="tipoExamen = 'lectura'; examenSeleccionadoId = null; examenDropdownOpen = false"
                          :class="['flex-1 flex items-center gap-2 p-2.5 rounded-xl border transition-all group cursor-pointer',
                            tipoExamen === 'lectura'
                              ? 'bg-white dark:bg-teal-500/10 border-teal-500 text-teal-700 dark:text-teal-400 shadow-md'
                              : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 text-slate-400 hover:border-slate-400']">
                          <BookOpen class="w-3.5 h-3.5 transition-transform" /> 
                          <span class="text-[10px] font-black uppercase">Comunicación</span>
                        </button>
                        <button type="button" @click="tipoExamen = 'matematica'; examenSeleccionadoId = null; examenDropdownOpen = false"
                          :class="['flex-1 flex items-center gap-2 p-2.5 rounded-xl border transition-all group cursor-pointer',
                            tipoExamen === 'matematica'
                              ? 'bg-white dark:bg-indigo-500/10 border-indigo-500 text-indigo-700 dark:text-indigo-400 shadow-md'
                              : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 text-slate-400 hover:border-slate-400']">
                          <Calculator class="w-3.5 h-3.5 transition-transform" /> 
                          <span class="text-[10px] font-black uppercase">Matemática</span>
                        </button>
                      </div>
                    </div>

                    <!-- Instrumento -->
                    <div class="space-y-3">
                      <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Instrumento a aplicar</label>
                      <div v-if="loadingExamenes" class="flex items-center gap-3 p-2.5 bg-white dark:bg-slate-800 rounded-lg border-2 border-slate-100 dark:border-slate-700">
                        <Loader2 class="w-3.5 h-3.5 animate-spin text-violet-500" />
                        <span class="text-[10px] font-bold text-slate-400">Cargando instrumentos...</span>
                      </div>
                      <div v-else-if="examenesActuales.length === 0"
                        class="p-2.5 bg-amber-50 dark:bg-amber-500/5 rounded-lg border-2 border-dashed border-amber-200 dark:border-amber-500/20 flex items-center justify-between">
                        <p class="text-[10px] font-bold text-amber-700 dark:text-amber-400">Sin instrumentos.</p>
                        <button @click="router.push(tipoExamen === 'lectura' ? '/lectosistem' : '/matsistem'); closeModal()"
                          class="text-amber-600 dark:text-amber-500 font-black text-[8px] uppercase tracking-widest hover:underline">
                          Crear →
                        </button>
                      </div>
                      <div v-else class="relative">
                        <button type="button" @click="examenDropdownOpen = !examenDropdownOpen"
                          :class="[
                            'w-full flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl border transition-all text-left bg-slate-50 dark:bg-slate-700 cursor-pointer',
                            examenDropdownOpen
                              ? 'border-violet-500 ring-4 ring-violet-500/10 shadow-lg'
                              : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500'
                          ]">
                          <div v-if="examenSeleccionado" class="min-w-0">
                            <p class="text-xs font-black text-slate-800 dark:text-white truncate leading-tight">{{ examenSeleccionado.titulo ?? 'Sin título' }}</p>
                            <p class="text-[9px] font-bold text-slate-400 flex items-center gap-1.5 mt-0.5">
                              <span>{{ examenSeleccionado.grado_nombre }}</span>
                            </p>
                          </div>
                          <span v-else class="text-slate-400 text-xs font-bold">— Seleccionar instrumento —</span>
                          <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-300" :class="examenDropdownOpen ? 'rotate-180' : ''" />
                        </button>

                        <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
                          leave-active-class="transition duration-150 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                          <div v-if="examenDropdownOpen"
                            class="absolute z-[130] left-0 right-0 top-full mt-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95">
                            <div class="max-h-60 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700 custom-scrollbar">
                              <button v-for="ex in examenesActuales" :key="ex.id" type="button"
                                @click="examenSeleccionadoId = ex.id; examenDropdownOpen = false"
                                class="w-full text-left p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-4 group cursor-pointer">
                                <div :class="examenSeleccionadoId === ex.id ? 'bg-violet-500' : 'bg-slate-200 dark:bg-slate-700'" class="w-2 h-10 rounded-full shrink-0 transition-colors"></div>
                                <div class="min-w-0">
                                  <p class="text-sm font-black text-slate-800 dark:text-white truncate">{{ ex.titulo ?? 'Sin título' }}</p>
                                  <p class="text-[10px] font-bold text-slate-400 mt-1 uppercase">{{ ex.grado_nombre }} · {{ formatFechaHora(ex.fecha_creacion) }}</p>
                                </div>
                              </button>
                            </div>
                          </div>
                        </Transition>
                      </div>
                    </div>
                  </div>
                </section>

                <!-- SECCIÓN 2: DESTINATARIO Y CONDICIONES -->
                <section class="space-y-6">
                  <div class="flex items-center gap-3 mb-2">
                    <div class="w-8 h-8 rounded-lg bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
                      <Users class="w-4 h-4" />
                    </div>
                    <h3 class="text-sm font-black text-slate-800 dark:text-white uppercase tracking-wider">Grupo Objetivo y Condiciones</h3>
                  </div>

                  <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                    <!-- Grupo Objetivo (Solo en creación) -->
                    <div v-if="!isEditing" class="lg:col-span-8 space-y-3">
                      <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">¿Quiénes rendirán el examen?</label>
                      
                      <!-- Docentes -->
                      <div v-if="usarCodigosClase">
                        <div v-if="codigosClase.length === 0" class="p-6 bg-white dark:bg-slate-800 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700 text-center">
                           <p class="text-xs font-bold text-slate-500">No tienes aulas activas creadas.</p>
                        </div>
                        <div v-else class="relative">
                          <button type="button" @click="claseDropdownOpen = !claseDropdownOpen"
                            :class="[
                              'w-full flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl border transition-all text-left bg-slate-50 dark:bg-slate-700 cursor-pointer',
                              claseDropdownOpen ? 'border-violet-500 ring-4 ring-violet-500/10 shadow-lg' : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500'
                            ]">
                            <div v-if="codigoClaseSeleccionado" class="min-w-0">
                              <p class="text-xs font-black text-slate-800 dark:text-white truncate">{{ codigoClaseSeleccionado.grado_nombre }} — Sección {{ codigoClaseSeleccionado.seccion }}</p>
                              <p class="text-[9px] font-bold text-slate-400 flex items-center gap-1.5 mt-0.5 uppercase">
                                <Users class="w-3 h-3" /> <span>{{ codigoClaseSeleccionado.total_estudiantes }} est.</span>
                              </p>
                            </div>
                            <span v-else class="text-slate-400 text-xs font-bold">— Todas mis secciones —</span>
                            <ChevronDown class="w-4 h-4 text-slate-400 transition-transform duration-300" :class="claseDropdownOpen ? 'rotate-180' : ''" />
                          </button>
                          <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100"
                            leave-active-class="transition duration-150 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                            <div v-if="claseDropdownOpen" class="absolute z-[120] left-0 right-0 top-full mt-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
                              <div class="max-h-60 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700 custom-scrollbar">
                                <button type="button" @click="codigoClaseId = null; claseDropdownOpen = false" class="w-full text-left p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-4 group cursor-pointer">
                                  <div :class="codigoClaseId === null ? 'bg-violet-500' : 'bg-slate-200 dark:bg-slate-700'" class="w-2 h-10 rounded-full shrink-0"></div>
                                  <p class="text-sm font-black text-slate-800 dark:text-white">Todas mis secciones</p>
                                </button>
                                <button v-for="c in codigosClase" :key="c.id" type="button" @click="codigoClaseId = c.id; claseDropdownOpen = false" class="w-full text-left p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-4 group cursor-pointer">
                                  <div :class="codigoClaseId === c.id ? 'bg-violet-500' : 'bg-slate-200 dark:bg-slate-700'" class="w-2 h-10 rounded-full shrink-0"></div>
                                  <div class="min-w-0"><p class="text-sm font-black text-slate-800 dark:text-white truncate">{{ c.grado_nombre }} — Sección {{ c.seccion }}</p></div>
                                </button>
                              </div>
                            </div>
                          </Transition>
                        </div>
                      </div>

                      <!-- Roles Superiores -->
                      <div v-else class="grid grid-cols-1 gap-4">
                        <div class="space-y-2">
                        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Grado</label>
                        <div class="relative">
                          <button type="button" @click="gradoDropdownOpen = !gradoDropdownOpen" :class="['w-full flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl border transition-all text-left bg-slate-50 dark:bg-slate-700 cursor-pointer', gradoDropdownOpen ? 'border-violet-500 ring-4 ring-violet-500/10 shadow-lg' : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500']">
                            <div class="min-w-0 flex items-center gap-2">
                              <div v-if="gradoSeleccionado" class="p-1 rounded-lg bg-violet-100 dark:bg-violet-900/40 text-violet-600 dark:text-violet-400"><GraduationCap class="w-3 h-3" /></div>
                              <div>
                                <p v-if="gradoSeleccionado" class="text-xs font-black text-slate-800 dark:text-white truncate leading-tight">{{ gradoSeleccionado.nombre }}</p>
                                <span v-else class="text-slate-400 text-xs font-bold">— Todos —</span>
                              </div>
                            </div>
                            <ChevronDown class="w-3.5 h-3.5 text-slate-400 transition-transform duration-300" :class="gradoDropdownOpen ? 'rotate-180' : ''" />
                          </button>
                          <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100" leave-active-class="transition duration-150 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                            <div v-if="gradoDropdownOpen" class="absolute z-[120] left-0 right-0 top-full mt-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
                              <div class="max-h-60 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700 custom-scrollbar">
                                <button type="button" @click="gradoSeleccionadoId = null; gradoDropdownOpen = false" class="w-full text-left p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-4 group cursor-pointer">
                                  <div :class="gradoSeleccionadoId === null ? 'bg-violet-500' : 'bg-slate-200 dark:bg-slate-700'" class="w-2 h-10 rounded-full shrink-0"></div>
                                  <p class="text-sm font-black text-slate-800 dark:text-white">Todos los grados</p>
                                </button>
                                <button v-for="g in grados" :key="g.id" type="button" @click="gradoSeleccionadoId = g.id; gradoDropdownOpen = false" class="w-full text-left p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-4 group cursor-pointer">
                                  <div :class="gradoSeleccionadoId === g.id ? 'bg-violet-500' : 'bg-slate-200 dark:bg-slate-700'" class="w-2 h-10 rounded-full shrink-0"></div>
                                  <p class="text-sm font-black text-slate-800 dark:text-white">{{ g.nombre }}</p>
                                </button>
                              </div>
                            </div>
                          </Transition>
                        </div>
                        </div>
                        <div class="space-y-2">
                        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Sección</label>
                        <div class="relative">
                          <button type="button" @click="seccionDropdownOpen = !seccionDropdownOpen" :class="['w-full flex items-center justify-between gap-3 px-3.5 py-2.5 rounded-xl border transition-all text-left bg-slate-50 dark:bg-slate-700 cursor-pointer', seccionDropdownOpen ? 'border-violet-500 ring-4 ring-violet-500/10 shadow-lg' : 'border-slate-300 dark:border-slate-600 hover:border-slate-400 dark:hover:border-slate-500']">
                            <div class="min-w-0"><p v-if="seccion" class="text-xs font-black text-slate-800 dark:text-white truncate leading-tight">Sección {{ seccion }}</p><span v-else class="text-slate-400 text-xs font-bold">— Todas —</span></div>
                            <ChevronDown class="w-3.5 h-3.5 text-slate-400 transition-transform duration-300" :class="seccionDropdownOpen ? 'rotate-180' : ''" />
                          </button>
                          <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100" leave-active-class="transition duration-150 ease-in" leave-from-class="transform scale-100 opacity-100" leave-to-class="transform scale-95 opacity-0">
                            <div v-if="seccionDropdownOpen" class="absolute z-[120] left-0 right-0 top-full mt-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-2xl shadow-2xl overflow-hidden">
                              <div class="max-h-60 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700 custom-scrollbar">
                                <button type="button" @click="seccion = ''; seccionDropdownOpen = false" class="w-full text-left p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-4 group cursor-pointer">
                                  <div :class="seccion === '' ? 'bg-violet-500' : 'bg-slate-200 dark:bg-slate-700'" class="w-2 h-10 rounded-full shrink-0"></div>
                                  <p class="text-sm font-black text-slate-800 dark:text-white">Todas las secciones</p>
                                </button>
                                <button v-for="s in ['A','B','C','D','E','F','G','H','I','J','Única']" :key="s" type="button" @click="seccion = s; seccionDropdownOpen = false" class="w-full text-left p-4 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors flex items-center gap-4 group cursor-pointer">
                                  <div :class="seccion === s ? 'bg-violet-500' : 'bg-slate-200 dark:bg-slate-700'" class="w-2 h-10 rounded-full shrink-0"></div>
                                  <p class="text-sm font-black text-slate-800 dark:text-white">Sección {{ s }}</p>
                                </button>
                              </div>
                            </div>
                          </Transition>
                        </div>
                        </div>
                      </div>
                    </div>

                    <!-- Intentos -->
                    <div :class="isEditing ? 'lg:col-span-12' : 'lg:col-span-4'" class="space-y-3">
                      <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Máximo de intentos</label>
                      <div class="relative group">
                        <div class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 scale-90">
                          <Hash class="w-4 h-4" />
                        </div>
                        <input v-model.number="intentosPermitidos" type="number" min="1" max="10"
                          class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 pl-10 pr-4 text-xs font-black text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all shadow-sm" />
                      </div>
                    </div>
                  </div>
                </section>

                <!-- SECCIÓN 3: PROGRAMACIÓN -->
                <section class="space-y-6">
                  <div class="flex items-center gap-3 mb-2">
                    <div class="w-8 h-8 rounded-lg bg-emerald-100 dark:bg-emerald-900/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                      <Calendar class="w-4 h-4" />
                    </div>
                    <h3 class="text-sm font-black text-slate-800 dark:text-white uppercase tracking-wider">Programación de la Fecha</h3>
                  </div>

                  <div class="bg-white dark:bg-slate-800/60 rounded-3xl p-8 border-2 border-slate-100 dark:border-slate-700/50 shadow-xl">
                    <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                      <!-- Fecha -->
                      <div class="space-y-3">
                        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Fecha de Aplicación</label>
                        <div class="relative">
                          <Calendar class="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-violet-500 dark:text-violet-400" />
                          <input v-model="fechaAplicacion" type="date"
                            class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 pl-10 pr-3.5 text-xs font-bold text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all" />
                        </div>
                      </div>
                      <!-- Hora Inicio -->
                      <div class="space-y-3">
                        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Hora de Apertura</label>
                        <div class="relative">
                          <Clock class="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-emerald-500 dark:text-emerald-400" />
                          <input v-model="horaInicio" type="time"
                            class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 pl-10 pr-3.5 text-xs font-bold text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all" />
                        </div>
                      </div>
                      <!-- Hora Fin -->
                      <div class="space-y-3">
                        <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Hora de Cierre</label>
                        <div class="relative">
                          <Clock class="absolute left-3.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-rose-500 dark:text-rose-400" />
                          <input v-model="horaFin" type="time"
                            class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 pl-10 pr-3.5 text-xs font-bold text-slate-800 dark:text-white outline-none focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition-all" />
                        </div>
                      </div>
                    </div>

                    <div class="mt-6 pt-6 border-t border-slate-100 dark:border-slate-700/50">
                      <div v-if="duracionVentanaTexto"
                        class="flex flex-wrap items-center gap-4 bg-gradient-to-r from-violet-50 to-indigo-50 dark:from-violet-500/10 dark:to-indigo-500/10 border border-violet-100 dark:border-violet-500/20 rounded-2xl px-5 py-4">
                        <div class="w-11 h-11 rounded-xl bg-violet-600 text-white flex items-center justify-center shrink-0 shadow-lg shadow-violet-600/30">
                          <Clock class="w-5 h-5" />
                        </div>
                        <div class="flex-1 min-w-[10rem]">
                          <p class="text-[10px] font-black text-violet-500 dark:text-violet-400 uppercase tracking-widest leading-none mb-1.5">Duración total de la evaluación</p>
                          <p class="text-lg font-black text-slate-800 dark:text-white leading-none">{{ duracionVentanaTexto }}</p>
                        </div>
                        <div class="flex items-center gap-2 text-xs font-black text-slate-500 dark:text-slate-400 shrink-0">
                          <span class="px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">{{ horaInicio }}</span>
                          <span class="text-slate-300 dark:text-slate-600">→</span>
                          <span class="px-2.5 py-1.5 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 shadow-sm">{{ horaFin }}</span>
                        </div>
                      </div>
                      <p v-else class="flex items-center gap-2 text-xs font-bold text-slate-400">
                        <AlertCircle class="w-4 h-4 text-amber-500 shrink-0" />
                        Selecciona la hora de apertura y cierre para calcular la duración total.
                      </p>
                    </div>
                  </div>
                </section>

                <!-- SECCIÓN 4: SEGURIDAD -->
                <section class="space-y-6">
                  <div class="flex items-center gap-3 mb-2">
                    <div class="w-8 h-8 rounded-lg bg-rose-100 dark:bg-rose-900/40 text-rose-600 dark:text-rose-400 flex items-center justify-center">
                      <ShieldCheck class="w-4 h-4" />
                    </div>
                    <h3 class="text-sm font-black text-slate-800 dark:text-white uppercase tracking-wider">Aleatoriedad y Seguridad</h3>
                  </div>

                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <button @click="mezclarPreguntas = !mezclarPreguntas"
                      :class="mezclarPreguntas ? 'bg-white dark:bg-slate-800 border-violet-500 shadow-md' : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 text-slate-400 hover:border-slate-400'"
                      class="flex items-center justify-between p-4 rounded-xl border transition-all group text-left">
                       <div class="flex items-center gap-3">
                          <div :class="mezclarPreguntas ? 'bg-violet-100 dark:bg-violet-500/20 text-violet-600 dark:text-violet-400' : 'bg-slate-50 dark:bg-slate-900/50 text-slate-300'" class="w-10 h-10 rounded-xl flex items-center justify-center transition-colors">
                             <RefreshCw class="w-5 h-5" :class="mezclarPreguntas ? 'animate-spin-slow' : ''" />
                          </div>
                          <div>
                             <p class="text-[11px] font-black" :class="mezclarPreguntas ? 'text-slate-800 dark:text-white' : 'text-slate-400'">Preguntas Aleatorias</p>
                             <p class="text-[9px] font-bold opacity-70 leading-none">Diferente orden para todos</p>
                          </div>
                       </div>
                       <div :class="mezclarPreguntas ? 'bg-violet-600' : 'bg-slate-200 dark:bg-slate-700'" class="w-5 h-5 rounded-full flex items-center justify-center transition-colors">
                          <Check v-if="mezclarPreguntas" class="w-3 h-3 text-white" />
                       </div>
                    </button>

                    <button @click="mezclarAlternativas = !mezclarAlternativas"
                      :class="mezclarAlternativas ? 'bg-white dark:bg-slate-800 border-indigo-500 shadow-md' : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 text-slate-400 hover:border-slate-400'"
                      class="flex items-center justify-between p-4 rounded-xl border transition-all group text-left">
                       <div class="flex items-center gap-3">
                          <div :class="mezclarAlternativas ? 'bg-indigo-100 dark:bg-indigo-500/20 text-indigo-600 dark:text-indigo-400' : 'bg-slate-50 dark:bg-slate-900/50 text-slate-300'" class="w-10 h-10 rounded-xl flex items-center justify-center transition-colors">
                             <TrendingUp class="w-5 h-5" />
                          </div>
                          <div>
                             <p class="text-[11px] font-black" :class="mezclarAlternativas ? 'text-slate-800 dark:text-white' : 'text-slate-400'">Alternativas Mezcladas</p>
                             <p class="text-[9px] font-bold opacity-70 leading-none">Cambia el orden de respuestas</p>
                          </div>
                       </div>
                       <div :class="mezclarAlternativas ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-700'" class="w-5 h-5 rounded-full flex items-center justify-center transition-colors">
                          <Check v-if="mezclarAlternativas" class="w-3 h-3 text-white" />
                       </div>
                    </button>
                  </div>
                </section>
              </div>

            </div>

            <!-- Footer -->
            <div class="px-8 py-6 bg-slate-50 dark:bg-slate-800/60 border-t border-slate-300 dark:border-slate-800 flex flex-col gap-3 shrink-0">
              <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="-translate-y-1 opacity-0" enter-to-class="translate-y-0 opacity-100">
                <div v-if="modalError" class="flex items-center gap-3 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 px-4 py-3 rounded-xl text-xs border border-red-100 dark:border-red-500/20">
                  <AlertCircle class="w-4 h-4 shrink-0" />
                  <span class="font-bold">{{ modalError }}</span>
                </div>
              </Transition>
              <div class="flex flex-col sm:flex-row gap-4">
              <button @click="closeModal()"
                class="flex-1 px-6 py-4 text-sm font-bold text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-2xl transition-colors">
                Cancelar
              </button>
              <button @click="guardar" :disabled="saving || (!isEditing && !examenSeleccionadoId)"
                class="flex-[1.5] flex items-center justify-center gap-3 px-8 py-4 bg-gradient-to-r from-violet-600 to-indigo-700 text-white font-black text-sm rounded-2xl shadow-xl shadow-violet-500/20 active:scale-95 transition-all disabled:opacity-50 disabled:cursor-not-allowed">
                <Loader2 v-if="saving" class="w-5 h-5 animate-spin" />
                <Save v-else class="w-5 h-5" />
                <span>{{ isEditing ? 'Actualizar Evaluación' : 'Confirmar Asignación' }}</span>
              </button>
              </div>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal Resultados: Premium Bottom Sheet pattern -->
    <Teleport to="body">
      <Transition name="details-modal">
        <div v-if="showResultados"
          class="fixed inset-0 z-[120] flex items-end sm:items-center justify-center sm:p-4">
          
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer" @click="showResultados = false"></div>

          <div class="relative bg-white dark:bg-slate-900 w-full sm:max-w-2xl max-h-[94dvh] sm:max-h-[85vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10 animate-slide-up">

            <!-- Drag handle mobile -->
            <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0" @click="showResultados = false">
              <div class="w-10 h-1.5 rounded-full bg-slate-200 dark:bg-slate-800"></div>
            </div>

            <!-- Header -->
            <div class="px-8 py-6 border-b border-slate-300 dark:border-slate-800 flex flex-col gap-4 shrink-0">
               <div class="flex items-center justify-between">
                  <div class="flex items-center gap-4 min-w-0">
                    <div class="w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-inner"
                      :class="resultadosAsig?.tipo_examen === 'lectura'
                        ? 'bg-teal-50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400'
                        : 'bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400'">
                      <BookOpen v-if="resultadosAsig?.tipo_examen === 'lectura'" class="w-7 h-7" />
                      <Calculator v-else class="w-7 h-7" />
                    </div>
                    <div class="min-w-0">
                      <h2 class="text-xl font-black text-slate-800 dark:text-white truncate tracking-tight">
                        {{ resultadosAsig?.titulo ?? 'Resultados del Examen' }}
                      </h2>
                      <p class="text-sm font-bold text-slate-500 dark:text-slate-400">
                        {{ resultadosAsig?.grado_nombre ?? `Grado ${resultadosAsig?.grado_id}` }}<span v-if="resultadosAsig?.seccion"> · Sección {{ resultadosAsig.seccion }}</span>
                      </p>
                    </div>
                  </div>
                  <button @click="showResultados = false" class="p-3 bg-slate-100 dark:bg-slate-800 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-2xl transition-all">
                    <X class="w-6 h-6" />
                  </button>
               </div>
               
               <div class="flex items-center justify-between bg-slate-50 dark:bg-slate-800/60 px-6 py-3 rounded-2xl border border-slate-300 dark:border-slate-800">
                  <div class="flex items-center gap-2">
                    <Users class="w-4 h-4 text-violet-500" />
                    <span class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">
                      {{ (resultados[resultadosAsig?.id ?? 0] ?? []).length }} Estudiantes
                    </span>
                  </div>
                  <div class="flex items-center gap-2">
                    <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                    <span class="text-xs font-black text-emerald-600 dark:text-emerald-400 uppercase tracking-widest">Sincronizado</span>
                  </div>
               </div>
            </div>

            <!-- Body -->
            <div class="flex-1 min-h-0 overflow-y-auto custom-scrollbar">

              <div v-if="loadingResultados" class="flex flex-col items-center justify-center py-20">
                <Loader2 class="w-10 h-10 text-violet-500 animate-spin mb-4" />
                <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Cargando reporte detallado…</p>
              </div>

              <div v-else-if="(resultados[resultadosAsig?.id ?? 0] ?? []).length === 0"
                class="flex flex-col items-center justify-center py-24 gap-4 text-center px-8">
                <div class="w-20 h-20 bg-slate-50 dark:bg-slate-800 rounded-2xl flex items-center justify-center mb-2">
                   <Users class="w-10 h-10 text-slate-300 dark:text-slate-600" />
                </div>
                <div>
                  <p class="text-lg font-black text-slate-800 dark:text-white tracking-tight">Sin registros aún</p>
                  <p class="text-sm text-slate-500 dark:text-slate-400 max-w-xs mx-auto">
                    Los resultados aparecerán aquí a medida que los estudiantes completen sus evaluaciones.
                  </p>
                </div>
              </div>

              <div v-else class="divide-y divide-slate-50 dark:divide-slate-800">
                <div v-for="r in resultados[resultadosAsig?.id ?? 0]" :key="r.codigo ?? r.estudiante"
                  class="flex items-center gap-4 px-8 py-5 hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-all group">
                  
                  <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-100 to-indigo-100 dark:from-violet-900/30 dark:to-indigo-900/30 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                    <span class="text-sm font-black text-violet-600 dark:text-violet-400">
                      {{ (r.estudiante || r.codigo || '?').slice(0, 2).toUpperCase() }}
                    </span>
                  </div>
                  
                  <div class="flex-1 min-w-0">
                    <p class="text-base font-black text-slate-800 dark:text-slate-200 truncate leading-tight">{{ r.estudiante || r.codigo }}</p>
                    <div class="flex items-center gap-3 mt-1.5">
                       <span class="text-[10px] font-black text-slate-400 uppercase tracking-wider font-mono">{{ r.codigo }}</span>
                       <span v-if="r.fecha" class="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-700"></span>
                       <span v-if="r.fecha" class="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                          <Clock class="w-3 h-3" />
                          {{ formatFechaHora(r.fecha) }}
                       </span>
                    </div>
                  </div>

                  <div class="flex flex-col items-end gap-2 shrink-0">
                    <div class="flex items-center gap-2">
                       <span v-if="r.puntaje !== null" class="text-lg font-black text-slate-800 dark:text-white leading-none">
                          {{ r.puntaje?.toFixed(0) }}<span class="text-xs font-bold text-slate-400 ml-0.5">%</span>
                       </span>
                       <span :class="estadoColors[r.estado] ?? estadoColors.sin_intento"
                        class="text-[10px] font-black uppercase px-2.5 py-1 rounded-full tracking-wider border-2 border-transparent">
                        {{ estadoLabels[r.estado] ?? r.estado }}
                      </span>
                    </div>
                    <div v-if="r.nivel_logro" :class="nivelColors[r.nivel_logro]"
                      class="text-[10px] font-black uppercase px-2.5 py-1 rounded-full tracking-wider shadow-sm">
                      {{ nivelLabels[r.nivel_logro] ?? r.nivel_logro }}
                    </div>
                  </div>
                </div>
              </div>

            </div>

            <div class="p-6 bg-slate-50 dark:bg-slate-800/40 text-center border-t border-slate-300 dark:border-slate-800">
              <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.4em]">LectoSistem Report Engine</p>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}

.animate-spin-slow {
  animation: spin 3s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Details Modal / Bottom Sheet Animation */
.details-modal-enter-active, .details-modal-leave-active {
  transition: opacity 0.3s ease;
}
.details-modal-enter-active .relative, .details-modal-leave-active .relative {
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.details-modal-enter-from, .details-modal-leave-to {
  opacity: 0;
}
.details-modal-enter-from .relative, .details-modal-leave-to .relative {
  transform: translateY(100%);
}
@media (min-width: 640px) {
  .details-modal-enter-from .relative, .details-modal-leave-to .relative {
    transform: translateY(0) scale(0.95);
  }
}
</style>
