<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient, asignacionesService, examenesService, organizacionService } from '../services/api'
import Header from '../components/Header.vue'
import Footer from '../components/Footer.vue'
import { useTheme } from '../composables/useTheme'
import { showDeleteConfirm, Toast } from '../utils/swal'
import {
  Home, ClipboardList, BookOpen, Calculator,
  ChevronDown, ChevronUp, Trash2, Loader2, Users,
  Clock, AlertCircle, Plus, X, BookMarked, Save
} from 'lucide-vue-next'
import type { Grado } from '../types'

const router = useRouter()
useTheme()

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
  is_active: boolean
  completados: number
  fecha_creacion: string | null
}

interface Resultado {
  estudiante: string
  codigo: string | null
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
const expanded = ref<number | null>(null)
const resultados = ref<Record<number, Resultado[]>>({})
const loadingResultados = ref<number | null>(null)
const loadingDelete = ref<number | null>(null)

// Modal nueva asignación
const showModal = ref(false)
const saving = ref(false)
const modalError = ref('')

// Datos para el formulario
const tipoExamen = ref<'lectura' | 'matematica'>('lectura')
const examenesLectura = ref<ExamenItem[]>([])
const examenesMatematica = ref<ExamenItem[]>([])
const grados = ref<Grado[]>([])
const loadingExamenes = ref(false)

const examenSeleccionadoId = ref<number | null>(null)
const gradoSeleccionadoId = ref<number | null>(null)
const seccion = ref('')
const fechaInicio = ref('')
const fechaFin = ref('')
const duracionMinutos = ref<number | null>(null)
const intentosPermitidos = ref(1)

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

async function openModal() {
  modalError.value = ''
  examenSeleccionadoId.value = null
  gradoSeleccionadoId.value = null
  seccion.value = ''
  fechaInicio.value = ''
  fechaFin.value = ''
  duracionMinutos.value = null
  intentosPermitidos.value = 1
  tipoExamen.value = 'lectura'

  showModal.value = true
  loadingExamenes.value = true
  try {
    const [lec, mat, grds] = await Promise.all([
      examenesService.getExamenesLectura(),
      examenesService.getExamenesMatematica(),
      organizacionService.getGrados(),
    ])
    examenesLectura.value = lec
    examenesMatematica.value = mat
    grados.value = grds
  } catch {
    modalError.value = 'Error al cargar datos'
  } finally {
    loadingExamenes.value = false
  }
}

async function guardar() {
  modalError.value = ''
  if (!examenSeleccionadoId.value) {
    modalError.value = 'Selecciona un examen'
    return
  }
  saving.value = true
  try {
    await asignacionesService.asignar({
      tipo_examen: tipoExamen.value,
      examen_id: examenSeleccionadoId.value,
      grado_id: gradoSeleccionadoId.value ?? undefined,
      seccion: seccion.value.trim() || null,
      fecha_inicio: fechaInicio.value || null,
      fecha_fin: fechaFin.value || null,
      duracion_minutos: duracionMinutos.value || null,
      intentos_permitidos: intentosPermitidos.value,
    } as any)
    showModal.value = false
    await fetchAsignaciones()
    Toast.fire({ icon: 'success', title: 'Examen asignado correctamente' })
  } catch (e: any) {
    modalError.value = e.response?.data?.detail ?? 'Error al asignar'
  } finally {
    saving.value = false
  }
}

async function toggleExpand(id: number) {
  if (expanded.value === id) {
    expanded.value = null
    return
  }
  expanded.value = id
  if (!resultados.value[id]) {
    loadingResultados.value = id
    try {
      const data = await asignacionesService.getResultados(id)
      resultados.value[id] = data
    } catch {
      resultados.value[id] = []
    } finally {
      loadingResultados.value = null
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
    if (expanded.value === id) expanded.value = null
    Toast.fire({ icon: 'success', title: 'Asignación eliminada' })
  } catch (e: any) {
    Toast.fire({ icon: 'error', title: e.response?.data?.detail ?? 'Error al eliminar' })
  } finally {
    loadingDelete.value = null
  }
}

onMounted(fetchAsignaciones)

function formatFecha(iso: string | null): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })
}

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
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-violet-50/20 to-indigo-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-colors">

    <Header
      title="Mis Asignaciones"
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
              class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0">
              <BookOpen v-if="asig.tipo_examen === 'lectura'" class="w-5 h-5" />
              <Calculator v-else class="w-5 h-5" />
            </div>

            <div class="flex-1 min-w-0">
              <p class="text-sm font-bold text-slate-800 dark:text-white truncate">
                {{ asig.titulo ?? (asig.tipo_examen === 'lectura' ? 'Examen de Lectura' : 'Examen de Matemática') }}
              </p>
              <p class="text-xs text-slate-500 dark:text-slate-400">
                {{ asig.grado_nombre ?? `Grado ${asig.grado_id}` }}
                <span v-if="asig.seccion"> — Sección {{ asig.seccion }}</span>
                <span class="mx-1.5">·</span>
                Creado {{ formatFecha(asig.fecha_creacion) }}
              </p>
            </div>

            <div class="flex items-center gap-3 flex-shrink-0">
              <div class="text-center hidden sm:block">
                <p class="text-lg font-black text-emerald-600 dark:text-emerald-400">{{ asig.completados }}</p>
                <p class="text-[10px] text-slate-400">completados</p>
              </div>
              <div v-if="asig.duracion_minutos" class="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                <Clock class="w-3.5 h-3.5" />
                {{ asig.duracion_minutos }}min
              </div>
              <div v-if="asig.fecha_fin" class="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                <AlertCircle class="w-3.5 h-3.5" />
                hasta {{ formatFecha(asig.fecha_fin) }}
              </div>
            </div>

            <div class="flex items-center gap-1.5 flex-shrink-0">
              <button @click="toggleExpand(asig.id)"
                class="p-2 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors">
                <ChevronUp v-if="expanded === asig.id" class="w-4 h-4" />
                <ChevronDown v-else class="w-4 h-4" />
              </button>
              <button @click="eliminar(asig.id)" :disabled="loadingDelete === asig.id"
                class="p-2 rounded-xl hover:bg-red-50 dark:hover:bg-red-900/20 text-red-400 hover:text-red-500 transition-colors disabled:opacity-40">
                <Loader2 v-if="loadingDelete === asig.id" class="w-4 h-4 animate-spin" />
                <Trash2 v-else class="w-4 h-4" />
              </button>
            </div>
          </div>

          <!-- Resultados expandidos -->
          <div v-if="expanded === asig.id" class="border-t border-slate-100 dark:border-slate-700">
            <div v-if="loadingResultados === asig.id" class="flex justify-center py-8">
              <Loader2 class="w-6 h-6 text-violet-400 animate-spin" />
            </div>
            <template v-else>
              <div class="px-4 py-3 bg-slate-50 dark:bg-slate-700/50 flex items-center gap-2">
                <Users class="w-4 h-4 text-slate-400" />
                <span class="text-xs font-bold text-slate-600 dark:text-slate-300">
                  {{ (resultados[asig.id] ?? []).length }} resultado(s) registrado(s)
                </span>
              </div>
              <div v-if="(resultados[asig.id] ?? []).length === 0"
                class="px-4 py-6 text-center text-sm text-slate-400 dark:text-slate-500">
                Sin resultados aún
              </div>
              <div v-else class="divide-y divide-slate-100 dark:divide-slate-700">
                <div v-for="r in resultados[asig.id]" :key="r.codigo ?? r.estudiante"
                  class="flex items-center gap-3 px-4 py-3 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                  <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-100 to-indigo-100 dark:from-violet-900/30 dark:to-indigo-900/30 flex items-center justify-center flex-shrink-0">
                    <span class="text-xs font-black text-violet-600 dark:text-violet-400">
                      {{ (r.estudiante || r.codigo || '?').slice(0, 2).toUpperCase() }}
                    </span>
                  </div>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate">{{ r.estudiante || r.codigo }}</p>
                    <p class="text-[10px] text-slate-400">{{ r.codigo }} · {{ formatFecha(r.fecha) }}</p>
                  </div>
                  <div class="flex items-center gap-2 flex-shrink-0">
                    <span class="text-sm font-black text-slate-700 dark:text-slate-200">
                      {{ r.correctas }}/{{ r.total }}
                    </span>
                    <span class="text-sm font-black text-emerald-600 dark:text-emerald-400">
                      {{ r.puntaje?.toFixed(1) }}%
                    </span>
                    <span v-if="r.nivel_logro"
                      :class="nivelColors[r.nivel_logro]"
                      class="text-[10px] font-bold px-2 py-0.5 rounded-full">
                      {{ nivelLabels[r.nivel_logro] ?? r.nivel_logro }}
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </div>

        </div>
      </div>

    </main>

    <Footer />

    <!-- Modal Nueva Asignación -->
    <Teleport to="body">
      <Transition enter-active-class="transition ease-out duration-200" enter-from-class="opacity-0 scale-95"
        enter-to-class="opacity-100 scale-100" leave-active-class="transition ease-in duration-150"
        leave-from-class="opacity-100 scale-100" leave-to-class="opacity-0 scale-95">
        <div v-if="showModal"
          class="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:p-4 bg-black/50 backdrop-blur-sm"
          @click.self="showModal = false">
          <div class="relative bg-white dark:bg-slate-800 w-full sm:max-w-lg max-h-[92dvh] sm:max-h-[88vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden">

            <!-- Drag handle mobile -->
            <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0">
              <div class="w-10 h-1 rounded-full bg-slate-200 dark:bg-slate-600"></div>
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between px-5 py-4 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
                  <BookMarked class="w-4 h-4 text-white" />
                </div>
                <h2 class="text-base font-bold text-slate-800 dark:text-white">Nueva Asignación</h2>
              </div>
              <button @click="showModal = false" class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Body -->
            <div class="flex-1 min-h-0 overflow-y-auto p-5 space-y-4">

              <div v-if="modalError"
                class="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-sm border border-red-100 dark:border-red-900/50">
                <AlertCircle class="w-4 h-4 shrink-0" /> {{ modalError }}
              </div>

              <!-- Tipo de examen -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-2">Tipo de examen</label>
                <div class="grid grid-cols-2 gap-2">
                  <button type="button" @click="tipoExamen = 'lectura'; examenSeleccionadoId = null"
                    :class="['flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-semibold transition-all',
                      tipoExamen === 'lectura'
                        ? 'bg-teal-50 dark:bg-teal-900/20 border-teal-400 text-teal-700 dark:text-teal-300'
                        : 'border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-slate-300']">
                    <BookOpen class="w-4 h-4" /> Comunicación
                  </button>
                  <button type="button" @click="tipoExamen = 'matematica'; examenSeleccionadoId = null"
                    :class="['flex items-center gap-2 px-3 py-2.5 rounded-xl border text-sm font-semibold transition-all',
                      tipoExamen === 'matematica'
                        ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-400 text-indigo-700 dark:text-indigo-300'
                        : 'border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-slate-300']">
                    <Calculator class="w-4 h-4" /> Matemática
                  </button>
                </div>
              </div>

              <!-- Selección de examen -->
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
                  <button @click="router.push(tipoExamen === 'lectura' ? '/lectosistem' : '/matsistem'); showModal = false"
                    class="text-violet-600 dark:text-violet-400 font-semibold hover:underline ml-1">
                    Generar uno
                  </button>
                </div>
                <select v-else v-model="examenSeleccionadoId"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all">
                  <option :value="null">— Selecciona un examen —</option>
                  <option v-for="ex in examenesActuales" :key="ex.id" :value="ex.id">
                    {{ ex.titulo ?? 'Sin título' }}{{ ex.grado_nombre ? ` (${ex.grado_nombre})` : '' }}
                  </option>
                </select>
              </div>

              <!-- Grado -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Grado</label>
                <select v-model="gradoSeleccionadoId"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all">
                  <option :value="null">— Todos los grados —</option>
                  <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
                </select>
              </div>

              <!-- Sección -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">
                  Sección <span class="font-normal text-slate-400">(dejar vacío = todas)</span>
                </label>
                <input v-model="seccion" type="text" placeholder="Ej: A, B, Única"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all" />
              </div>

              <!-- Fechas -->
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Fecha inicio</label>
                  <input v-model="fechaInicio" type="datetime-local"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 transition-all" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Fecha límite</label>
                  <input v-model="fechaFin" type="datetime-local"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 transition-all" />
                </div>
              </div>

              <!-- Duración e intentos -->
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">
                    Duración (min) <span class="font-normal text-slate-400">(opcional)</span>
                  </label>
                  <input v-model.number="duracionMinutos" type="number" min="1" placeholder="Sin límite"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 transition-all" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Intentos permitidos</label>
                  <input v-model.number="intentosPermitidos" type="number" min="1" max="10"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 transition-all" />
                </div>
              </div>

            </div>

            <!-- Footer -->
            <div class="flex items-center justify-end gap-2 px-5 py-4 border-t border-slate-100 dark:border-slate-700 shrink-0">
              <button @click="showModal = false"
                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
                Cancelar
              </button>
              <button @click="guardar" :disabled="saving || !examenSeleccionadoId"
                class="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-violet-500 to-indigo-600 hover:from-violet-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-60 disabled:cursor-not-allowed">
                <Loader2 v-if="saving" class="w-3.5 h-3.5 animate-spin" />
                <Save v-else class="w-3.5 h-3.5" />
                Asignar examen
              </button>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>
