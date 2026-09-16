<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import {
  UserCog, Search, ArrowRightLeft, Trash2, AlertTriangle,
  Users, ChevronLeft, ChevronRight, ShieldAlert, X, Square, CheckSquare
} from 'lucide-vue-next'
import Header from '../../shared/components/Header.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import ComboBox from '../../shared/components/ComboBox.vue'
import BaseButton from '../../shared/components/BaseButton.vue'
import Swal from 'sweetalert2'
import {
  gestionEstudiantesService,
  organizacionService,
  adminUsuariosService,
} from '../../shared/services/api'
import type { EstudianteGestionItem } from '../../shared/services/api'
import type { Grado, InstitucionEducativa, Docente } from '../../shared/types'

// ── Estado ───────────────────────────────────────────────────────────────────
const estudiantes = ref<EstudianteGestionItem[]>([])
const loading = ref(true)
const selectedIds = ref<number[]>([])
const grados = ref<Grado[]>([])
const instituciones = ref<InstitucionEducativa[]>([])
const creadores = ref<Docente[]>([])

const filtroQ = ref('')
const filtroIe = ref<number | null>(null)
const filtroGrado = ref<number | null>(null)
const filtroSeccion = ref<string | null>(null)
const filtroCreador = ref<number | null>(null)

const page = ref(1)
const size = ref(20)
const total = ref(0)
const pages = ref(0)

const showTransfer = ref(false)
const savingTransfer = ref(false)
const transferForm = ref({
  nuevo_creador_id: null as number | null,
  nueva_institucion_educativa_id: null as number | null,
  nuevo_grado_id: null as number | null,
  nueva_seccion: '',
})

const seccionesOpciones = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'Única'].map(s => ({ id: s, label: s }))
const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
const gradosOpciones = computed(() => grados.value.map(g => ({ id: g.id, label: g.nombre })))
const ieOpciones = computed(() =>
  instituciones.value.map(ie => ({ id: ie.id, label: ie.nombre, group: ie.ugel_nombre || undefined }))
)
const creadoresOpciones = computed(() =>
  creadores.value.map(u => ({
    id: u.id,
    label: `${u.apellidos || ''}, ${u.nombres || ''}`.replace(/^,\s*/, '') || u.dni || `#${u.id}`,
  }))
)

const CREATOR_ROLES = ['docente', 'auxiliar', 'director']

// ── Selección ────────────────────────────────────────────────────────────────
const allSelected = computed(() =>
  estudiantes.value.length > 0 && estudiantes.value.every(e => selectedIds.value.includes(e.id))
)
const someSelected = computed(() => selectedIds.value.length > 0)

function toggleAll() {
  if (allSelected.value) {
    selectedIds.value = []
  } else {
    selectedIds.value = estudiantes.value.map(e => e.id)
  }
}
function toggleOne(id: number) {
  const idx = selectedIds.value.indexOf(id)
  if (idx > -1) selectedIds.value.splice(idx, 1)
  else selectedIds.value.push(id)
}
function limpiarSeleccion() {
  selectedIds.value = []
}

// ── Carga de datos ───────────────────────────────────────────────────────────
async function cargar(resetPage = false) {
  if (resetPage) page.value = 1
  loading.value = true
  try {
    const res = await gestionEstudiantesService.listar({
      page: page.value,
      size: size.value,
      q: filtroQ.value || undefined,
      institucion_educativa_id: filtroIe.value ?? undefined,
      grado_id: filtroGrado.value ?? undefined,
      seccion: filtroSeccion.value ?? undefined,
      creado_por_id: filtroCreador.value ?? undefined,
    })
    estudiantes.value = res.items
    total.value = res.total
    pages.value = res.pages
    // Conservar solo selecciones visibles
    const visibles = new Set(res.items.map(e => e.id))
    selectedIds.value = selectedIds.value.filter(id => visibles.has(id))
  } catch {
    Swal.fire('Error', 'No se pudo cargar la lista de estudiantes', 'error')
  } finally {
    loading.value = false
  }
}

async function cargarCatalogos() {
  try { grados.value = await organizacionService.getGrados() } catch { /* silencioso */ }
  try { instituciones.value = await organizacionService.getInstituciones() } catch { /* silencioso */ }
  try {
    const res = await adminUsuariosService.getAll(1, 500)
    creadores.value = res.items.filter(u => CREATOR_ROLES.includes(u.rol_codigo ?? ''))
  } catch { /* silencioso */ }
}

