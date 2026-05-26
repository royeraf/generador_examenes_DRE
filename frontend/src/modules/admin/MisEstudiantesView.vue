<script setup lang="ts">
import * as XLSX from 'xlsx'
import { ref, computed, onMounted, onUnmounted, useTemplateRef, watch } from 'vue'
import {
  docenteEstudiantesService,
  organizacionService,
  type EstudianteDocente,
  type ImportarEstudianteFilaPayload,
  type RegistrarEstudianteDirectoPayload,
} from '../../shared/services/api'
import type { Grado } from '../../shared/types'
import Header from '../../shared/components/Header.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import ComboBox from '../../shared/components/ComboBox.vue'
import Swal from 'sweetalert2'
import {
  Plus, Edit2, Search, X, Eye, EyeOff,
  GraduationCap, Loader2, AlertCircle, CheckCircle, Users, Download, FileSpreadsheet,
  Filter, ChevronDown, ChevronLeft, ChevronRight, CalendarPlus
} from 'lucide-vue-next'

// ── State ────────────────────────────────────────────────────────────────────
const estudiantes = ref<EstudianteDocente[]>([])
const grados = ref<Grado[]>([])
const loading = ref(true)
const showModal = ref(false)
const editingId = ref<number | null>(null)
const saving = ref(false)
const serverError = ref('')
const successCodigo = ref('')
const showSuccessModal = ref(false)
const showImportModal = ref(false)
const importing = ref(false)
const selectedImportFileName = ref('')
const nominaFileInput = useTemplateRef<HTMLInputElement>('nominaFileInput')
const currentEditStudent = ref<EstudianteDocente | null>(null)

// Nueva matrícula / avance de año
const showAdvanceModal = ref(false)
const advancingId = ref<number | null>(null)
const advancing = ref(false)
const advanceForm = ref({ grado_id: 0, seccion: '', año_escolar: new Date().getFullYear() + 1 })
const advanceServerError = ref('')

// Responsive State
const isDesktop = ref(window.innerWidth >= 1024)
const onResize = () => { isDesktop.value = window.innerWidth >= 1024 }
onMounted(() => {
  window.addEventListener('resize', onResize)
  cargarEstudiantes()
  cargarGrados()
})
onUnmounted(() => window.removeEventListener('resize', onResize))
const mobileTab = ref<'filtros' | 'estudiantes'>('estudiantes')

// Filtros
const filtroQ = ref('')
const filtroGrado = ref<number | null>(null)
const filtroSeccion = ref('')

const gradosOpciones = computed(() => [
  { id: null, label: 'Todos los grados' },
  ...grados.value.map(g => ({ id: g.id, label: g.nombre })),
])

const gradosOpcionesForm = computed(() =>
  grados.value.map(g => ({ id: g.id, label: g.nombre }))
)

const seccionesOpciones = ['A','B','C','D','E','F','G','H','I','J','Única'].map(s => ({ id: s, label: s }))

// Formulario
const form = ref<RegistrarEstudianteDirectoPayload>({
  nombres: '',
  apellidos: '',
  dni: '',
  password: '',
  grado_id: 0,
  seccion: '',
})
const showPass = ref(false)
const importForm = ref({
  grado_id: 0,
  seccion: '',
})

// ── Computed ─────────────────────────────────────────────────────────────────
const formError = computed(() => {
  if (!form.value.nombres.trim()) return 'Los nombres son requeridos'
  if (!form.value.apellidos.trim()) return 'Los apellidos son requeridos'
  if (!form.value.grado_id) return 'El grado es requerido'
  if (!form.value.seccion.trim()) return 'La sección es requerida'
  if (!editingId.value && form.value.password.length < 4) return 'La contraseña debe tener al menos 4 caracteres'
  if (form.value.dni && !/^\d{8}$/.test(form.value.dni)) return 'El DNI debe tener exactamente 8 dígitos'
  return ''
})

const estudiantesFiltrados = computed(() => {
  return estudiantes.value.filter(e => {
    const q = filtroQ.value.toLowerCase()
    if (q && !(
      (e.nombres || '').toLowerCase().includes(q) ||
      (e.apellidos || '').toLowerCase().includes(q) ||
      (e.dni || '').includes(q) ||
      (e.codigo_estudiante || '').toLowerCase().includes(q)
    )) return false
    if (filtroGrado.value && e.grado_id !== filtroGrado.value) return false
    if (filtroSeccion.value && e.seccion !== filtroSeccion.value) return false
    return true
  })
})

const importFormError = computed(() => {
  if (!importForm.value.grado_id) return 'Selecciona el grado de la nómina'
  if (!importForm.value.seccion.trim()) return 'La sección es requerida'
  if (!selectedImportFileName.value) return 'Selecciona el archivo Excel de la nómina'
  return ''
})

const advanceFormError = computed(() => {
  if (!advanceForm.value.grado_id) return 'El grado es requerido'
  if (!advanceForm.value.seccion.trim()) return 'La sección es requerida'
  if (!advanceForm.value.año_escolar || advanceForm.value.año_escolar < 2020) return 'Año escolar inválido'
  return ''
})

