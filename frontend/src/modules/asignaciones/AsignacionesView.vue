<script setup lang="ts">
import { construirFechaISO, extraerFechaHora, formatFechaHora } from '../../shared/utils/dateUtils'
import { ref, shallowRef, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient, asignacionesService, examenesService, organizacionService, codigosClaseService } from '../../shared/services/api'
import type { UpdateAsignacionPayload, CodigoClase } from '../../shared/services/api'
import Header from '../../shared/components/Header.vue'
import Footer from '../../shared/components/Footer.vue'
import Checkbox from '../../shared/components/Checkbox.vue'
import { useTheme } from '../../shared/composables/useTheme'
import { showDeleteConfirm, Toast } from '../../shared/utils/swal'
import {
  Home, ClipboardList, BookOpen, Calculator,
  Trash2, Loader2, Users, ChevronDown,
  Clock, AlertCircle, Plus, X, BookMarked, Save, User, Pencil
} from 'lucide-vue-next'
import type { Grado } from '../../shared/types'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()
useTheme()

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
const loadingDelete = ref<number | null>(null)

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
const gradoSeleccionadoId = ref<number | null>(null)
const seccion = ref('')

// Para docentes: usa codigos_clase; para roles superiores: usa grado+sección libres
const usarCodigosClase = computed(() => auth.isDocente || auth.isAuxiliar)
const codigoClaseSeleccionado = computed(() =>
  codigosClase.value.find(c => c.id === codigoClaseId.value) ?? null
)
const fechaAplicacion = ref('')
const horaInicio = ref('')
const horaFin = ref('')
const duracionMinutos = ref<number | null>(null)
const intentosPermitidos = ref(1)
const mezclarPreguntas = ref(true)
const mezclarAlternativas = ref(true)

const examenesActuales = computed(() =>
  tipoExamen.value === 'lectura' ? examenesLectura.value : examenesMatematica.value
)

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
  duracionMinutos.value = asig.duracion_minutos
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
  duracionMinutos.value = null
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
        duracion_minutos: duracionMinutos.value || null,
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
      duracion_minutos: duracionMinutos.value || null,
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