onMounted(async () => {
  await cargar()
  await cargarCatalogos()
})

let searchTimeout: ReturnType<typeof setTimeout> | null = null
watch(filtroQ, () => {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => cargar(true), 400)
})
watch([filtroIe, filtroGrado, filtroSeccion, filtroCreador], () => cargar(true))
watch(size, () => cargar(true))

function setPage(p: number) {
  if (p < 1 || p > pages.value) return
  page.value = p
  cargar()
}
function nextPage() {
  if (page.value < pages.value) {
    page.value++
    cargar()
  }
}
function prevPage() {
  if (page.value > 1) {
    page.value--
    cargar()
  }
}

// ── Transferencia ────────────────────────────────────────────────────────────
const transferFormError = computed(() => {
  if (!transferForm.value.nuevo_creador_id &&
      !transferForm.value.nueva_institucion_educativa_id &&
      !transferForm.value.nuevo_grado_id &&
      !transferForm.value.nueva_seccion.trim()) {
    return 'Indica al menos un cambio (docente, IE, grado o sección)'
  }
  return ''
})

function openTransfer() {
  if (!someSelected.value) return
  transferForm.value = {
    nuevo_creador_id: null,
    nueva_institucion_educativa_id: null,
    nuevo_grado_id: null,
    nueva_seccion: '',
  }
  showTransfer.value = true
}

async function aplicarTransfer() {
  if (transferFormError.value) return
  savingTransfer.value = true
  try {
    const res = await gestionEstudiantesService.transferir({
      estudiante_ids: selectedIds.value,
      nuevo_creador_id: transferForm.value.nuevo_creador_id ?? undefined,
      nueva_institucion_educativa_id: transferForm.value.nueva_institucion_educativa_id ?? undefined,
      nuevo_grado_id: transferForm.value.nuevo_grado_id ?? undefined,
      nueva_seccion: transferForm.value.nueva_seccion.trim() || undefined,
    })
    showTransfer.value = false
    limpiarSeleccion()
    await cargar()
    Swal.fire({
      icon: 'success',
      title: `${res.actualizados} estudiante${res.actualizados !== 1 ? 's' : ''} actualizado${res.actualizados !== 1 ? 's' : ''}`,
      showConfirmButton: false,
      timer: 2000,
    })
  } catch (e: any) {
    Swal.fire('Error', e.response?.data?.detail ?? 'No se pudo completar la transferencia', 'error')
  } finally {
    savingTransfer.value = false
  }
}