const editingPendingUser = computed(() =>
  Boolean(editingId.value && currentEditStudent.value && !currentEditStudent.value.codigo_estudiante)
)

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]
const currentPage = ref(1)
const pageSize = ref(20)
const totalPages = computed(() => Math.ceil(estudiantesFiltrados.value.length / pageSize.value))
const paginados = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return estudiantesFiltrados.value.slice(start, start + pageSize.value)
})

watch([filtroQ, filtroGrado, filtroSeccion], () => { currentPage.value = 1 })
watch(pageSize, () => { currentPage.value = 1 })

// ── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  const onResize = () => {
    isDesktop.value = window.innerWidth >= 1024
  }
  window.addEventListener('resize', onResize)
  await Promise.all([cargarEstudiantes(), cargarGrados()])
})

onUnmounted(() => {
  window.removeEventListener('resize', () => {})
})

async function cargarEstudiantes() {
  loading.value = true
  try {
    estudiantes.value = await docenteEstudiantesService.getMisEstudiantes()
  } catch {
    Swal.fire('Error', 'No se pudo cargar la lista de estudiantes', 'error')
  } finally {
    loading.value = false
  }
}

async function cargarGrados() {
  try {
    grados.value = await organizacionService.getGrados()
  } catch { /* silencioso */ }
}

// ── Modal ────────────────────────────────────────────────────────────────────
function openCreate() {
  currentEditStudent.value = null
  editingId.value = null
  serverError.value = ''
  showPass.value = false
  form.value = { nombres: '', apellidos: '', dni: '', password: '', grado_id: grados.value[0]?.id || 0, seccion: '' }
  showModal.value = true
}

function openEdit(e: EstudianteDocente) {
  currentEditStudent.value = e
  editingId.value = e.id
  serverError.value = ''
  showPass.value = false
  form.value = {
    nombres: e.nombres || '',
    apellidos: e.apellidos || '',
    dni: e.dni || '',
    password: '',
    grado_id: e.grado_id || 0,
    seccion: e.seccion || '',
  }
  showModal.value = true
}

function closeModal() {
  showModal.value = false
  currentEditStudent.value = null
}

function openImport() {
  importForm.value = { grado_id: grados.value[0]?.id || 0, seccion: '' }
  selectedImportFileName.value = ''
  showImportModal.value = true
}

function closeImportModal() {
  showImportModal.value = false
  selectedImportFileName.value = ''
  if (nominaFileInput.value) nominaFileInput.value.value = ''
}

function openNuevaMatricula(est: EstudianteDocente) {
  advancingId.value = est.id
  advanceServerError.value = ''
  advanceForm.value = {
    grado_id: est.grado_id || 0,
    seccion: est.seccion || '',
    año_escolar: new Date().getFullYear() + 1,
  }
  showAdvanceModal.value = true
}

function closeAdvanceModal() {
  showAdvanceModal.value = false
  advancingId.value = null
}

// ── Actions ──────────────────────────────────────────────────────────────────
async function guardar() {
  if (formError.value) return
  serverError.value = ''
  saving.value = true
  try {
    const payload: RegistrarEstudianteDirectoPayload = {
      nombres: form.value.nombres.trim(),
      apellidos: form.value.apellidos.trim(),
      dni: form.value.dni?.trim() || null,
      password: form.value.password,
      grado_id: form.value.grado_id,
      seccion: form.value.seccion.trim(),
    }

    if (editingId.value) {
      await docenteEstudiantesService.actualizar(editingId.value, payload)
      closeModal()
      Swal.fire({ icon: 'success', title: 'Estudiante actualizado', showConfirmButton: false, timer: 1800 })
    } else {
      const res = await docenteEstudiantesService.registrar(payload)
      closeModal()
      successCodigo.value = res.codigo_estudiante
      showSuccessModal.value = true
    }
    await cargarEstudiantes()
  } catch (e: any) {
    serverError.value = e.response?.data?.detail ?? 'Error al guardar'
  } finally {
    saving.value = false
  }
}

async function avanzarAño() {
  if (advanceFormError.value || !advancingId.value) return
  advanceServerError.value = ''
  advancing.value = true
  try {
    await docenteEstudiantesService.nuevaMatricula(advancingId.value, {
      grado_id: advanceForm.value.grado_id,
      seccion: advanceForm.value.seccion.trim(),
      año_escolar: advanceForm.value.año_escolar,
    })
    closeAdvanceModal()
    await cargarEstudiantes()
    Swal.fire({ icon: 'success', title: 'Nueva matrícula creada', showConfirmButton: false, timer: 1800 })
  } catch (e: any) {
    advanceServerError.value = e.response?.data?.detail ?? 'Error al crear la matrícula'
  } finally {
    advancing.value = false
  }
}