async function eliminar(id: number) {
  const ok = await showDeleteConfirm('¿Eliminar asignación?', 'Se eliminarán todos los intentos relacionados')
  if (!ok) return
  loadingDelete.value = id
  try {
    await asignacionesService.deleteAsignacion(id)
    asignaciones.value = asignaciones.value.filter(a => a.id !== id)
    if (resultadosAsig.value?.id === id) showResultados.value = false
    Toast.fire({ icon: 'success', title: 'Asignación eliminada' })
  } catch (e: any) {
    Toast.fire({ icon: 'error', title: e.response?.data?.detail ?? 'Error al eliminar' })
  } finally {
    loadingDelete.value = null
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

    <Header
      :title="headerTitle"
      subtitle="Exámenes asignados a estudiantes"
      gradient-class="from-violet-600 via-purple-600 to-indigo-600 shadow-violet-500/20"
      subtitle-class="text-violet-100 dark:text-slate-400"
    >
      <template #actions-before>
        <button @click="router.push('/')"
          class="p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 transition-all"
          title="Inicio">
          <Home class="w-5 h-5" />
        </button>
      </template>
    </Header>

    <main class="flex-1 max-w-4xl mx-auto px-4 sm:px-6 py-6 w-full space-y-4">

      <!-- Toolbar -->
      <div class="flex items-center justify-between gap-3">
        <h2 class="text-sm font-semibold text-slate-500 dark:text-slate-400">
          {{ asignaciones.length }} asignación(es) activas
        </h2>
        <button @click="openModal"
          class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all">
          <Plus class="w-4 h-4" /> Nueva asignación
        </button>
      </div>

      <!-- Error -->
      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl p-4 text-red-600 dark:text-red-400 text-sm">
        {{ error }}
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex justify-center py-20">
        <Loader2 class="w-10 h-10 text-violet-500 animate-spin" />
      </div>

      <!-- Empty -->
      <div v-else-if="asignaciones.length === 0"
        class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-12 text-center shadow-sm">
        <ClipboardList class="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
        <h3 class="text-lg font-bold text-slate-700 dark:text-slate-200 mb-2">Sin asignaciones aún</h3>
        <p class="text-sm text-slate-500 dark:text-slate-400 mb-5">
          Asigna un examen generado a tus estudiantes usando el botón de arriba.
        </p>
        <button @click="openModal"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-violet-500 to-indigo-600 text-white font-bold text-sm rounded-xl shadow transition-all hover:from-violet-600 hover:to-indigo-700">
          <Plus class="w-4 h-4" /> Nueva asignación
        </button>
      </div>

      <!-- List -->
      <div v-else class="space-y-3">
        <div v-for="asig in asignaciones" :key="asig.id"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm overflow-hidden">

          <!-- Header row -->
          <div class="flex items-center gap-3 p-4">
            <div :class="asig.tipo_examen === 'lectura'
              ? 'bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400'
              : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'"
              class="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0">
              <BookOpen v-if="asig.tipo_examen === 'lectura'" class="w-4 h-4" />
              <Calculator v-else class="w-4 h-4" />
            </div>

            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold text-slate-800 dark:text-white truncate">
                {{ asig.titulo ?? (asig.tipo_examen === 'lectura' ? 'Examen de Lectura' : 'Examen de Matemática') }}
              </p>
              <p class="text-xs text-slate-500 dark:text-slate-400 truncate">
                {{ asig.grado_nombre ?? `Grado ${asig.grado_id}` }}<span v-if="asig.seccion"> — {{ asig.seccion }}</span>
                <span class="mx-1">·</span>
                <span class="text-emerald-600 dark:text-emerald-400 font-medium">{{ asig.completados }} completados</span>
              </p>
              <div class="flex items-center gap-2.5 mt-0.5 flex-wrap">
                <span v-if="asig.duracion_minutos" class="flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500">
                  <Clock class="w-3 h-3" />{{ asig.duracion_minutos }}min
                </span>
                <span v-if="asig.fecha_fin" class="flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500">
                  <AlertCircle class="w-3 h-3" />{{ formatFechaHora(asig.fecha_inicio) }} – {{ formatFechaHora(asig.fecha_fin) }}
                </span>
                <span v-if="asig.asignado_por_nombre" class="flex items-center gap-1 text-[11px] text-slate-400 dark:text-slate-500">
                  <User class="w-3 h-3" />{{ asig.asignado_por_nombre }}
                </span>
              </div>
            </div>

            <div class="flex items-center gap-1 flex-shrink-0">
              <button @click="openResultados(asig)"
                class="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 dark:text-slate-500 transition-colors"
                title="Ver resultados">
                <Users class="w-4 h-4" />
              </button>
              <button v-if="asig.puede_eliminar" @click="openEditModal(asig)"
                class="p-2 rounded-xl hover:bg-violet-50 dark:hover:bg-violet-900/20 text-slate-400 hover:text-violet-500 dark:hover:text-violet-400 transition-colors"
                title="Editar condiciones">
                <Pencil class="w-4 h-4" />
              </button>
              <button v-if="asig.puede_eliminar" @click="eliminar(asig.id)" :disabled="loadingDelete === asig.id"
                class="p-2 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 text-red-400 hover:text-red-500 transition-colors disabled:opacity-40">
                <Loader2 v-if="loadingDelete === asig.id" class="w-4 h-4 animate-spin" />
                <Trash2 v-else class="w-4 h-4" />
              </button>
            </div>
          </div>

        </div>
      </div>

    </main>

    <Footer />

    <!-- Modal Nueva Asignación -->
    <Teleport to="body">
      <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0"
        enter-to-class="opacity-100" leave-active-class="transition duration-150"
        leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="showModal"
          class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          @click.self="closeModal()">
          <div class="bg-white dark:bg-slate-800 w-full max-w-lg max-h-[88vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden">

            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
                  <BookMarked class="w-4 h-4 text-white" />
                </div>
                <h2 class="text-base font-bold text-slate-800 dark:text-white">
                  {{ isEditing ? 'Editar condiciones' : 'Nueva Asignación' }}
                </h2>
              </div>
              <button @click="closeModal()" class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl transition-colors">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Body -->
            <div class="flex-1 min-h-0 overflow-y-auto p-5 space-y-4">

              <div v-if="modalError"
                class="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-sm border border-red-100 dark:border-red-900/50">
                <AlertCircle class="w-4 h-4 shrink-0" /> {{ modalError }}
              </div>

              <!-- Tipo de examen / Examen / Grado / Sección — solo en creación -->
              <template v-if="!isEditing">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-2">Tipo de examen</label>
                  <div class="grid grid-cols-2 gap-2">
                    <button type="button" @click="tipoExamen = 'lectura'; examenSeleccionadoId = null; examenDropdownOpen = false"
                      :class="['flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-semibold transition-all',
                        tipoExamen === 'lectura'
                          ? 'bg-teal-50 dark:bg-teal-900/20 border-teal-400 text-teal-700 dark:text-teal-300'
                          : 'border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-slate-300']">
                      <BookOpen class="w-4 h-4" /> Comunicación
                    </button>
                    <button type="button" @click="tipoExamen = 'matematica'; examenSeleccionadoId = null; examenDropdownOpen = false"
                      :class="['flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-semibold transition-all',
                        tipoExamen === 'matematica'
                          ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-400 text-indigo-700 dark:text-indigo-300'
                          : 'border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-slate-300']">
                      <Calculator class="w-4 h-4" /> Matemática
                    </button>
                  </div>
                </div>

                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">
                    Examen a asignar <span class="text-red-500">*</span>
                  </label>
                  <div v-if="loadingExamenes" class="flex justify-center py-4">
                    <Loader2 class="w-5 h-5 animate-spin text-violet-400" />
                  </div>
                  <div v-else-if="examenesActuales.length === 0"
                    class="text-sm text-slate-400 dark:text-slate-500 italic py-2">
                    No tienes exámenes de este tipo guardados.
                    <button @click="router.push(tipoExamen === 'lectura' ? '/lectosistem' : '/matsistem'); closeModal()"
                      class="text-violet-600 dark:text-violet-400 font-semibold hover:underline ml-1">
                      Generar uno
                    </button>
                  </div>
                  <div v-else class="relative">
                    <!-- Trigger -->
                    <button type="button" @click="examenDropdownOpen = !examenDropdownOpen"
                      :class="[
                        'w-full flex items-center justify-between gap-2 px-3.5 py-2.5 rounded-xl border text-sm transition-all',
                        examenDropdownOpen
                          ? 'border-violet-500 ring-2 ring-violet-500/30 bg-white dark:bg-slate-700'
                          : 'border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-700 hover:border-violet-300'
                      ]">
                      <div v-if="examenSeleccionado" class="flex-1 min-w-0 text-left">
                        <p class="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{{ examenSeleccionado.titulo ?? 'Sin título' }}</p>
                        <p class="text-[11px] text-slate-400 dark:text-slate-500 flex items-center gap-1.5 mt-0.5">
                          <span v-if="examenSeleccionado.grado_nombre">{{ examenSeleccionado.grado_nombre }}</span>
                          <span v-if="examenSeleccionado.grado_nombre">·</span>
                          <span>{{ formatFechaHora(examenSeleccionado.fecha_creacion) }}</span>
                        </p>
                      </div>
                      <span v-else class="text-slate-400 dark:text-slate-500 text-sm flex-1 text-left">— Selecciona un examen —</span>
                      <ChevronDown class="w-4 h-4 flex-shrink-0 text-slate-400 transition-transform duration-200"
                        :class="examenDropdownOpen ? 'rotate-180' : ''" />
                    </button>

                    <!-- Backdrop para cerrar -->
                    <div v-if="examenDropdownOpen" class="fixed inset-0 z-10" @click="examenDropdownOpen = false" />

                    <!-- Panel flotante -->
                    <div v-if="examenDropdownOpen"
                      class="absolute z-20 left-0 right-0 top-full mt-1 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-600 rounded-xl shadow-lg overflow-hidden">
                      <div class="max-h-52 overflow-y-auto divide-y divide-slate-100 dark:divide-slate-700">
                        <button v-for="ex in examenesActuales" :key="ex.id" type="button"
                          @click="examenSeleccionadoId = ex.id; examenDropdownOpen = false"
                          :class="[
                            'w-full text-left flex items-center gap-3 px-3.5 py-2.5 transition-colors',
                            examenSeleccionadoId === ex.id
                              ? 'bg-violet-50 dark:bg-violet-900/20'
                              : 'hover:bg-slate-50 dark:hover:bg-slate-700/50'
                          ]">
                          <div :class="[
                            'w-4 h-4 rounded-full border-2 flex-shrink-0 flex items-center justify-center transition-colors',
                            examenSeleccionadoId === ex.id ? 'border-violet-500' : 'border-slate-300 dark:border-slate-500'
                          ]">
                            <div v-if="examenSeleccionadoId === ex.id" class="w-2 h-2 rounded-full bg-violet-500" />
                          </div>
                          <div class="flex-1 min-w-0">
                            <p class="text-sm font-semibold text-slate-800 dark:text-slate-100 truncate">{{ ex.titulo ?? 'Sin título' }}</p>
                            <p class="text-[11px] text-slate-400 dark:text-slate-500 flex items-center gap-1.5 mt-0.5">
                              <span v-if="ex.grado_nombre">{{ ex.grado_nombre }}</span>
                              <span v-if="ex.grado_nombre">·</span>
                              <span>{{ formatFechaHora(ex.fecha_creacion) }}</span>
                            </p>
                          </div>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Docentes/Auxiliares: picker de Códigos de Clase -->
                <div v-if="usarCodigosClase">
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">
                    Sección <span class="font-normal text-slate-400">(de mis aulas)</span>
                  </label>
                  <div v-if="codigosClase.length === 0" class="text-xs text-slate-400 dark:text-slate-500 bg-slate-50 dark:bg-slate-800 rounded-xl px-4 py-3 border border-slate-200 dark:border-slate-700">
                    No tienes aulas activas. Crea una primero en la sección Aulas.
                  </div>
                  <template v-else>
                    <select v-model="codigoClaseId"
                      class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all">
                      <option :value="null">— Todas mis secciones —</option>
                      <option v-for="c in codigosClase" :key="c.id" :value="c.id">
                        {{ c.grado_nombre }} — Sección {{ c.seccion }}
                        <template v-if="c.total_estudiantes"> ({{ c.total_estudiantes }} est.)</template>
                      </option>
                    </select>
                    <p v-if="codigoClaseSeleccionado" class="mt-1.5 text-[11px] text-slate-400 dark:text-slate-500 flex items-center gap-1">
                      <QrCode class="w-3 h-3 shrink-0" />
                      Código: <span class="font-mono font-bold">{{ codigoClaseSeleccionado.codigo }}</span>
                      · {{ codigoClaseSeleccionado.total_estudiantes }} estudiante(s) registrado(s)
                    </p>
                  </template>
                </div>

                <!-- Roles superiores: Grado + Sección libres -->
                <template v-else>
                  <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Grado</label>
                    <select v-model="gradoSeleccionadoId"
                      class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all">
                      <option :value="null">— Todos los grados —</option>
                      <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">
                      Sección <span class="font-normal text-slate-400">(dejar vacío = todas)</span>
                    </label>
                    <select v-model="seccion"
                      class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all">
                      <option value="">— Todas las secciones —</option>
                      <option v-for="s in ['A','B','C','D','E','F','G','H','I','J','Única']" :key="s" :value="s">{{ s }}</option>
                    </select>
                  </div>
                </template>
              </template>

              <!-- Rango horario -->
              <div class="space-y-3 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/40">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Día de aplicación</label>
                  <input v-model="fechaAplicacion" type="date"
                    class="w-full bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 transition-all" />
                </div>
                <div class="grid grid-cols-2 gap-3">
                  <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Hora inicio</label>
                    <input v-model="horaInicio" type="time"
                      class="w-full bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 transition-all" />
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Hora fin</label>
                    <input v-model="horaFin" type="time"
                      class="w-full bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 transition-all" />
                  </div>
                </div>
                <p class="text-[11px] text-slate-500 dark:text-slate-400">El examen quedará disponible solo ese día dentro del rango de horas indicado.</p>
              </div>

              <div class="space-y-2 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-900/40">
                <Checkbox v-model="mezclarPreguntas"
                  class="group flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 transition-all duration-150 dark:border-slate-700 dark:bg-slate-800/80"
                  color="checked:bg-violet-600 checked:border-violet-600 dark:checked:bg-violet-500 dark:checked:border-violet-500 focus:ring-violet-500/50">
                  <span>
                    <strong class="block text-sm font-bold text-slate-700 dark:text-slate-200">Aleatorizar preguntas</strong>
                    <span class="text-xs text-slate-500 dark:text-slate-400">El estudiante verá las preguntas en orden aleatorio.</span>
                  </span>
                </Checkbox>
                <Checkbox v-model="mezclarAlternativas"
                  class="group flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-3 transition-all duration-150 dark:border-slate-700 dark:bg-slate-800/80"
                  color="checked:bg-violet-600 checked:border-violet-600 dark:checked:bg-violet-500 dark:checked:border-violet-500 focus:ring-violet-500/50">
                  <span>
                    <strong class="block text-sm font-bold text-slate-700 dark:text-slate-200">Aleatorizar alternativas</strong>
                    <span class="text-xs text-slate-500 dark:text-slate-400">Las opciones se mostrarán mezcladas en cada pregunta.</span>
                  </span>
                </Checkbox>
              </div>

              <!-- Intentos -->
              <div class="grid grid-cols-1 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Intentos permitidos</label>
                  <input v-model.number="intentosPermitidos" type="number" min="1" max="10"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 transition-all" />
                </div>
              </div>

            </div>

            <!-- Footer -->
            <div class="flex items-center justify-end gap-2 px-5 py-4 border-t border-slate-100 dark:border-slate-700 shrink-0">
              <button @click="closeModal()"
                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
                Cancelar
              </button>
              <button @click="guardar" :disabled="saving || (!isEditing && !examenSeleccionadoId)"
                class="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-60 disabled:cursor-not-allowed">
                <Loader2 v-if="saving" class="w-3.5 h-3.5 animate-spin" />
                <Save v-else class="w-3.5 h-3.5" />
                {{ isEditing ? 'Guardar cambios' : 'Asignar examen' }}
              </button>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal Resultados -->
    <Teleport to="body">
      <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0"
        enter-to-class="opacity-100" leave-active-class="transition duration-150"
        leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="showResultados"
          class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          @click.self="showResultados = false">
          <div class="bg-white dark:bg-slate-800 w-full max-w-lg max-h-[85vh] flex flex-col rounded-2xl shadow-2xl overflow-hidden">

            <!-- Drag handle mobile -->
            <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0">
              <div class="w-10 h-1 rounded-full bg-slate-200 dark:bg-slate-600"></div>
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <div class="flex items-center gap-2.5 min-w-0">
                <div class="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0"
                  :class="resultadosAsig?.tipo_examen === 'lectura'
                    ? 'bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400'
                    : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'">
                  <BookOpen v-if="resultadosAsig?.tipo_examen === 'lectura'" class="w-4 h-4" />
                  <Calculator v-else class="w-4 h-4" />
                </div>
                <div class="min-w-0">
                  <h2 class="text-sm font-bold text-slate-800 dark:text-white truncate">
                    {{ resultadosAsig?.titulo ?? 'Resultados' }}
                  </h2>
                  <p class="text-xs text-slate-400 dark:text-slate-500">
                    {{ resultadosAsig?.grado_nombre ?? `Grado ${resultadosAsig?.grado_id}` }}<span v-if="resultadosAsig?.seccion"> — {{ resultadosAsig.seccion }}</span>
                  </p>
                </div>
              </div>
              <button @click="showResultados = false" class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl transition-colors flex-shrink-0">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Subheader con conteo -->
            <div class="px-5 py-2.5 bg-slate-50 dark:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700 shrink-0 flex items-center gap-2">
              <Users class="w-3.5 h-3.5 text-slate-400" />
              <span class="text-xs font-semibold text-slate-500 dark:text-slate-400">
                <template v-if="loadingResultados">Cargando…</template>
                <template v-else>{{ (resultados[resultadosAsig?.id ?? 0] ?? []).length }} estudiante(s) asignado(s)</template>
              </span>
            </div>

            <!-- Body -->
            <div class="flex-1 min-h-0 overflow-y-auto">

              <div v-if="loadingResultados" class="flex justify-center py-12">
                <Loader2 class="w-6 h-6 text-violet-400 animate-spin" />
              </div>

              <div v-else-if="(resultados[resultadosAsig?.id ?? 0] ?? []).length === 0"
                class="flex flex-col items-center justify-center py-12 gap-2 text-center px-6">
                <Users class="w-8 h-8 text-slate-300 dark:text-slate-600" />
                <p class="text-sm text-slate-400 dark:text-slate-500">Sin estudiantes en el alcance de esta asignación</p>
              </div>

              <div v-else class="divide-y divide-slate-100 dark:divide-slate-700">
                <div v-for="r in resultados[resultadosAsig?.id ?? 0]" :key="r.codigo ?? r.estudiante"
                  class="flex items-center gap-3 px-5 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-100 to-indigo-100 dark:from-violet-900/30 dark:to-indigo-900/30 flex items-center justify-center flex-shrink-0">
                    <span class="text-xs font-black text-violet-600 dark:text-violet-400">
                      {{ (r.estudiante || r.codigo || '?').slice(0, 2).toUpperCase() }}
                    </span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate">{{ r.estudiante || r.codigo }}</p>
                    <p class="text-[10px] text-slate-400">{{ r.codigo }}<span v-if="r.fecha"> · {{ formatFechaHora(r.fecha) }}</span></p>
                  </div>
                  <div class="flex items-center gap-2 flex-shrink-0">
                    <span :class="estadoColors[r.estado] ?? estadoColors.sin_intento"
                      class="text-[10px] font-bold px-2 py-0.5 rounded-full">
                      {{ estadoLabels[r.estado] ?? r.estado }}
                    </span>
                    <span v-if="r.correctas !== null && r.total !== null"
                      class="text-sm font-black text-slate-700 dark:text-slate-200">
                      {{ r.correctas }}/{{ r.total }}
                    </span>
                    <span v-if="r.puntaje !== null"
                      class="text-sm font-black text-emerald-600 dark:text-emerald-400">
                      {{ r.puntaje?.toFixed(1) }}%
                    </span>
                    <span v-if="r.nivel_logro" :class="nivelColors[r.nivel_logro]"
                      class="text-[10px] font-bold px-2 py-0.5 rounded-full">
                      {{ nivelLabels[r.nivel_logro] ?? r.nivel_logro }}
                    </span>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>
