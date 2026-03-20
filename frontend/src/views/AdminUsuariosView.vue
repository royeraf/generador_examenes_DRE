<script setup lang="ts">
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { adminUsuariosService, ubigeoService, type DocenteCreatePayload, type DocenteUpdatePayload } from '../services/api'
import type { Docente, Provincia, Distrito } from '../types'
import {
  Plus, Edit2, Trash2, Home,
  Shield, X, Eye, EyeOff, AlertCircle, KeyRound, CheckCircle,
  ChevronLeft, ChevronRight, Loader2, MoreVertical, Search, MapPin
} from 'lucide-vue-next'
import ComboBox from '../components/ComboBox.vue'
import Swal from 'sweetalert2'
import { useForm, useField } from 'vee-validate'
import * as yup from 'yup'

const router = useRouter()
const auth = useAuthStore()

// State
const docentes = ref<Docente[]>([])
const loading = ref(true)
const saving = ref(false)
const showModal = ref(false)
const editingId = ref<number | null>(null)
const showPassword = ref(false)
const serverError = ref('')
const showDeleteFor = ref<number | null>(null)
const togglingId = ref<number | null>(null)
const showDetailsModal = ref(false)
const detailsTarget = ref<Docente | null>(null)
const searchQuery = ref('')
let searchTimeout: any = null

// Ubigeo
const provincias = ref<Provincia[]>([])
const distritos = ref<Distrito[]>([])
const loadingDistritos = ref(false)
let isInitialLoad = false

// ComboBox options
const nivelOptions = [
  { id: '', label: '— Sin especificar —' },
  { id: 'inicial', label: 'Inicial' },
  { id: 'primaria', label: 'Primaria' },
  { id: 'secundaria', label: 'Secundaria' },
]

const provinciaOptions = computed(() => [
  { id: null as null, label: '— Sin especificar —' },
  ...provincias.value.map(p => ({ id: p.id, label: p.nombre })),
])

const distritoOptions = computed(() => [
  { id: null as null, label: '— Sin especificar —' },
  ...distritos.value.map(d => ({ id: d.id, label: d.nombre })),
])

// Pagination
const currentPage = ref(1)
const pageSize = ref(10)
const totalPages = ref(0)
const totalCount = ref(0)

// =====================================================
// ESTADÍSTICAS
// =====================================================
const stats = computed(() => {
  const total = docentes.value.length
  const active = docentes.value.filter(d => d.is_active).length
  const inactive = total - active
  const admins = docentes.value.filter(d => d.is_superuser).length
  return { total, active, inactive, admins }
})

// =====================================================
// VEE-VALIDATE — Schema dinámico según modo crear/editar
// =====================================================
const schema = computed(() => yup.object({
  dni: yup
    .string()
    .required('El DNI es obligatorio')
    .matches(/^\d{8}$/, 'El DNI debe tener exactamente 8 dígitos numéricos'),
  nombres: yup.string().required('Los nombres son obligatorios'),
  apellidos: yup.string().required('Los apellidos son obligatorios'),
  profesion: yup.string().optional(),
  institucion_educativa: yup.string().optional(),
  nivel_educativo: yup.string().optional(),
  provincia_id: yup.number().nullable().optional(),
  distrito_id: yup.number().nullable().optional(),
  password: editingId.value
    ? yup.string().optional().test(
      'min-if-filled',
      'La contraseña debe tener al menos 6 caracteres',
      (v) => !v || v.length >= 6
    )
    : yup
      .string()
      .required('La contraseña es obligatoria')
      .min(6, 'La contraseña debe tener al menos 6 caracteres'),
  is_active: yup.boolean().optional(),
  is_superuser: yup.boolean().optional(),
}))

const { handleSubmit, resetForm, setValues } = useForm({
  validationSchema: schema,
  initialValues: {
    dni: '',
    nombres: '',
    apellidos: '',
    profesion: '',
    institucion_educativa: '',
    nivel_educativo: '',
    provincia_id: null as number | null,
    distrito_id: null as number | null,
    password: '',
    is_active: true,
    is_superuser: false,
  },
})

const { value: dni, errorMessage: dniError } = useField<string>('dni')
const { value: nombres, errorMessage: nombresError } = useField<string>('nombres')
const { value: apellidos, errorMessage: apellidosError } = useField<string>('apellidos')
const { value: profesion } = useField<string>('profesion')
const { value: institucion_educativa } = useField<string>('institucion_educativa')
const { value: nivel_educativo } = useField<string>('nivel_educativo')
const { value: provincia_id } = useField<number | null>('provincia_id')
const { value: distrito_id } = useField<number | null>('distrito_id')
const { value: password, errorMessage: passwordError } = useField<string>('password')
const { value: is_active } = useField<boolean>('is_active')
const { value: is_superuser } = useField<boolean>('is_superuser')

// Load
async function loadDocentes(resetPage = false) {
  if (resetPage) currentPage.value = 1
  try {
    loading.value = true
    const response = await adminUsuariosService.getAll(currentPage.value, pageSize.value, searchQuery.value)
    docentes.value = response.items
    totalPages.value = response.pages
    totalCount.value = response.total
  } catch {
    Swal.fire('Error', 'No se pudo cargar la lista de usuarios', 'error')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  if (searchTimeout) clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    loadDocentes(true)
  }, 400) // Debounce 400ms
}

function setPage(page: number) {
  if (page < 1 || page > totalPages.value) return
  currentPage.value = page
  loadDocentes()
}

function nextPage() {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    loadDocentes()
  }
}

function prevPage() {
  if (currentPage.value > 1) {
    currentPage.value--
    loadDocentes()
  }
}

// Watch provincia_id to cascade distritos
watch(provincia_id, async (newVal) => {
  if (isInitialLoad) return
  distrito_id.value = null
  distritos.value = []
  if (newVal) {
    loadingDistritos.value = true
    try {
      distritos.value = await ubigeoService.getDistritos(newVal)
    } finally {
      loadingDistritos.value = false
    }
  }
})

onMounted(async () => {
  loadDocentes()
  try {
    provincias.value = await ubigeoService.getProvincias()
  } catch (e) {
    console.error('Error cargando provincias:', e)
  }
})

// Modal
function openCreate() {
  editingId.value = null
  showPassword.value = false
  serverError.value = ''
  distritos.value = []
  resetForm()
  showModal.value = true
}