function exportarExcel() {
  const wsData = [['nombres', 'apellidos', 'dni', 'codigo', 'grado', 'sección']]
  estudiantes.value.forEach(e => {
    wsData.push([e.nombres || '', e.apellidos || '', e.dni || '', e.codigo_estudiante || '', e.grado_nombre || '', e.seccion || ''])
  })
  const ws = XLSX.utils.aoa_to_sheet(wsData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Estudiantes')
  XLSX.writeFile(wb, `estudiantes_${new Date().toISOString().split('T')[0]}.xlsx`)
}

function descargarPlantillaNomina() {
  const wsData = [['dni', 'nombres', 'apellidos'], ['12345678', 'María Fernanda', 'García López']]
  const ws = XLSX.utils.aoa_to_sheet(wsData)
  const wb = XLSX.utils.book_new()
  XLSX.utils.book_append_sheet(wb, ws, 'Nomina')
  XLSX.writeFile(wb, 'plantilla_nomina.xlsx')
}

function seleccionarArchivoNomina() {
  nominaFileInput.value?.click()
}

async function onNominaFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) selectedImportFileName.value = file.name
}

async function importarNomina() {
  if (importFormError.value) return
  const file = nominaFileInput.value?.files?.[0]
  if (!file) return
  importing.value = true
  try {
    const data = new Uint8Array(await file.arrayBuffer())
    const workbook = XLSX.read(data, { type: 'array' })
    const sheetName = workbook.SheetNames[0]
    if (!sheetName) throw new Error('El archivo Excel está vacío')
    const sheet = workbook.Sheets[sheetName]
    if (!sheet) throw new Error('No se encontró la hoja en el archivo')
    const rows = XLSX.utils.sheet_to_json<any[]>(sheet, { header: 1, defval: '' })
    
    // Obtener filas válidas
    const estudiantesImportados: ImportarEstudianteFilaPayload[] = rows.slice(1)
        .filter(r => r[0] && r[1] && r[2]) // Asegurar que tenga DNI, nombres y apellidos
        .map(r => ({ 
            dni: String(r[0]).trim(), 
            nombres: String(r[1]).trim(), 
            apellidos: String(r[2]).trim() 
        }))

    if (estudiantesImportados.length === 0) {
        throw new Error('No se encontraron estudiantes válidos en el archivo')
    }

    await docenteEstudiantesService.importarNomina({
      grado_id: importForm.value.grado_id,
      seccion: importForm.value.seccion.trim(),
      estudiantes: estudiantesImportados,
    })
    closeImportModal()
    await cargarEstudiantes()
    Swal.fire('Éxito', 'Nómina importada correctamente', 'success')
  } catch (error: any) {
    Swal.fire('Error', error.message || 'No se pudo importar la nómina', 'error')
  } finally {
    importing.value = false
  }
}

async function toggle(est: EstudianteDocente) {
  const nombre = [est.apellidos, est.nombres].filter(Boolean).join(', ') || est.codigo_estudiante || `#${est.id}`
  const accion = est.is_active ? 'desactivar' : 'activar'
  const result = await Swal.fire({
    title: est.is_active ? '¿Desactivar estudiante?' : '¿Activar estudiante?',
    html: `¿Seguro de <strong>${accion}</strong> a <strong>${nombre}</strong>?`,
    icon: 'question',
    showCancelButton: true,
    confirmButtonColor: est.is_active ? '#64748b' : '#14b8a6',
    confirmButtonText: est.is_active ? 'Desactivar' : 'Activar',
    cancelButtonText: 'Cancelar',
  })
  if (result.isConfirmed) {
    try {
      const { is_active } = await docenteEstudiantesService.toggle(est.id)
      est.is_active = is_active
    } catch {
      Swal.fire('Error', `No se pudo ${accion} el estudiante`, 'error')
    }
  }
}