// ── Eliminación ──────────────────────────────────────────────────────────────
async function eliminarSeleccionados() {
  if (!someSelected.value) return
  const totalSeleccionados = selectedIds.value.length
  const confirm = await Swal.fire({
    title: '¿Eliminar estudiantes?',
    html: `Se eliminarán <strong>${totalSeleccionados}</strong> estudiante(s) junto con sus matrículas.<br>Esta acción no se puede deshacer.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#e11d48',
    confirmButtonText: 'Eliminar',
    cancelButtonText: 'Cancelar',
  })
  if (!confirm.isConfirmed) return

  try {
    const res = await gestionEstudiantesService.eliminar(selectedIds.value, false)
    limpiarSeleccion()
    await cargar()
    Swal.fire({
      icon: 'success',
      title: `${res.eliminados} estudiante${res.eliminados !== 1 ? 's' : ''} eliminado${res.eliminados !== 1 ? 's' : ''}`,
      showConfirmButton: false,
      timer: 2000,
    })
  } catch (e: any) {
    if (e.response?.status === 400) {
      const forzar = await Swal.fire({
        title: 'Hay intentos de examen',
        html: e.response.data.detail,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e11d48',
        confirmButtonText: 'Eliminar de todas formas',
        cancelButtonText: 'Cancelar',
      })
      if (!forzar.isConfirmed) return
      try {
        const res = await gestionEstudiantesService.eliminar(selectedIds.value, true)
        limpiarSeleccion()
        await cargar()
        Swal.fire({
          icon: 'success',
          title: `${res.eliminados} eliminado(s)`,
          html: `Se borraron también ${res.intentos_eliminados} intento(s) de examen.`,
          showConfirmButton: false,
          timer: 2600,
        })
      } catch (e2: any) {
        Swal.fire('Error', e2.response?.data?.detail ?? 'No se pudo eliminar', 'error')
      }
    } else {
      Swal.fire('Error', e.response?.data?.detail ?? 'No se pudo eliminar', 'error')
    }
  }
}

function nombreEstudiante(e: EstudianteGestionItem) {
  return [e.apellidos, e.nombres].filter(Boolean).join(', ') || e.codigo_estudiante || e.dni || `#${e.id}`
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950">
    <EduBackground variant="teal" />
    <Header title="Administración" subtitle="Gestión de Estudiantes" :show-home="true" />

    <div class="flex-1 w-full max-w-7xl mx-auto p-4 md:p-8 relative z-10 overflow-hidden flex flex-col">
      <!-- Encabezado -->
      <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-xl shadow-amber-500/20 shrink-0">
            <UserCog class="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 class="text-2xl font-black text-slate-800 dark:text-white tracking-tight leading-none">Gestión de Estudiantes</h2>
            <p class="text-sm font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mt-1.5 flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
              {{ total }} encontrados
            </p>
          </div>
        </div>
      </div>

      <!-- Barra de acciones de selección -->
      <div v-if="someSelected" class="mb-4 flex flex-col sm:flex-row items-center justify-between gap-3 p-4 rounded-2xl border-2 border-amber-200 dark:border-amber-900/50 bg-amber-50 dark:bg-amber-900/20 shadow-sm">
        <div class="flex items-center gap-2 text-amber-700 dark:text-amber-300 text-sm font-bold">
          <ShieldAlert class="w-5 h-5" />
          {{ selectedIds.length }} seleccionado{{ selectedIds.length !== 1 ? 's' : '' }}
        </div>
        <div class="flex items-center gap-2 w-full sm:w-auto">
          <BaseButton variant="secondary" size="sm" class="flex-1 sm:flex-none" @click="limpiarSeleccion">
            Limpiar
          </BaseButton>
          <BaseButton variant="secondary" size="sm" class="flex-1 sm:flex-none" @click="openTransfer">
            <template #icon><ArrowRightLeft class="w-4 h-4 text-indigo-500" /></template>
            Transferir
          </BaseButton>
          <BaseButton variant="primary" size="sm" class="flex-1 sm:flex-none !bg-rose-600 hover:!bg-rose-700" @click="eliminarSeleccionados">
            <template #icon><Trash2 class="w-4 h-4" /></template>
            Eliminar
          </BaseButton>
        </div>
      </div>

      <!-- Filtros -->
      <div class="mb-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 p-6 bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm">
        <div class="space-y-2 lg:col-span-2">
          <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1 flex items-center gap-1.5"><Search class="w-3 h-3" /> Buscar</label>
          <input v-model="filtroQ" type="text" placeholder="Nombre, DNI o código"
            class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-amber-500/50 focus:border-amber-500 transition-all font-bold" />
        </div>
        <div class="space-y-2">
          <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Institución</label>
          <ComboBox v-model="filtroIe" :options="ieOpciones" placeholder="Todas" searchable />
        </div>
        <div class="space-y-2">
          <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Grado</label>
          <ComboBox v-model="filtroGrado" :options="gradosOpciones" placeholder="Todos" />
        </div>
        <div class="space-y-2">
          <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Sección</label>
          <ComboBox v-model="filtroSeccion" :options="seccionesOpciones" placeholder="Todas" />
        </div>
        <div class="space-y-2 lg:col-span-2">
          <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Docente creador</label>
          <ComboBox v-model="filtroCreador" :options="creadoresOpciones" placeholder="Todos" searchable />
        </div>
      </div>

      <!-- Lista -->
      <div class="flex-1 min-h-0 bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden flex flex-col">
        <!-- Cabecera de tabla (desktop) -->
        <div class="hidden md:grid grid-cols-[40px_1.6fr_1fr_1fr_0.8fr_0.7fr] gap-3 items-center px-4 py-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 text-[10px] font-black uppercase tracking-widest text-slate-400">
          <button @click="toggleAll" class="flex items-center justify-center text-slate-400 hover:text-amber-500 transition-colors cursor-pointer">
            <CheckSquare v-if="allSelected" class="w-5 h-5" />
            <Square v-else class="w-5 h-5" />
          </button>
          <span>Estudiante</span>
          <span>Institución</span>
          <span>Creador</span>
          <span>Grado / Secc.</span>
          <span class="text-center">Intentos</span>
        </div>

        <div v-if="loading" class="flex-1 flex items-center justify-center py-20">
          <div class="flex items-center gap-3 text-slate-400 font-bold text-sm">
            <span class="w-5 h-5 border-2 border-amber-500 border-t-transparent rounded-full animate-spin"></span>
            Cargando...
          </div>
        </div>

        <div v-else-if="estudiantes.length === 0" class="flex-1 flex flex-col items-center justify-center py-20 text-center px-6">
          <Users class="w-10 h-10 text-slate-300 dark:text-slate-600 mb-3" />
          <p class="text-sm font-bold text-slate-400">No se encontraron estudiantes con esos filtros</p>
        </div>

        <div v-else class="flex-1 overflow-y-auto custom-scrollbar divide-y divide-slate-100 dark:divide-slate-700/50">
          <div v-for="est in estudiantes" :key="est.id"
            class="grid grid-cols-1 md:grid-cols-[40px_1.6fr_1fr_1fr_0.8fr_0.7fr] gap-3 items-center px-4 py-3 transition-colors"
            :class="selectedIds.includes(est.id) ? 'bg-amber-50 dark:bg-amber-900/10' : 'hover:bg-slate-50 dark:hover:bg-slate-700/30'">
            <button @click="toggleOne(est.id)" class="hidden md:flex items-center justify-center text-slate-400 hover:text-amber-500 transition-colors cursor-pointer">
              <CheckSquare v-if="selectedIds.includes(est.id)" class="w-5 h-5 text-amber-500" />
              <Square v-else class="w-5 h-5" />
            </button>

            <div class="flex items-center gap-3 min-w-0">
              <button @click="toggleOne(est.id)" class="md:hidden shrink-0 text-slate-400">
                <CheckSquare v-if="selectedIds.includes(est.id)" class="w-5 h-5 text-amber-500" />
                <Square v-else class="w-5 h-5" />
              </button>
              <div class="min-w-0">
                <p class="text-sm font-black text-slate-800 dark:text-white truncate">{{ nombreEstudiante(est) }}</p>
                <p class="text-[11px] font-bold text-slate-400 font-mono">{{ est.codigo_estudiante || '—' }} · DNI {{ est.dni || '—' }}</p>
              </div>
              <span v-if="!est.is_active" class="ml-auto md:hidden shrink-0 px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-200 text-slate-500 dark:bg-slate-700 dark:text-slate-300">INACTIVO</span>
            </div>

            <div class="min-w-0 text-xs font-bold text-slate-500 dark:text-slate-300">
              <span class="md:hidden text-[9px] uppercase tracking-widest text-slate-400 mr-1">IE:</span>
              {{ est.institucion_nombre || '—' }}
            </div>
            <div class="min-w-0 text-xs font-bold text-slate-500 dark:text-slate-300 truncate">
              <span class="md:hidden text-[9px] uppercase tracking-widest text-slate-400 mr-1">Creador:</span>
              {{ est.creado_por_nombre || '—' }}
            </div>
            <div class="text-xs font-bold text-slate-500 dark:text-slate-300">
              <span class="md:hidden text-[9px] uppercase tracking-widest text-slate-400 mr-1">Grado:</span>
              {{ est.grado_nombre || '—' }}<span v-if="est.seccion"> · {{ est.seccion }}</span>
            </div>
            <div class="text-center">
              <span class="inline-flex items-center justify-center min-w-[24px] h-6 px-2 rounded-full text-[10px] font-black"
                :class="est.intentos > 0 ? 'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/30 dark:text-indigo-300' : 'bg-slate-100 text-slate-400 dark:bg-slate-700 dark:text-slate-400'">
                {{ est.intentos }}
              </span>
            </div>
          </div>
        </div>

        <!-- Paginación -->
        <div v-if="!loading && estudiantes.length > 0" class="px-4 py-3 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex flex-col sm:flex-row items-center justify-between gap-4">
          <!-- Izquierda: info + tamaño de página -->
          <div class="flex items-center gap-4 flex-wrap justify-center">
            <p class="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
              Mostrando
              <span class="font-bold text-slate-700 dark:text-slate-200">{{ total === 0 ? 0 : (page - 1) * size + 1 }}</span>
              –
              <span class="font-bold text-slate-700 dark:text-slate-200">{{ Math.min(page * size, total) }}</span>
              de
              <span class="font-bold text-slate-700 dark:text-slate-200">{{ total }}</span>
            </p>
            <div class="flex items-center gap-1">
              <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest mr-1">Por página</span>
              <button v-for="n in PAGE_SIZE_OPTIONS" :key="n" @click="size = n"
                :class="['h-7 px-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer',
                  size === n
                    ? 'bg-amber-500 text-white shadow-sm'
                    : 'bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-slate-500 dark:text-slate-400 hover:border-amber-400 hover:text-amber-600']">
                {{ n }}
              </button>
            </div>
          </div>
          <!-- Derecha: navegación de páginas -->
          <div v-if="pages > 1" class="flex items-center gap-1">
            <button @click="prevPage" :disabled="page === 1"
              class="p-2 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
              <ChevronLeft class="w-4 h-4" />
            </button>
            <div class="flex items-center gap-1 mx-1">
              <template v-for="p in pages" :key="p">
                <button v-if="p === 1 || p === pages || Math.abs(p - page) <= 1"
                  @click="setPage(p)"
                  :class="['w-8 h-8 rounded-lg text-xs font-bold transition-all cursor-pointer',
                    page === p
                      ? 'bg-amber-500 text-white shadow-md scale-110'
                      : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700']">
                  {{ p }}
                </button>
                <span v-else-if="p === page - 2 || p === page + 2"
                  class="w-8 h-8 flex items-center justify-center text-slate-400 text-xs">…</span>
              </template>
            </div>
            <button @click="nextPage" :disabled="page === pages"
              class="p-2 rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal: Transferir -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showTransfer" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-900/60 backdrop-blur-sm" @click.self="showTransfer = false">
          <div class="w-full max-w-lg overflow-hidden rounded-t-2xl sm:rounded-2xl bg-white shadow-2xl dark:bg-slate-800 relative">
            <div class="flex items-center justify-between border-b border-slate-300 p-6 dark:border-slate-700">
              <div class="flex items-center gap-4">
                <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 shadow-lg shadow-indigo-500/20">
                  <ArrowRightLeft class="h-6 w-6 text-white" />
                </div>
                <div>
                  <h2 class="text-lg font-black text-slate-800 dark:text-white tracking-tight">Transferir estudiantes</h2>
                  <p class="text-xs text-slate-500 font-bold uppercase tracking-widest">{{ selectedIds.length }} seleccionado(s)</p>
                </div>
              </div>
              <button @click="showTransfer = false" class="p-2 text-slate-400"><X class="h-5 w-5" /></button>
            </div>
            <div class="space-y-5 p-6">
              <div class="rounded-xl border border-indigo-100 bg-indigo-50/50 p-4 text-xs font-bold text-indigo-700 dark:border-indigo-900/40 dark:bg-indigo-900/20 dark:text-indigo-300 flex items-start gap-3">
                <AlertTriangle class="w-5 h-5 shrink-0" />
                <p>Solo se aplicarán los campos que completes. Si cambias el docente y dejas la institución vacía, los estudiantes pasarán a la institución de ese docente.</p>
              </div>
              <div class="space-y-1.5">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nuevo docente creador</label>
                <ComboBox v-model="transferForm.nuevo_creador_id" :options="creadoresOpciones" placeholder="Sin cambio" searchable />
              </div>
              <div class="space-y-1.5">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nueva institución educativa</label>
                <ComboBox v-model="transferForm.nueva_institucion_educativa_id" :options="ieOpciones" placeholder="Seguir al docente" searchable />
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nuevo grado</label>
                  <ComboBox v-model="transferForm.nuevo_grado_id" :options="gradosOpciones" placeholder="Sin cambio" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nueva sección</label>
                  <ComboBox v-model="transferForm.nueva_seccion" :options="seccionesOpciones" placeholder="Sin cambio" />
                </div>
              </div>
              <p v-if="transferFormError" class="text-[10px] font-bold text-amber-600 uppercase">{{ transferFormError }}</p>
            </div>
            <div class="flex flex-col sm:flex-row gap-3 p-6 bg-slate-50 dark:bg-slate-900/50">
              <BaseButton variant="secondary" size="md" class="flex-1" @click="showTransfer = false">Cancelar</BaseButton>
              <BaseButton variant="primary" size="md" class="flex-1" :disabled="savingTransfer || !!transferFormError" :loading="savingTransfer" @click="aplicarTransfer">
                Aplicar cambios
              </BaseButton>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>