async function openEdit(docente: Docente) {
  editingId.value = docente.id
  showPassword.value = false
  serverError.value = ''

  // Pre-load distritos if docente has a provincia
  if (docente.provincia_id) {
    loadingDistritos.value = true
    try {
      distritos.value = await ubigeoService.getDistritos(docente.provincia_id)
    } finally {
      loadingDistritos.value = false
    }
  } else {
    distritos.value = []
  }

  isInitialLoad = true
  setValues({
    dni: docente.dni,
    nombres: docente.nombres ?? '',
    apellidos: docente.apellidos ?? '',
    profesion: docente.profesion ?? '',
    institucion_educativa: docente.institucion_educativa ?? '',
    nivel_educativo: docente.nivel_educativo ?? '',
    provincia_id: docente.provincia_id ?? null,
    distrito_id: docente.distrito_id ?? null,
    password: '',
    is_active: docente.is_active,
    is_superuser: docente.is_superuser,
  })
  isInitialLoad = false
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

function openDetails(docente: Docente) {
  detailsTarget.value = docente
  showDetailsModal.value = true
}

// Save — vee-validate handleSubmit valida antes de ejecutar
const saveDocente = handleSubmit(
  async (values) => {
    serverError.value = ''

    // Confirmar si se está asignando rol de administrador
    if (values.is_superuser) {
      const isEditing = !!editingId.value
      const confirm = await Swal.fire({
        title: '¿Asignar rol de Administrador?',
        html: `El usuario <strong>${values.nombres ?? values.dni}</strong> tendrá acceso completo al panel de administración y podrá gestionar otros usuarios.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#6366f1',
        cancelButtonColor: '#94a3b8',
        confirmButtonText: isEditing ? 'Sí, guardar como Admin' : 'Sí, crear como Admin',
        cancelButtonText: 'Cancelar',
      })
      if (!confirm.isConfirmed) return
    }

    saving.value = true
    try {
      if (editingId.value) {
        const payload: DocenteUpdatePayload = {
          nombres: values.nombres || undefined,
          apellidos: values.apellidos || undefined,
          profesion: values.profesion || undefined,
          institucion_educativa: values.institucion_educativa || undefined,
          nivel_educativo: values.nivel_educativo || undefined,
          provincia_id: values.provincia_id || null,
          distrito_id: values.distrito_id || null,
          is_active: values.is_active,
          is_superuser: values.is_superuser,
        }
        if (values.password) payload.password = values.password
        await adminUsuariosService.update(editingId.value, payload)
        await loadDocentes()
        closeModal()
        Swal.fire({ icon: 'success', title: 'Cambios guardados', showConfirmButton: false, timer: 2000 })
      } else {
        const payload: DocenteCreatePayload = {
          dni: values.dni,
          nombres: values.nombres,
          apellidos: values.apellidos,
          profesion: values.profesion,
          institucion_educativa: values.institucion_educativa,
          nivel_educativo: values.nivel_educativo,
          provincia_id: values.provincia_id || null,
          distrito_id: values.distrito_id || null,
          is_active: values.is_active ?? true,
          is_superuser: values.is_superuser ?? false,
          password: values.password!,
        }
        await adminUsuariosService.create(payload)
        await loadDocentes()
        closeModal()
        Swal.fire({ icon: 'success', title: 'Usuario creado correctamente', showConfirmButton: false, timer: 2000 })
      }
    } catch (e: any) {
      const detail = e.response?.data?.detail ?? ''
      if (detail === 'DNI ya registrado') {
        Swal.fire({ icon: 'error', title: 'DNI ya registrado', text: 'Ya existe un usuario con ese número de DNI.', confirmButtonColor: '#6366f1' })
      } else {
        serverError.value = detail || 'Error al guardar el usuario'
      }
    } finally {
      saving.value = false
    }
  },
  // onInvalidSubmit — no hace nada extra, los errores se muestran en el template
)

// Toggle active
async function toggleActive(docente: Docente) {
  if (docente.id === auth.user?.id) return

  const isDeactivating = docente.is_active;
  
  const result = await Swal.fire({
    title: isDeactivating ? '¿Desactivar usuario?' : '¿Activar usuario?',
    html: isDeactivating 
      ? `El usuario <strong>${docente.nombres ?? docente.dni}</strong> perderá el acceso al sistema.`
      : `El usuario <strong>${docente.nombres ?? docente.dni}</strong> volverá a tener acceso al sistema.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: isDeactivating ? '#f59e0b' : '#14b8a6', // amber-500 or teal-500
    cancelButtonColor: '#94a3b8', // slate-400
    confirmButtonText: isDeactivating ? 'Sí, desactivar' : 'Sí, activar',
    cancelButtonText: 'Cancelar'
  })

  if (!result.isConfirmed) {
    showDeleteFor.value = null; // Cierra las opciones expandidas si cancela
    return
  }

  togglingId.value = docente.id
  try {
    await adminUsuariosService.toggleActive(docente.id)
    await loadDocentes()
    
    // Success notification
    Swal.fire({
      icon: 'success',
      title: isDeactivating ? 'Usuario desactivado' : 'Usuario activado',
      showConfirmButton: false,
      timer: 2000,
    });
  } catch {
    Swal.fire('Error', 'No se pudo cambiar el estado del usuario', 'error')
  } finally {
    togglingId.value = null
    showDeleteFor.value = null // Oculta barra si todo finalizó
  }
}

// Delete
async function deleteDocente(docente: Docente) {
  if (docente.id === auth.user?.id) {
    Swal.fire('No permitido', 'No puedes eliminar tu propio usuario', 'warning')
    return
  }

  const result = await Swal.fire({
    title: '¿Eliminar usuario?',
    html: `¿Estás seguro de eliminar a <strong>${docente.nombres ?? docente.dni}</strong>?<br>Esta acción no se puede deshacer.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#94a3b8',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
  })

  if (result.isConfirmed) {
    try {
      await adminUsuariosService.delete(docente.id)
      await loadDocentes()
      Swal.fire('Eliminado', 'El usuario fue eliminado correctamente', 'success')
    } catch (e: any) {
      Swal.fire('Error', e.response?.data?.detail ?? 'No se pudo eliminar el usuario', 'error')
    }
  }
}

const levelLabel: Record<string, string> = {
  inicial: 'Inicial',
  primaria: 'Primaria',
  secundaria: 'Secundaria',
}

function creadorNombre(creado_por_id: number): string {
  const creador = docentes.value.find(d => d.id === creado_por_id)
  if (!creador) return `#${creado_por_id}`
  return [creador.nombres, creador.apellidos].filter(Boolean).join(' ') || creador.dni
}

function formatFecha(fecha: string): string {
  return new Date(fecha).toLocaleDateString('es-PE', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

// --- Reset de contraseña (admin) ---
const showResetModal = ref(false)
const resetTarget = ref<Docente | null>(null)
const resetPassword = ref('')
const resetPasswordError = ref('')
const showResetPass = ref(false)
const resetSaving = ref(false)
const resetSuccess = ref(false)

function openResetPassword(docente: Docente) {
  resetTarget.value = docente
  resetPassword.value = ''
  showResetPass.value = false
  resetPasswordError.value = ''
  resetSuccess.value = false
  showResetModal.value = true
}

async function saveResetPassword() {
  resetPasswordError.value = ''
  resetSuccess.value = false

  if (!resetPassword.value || resetPassword.value.length < 6) {
    resetPasswordError.value = 'La contraseña debe tener al menos 6 caracteres'
    return
  }

  resetSaving.value = true
  try {
    await adminUsuariosService.update(resetTarget.value!.id, { password: resetPassword.value })
    resetPassword.value = ''
    showResetModal.value = false
    Swal.fire({ icon: 'success', title: 'Contraseña restablecida', showConfirmButton: false, timer: 2000 })
  } catch (e: any) {
    resetPasswordError.value = e.response?.data?.detail ?? 'Error al actualizar la contraseña'
  } finally {
    resetSaving.value = false
  }
}
</script>

<template>
  <div @click="showDeleteFor = null"
    class="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-950 p-4 md:p-8">

    <!-- Header -->
    <div class="max-w-7xl mx-auto">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-black text-slate-800 dark:text-white leading-tight">
            Gestión de <span
              class="bg-gradient-to-r from-teal-500 to-indigo-600 bg-clip-text text-transparent">Usuarios</span>
          </h1>
          <p class="text-slate-500 dark:text-slate-400 text-sm mt-1">Administra los docentes del sistema</p>
        </div>
        <div class="flex items-center gap-2 sm:gap-3">
          <button @click="openCreate"
            class="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold px-4 py-2.5 rounded-xl shadow-lg transition-all duration-200 hover:-translate-y-0.5 text-sm">
            <Plus class="w-4 h-4" />
            <span class="hidden xs:inline">Nuevo Usuario</span>
            <span class="xs:hidden">Nuevo</span>
          </button>
          <button @click="router.push('/')"
            class="flex items-center gap-2 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-medium px-4 py-2.5 rounded-xl shadow border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all text-sm">
            <Home class="w-4 h-4" />
            <span class="hidden xs:inline">Inicio</span>
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">

        <!-- Total -->
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-3 md:p-4 flex items-center gap-3 md:gap-4">
          <div
            class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-teal-400 to-indigo-500 flex items-center justify-center shadow-lg shrink-0">
            <svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div class="min-w-0">
            <p class="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide truncate">Total</p>
            <p class="text-xl md:text-2xl font-black text-slate-800 dark:text-white leading-none mt-0.5">
              <span v-if="loading"
                class="inline-block w-6 md:w-8 h-5 md:h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ stats.total }}</span>
            </p>
            <p class="text-[10px] md:text-xs text-slate-400 dark:text-slate-500 mt-0.5 hidden xs:block truncate">registrados</p>
          </div>
        </div>

        <!-- Activos -->
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-3 md:p-4 flex items-center gap-3 md:gap-4">
          <div
            class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center shadow-lg shrink-0">
            <svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="min-w-0">
            <p class="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide truncate">Activos</p>
            <p class="text-xl md:text-2xl font-black text-slate-800 dark:text-white leading-none mt-0.5">
              <span v-if="loading"
                class="inline-block w-6 md:w-8 h-5 md:h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ stats.active }}</span>
            </p>
            <p class="text-[10px] md:text-xs text-slate-400 dark:text-slate-500 mt-0.5 hidden xs:block truncate">con acceso</p>
          </div>
        </div>

        <!-- Inactivos -->
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-3 md:p-4 flex items-center gap-3 md:gap-4">
          <div
            class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-red-400 to-rose-500 flex items-center justify-center shadow-lg shrink-0">
            <svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
          <div class="min-w-0">
            <p class="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide truncate">Inactivos</p>
            <p class="text-xl md:text-2xl font-black text-slate-800 dark:text-white leading-none mt-0.5">
              <span v-if="loading"
                class="inline-block w-6 md:w-8 h-5 md:h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ stats.inactive }}</span>
            </p>
            <p class="text-[10px] md:text-xs text-slate-400 dark:text-slate-500 mt-0.5 hidden xs:block truncate">sin acceso</p>
          </div>
        </div>

        <!-- Administradores -->
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-3 md:p-4 flex items-center gap-3 md:gap-4">
          <div
            class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center shadow-lg shrink-0">
            <svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div class="min-w-0">
            <p class="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide truncate">Admins</p>
            <p class="text-xl md:text-2xl font-black text-slate-800 dark:text-white leading-none mt-0.5">
              <span v-if="loading"
                class="inline-block w-6 md:w-8 h-5 md:h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ stats.admins }}</span>
            </p>
            <p class="text-[10px] md:text-xs text-slate-400 dark:text-slate-500 mt-0.5 hidden xs:block truncate">rol admin</p>
          </div>
        </div>

      </div>

      <!-- Search Bar -->
      <div class="mb-6 flex">
        <div class="relative w-full md:w-96">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search class="h-5 w-5 text-slate-400 dark:text-slate-500" />
          </div>
          <input type="text" v-model="searchQuery" @input="handleSearch"
            class="block w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-700 rounded-xl leading-5 bg-white dark:bg-slate-800/80 text-slate-900 dark:text-slate-100 placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 dark:focus:ring-teal-400/50 dark:focus:border-teal-400 transition-colors shadow-sm"
            placeholder="Buscar por DNI, Nombres o Apellidos...">
          <div class="absolute inset-y-0 right-0 pr-3 flex items-center" v-if="searchQuery">
            <button @click="searchQuery = ''; handleSearch()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
              <X class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- User List Container -->
      <div class="bg-white dark:bg-slate-800 md:rounded-2xl shadow-xl md:border border-slate-100 dark:border-slate-700 -mx-4 md:mx-0">
        
        <!-- Mobile Cards View -->
        <div class="md:hidden">
          <Transition name="table-content" mode="out-in">
          <div v-if="loading" key="loading" class="divide-y divide-slate-100 dark:divide-slate-700/50">
            <div v-for="n in 5" :key="n" class="p-4 animate-pulse">
              <div class="flex justify-between mb-3">
                <div class="space-y-2 w-1/2">
                   <div class="h-3 w-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
                   <div class="h-4 w-full bg-slate-200 dark:bg-slate-700 rounded"></div>
                </div>
                <div class="space-y-2 items-end flex flex-col">
                   <div class="h-4 w-12 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                   <div class="h-4 w-16 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                </div>
              </div>
              <div class="space-y-2 pt-2 border-t border-slate-50 dark:border-slate-700/30">
                <div class="h-3 w-3/4 bg-slate-200 dark:bg-slate-700 rounded"></div>
                <div class="h-3 w-1/2 bg-slate-200 dark:bg-slate-700 rounded"></div>
              </div>
              <div class="flex justify-end gap-2 mt-3 pt-3 border-t border-slate-50 dark:border-slate-700/30">
                 <div class="h-7 w-20 bg-slate-200 dark:bg-slate-700 rounded-lg"></div>
                 <div class="h-7 w-20 bg-slate-200 dark:bg-slate-700 rounded-lg"></div>
                 <div class="h-7 w-10 bg-slate-200 dark:bg-slate-700 rounded-lg"></div>
              </div>
            </div>
          </div>

          <div v-else key="data" class="divide-y divide-slate-100 dark:divide-slate-700/50">
            <div v-if="docentes.length === 0" class="text-center py-10 px-4 text-slate-400 dark:text-slate-500 text-sm">
              No hay usuarios registrados.
            </div>
            <div v-else v-for="docente in docentes" :key="docente.id"
              class="p-4 transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/30"
              :class="{ 'opacity-60': !docente.is_active }">
              
              <!-- Card Header: DNI & Name + Roles -->
              <div class="flex justify-between items-start gap-4 mb-3">
                <div class="min-w-0 flex-1">
                  <div class="text-[11px] font-mono text-slate-500 dark:text-slate-400 mb-0.5">{{ docente.dni }}</div>
                  <div class="font-bold text-slate-800 dark:text-white leading-tight">
                    {{ [docente.nombres, docente.apellidos].filter(Boolean).join(' ') || '—' }}
                    <span v-if="docente.id === auth.user?.id" 
                      class="ml-1 align-middle inline-flex text-[10px] text-teal-600 dark:text-teal-400 font-bold bg-teal-50 dark:bg-teal-900/30 px-1.5 py-0.5 rounded-full">tú</span>
                  </div>
                </div>
                <div class="flex flex-col items-end gap-1.5 shrink-0">
                  <span class="inline-flex items-center gap-1 text-[10px] font-bold px-2 py-0.5 rounded-full" :class="docente.is_superuser
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                    : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'">
                    <Shield class="w-3 h-3" />
                    {{ docente.is_superuser ? 'Admin' : 'Docente' }}
                  </span>
                </div>
              </div>

              <!-- Card Actions -->
              <div class="flex items-center justify-end pt-3 mt-1 border-t border-slate-50 dark:border-slate-700/30 h-[48px] overflow-hidden">
                  
                  <!-- Default Actions -->
                  <div v-if="showDeleteFor !== docente.id" class="flex items-center gap-2 w-full h-full">
                    <button @click.stop="openDetails(docente)"
                      class="has-tooltip relative flex flex-1 justify-center items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-indigo-700 dark:text-indigo-300 bg-indigo-50 hover:bg-indigo-100/80 dark:bg-indigo-900/30 dark:hover:bg-indigo-900/50 rounded-xl transition-all duration-200 border border-indigo-100/50 dark:border-indigo-800/60 shadow-sm hover:shadow h-full">
                      <Eye class="w-4 h-4" /> <span class="hidden sm:inline">Ver</span>
                      <span class="tooltip-top hidden sm:block">Ver detalles del usuario</span>
                    </button>
                    <button @click.stop="openEdit(docente)"
                      class="has-tooltip relative flex flex-1 justify-center items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-teal-700 dark:text-teal-300 bg-teal-50 hover:bg-teal-100/80 dark:bg-teal-900/30 dark:hover:bg-teal-900/50 rounded-xl transition-all duration-200 border border-teal-100/50 dark:border-teal-800/60 shadow-sm hover:shadow h-full">
                      <Edit2 class="w-4 h-4" /> <span class="hidden sm:inline">Editar</span>
                      <span class="tooltip-top hidden sm:block">Modificar información</span>
                    </button>
                    <button @click.stop="openResetPassword(docente)"
                      class="has-tooltip relative flex flex-1 justify-center items-center gap-1.5 px-3 py-1.5 text-xs font-bold text-amber-700 dark:text-amber-300 bg-amber-50 hover:bg-amber-100/80 dark:bg-amber-900/30 dark:hover:bg-amber-900/50 rounded-xl transition-all duration-200 border border-amber-100/50 dark:border-amber-800/60 shadow-sm hover:shadow h-full">
                      <KeyRound class="w-4 h-4" /> <span class="hidden sm:inline">Pass</span>
                      <span class="tooltip-top hidden sm:block">Restablecer la contraseña</span>
                    </button>
                    <button @click.stop="showDeleteFor = docente.id" :disabled="docente.id === auth.user?.id"
                      class="has-tooltip relative flex items-center justify-center w-10 shrink-0 h-full rounded-xl text-slate-500 hover:text-slate-700 bg-slate-50 hover:bg-slate-200 dark:text-slate-400 dark:bg-slate-700/40 dark:hover:bg-slate-700 dark:hover:text-slate-200 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed border border-slate-200/50 dark:border-slate-700 shadow-sm hover:shadow transform hover:scale-105 active:scale-95">
                      <MoreVertical class="w-5 h-5" />
                      <span class="tooltip-top hidden sm:block">Acciones</span>
                    </button>
                  </div>

                  <!-- Expanded Actions Toolbar -->
                  <div v-else class="flex items-center gap-2 w-full h-full animate-pop-in">
                    <button @click.stop="toggleActive(docente)"
                      class="flex-[1.5] flex justify-center items-center gap-2 h-full bg-slate-50 dark:bg-slate-700/30 rounded-xl border border-slate-200/50 dark:border-slate-700 cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-700/50 transition-colors">
                      <div class="relative w-11 h-6 rounded-full transition-colors flex items-center shrink-0"
                          :class="docente.is_active ? 'bg-teal-500' : 'bg-slate-300 dark:bg-slate-600'">
                        <div class="absolute w-5 h-5 bg-white rounded-full transition-transform duration-200 flex flex-col justify-center items-center shadow-sm"
                            :class="docente.is_active ? 'translate-x-[22px]' : 'translate-x-0.5'">
                             <Loader2 v-if="togglingId === docente.id" class="w-3.5 h-3.5 text-slate-500 animate-spin" />
                        </div>
                      </div>
                      <span class="text-xs font-semibold" :class="docente.is_active ? 'text-teal-600 dark:text-teal-400' : 'text-slate-500 dark:text-slate-400'">
                        {{ docente.is_active ? 'Activo' : 'Inactivo' }}
                      </span>
                    </button>
                    
                    <button @click.stop="deleteDocente(docente)"
                      class="flex-[2] flex items-center justify-center h-full gap-1.5 px-3 py-1.5 text-sm font-semibold text-white bg-red-500 hover:bg-red-600 rounded-xl transition-colors shadow-sm shadow-red-500/20">
                      <Trash2 class="w-4 h-4 shrink-0" />
                      <span>Eliminar</span>
                    </button>
                    
                    <button @click.stop="showDeleteFor = null"
                      class="flex items-center justify-center w-10 shrink-0 h-full rounded-xl text-slate-500 hover:text-slate-700 bg-slate-100 hover:bg-slate-200 dark:text-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 transition-colors"
                      title="Cancelar">
                      <X class="w-5 h-5" />
                    </button>
                  </div>
              </div>

            </div>
          </div>
          </Transition>
        </div>

        <!-- Desktop Table View -->
        <div class="hidden md:block overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700">
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">DNI</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">Nombre Completo</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 hidden xl:table-cell">
                  Creado por</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 hidden xl:table-cell">
                  Fecha</th>
                <th class="text-center px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">Rol</th>
                <th class="text-right px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 w-[204px] xl:w-[252px]">Acciones</th>
              </tr>
            </thead>
            <Transition name="table-content" mode="out-in">
              <tbody v-if="loading" key="loading" class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr v-for="n in 5" :key="n" class="animate-pulse">
                  <td class="px-4 py-3">
                    <div class="h-4 w-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-4 w-40 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <div class="h-4 w-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <div class="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded-full mx-auto"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-8 w-20 bg-slate-200 dark:bg-slate-700 rounded ml-auto"></div>
                  </td>
                </tr>
              </tbody>
              <tbody v-else key="data" class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr v-for="docente in docentes" :key="docente.id"
                  class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors"
                  :class="{ 'opacity-60': !docente.is_active }">
                  <td class="px-4 py-3 font-mono text-slate-700 dark:text-slate-300">{{ docente.dni }}</td>
                  <td class="px-4 py-3">
                    <span class="font-medium text-slate-800 dark:text-white">
                      {{ [docente.nombres, docente.apellidos].filter(Boolean).join(' ') || '—' }}
                    </span>
                    <span v-if="docente.id === auth.user?.id"
                      class="ml-2 text-[10px] text-teal-600 dark:text-teal-400 font-bold bg-teal-50 dark:bg-teal-900/30 px-1.5 py-0.5 rounded-full">tú</span>
                  </td>
                  <!-- Creado por -->
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <span v-if="docente.creado_por_id" class="text-xs text-slate-600 dark:text-slate-300">
                      {{ creadorNombre(docente.creado_por_id) }}
                    </span>
                    <span v-else class="text-slate-400 text-xs">—</span>
                  </td>
                  <!-- Fecha de creación -->
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <span v-if="docente.fecha_creacion" class="text-xs text-slate-500 dark:text-slate-400">
                      {{ formatFecha(docente.fecha_creacion) }}
                    </span>
                    <span v-else class="text-slate-400 text-xs">—</span>
                  </td>
                  <td class="px-4 py-3 text-center">
                    <span class="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full" :class="docente.is_superuser
                      ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'
                      : 'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'">
                      <Shield class="w-3 h-3" />
                      {{ docente.is_superuser ? 'Admin' : 'Docente' }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end h-[44px] w-[172px] xl:w-[220px] ml-auto">
                      
                      <!-- Default Actions -->
                      <div v-if="showDeleteFor !== docente.id" class="flex items-center gap-2">
                        <button @click.stop="openDetails(docente)"
                          class="has-tooltip relative flex items-center justify-center w-8 h-8 md:w-9 md:h-9 bg-slate-50 text-slate-400 hover:bg-indigo-500 hover:text-white dark:bg-slate-800/80 dark:text-slate-400 dark:hover:bg-indigo-500 dark:hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md hover:shadow-indigo-500/20 transform hover:-translate-y-0.5">
                          <Eye class="w-4 h-4 md:w-[18px] md:h-[18px]" />
                          <span class="tooltip-top">Ver detalles del usuario</span>
                        </button>
                        <button @click.stop="openEdit(docente)"
                          class="has-tooltip relative flex items-center justify-center w-8 h-8 md:w-9 md:h-9 bg-slate-50 text-slate-400 hover:bg-teal-500 hover:text-white dark:bg-slate-800/80 dark:text-slate-400 dark:hover:bg-teal-500 dark:hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md hover:shadow-teal-500/20 transform hover:-translate-y-0.5">
                          <Edit2 class="w-4 h-4 md:w-[18px] md:h-[18px]" />
                          <span class="tooltip-top">Editar información del usuario</span>
                        </button>
                        <button @click.stop="openResetPassword(docente)"
                          class="has-tooltip relative flex items-center justify-center w-8 h-8 md:w-9 md:h-9 bg-slate-50 text-slate-400 hover:bg-amber-500 hover:text-white dark:bg-slate-800/80 dark:text-slate-400 dark:hover:bg-amber-500 dark:hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md hover:shadow-amber-500/20 transform hover:-translate-y-0.5">
                          <KeyRound class="w-4 h-4 md:w-[18px] md:h-[18px]" />
                          <span class="tooltip-top">Restablecer contraseña mediante PIN</span>
                        </button>
                        <button @click.stop="showDeleteFor = docente.id" :disabled="docente.id === auth.user?.id"
                          class="has-tooltip relative flex items-center justify-center w-8 h-8 md:w-9 md:h-9 bg-slate-50 text-slate-400 hover:bg-slate-700 hover:text-white dark:bg-slate-800/80 dark:text-slate-400 dark:hover:bg-slate-600 dark:hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md disabled:opacity-40 disabled:hover:bg-slate-50 disabled:hover:text-slate-400 disabled:hover:-translate-y-0 disabled:hover:shadow-sm transform hover:-translate-y-0.5 active:scale-95">
                          <MoreVertical class="w-4 h-4 md:w-[18px] md:h-[18px]" />
                          <span class="tooltip-top">Desplegar opciones avanzadas</span>
                        </button>
                      </div>

                      <!-- Expanded Actions Toolbar -->
                      <div v-else class="flex items-center gap-1 xl:gap-1.5 bg-slate-50 dark:bg-slate-800/80 p-1 rounded-xl border border-slate-100 dark:border-slate-700 shadow-sm animate-pop-in">
                        <button @click.stop="toggleActive(docente)"
                          class="flex items-center gap-2 px-2.5 py-1.5 cursor-pointer rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700/50 transition-colors">
                          <div class="relative w-11 h-6 rounded-full transition-colors flex items-center shrink-0"
                              :class="docente.is_active ? 'bg-teal-500' : 'bg-slate-300 dark:bg-slate-600'">
                            <div class="absolute w-5 h-5 bg-white rounded-full transition-transform duration-200 flex justify-center items-center shadow-sm"
                                :class="docente.is_active ? 'translate-x-5' : 'translate-x-0.5'">
                                <Loader2 v-if="togglingId === docente.id" class="w-3.5 h-3.5 text-slate-500 animate-spin" />
                            </div>
                          </div>
                          <span class="text-xs font-semibold" :class="docente.is_active ? 'text-teal-600 dark:text-teal-400' : 'text-slate-500 dark:text-slate-400'">
                            {{ docente.is_active ? 'Activo' : 'Inactivo' }}
                          </span>
                        </button>
                        
                        <div class="w-px h-4 bg-slate-200 dark:bg-slate-700"></div>

                        <button @click.stop="deleteDocente(docente)"
                          class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-red-600 hover:text-white dark:text-red-400 hover:bg-red-500 rounded-lg transition-colors">
                          <Trash2 class="w-3.5 h-3.5 shrink-0" />
                          <span class="hidden xl:inline">Eliminar</span>
                        </button>
                        
                        <div class="w-px h-4 bg-slate-200 dark:bg-slate-700"></div>

                        <button @click.stop="showDeleteFor = null"
                          class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200 dark:hover:bg-slate-700 dark:text-slate-400 dark:hover:text-slate-200 rounded-lg transition-colors"
                          title="Cancelar">
                          <X class="w-3.5 h-3.5 shrink-0" />
                        </button>
                      </div>

                    </div>
                  </td>
                </tr>
                <tr v-if="docentes.length === 0">
                  <td colspan="6" class="text-center py-12 text-slate-400 dark:text-slate-500">
                    No hay usuarios registrados.
                  </td>
                </tr>
              </tbody>
            </Transition>
          </table>
        </div>

        <!-- Pagination Controls -->
        <div v-if="!loading && totalPages > 1"
          class="px-4 py-4 bg-slate-50 dark:bg-slate-700/30 border-t border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">

          <div class="text-[11px] md:text-xs text-slate-500 dark:text-slate-400">
            Mostrando <span class="font-bold text-slate-700 dark:text-slate-200">{{ Math.min((currentPage - 1) *
              pageSize + 1, totalCount) }}</span>
            a <span class="font-bold text-slate-700 dark:text-slate-200">{{ Math.min(currentPage * pageSize, totalCount)
            }}</span>
            de <span class="font-bold text-slate-700 dark:text-slate-200">{{ totalCount }}</span>
          </div>

          <div class="flex items-center gap-1">
            <!-- Prev -->
            <button @click="prevPage" :disabled="currentPage === 1"
              class="p-1.5 sm:p-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
              <ChevronLeft class="w-4 h-4" />
            </button>

            <!-- Pages -->
            <div class="flex items-center gap-1 mx-1">
              <button v-for="p in totalPages" :key="p" @click="setPage(p)" :class="[
                'w-7 h-7 sm:w-8 sm:h-8 rounded-lg text-xs font-bold transition-all',
                currentPage === p
                  ? 'bg-gradient-to-r from-teal-500 to-indigo-600 text-white shadow-md scale-110'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              ]">
                {{ p }}
              </button>
            </div>

            <!-- Next -->
            <button @click="nextPage" :disabled="currentPage === totalPages"
              class="p-1.5 sm:p-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <Teleport to="body">
      <Transition name="details-modal">
        <div v-if="showModal"
          class="fixed inset-0 z-[200] flex items-end sm:items-center justify-center sm:p-4">
          
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="closeModal"></div>

          <!-- Bottom Sheet (Mobile) / Card (Desktop) -->
          <div class="relative bg-white dark:bg-slate-800 w-full sm:max-w-lg max-h-[92dvh] sm:max-h-[90vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10">
            
            <!-- Drag handle (mobile) -->
            <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0" @click="closeModal">
                <div class="w-10 h-1 rounded-full bg-slate-200 dark:bg-slate-600"></div>
            </div>

            <!-- Modal Header -->
            <div class="flex items-center justify-between p-4 sm:p-6 sm:pt-6 pt-3 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <h2 class="text-base sm:text-lg font-bold text-slate-800 dark:text-white">
                {{ editingId ? 'Editar Usuario' : 'Nuevo Usuario' }}
              </h2>
              <button @click="closeModal"
                class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Modal Body -->
            <div class="p-4 sm:p-6 space-y-4 overflow-y-auto">

              <!-- Error del servidor -->
              <div v-if="serverError"
                class="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-sm border border-red-100 dark:border-red-900/50">
                <AlertCircle class="w-4 h-4 shrink-0" />
                {{ serverError }}
              </div>

              <!-- DNI -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">DNI <span
                    class="text-red-500">*</span></label>
                <input v-model="dni" type="text" maxlength="8" placeholder="12345678" :disabled="!!editingId" :class="[
                  'w-full bg-slate-50 dark:bg-slate-700 border rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed font-mono',
                  dniError
                    ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                    : 'border-slate-200 dark:border-slate-600 focus:ring-teal-500/50 focus:border-teal-500'
                ]" />
                <p v-if="dniError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
                  <AlertCircle class="w-3 h-3" /> {{ dniError }}
                </p>
              </div>

              <!-- Nombres + Apellidos -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Nombres <span
                      class="text-red-500">*</span></label>
                  <input v-model="nombres" type="text" placeholder="Juan" :class="[
                    'w-full bg-slate-50 dark:bg-slate-700 border rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 transition-all',
                    nombresError
                      ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                      : 'border-slate-200 dark:border-slate-600 focus:ring-teal-500/50 focus:border-teal-500'
                  ]" />
                  <p v-if="nombresError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle class="w-3 h-3" /> {{ nombresError }}
                  </p>
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Apellidos <span
                      class="text-red-500">*</span></label>
                  <input v-model="apellidos" type="text" placeholder="Pérez" :class="[
                    'w-full bg-slate-50 dark:bg-slate-700 border rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 transition-all',
                    apellidosError
                      ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                      : 'border-slate-200 dark:border-slate-600 focus:ring-teal-500/50 focus:border-teal-500'
                  ]" />
                  <p v-if="apellidosError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle class="w-3 h-3" /> {{ apellidosError }}
                  </p>
                </div>
              </div>

              <!-- Profesión -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Profesión</label>
                <input v-model="profesion" type="text" placeholder="Docente de Primaria"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
              </div>

              <!-- Institución Educativa -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Institución
                  Educativa</label>
                <input v-model="institucion_educativa" type="text" placeholder="IE 32001 Hermilio Valdizán"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
              </div>

              <!-- Nivel Educativo -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Nivel Educativo</label>
                <ComboBox v-model="nivel_educativo" :options="nivelOptions" placeholder="— Sin especificar —" />
              </div>

              <!-- Provincia + Distrito -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Provincia</label>
                  <ComboBox v-model="provincia_id" :options="provinciaOptions" placeholder="— Sin especificar —" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">
                    Distrito
                    <Loader2 v-if="loadingDistritos" class="inline w-3 h-3 animate-spin ml-1" />
                  </label>
                  <ComboBox v-model="distrito_id" :options="distritoOptions" placeholder="— Sin especificar —"
                    :disabled="!provincia_id || loadingDistritos" />
                </div>
              </div>

              <!-- Contraseña -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">
                  Contraseña {{ editingId ? '(dejar en blanco para no cambiar)' : '*' }}
                </label>
                <div class="relative">
                  <input v-model="password" :type="showPassword ? 'text' : 'password'"
                    :placeholder="editingId ? 'Nueva contraseña (opcional)' : 'Mínimo 6 caracteres'" :class="[
                      'w-full bg-slate-50 dark:bg-slate-700 border rounded-xl py-2.5 pl-3.5 pr-10 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 transition-all',
                      passwordError
                        ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                        : 'border-slate-200 dark:border-slate-600 focus:ring-indigo-500/50 focus:border-indigo-500'
                    ]" />
                  <button type="button" @click="showPassword = !showPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <Eye v-if="!showPassword" class="w-4 h-4" />
                    <EyeOff v-else class="w-4 h-4" />
                  </button>
                </div>
                <p v-if="passwordError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
                  <AlertCircle class="w-3 h-3" /> {{ passwordError }}
                </p>
              </div>

              <!-- Roles y estado -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <label class="flex items-center gap-2.5 cursor-pointer group">
                  <div class="relative">
                    <input type="checkbox" v-model="is_active" class="sr-only peer" />
                    <div
                      class="w-10 h-5 bg-slate-200 dark:bg-slate-600 rounded-full peer-checked:bg-teal-500 transition-colors">
                    </div>
                    <div
                      class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5">
                    </div>
                  </div>
                  <span class="text-xs font-semibold text-slate-600 dark:text-slate-300">Activo</span>
                </label>

                <label class="flex items-center gap-2.5 cursor-pointer group">
                  <div class="relative">
                    <input type="checkbox" v-model="is_superuser" class="sr-only peer" />
                    <div
                      class="w-10 h-5 bg-slate-200 dark:bg-slate-600 rounded-full peer-checked:bg-indigo-500 transition-colors">
                    </div>
                    <div
                      class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5">
                    </div>
                  </div>
                  <span class="text-xs font-semibold text-slate-600 dark:text-slate-300">Administrador</span>
                </label>
              </div>


            </div>

            <!-- Modal Footer -->
            <div class="flex justify-end gap-2 sm:gap-3 p-4 sm:px-6 sm:py-4 border-t border-slate-100 dark:border-slate-700 shrink-0 bg-slate-50 dark:bg-slate-800/50">
              <button @click="closeModal"
                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
                Cancelar
              </button>
              <button @click="saveDocente" :disabled="saving"
                class="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow-lg transition-all disabled:opacity-70 disabled:cursor-not-allowed">
                <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
                {{ editingId ? 'Guardar Cambios' : 'Crear Usuario' }}
              </button>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- Modal: Restablecer contraseña -->
    <Teleport to="body">
      <Transition name="details-modal">
        <div v-if="showResetModal"
          class="fixed inset-0 z-[200] flex items-end sm:items-center justify-center sm:p-4">
          
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showResetModal = false"></div>

          <!-- Bottom Sheet (Mobile) / Card (Desktop) -->
          <div class="relative bg-white dark:bg-slate-800 w-full sm:max-w-sm max-h-[92dvh] sm:max-h-[90vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10">

            <!-- Drag handle (mobile) -->
            <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0" @click="showResetModal = false">
                <div class="w-10 h-1 rounded-full bg-slate-200 dark:bg-slate-600"></div>
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between p-4 sm:p-5 sm:pt-5 pt-3 border-b border-slate-100 dark:border-slate-700 shrink-0">
              <div class="flex items-center gap-2.5 max-w-[85%]">
                <div class="w-8 h-8 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <KeyRound class="w-4 h-4 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <h2 class="text-base font-bold text-slate-800 dark:text-white">Restablecer Contraseña</h2>
                  <p class="text-xs text-slate-500 dark:text-slate-400 truncate max-w-[200px]">
                    {{ [resetTarget?.nombres, resetTarget?.apellidos].filter(Boolean).join(' ') || resetTarget?.dni }}
                  </p>
                </div>
              </div>
              <button @click="showResetModal = false"
                class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors">
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- Body -->
            <div class="p-4 sm:p-5 space-y-4 overflow-y-auto">

              <p
                class="text-xs text-slate-500 dark:text-slate-400 bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800/50 rounded-xl p-3">
                Esta acción restablece la contraseña sin necesitar la contraseña actual. Úsala cuando el usuario no
                puede acceder al sistema.
              </p>

              <div v-if="resetPasswordError"
                class="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-xs border border-red-100 dark:border-red-900/50">
                <AlertCircle class="w-3.5 h-3.5 shrink-0" />
                {{ resetPasswordError }}
              </div>

              <div v-if="resetSuccess"
                class="flex items-center gap-2 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded-xl text-xs border border-green-100 dark:border-green-900/50">
                <CheckCircle class="w-3.5 h-3.5 shrink-0" />
                Contraseña restablecida correctamente.
              </div>

              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Nueva contraseña <span
                    class="text-red-500">*</span></label>
                <div class="relative">
                  <input v-model="resetPassword" :type="showResetPass ? 'text' : 'password'"
                    placeholder="Mínimo 6 caracteres" :class="[
                      'w-full bg-slate-50 dark:bg-slate-700 border rounded-xl py-2.5 pl-3.5 pr-9 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 transition-all',
                      resetPasswordError
                        ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                        : 'border-slate-200 dark:border-slate-600 focus:ring-amber-500/50 focus:border-amber-500'
                    ]" />
                  <button type="button" @click="showResetPass = !showResetPass"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                    <Eye v-if="!showResetPass" class="w-4 h-4" />
                    <EyeOff v-else class="w-4 h-4" />
                  </button>
                </div>
              </div>

            </div>

            <!-- Footer -->
            <div class="flex items-center justify-end gap-2 p-4 sm:px-5 sm:py-4 border-t border-slate-100 dark:border-slate-700 shrink-0 bg-slate-50 dark:bg-slate-800/50">
              <button @click="showResetModal = false"
                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
                Cerrar
              </button>
              <button @click="saveResetPassword" :disabled="resetSaving || !resetPassword"
                class="flex items-center gap-2 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-60 disabled:cursor-not-allowed">
                <Loader2 v-if="resetSaving" class="w-3.5 h-3.5 animate-spin" />
                <KeyRound v-else class="w-3.5 h-3.5" />
                Restablecer
              </button>
            </div>

          </div>
        </div>
      </Transition>
    </Teleport>

    <Teleport to="body">
      <Transition name="details-modal">
        <div v-if="showDetailsModal && detailsTarget"
          class="fixed inset-0 z-[200] flex items-end sm:items-center justify-center sm:p-4">
          
          <!-- Backdrop -->
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showDetailsModal = false"></div>

          <!-- Bottom Sheet (Mobile) / Card (Desktop) -->
          <div class="relative bg-white dark:bg-slate-800 w-full sm:max-w-lg max-h-[92dvh] sm:max-h-[90vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10">
            
            <!-- Drag handle (mobile) -->
            <div class="sm:hidden absolute top-0 inset-x-0 h-4 flex justify-center items-center z-20" @click="showDetailsModal = false">
                <div class="w-10 h-1 rounded-full bg-white/40"></div>
            </div>

            <div class="bg-gradient-to-r from-teal-500 to-indigo-600 pt-7 pb-5 px-5 sm:p-6 flex items-center gap-3 sm:gap-4 text-white relative shrink-0">
               <button @click="showDetailsModal = false"
                  class="absolute top-3 right-3 sm:top-4 sm:right-4 p-1.5 bg-white/10 hover:bg-white/20 rounded-lg transition-colors">
                  <X class="w-4 h-4 sm:w-5 sm:h-5" />
                </button>
               <div class="w-14 h-14 sm:w-16 sm:h-16 shrink-0 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center font-bold text-xl sm:text-2xl border border-white/20 shadow-inner">
                 {{ detailsTarget.nombres ? detailsTarget.nombres.charAt(0) : (detailsTarget.dni?.charAt(0) || 'U') }}
               </div>
               <div class="min-w-0 pr-6">
                  <h2 class="text-lg sm:text-xl font-bold leading-tight truncate">{{ [detailsTarget.nombres, detailsTarget.apellidos].filter(Boolean).join(' ') || 'Sin Nombre' }}</h2>
                  <p class="text-indigo-100 text-xs sm:text-sm opacity-90 font-mono mt-0.5 truncate">{{ detailsTarget.dni }}</p>
               </div>
            </div>

            <div class="p-4 sm:p-6 overflow-y-auto">
                <!-- Data Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6">
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">DNI</p>
                        <p class="font-medium text-slate-700 dark:text-slate-200">{{ detailsTarget.dni }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Nombres</p>
                        <p class="font-medium text-slate-700 dark:text-slate-200">{{ detailsTarget.nombres || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Apellidos</p>
                        <p class="font-medium text-slate-700 dark:text-slate-200">{{ detailsTarget.apellidos || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Profesión</p>
                        <p class="font-medium text-slate-700 dark:text-slate-200">{{ detailsTarget.profesion || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Inst. Educativa</p>
                        <p class="font-medium text-slate-700 dark:text-slate-200">{{ detailsTarget.institucion_educativa || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Nivel Educativo</p>
                        <p class="font-medium text-slate-700 dark:text-slate-200">
                          <span v-if="detailsTarget.nivel_educativo" class="inline-flex bg-slate-100 dark:bg-slate-700 px-2 py-0.5 rounded-full text-xs">
                             {{ levelLabel[detailsTarget.nivel_educativo] ?? detailsTarget.nivel_educativo }}
                          </span>
                          <span v-else>—</span>
                        </p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Provincia</p>
                        <p class="font-medium text-slate-700 dark:text-slate-200">
                          <span v-if="detailsTarget.provincia_nombre" class="inline-flex items-center gap-1">
                            <MapPin class="w-3 h-3 text-teal-500" />
                            {{ detailsTarget.provincia_nombre }}
                          </span>
                          <span v-else>—</span>
                        </p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Distrito</p>
                        <p class="font-medium text-slate-700 dark:text-slate-200">
                          <span v-if="detailsTarget.distrito_nombre" class="inline-flex items-center gap-1">
                            <MapPin class="w-3 h-3 text-indigo-500" />
                            {{ detailsTarget.distrito_nombre }}
                          </span>
                          <span v-else>—</span>
                        </p>
                    </div>

                    <div class="col-span-1 sm:col-span-2 pt-3 mt-3 border-t border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row gap-4">
                        <div class="flex-1">
                           <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Estado</p>
                           <div class="flex items-center gap-1.5">
                             <div class="w-2.5 h-2.5 rounded-full" :class="detailsTarget.is_active ? 'bg-green-500' : 'bg-red-500'"></div>
                             <span class="font-medium text-slate-700 dark:text-slate-200 text-sm">{{ detailsTarget.is_active ? 'Activo' : 'Inactivo' }}</span>
                           </div>
                        </div>
                        <div class="flex-1">
                           <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Rol</p>
                           <div class="flex items-center gap-1.5">
                             <Shield class="w-3.5 h-3.5" :class="detailsTarget.is_superuser ? 'text-indigo-500' : 'text-slate-500'" />
                             <span class="font-medium text-slate-700 dark:text-slate-200 text-sm">{{ detailsTarget.is_superuser ? 'Administrador' : 'Docente regular' }}</span>
                           </div>
                        </div>
                    </div>
                    
                    <div class="col-span-1 sm:col-span-2 pt-3 mt-1 border-t border-slate-100 dark:border-slate-700 flex flex-col sm:flex-row gap-4">
                        <div class="flex-1">
                           <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Creado por</p>
                           <p class="font-medium text-slate-700 dark:text-slate-200 text-sm">
                             {{ detailsTarget.creado_por_id ? creadorNombre(detailsTarget.creado_por_id) : 'Sistema / Desconocido' }}
                           </p>
                        </div>
                        <div class="flex-1">
                           <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-1">Fecha de Creación</p>
                           <p class="font-medium text-slate-700 dark:text-slate-200 text-sm">
                             {{ detailsTarget.fecha_creacion ? formatFecha(detailsTarget.fecha_creacion) : '—' }}
                           </p>
                        </div>
                    </div>

                </div>
            </div>
            
            <div class="bg-slate-50 dark:bg-slate-800/50 p-4 border-t border-slate-100 dark:border-slate-700 flex justify-end shrink-0">
               <button @click="showDetailsModal = false"
                  class="w-full sm:w-auto px-5 py-2.5 sm:py-2 text-sm font-bold text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600 rounded-xl transition-all shadow-sm">
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
/* Table content fade on load */
.table-content-enter-active {
    transition: opacity 0.2s ease;
}
.table-content-leave-active {
    transition: opacity 0.12s ease;
}
.table-content-enter-from,
.table-content-leave-to {
    opacity: 0;
}

/* Bottom Sheet / Modal Animations */
.details-modal-enter-active,
.details-modal-leave-active {
    transition: opacity 0.25s ease;
}
.details-modal-enter-active .relative,
.details-modal-leave-active .relative {
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.details-modal-enter-from,
.details-modal-leave-to {
    opacity: 0;
}
/* Mobile slides from bottom */
.details-modal-enter-from .relative,
.details-modal-leave-to .relative {
    transform: translateY(100%);
}
/* Desktop scales from center */
@media (min-width: 640px) {
    .details-modal-enter-from .relative,
    .details-modal-leave-to .relative {
        transform: translateY(0) scale(0.95);
    }
}

/* Tooltips */
.has-tooltip {
  position: relative;
}
.tooltip-top {
  position: absolute;
  bottom: calc(100% + 8px);
  right: 0;
  transform: translateY(4px);
  background-color: #1e293b; /* slate-800 */
  color: #fff;
  padding: 6px 10px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  visibility: hidden;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
  z-index: 50;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.tooltip-top::after {
  content: '';
  position: absolute;
  top: 100%;
  right: 12px;
  border-width: 5px;
  border-style: solid;
  border-color: #1e293b transparent transparent transparent;
}
.has-tooltip:hover .tooltip-top {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}
.dark .tooltip-top {
  background-color: #f8fafc; /* slate-50 */
  color: #0f172a; /* slate-900 */
  border-color: rgba(0, 0, 0, 0.1);
}
.dark .tooltip-top::after {
  border-color: #f8fafc transparent transparent transparent;
}

@keyframes popIn {
  0% {
    opacity: 0;
    transform: scale(0.95) translateX(10px);
  }
  100% {
    opacity: 1;
    transform: scale(1) translateX(0);
  }
}
.animate-pop-in {
  animation: popIn 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;
}
</style>