function nombreGrado(id: number | null) {
  return grados.value.find(g => g.id === id)?.nombre ?? '—'
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-surface">
    <EduBackground variant="teal" />
    <Header title="Gestión" subtitle="Mis Estudiantes" :show-home="true" />
    <div class="flex-1 w-full max-w-7xl mx-auto p-4 md:p-8 relative z-10 overflow-hidden flex flex-col">
      
      <!-- Mobile Navigation Tabs -->
      <div v-if="!isDesktop" class="shrink-0 flex items-center justify-around bg-surface-card rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-1.5 mb-6 shadow-sm">
        <button @click="mobileTab = 'filtros'" 
          class="flex-1 py-2.5 flex flex-col items-center justify-center gap-1 rounded-xl transition-all" 
          :class="mobileTab === 'filtros' ? 'text-primary bg-teal-50 dark:bg-emerald-900/30' : 'text-slate-500'">
          <Filter class="w-5 h-5" />
          <span class="text-[10px] font-black uppercase tracking-widest">Filtros</span>
        </button>
        <button @click="mobileTab = 'estudiantes'" 
          class="flex-1 py-2.5 flex flex-col items-center justify-center gap-1 rounded-xl transition-all" 
          :class="mobileTab === 'estudiantes' ? 'text-primary bg-teal-50 dark:bg-emerald-900/30' : 'text-slate-500'">
          <Users class="w-5 h-5" />
          <span class="text-[10px] font-black uppercase tracking-widest">Estudiantes</span>
        </button>
      </div>

      <!-- Header & Actions -->
      <div v-show="isDesktop || mobileTab === 'filtros'" class="mb-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6 animate-in fade-in slide-in-from-top-4 duration-500">
        <div class="flex items-center gap-5">
          <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center shadow-xl shadow-teal-500/20 shrink-0">
            <Users class="w-7 h-7 text-white" />
          </div>
          <div>
            <h2 class="text-2xl font-black text-text tracking-tight leading-none">Mis Estudiantes</h2>
            <p class="text-sm font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest mt-1.5 flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-teal-500 animate-pulse"></span>
              {{ estudiantes.length }} registrados
            </p>
          </div>
        </div>
        
        <div class="flex items-center gap-3 flex-wrap">
          <button @click="openCreate" class="flex-1 lg:flex-none flex items-center justify-center gap-3 bg-slate-900 dark:bg-white text-white dark:text-text-inverse font-black px-6 py-3.5 rounded-2xl shadow-xl hover:-translate-y-1 transition-all active:scale-95 text-xs uppercase tracking-widest">
            <Plus class="w-5 h-5" /> Nuevo Alumno
          </button>
          <div class="flex items-center gap-2 flex-1 lg:flex-none">
            <button @click="exportarExcel" class="flex-1 lg:flex-none flex items-center justify-center gap-2 bg-surface-card text-slate-600 dark:text-text-muted font-bold px-5 py-3.5 rounded-2xl border-2 border-slate-200 dark:border-slate-700 hover:bg-slate-50 transition-all text-xs uppercase tracking-widest">
              <Download class="w-4 h-4 text-teal-500" /> Exportar
            </button>
            <button @click="openImport" class="flex-1 lg:flex-none flex items-center justify-center gap-2 bg-surface-card text-slate-600 dark:text-text-muted font-bold px-5 py-3.5 rounded-2xl border-2 border-slate-200 dark:border-slate-700 hover:bg-slate-50 transition-all text-xs uppercase tracking-widest">
              <FileSpreadsheet class="w-4 h-4 text-emerald-500" /> Importar
            </button>
          </div>
        </div>
      </div>

      <!-- Filters -->
      <div v-show="isDesktop || mobileTab === 'filtros'" class="mb-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-6 bg-surface-card rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm animate-in fade-in slide-in-from-top-2 duration-700">
        <div class="space-y-2">
          <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Filtrar Grado</label>
          <ComboBox v-model="filtroGrado" :options="gradosOpciones" placeholder="Todos los grados" />
        </div>
        <div class="space-y-2">
          <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Sección</label>
          <div class="relative">
            <select v-model="filtroSeccion" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none appearance-none cursor-pointer">
              <option value="">Todas las secciones</option>
              <option v-for="sec in ['A','B','C','D','E','F','G','H','I','J','Única']" :key="sec" :value="sec">{{ sec }}</option>
            </select>
            <ChevronDown class="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
          </div>
        </div>
        <div class="sm:col-span-2 space-y-2">
          <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Búsqueda Rápida</label>
          <div class="relative">
            <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input v-model="filtroQ" type="text" placeholder="Nombre, apellido o DNI..." class="w-full pl-12 pr-4 py-2.5 bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl text-sm font-bold outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all placeholder-slate-400" />
          </div>
        </div>
      </div>

      <!-- Main Content -->
      <div v-show="isDesktop || mobileTab === 'estudiantes'" class="flex-1 flex flex-col min-h-0">
        
        <!-- Desktop View: Table -->
        <div v-if="isDesktop" class="bg-surface-card rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden flex flex-col">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full border-collapse text-sm">
              <thead>
                <tr class="bg-surface border-b-2 border-slate-100 dark:border-slate-700">
                  <th class="p-4 text-left font-black text-slate-500 uppercase text-xs">Estudiante</th>
                  <th class="p-4 text-left font-black text-slate-500 uppercase text-xs">Código</th>
                  <th class="p-4 text-left font-black text-slate-500 uppercase text-xs">DNI</th>
                  <th class="p-4 text-left font-black text-slate-500 uppercase text-xs">Grado/Sección</th>
                  <th class="p-4 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr v-for="est in paginados" :key="est.id" class="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors" :class="!est.is_active ? 'opacity-50' : ''">
                  <td class="p-4">
                    <div class="flex items-center gap-3">
                      <div class="w-10 h-10 rounded-xl bg-teal-50 dark:bg-emerald-900/30 flex items-center justify-center font-black text-teal-600">
                  {{ (est.nombres || '?').charAt(0) }}{{ (est.apellidos || '?').charAt(0) }}
                      </div>
                      <span class="font-bold text-text">{{ est.apellidos }}, {{ est.nombres }}</span>
                    </div>
                  </td>
                  <td class="p-4">
                    <span class="font-mono font-black text-teal-600 bg-teal-50 dark:bg-emerald-900/20 px-3 py-1 rounded-full text-xs">
                      {{ est.codigo_estudiante || 'Pendiente' }}
                    </span>
                  </td>
                  <td class="p-4 font-medium text-slate-600 dark:text-text-muted">{{ est.dni || '—' }}</td>
                  <td class="p-4 text-xs font-black uppercase text-slate-500">
                    {{ nombreGrado(est.grado_id) }} · <span class="text-emerald-500">{{ est.seccion }}</span>
                  </td>
                  <td class="p-4 text-right">
                    <div class="flex items-center justify-end gap-3">
                      <button @click="openNuevaMatricula(est)" title="Nueva matrícula / avance de año" class="p-2.5 rounded-xl text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition-all"><CalendarPlus class="w-4 h-4" /></button>
                      <button @click="openEdit(est)" class="p-2.5 rounded-xl text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition-all"><Edit2 class="w-4 h-4" /></button>
                      <button @click="toggle(est)" title="Activar / Desactivar"
                        class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 cursor-pointer focus:outline-none"
                        :class="est.is_active ? 'bg-teal-500' : 'bg-slate-300 dark:bg-surface-elevated'">
                        <span class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200"
                          :class="est.is_active ? 'translate-x-6' : 'translate-x-1'" />
                      </button>
                    </div>
                  </td>
                </tr>
                <tr v-if="estudiantesFiltrados.length === 0">
                  <td colspan="5" class="p-12 text-center text-slate-400 font-bold uppercase tracking-widest text-xs">Sin resultados</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Pagination (desktop) -->
          <div class="px-6 py-4 bg-surface-input/30 border-t border-slate-200 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">
            <!-- Left: count info + page size selector -->
            <div class="flex items-center gap-4 flex-wrap">
              <p class="text-xs text-slate-500 dark:text-text-muted whitespace-nowrap">
                Mostrando
                <span class="font-bold text-slate-700 dark:text-text">{{ estudiantesFiltrados.length === 0 ? 0 : (currentPage - 1) * pageSize + 1 }}</span>
                –
                <span class="font-bold text-slate-700 dark:text-text">{{ Math.min(currentPage * pageSize, estudiantesFiltrados.length) }}</span>
                de
                <span class="font-bold text-slate-700 dark:text-text">{{ estudiantesFiltrados.length }}</span>
              </p>
              <div class="flex items-center gap-1">
                <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest mr-1">Por página</span>
                <button v-for="n in PAGE_SIZE_OPTIONS" :key="n" @click="pageSize = n"
                  :class="['h-7 px-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer',
                    pageSize === n
                      ? 'bg-teal-600 text-white shadow-sm'
                      : 'bg-surface-card border border-slate-300 dark:border-slate-600 text-slate-500 dark:text-text-muted hover:border-teal-400 hover:text-teal-600']">
                  {{ n }}
                </button>
              </div>
            </div>
            <!-- Right: page navigation -->
            <div v-if="totalPages > 1" class="flex items-center gap-1">
              <button @click="currentPage--" :disabled="currentPage === 1"
                class="p-2 rounded-xl border border-slate-300 dark:border-slate-600 bg-surface-card text-slate-600 dark:text-text-muted hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
                <ChevronLeft class="w-4 h-4" />
              </button>
              <div class="flex items-center gap-1 mx-1">
                <template v-for="p in totalPages" :key="p">
                  <button v-if="p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1"
                    @click="currentPage = p"
                    :class="['w-8 h-8 rounded-lg text-xs font-bold transition-all cursor-pointer',
                      currentPage === p
                        ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white shadow-md scale-110'
                        : 'text-slate-600 dark:text-text-muted hover:bg-slate-100 dark:hover:bg-slate-700']">
                    {{ p }}
                  </button>
                  <span v-else-if="p === currentPage - 2 || p === currentPage + 2"
                    class="w-8 h-8 flex items-center justify-center text-slate-400 text-xs">…</span>
                </template>
              </div>
              <button @click="currentPage++" :disabled="currentPage === totalPages"
                class="p-2 rounded-xl border border-slate-300 dark:border-slate-600 bg-surface-card text-slate-600 dark:text-text-muted hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
                <ChevronRight class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>

        <!-- Mobile View: Cards -->
        <div v-else class="flex-1 overflow-y-auto space-y-4 pb-4">
          <div v-for="est in paginados" :key="est.id" class="bg-surface-card p-5 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-500" :class="!est.is_active ? 'opacity-50' : ''">
            <div class="flex justify-between items-start mb-4">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-2xl bg-surface-input flex items-center justify-center font-black text-teal-600 text-lg">
                  {{ (est.nombres || '?').charAt(0) }}{{ (est.apellidos || '?').charAt(0) }}
                </div>
                <div>
                  <h3 class="font-black text-text tracking-tight">{{ est.apellidos }}, {{ est.nombres }}</h3>
                  <p class="text-[11px] font-black text-slate-400 uppercase tracking-widest mt-1">{{ nombreGrado(est.grado_id) }} · Secc. {{ est.seccion }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <button @click="openNuevaMatricula(est)" title="Nueva matrícula" class="p-2.5 bg-emerald-50 dark:bg-emerald-900/20 rounded-xl text-emerald-500 transition-all"><CalendarPlus class="w-4 h-4" /></button>
                <button @click="openEdit(est)" class="p-2.5 bg-surface-input rounded-xl text-slate-400 transition-all"><Edit2 class="w-4 h-4" /></button>
                <button @click="toggle(est)" title="Activar / Desactivar"
                  class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200 cursor-pointer focus:outline-none"
                  :class="est.is_active ? 'bg-teal-500' : 'bg-slate-300 dark:bg-surface-elevated'">
                  <span class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform duration-200"
                    :class="est.is_active ? 'translate-x-6' : 'translate-x-1'" />
                </button>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4 pt-4 border-t border-slate-100 dark:border-slate-700">
              <div>
                <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">Código Acceso</p>
                <p class="font-mono font-bold text-primary">{{ est.codigo_estudiante || 'Pendiente' }}</p>
              </div>
              <div>
                <p class="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">DNI</p>
                <p class="font-bold text-slate-600 dark:text-text-muted">{{ est.dni || '—' }}</p>
              </div>
            </div>
          </div>
          <div v-if="estudiantesFiltrados.length === 0" class="py-12 text-center text-slate-400 font-bold uppercase tracking-widest text-xs">Sin resultados</div>

          <!-- Pagination (mobile) -->
          <div class="bg-surface-card rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-4 flex flex-col items-center gap-3">
            <!-- Page size selector -->
            <div class="flex items-center gap-1.5 w-full justify-center">
              <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Por página</span>
              <button v-for="n in PAGE_SIZE_OPTIONS" :key="n" @click="pageSize = n"
                :class="['h-7 px-2.5 rounded-lg text-xs font-bold transition-all cursor-pointer',
                  pageSize === n
                    ? 'bg-teal-600 text-white shadow-sm'
                    : 'bg-surface-input border border-slate-300 dark:border-slate-600 text-slate-500 dark:text-text-muted']">
                {{ n }}
              </button>
            </div>
            <p class="text-[11px] text-slate-500 dark:text-text-muted">
              Página <span class="font-bold text-slate-700 dark:text-text">{{ currentPage }}</span> de <span class="font-bold text-slate-700 dark:text-text">{{ totalPages }}</span>
              · <span class="font-bold text-slate-700 dark:text-text">{{ estudiantesFiltrados.length }}</span> alumnos
            </p>
            <div v-if="totalPages > 1" class="flex items-center gap-2">
              <button @click="currentPage--" :disabled="currentPage === 1"
                class="p-2 rounded-xl border border-slate-300 dark:border-slate-600 bg-surface-card text-slate-600 dark:text-text-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
                <ChevronLeft class="w-4 h-4" />
              </button>
              <div class="flex items-center gap-1">
                <template v-for="p in totalPages" :key="p">
                  <button v-if="p === 1 || p === totalPages || Math.abs(p - currentPage) <= 1"
                    @click="currentPage = p"
                    :class="['w-9 h-9 rounded-xl text-xs font-bold transition-all cursor-pointer',
                      currentPage === p
                        ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white shadow-md'
                        : 'text-slate-600 dark:text-text-muted hover:bg-slate-100 dark:hover:bg-slate-700']">
                    {{ p }}
                  </button>
                  <span v-else-if="p === currentPage - 2 || p === currentPage + 2"
                    class="w-9 h-9 flex items-center justify-center text-slate-400 text-xs">…</span>
                </template>
              </div>
              <button @click="currentPage++" :disabled="currentPage === totalPages"
                class="p-2 rounded-xl border border-slate-300 dark:border-slate-600 bg-surface-card text-slate-600 dark:text-text-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
                <ChevronRight class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <!-- ── Modal: Crear / Editar ── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center sm:items-center justify-center items-end bg-slate-900/60 backdrop-blur-sm cursor-pointer" @click.self="closeModal">
          <div class="bg-surface-card rounded-t-2xl sm:rounded-2xl shadow-2xl w-full max-w-xl overflow-hidden relative">
            <div class="sm:hidden flex justify-center pt-4 pb-1" @click="closeModal"><div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-surface-input"></div></div>
            <div class="flex items-center justify-between p-6 border-b border-slate-300 dark:border-slate-700">
              <div class="flex items-center gap-4">
                <div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-lg shadow-teal-500/20"><GraduationCap class="w-5 h-5 text-white" /></div>
                <div>
                  <h2 class="text-lg font-black text-text tracking-tight">{{ editingId ? 'Editar Estudiante' : 'Registrar Estudiante' }}</h2>
                  <p class="text-xs text-slate-500 font-bold uppercase tracking-widest">Gestión de Aula</p>
                </div>
              </div>
              <button @click="closeModal" class="p-2 rounded-xl text-slate-400 hover:bg-slate-100 transition-all"><X class="w-5 h-5" /></button>
            </div>
            <div class="p-6 space-y-5 max-h-[70vh] overflow-y-auto custom-scrollbar">
              <div v-if="serverError" class="bg-red-50 text-red-600 p-4 rounded-2xl text-xs font-bold border border-red-100">{{ serverError }}</div>
              <div v-if="editingPendingUser" class="bg-amber-50 text-amber-700 p-4 rounded-2xl text-xs font-bold border border-amber-100">Falta activar usuario (asignar contraseña).</div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombres</label>
                  <input v-model="form.nombres" type="text" placeholder="Ej: Juan" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all font-bold" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Apellidos</label>
                  <input v-model="form.apellidos" type="text" placeholder="Ej: Perez" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all font-bold" />
                </div>
              </div>
              <div class="space-y-1.5">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">DNI</label>
                <input v-model="form.dni" type="text" maxlength="8" placeholder="Ocho dígitos" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all font-bold" />
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Grado</label>
                  <ComboBox v-model="form.grado_id" :options="gradosOpcionesForm" placeholder="Selecciona grado" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Sección</label>
                  <ComboBox v-model="form.seccion" :options="seccionesOpciones" placeholder="Selecciona sección" />
                </div>
              </div>
              <div class="space-y-1.5">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Contraseña</label>
                <div class="relative">
                  <input v-model="form.password" :type="showPass ? 'text' : 'password'" placeholder="••••" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all font-bold" />
                  <button @click="showPass = !showPass" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400"><Eye v-if="!showPass" class="w-5 h-5" /><EyeOff v-else class="w-5 h-5" /></button>
                </div>
              </div>
              <p v-if="formError" class="text-[10px] font-bold text-amber-600 uppercase">{{ formError }}</p>
            </div>
            <div class="p-6 bg-surface/50 flex flex-col sm:flex-row gap-3">
              <button @click="closeModal" class="flex-1 px-6 py-3.5 text-xs font-black uppercase tracking-widest text-slate-500 bg-surface-card rounded-2xl border border-slate-200 dark:border-slate-700 transition-all">Cancelar</button>
              <button @click="guardar" :disabled="saving || !!formError" class="flex-1 flex items-center justify-center gap-3 py-3.5 bg-gradient-to-r from-teal-500 to-emerald-600 text-white font-black text-xs rounded-2xl shadow-xl shadow-teal-500/20 transition-all disabled:opacity-50 active:scale-95">
                <Loader2 v-if="saving" class="w-5 h-5 animate-spin" />
                <span class="uppercase tracking-widest">{{ editingPendingUser ? 'Activar' : editingId ? 'Actualizar' : 'Registrar' }}</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Modal: Importar nómina ── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showImportModal" class="fixed inset-0 z-50 flex items-center sm:items-center justify-center items-end bg-slate-900/60 backdrop-blur-sm cursor-pointer" @click.self="closeImportModal">
          <div class="w-full max-w-lg overflow-hidden rounded-t-2xl sm:rounded-2xl bg-white shadow-2xl dark:bg-surface-card relative">
            <div class="sm:hidden flex justify-center pt-4 pb-1" @click="closeImportModal"><div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-surface-input"></div></div>
            <div class="flex items-center justify-between border-b border-slate-300 p-6 dark:border-slate-700">
              <div class="flex items-center gap-4">
                <div class="flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 shadow-lg shadow-teal-500/20"><FileSpreadsheet class="h-6 w-6 text-white" /></div>
                <div>
                  <h2 class="text-lg font-black text-text tracking-tight">Importar nómina Excel</h2>
                  <p class="text-xs text-slate-500 font-bold uppercase tracking-widest">Carga Masiva</p>
                </div>
              </div>
              <button @click="closeImportModal" class="p-2 text-slate-400"><X class="h-5 w-5" /></button>
            </div>
            <div class="space-y-6 p-6">
              <div class="rounded-xl border border-teal-100 bg-teal-50/50 p-5 text-xs font-bold text-teal-700 shadow-sm flex items-start gap-3">
                <AlertCircle class="w-5 h-5 shrink-0" />
                <div><p class="text-base font-black tracking-tight">Columnas: dni, nombres, apellidos</p></div>
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Grado</label>
                  <ComboBox v-model="importForm.grado_id" :options="gradosOpcionesForm" placeholder="Selecciona grado" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Sección</label>
                  <ComboBox v-model="importForm.seccion" :options="seccionesOpciones" placeholder="Selecciona sección" />
                </div>
              </div>
              <input ref="nominaFileInput" type="file" accept=".xlsx,.xls" class="hidden" @change="onNominaFileChange" />
              <div class="rounded-2xl border-2 border-dashed border-slate-300 p-6 bg-slate-50/50">
                <div class="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                  <div class="min-w-0">
                    <p class="text-sm font-black text-text uppercase tracking-tight mb-1">Archivo Excel</p>
                    <p class="text-xs font-bold text-slate-400 truncate">{{ selectedImportFileName || 'No seleccionado' }}</p>
                  </div>
                  <div class="flex gap-2">
                    <button @click="descargarPlantillaNomina" class="px-4 py-2.5 bg-surface-card border-2 border-slate-200 dark:border-slate-700 rounded-xl text-[10px] font-black uppercase tracking-widest text-slate-500 cursor-pointer">Modelo</button>
                    <button @click="seleccionarArchivoNomina" class="px-4 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-text-inverse rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg cursor-pointer">Subir</button>
                  </div>
                </div>
              </div>
              <p v-if="importFormError" class="text-[10px] font-bold text-amber-600 uppercase">{{ importFormError }}</p>
            </div>
            <div class="flex flex-col sm:flex-row gap-3 p-6 bg-surface/50">
              <button @click="closeImportModal" class="flex-1 rounded-2xl bg-white px-6 py-3.5 text-xs font-black uppercase tracking-widest text-slate-500 border border-slate-200">Cancelar</button>
              <button @click="importarNomina" :disabled="importing || !!importFormError" class="flex-1 flex items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-teal-500 to-emerald-600 py-3.5 text-xs font-black uppercase tracking-widest text-white shadow-xl shadow-teal-500/20 transition-all disabled:opacity-50">
                <Loader2 v-if="importing" class="h-5 w-5 animate-spin" />
                <span>Confirmar Importación</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Modal: Código generado ── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showSuccessModal" class="fixed inset-0 z-50 flex items-center sm:items-center justify-center items-end bg-slate-900/60 backdrop-blur-sm cursor-pointer" @click.self="showSuccessModal = false">
          <div class="bg-surface-card rounded-t-2xl sm:rounded-2xl shadow-2xl w-full max-w-sm p-8 text-center space-y-6 relative">
            <div class="sm:hidden flex justify-center pb-2" @click="showSuccessModal = false"><div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-surface-input"></div></div>
            <div class="w-20 h-20 rounded-2xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center mx-auto shadow-inner"><CheckCircle class="w-10 h-10 text-emerald-500" /></div>
            <div>
              <h2 class="text-2xl font-black text-text tracking-tight leading-none mb-1">¡Registro Exitoso!</h2>
              <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Usuario Generado</p>
            </div>
            <div class="space-y-2">
                <p class="text-xs font-bold text-slate-500">El código de acceso es:</p>
                <div class="bg-surface-input/50 rounded-2xl py-5 px-6 border-2 border-dashed border-teal-500/30">
                  <span class="text-4xl font-mono font-black text-primary tracking-[0.2em]">{{ successCodigo }}</span>
                </div>
            </div>
            <div class="bg-amber-50 dark:bg-amber-900/20 rounded-2xl p-4 border border-amber-100 dark:border-amber-900/30">
                <p class="text-[10px] font-bold text-amber-700 dark:text-amber-300 leading-relaxed uppercase tracking-tight">Comparte este código con el estudiante. Lo necesitará junto a su contraseña para entrar.</p>
            </div>
            <button @click="showSuccessModal = false" class="w-full py-4 bg-slate-900 dark:bg-white text-white dark:text-text-inverse font-black rounded-2xl shadow-xl transition-all active:scale-95 uppercase tracking-widest text-sm">Entendido</button>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Modal: Nueva matrícula / avance de año ── -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showAdvanceModal" class="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-slate-900/60 backdrop-blur-sm" @click.self="closeAdvanceModal">
          <div class="bg-surface-card rounded-t-3xl sm:rounded-3xl shadow-2xl w-full max-w-md relative overflow-hidden">
            <div class="sm:hidden flex justify-center pt-3 pb-1" @click="closeAdvanceModal"><div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-surface-input"></div></div>
            <div class="px-6 pt-5 pb-2 border-b border-slate-100 dark:border-slate-700 flex items-center justify-between">
              <div class="flex items-center gap-3">
                <div class="w-10 h-10 rounded-2xl bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center">
                  <CalendarPlus class="w-5 h-5 text-emerald-600" />
                </div>
                <div>
                  <h2 class="text-sm font-black text-text uppercase tracking-tight">Nueva Matrícula</h2>
                  <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Avance de año escolar</p>
                </div>
              </div>
              <button @click="closeAdvanceModal" class="p-2 rounded-xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all"><X class="w-4 h-4" /></button>
            </div>

            <div class="p-6 space-y-4">
              <p class="text-xs font-bold text-slate-500 dark:text-text-muted">
                La matrícula actual quedará en el historial como inactiva. El estudiante pasará al nuevo grado/sección/año.
              </p>

              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">Grado</label>
                  <select v-model="advanceForm.grado_id" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all">
                    <option :value="0" disabled>Selecciona</option>
                    <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">Sección</label>
                  <select v-model="advanceForm.seccion" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all">
                    <option value="" disabled>Selecciona</option>
                    <option v-for="s in ['A','B','C','D','E','F']" :key="s" :value="s">{{ s }}</option>
                  </select>
                </div>
              </div>

              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5">Año Escolar</label>
                <input v-model.number="advanceForm.año_escolar" type="number" min="2020" max="2099"
                  class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all" />
              </div>

              <p v-if="advanceFormError" class="text-[10px] font-bold text-amber-600 uppercase">{{ advanceFormError }}</p>
              <p v-if="advanceServerError" class="text-[10px] font-bold text-red-500 uppercase">{{ advanceServerError }}</p>
            </div>

            <div class="flex gap-3 px-6 pb-6">
              <button @click="closeAdvanceModal" class="flex-1 rounded-2xl bg-surface-input px-6 py-3.5 text-xs font-black uppercase tracking-widest text-slate-500 border border-slate-200 dark:border-slate-600">Cancelar</button>
              <button @click="avanzarAño" :disabled="advancing || !!advanceFormError"
                class="flex-1 flex items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-emerald-500 to-teal-600 py-3.5 text-xs font-black uppercase tracking-widest text-white shadow-xl shadow-emerald-500/20 transition-all disabled:opacity-50 active:scale-95">
                <Loader2 v-if="advancing" class="h-4 w-4 animate-spin" />
                <span>Crear Matrícula</span>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-enter-active .relative, .modal-leave-active .relative { transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .relative, .modal-leave-to .relative { transform: translateY(100%); }
@media (min-width: 640px) {
    .modal-enter-from .relative, .modal-leave-to .relative { transform: translateY(0) scale(0.9) translateZ(0); }
}

.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 10px; }
</style>
