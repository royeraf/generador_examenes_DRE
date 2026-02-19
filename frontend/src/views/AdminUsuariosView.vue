<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { adminUsuariosService, type DocenteCreatePayload, type DocenteUpdatePayload } from '../services/api'
import type { Docente } from '../types'
import {
  Plus, Edit2, Trash2, ToggleLeft, ToggleRight, Home,
  Shield, X, Eye, EyeOff, AlertCircle, KeyRound, CheckCircle,
  ChevronLeft, ChevronRight
} from 'lucide-vue-next'
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
const { value: password, errorMessage: passwordError } = useField<string>('password')
const { value: is_active } = useField<boolean>('is_active')
const { value: is_superuser } = useField<boolean>('is_superuser')

// Load
async function loadDocentes() {
  try {
    loading.value = true
    const response = await adminUsuariosService.getAll(currentPage.value, pageSize.value)
    docentes.value = response.items
    totalPages.value = response.pages
    totalCount.value = response.total
  } catch {
    Swal.fire('Error', 'No se pudo cargar la lista de usuarios', 'error')
  } finally {
    loading.value = false
  }
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

onMounted(loadDocentes)

// Modal
function openCreate() {
  editingId.value = null
  showPassword.value = false
  serverError.value = ''
  resetForm()
  showModal.value = true
}

function openEdit(docente: Docente) {
  editingId.value = docente.id
  showPassword.value = false
  serverError.value = ''
  setValues({
    dni: docente.dni,
    nombres: docente.nombres ?? '',
    apellidos: docente.apellidos ?? '',
    profesion: docente.profesion ?? '',
    institucion_educativa: docente.institucion_educativa ?? '',
    nivel_educativo: docente.nivel_educativo ?? '',
    password: '',
    is_active: docente.is_active,
    is_superuser: docente.is_superuser,
  })
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

// Save — vee-validate handleSubmit valida antes de ejecutar
const saveDocente = handleSubmit(
  async (values) => {
    serverError.value = ''
    saving.value = true
    try {
      if (editingId.value) {
        const payload: DocenteUpdatePayload = {
          nombres: values.nombres || undefined,
          apellidos: values.apellidos || undefined,
          profesion: values.profesion || undefined,
          institucion_educativa: values.institucion_educativa || undefined,
          nivel_educativo: values.nivel_educativo || undefined,
          is_active: values.is_active,
          is_superuser: values.is_superuser,
        }
        if (values.password) payload.password = values.password
        await adminUsuariosService.update(editingId.value, payload)
      } else {
        const payload: DocenteCreatePayload = {
          dni: values.dni,
          nombres: values.nombres,
          apellidos: values.apellidos,
          profesion: values.profesion,
          institucion_educativa: values.institucion_educativa,
          nivel_educativo: values.nivel_educativo,
          is_active: values.is_active ?? true,
          is_superuser: values.is_superuser ?? false,
          password: values.password!,
        }
        await adminUsuariosService.create(payload)
      }
      await loadDocentes()
      closeModal()
    } catch (e: any) {
      serverError.value = e.response?.data?.detail ?? 'Error al guardar el usuario'
    } finally {
      saving.value = false
    }
  },
  // onInvalidSubmit — no hace nada extra, los errores se muestran en el template
)

// Toggle active
async function toggleActive(docente: Docente) {
  if (docente.id === auth.user?.id) return
  try {
    await adminUsuariosService.toggleActive(docente.id)
    await loadDocentes()
  } catch {
    Swal.fire('Error', 'No se pudo cambiar el estado del usuario', 'error')
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
    resetSuccess.value = true
    resetPassword.value = ''
  } catch (e: any) {
    resetPasswordError.value = e.response?.data?.detail ?? 'Error al actualizar la contraseña'
  } finally {
    resetSaving.value = false
  }
}
</script>

<template>
  <div
    class="min-h-screen bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-950 p-4 md:p-8">

    <!-- Header -->
    <div class="max-w-7xl mx-auto">
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-black text-slate-800 dark:text-white">
            Gestión de <span
              class="bg-gradient-to-r from-teal-500 to-indigo-600 bg-clip-text text-transparent">Usuarios</span>
          </h1>
          <p class="text-slate-500 dark:text-slate-400 text-sm mt-1">Administra los docentes del sistema</p>
        </div>
        <div class="flex items-center gap-3">
          <button @click="openCreate"
            class="flex items-center gap-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold px-4 py-2.5 rounded-xl shadow-lg transition-all duration-200 hover:-translate-y-0.5 text-sm">
            <Plus class="w-4 h-4" />
            Nuevo Usuario
          </button>
          <button @click="router.push('/')"
            class="flex items-center gap-2 bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 font-medium px-4 py-2.5 rounded-xl shadow border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all text-sm">
            <Home class="w-4 h-4" />
            Inicio
          </button>
        </div>
      </div>

      <!-- Stats Cards -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">

        <!-- Total -->
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-4 flex items-center gap-4">
          <div
            class="w-11 h-11 rounded-xl bg-gradient-to-br from-teal-400 to-indigo-500 flex items-center justify-center shadow-lg shrink-0">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <div>
            <p class="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Total</p>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none mt-0.5">
              <span v-if="loading"
                class="inline-block w-8 h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ stats.total }}</span>
            </p>
            <p class="text-xs text-slate-400 dark:text-slate-500 mt-0.5">usuarios registrados</p>
          </div>
        </div>

        <!-- Activos -->
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-4 flex items-center gap-4">
          <div
            class="w-11 h-11 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center shadow-lg shrink-0">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p class="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Activos</p>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none mt-0.5">
              <span v-if="loading"
                class="inline-block w-8 h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ stats.active }}</span>
            </p>
            <p class="text-xs text-slate-400 dark:text-slate-500 mt-0.5">con acceso al sistema</p>
          </div>
        </div>

        <!-- Inactivos -->
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-4 flex items-center gap-4">
          <div
            class="w-11 h-11 rounded-xl bg-gradient-to-br from-red-400 to-rose-500 flex items-center justify-center shadow-lg shrink-0">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
            </svg>
          </div>
          <div>
            <p class="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Inactivos</p>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none mt-0.5">
              <span v-if="loading"
                class="inline-block w-8 h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ stats.inactive }}</span>
            </p>
            <p class="text-xs text-slate-400 dark:text-slate-500 mt-0.5">sin acceso activo</p>
          </div>
        </div>

        <!-- Administradores -->
        <div
          class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-4 flex items-center gap-4">
          <div
            class="w-11 h-11 rounded-xl bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center shadow-lg shrink-0">
            <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <p class="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-wide">Admins</p>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none mt-0.5">
              <span v-if="loading"
                class="inline-block w-8 h-6 bg-slate-200 dark:bg-slate-700 rounded animate-pulse"></span>
              <span v-else>{{ stats.admins }}</span>
            </p>
            <p class="text-xs text-slate-400 dark:text-slate-500 mt-0.5">con rol administrador</p>
          </div>
        </div>

      </div>

      <!-- Table -->
      <div
        class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl overflow-hidden border border-slate-100 dark:border-slate-700">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-slate-50 dark:bg-slate-700/50 border-b border-slate-100 dark:border-slate-700">
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">DNI</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">Nombre Completo</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 hidden md:table-cell">
                  Profesión</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 hidden lg:table-cell">IE
                </th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 hidden lg:table-cell">
                  Nivel</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 hidden xl:table-cell">
                  Creado por</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-slate-300 hidden xl:table-cell">
                  Fecha</th>
                <th class="text-center px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">Estado</th>
                <th class="text-center px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">Rol</th>
                <th class="text-right px-4 py-3 font-semibold text-slate-600 dark:text-slate-300">Acciones</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
              <template v-if="loading">
                <tr v-for="n in 5" :key="n" class="animate-pulse">
                  <td class="px-4 py-3">
                    <div class="h-4 w-16 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-4 w-40 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3 hidden md:table-cell">
                    <div class="h-4 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3 hidden lg:table-cell">
                    <div class="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3 hidden lg:table-cell">
                    <div class="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                  </td>
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <div class="h-4 w-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <div class="h-4 w-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-6 w-12 bg-slate-200 dark:bg-slate-700 rounded-full mx-auto"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded-full mx-auto"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-8 w-20 bg-slate-200 dark:bg-slate-700 rounded ml-auto"></div>
                  </td>
                </tr>
              </template>
              <template v-else>
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
                  <td class="px-4 py-3 text-slate-500 dark:text-slate-400 hidden md:table-cell">{{ docente.profesion ||
                    '—' }}</td>
                  <td class="px-4 py-3 text-slate-500 dark:text-slate-400 hidden lg:table-cell max-w-[180px] truncate">
                    {{
                      docente.institucion_educativa || '—' }}</td>
                  <td class="px-4 py-3 hidden lg:table-cell">
                    <span v-if="docente.nivel_educativo"
                      class="text-xs bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 px-2 py-0.5 rounded-full">
                      {{ levelLabel[docente.nivel_educativo] ?? docente.nivel_educativo }}
                    </span>
                    <span v-else class="text-slate-400">—</span>
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
                    <button @click="toggleActive(docente)" :disabled="docente.id === auth.user?.id"
                      :title="docente.is_active ? 'Desactivar' : 'Activar'"
                      class="inline-flex items-center gap-1 text-xs font-medium px-2.5 py-1 rounded-full transition-colors disabled:cursor-not-allowed"
                      :class="docente.is_active
                        ? 'bg-green-50 dark:bg-green-900/30 text-green-700 dark:text-green-400 hover:bg-green-100 dark:hover:bg-green-900/50'
                        : 'bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/50'">
                      <ToggleRight v-if="docente.is_active" class="w-3.5 h-3.5" />
                      <ToggleLeft v-else class="w-3.5 h-3.5" />
                      {{ docente.is_active ? 'Activo' : 'Inactivo' }}
                    </button>
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
                    <div class="flex items-center justify-end gap-1.5">
                      <button @click="openEdit(docente)"
                        class="p-1.5 text-slate-400 hover:text-teal-600 dark:hover:text-teal-400 hover:bg-teal-50 dark:hover:bg-teal-900/30 rounded-lg transition-colors"
                        title="Editar datos">
                        <Edit2 class="w-4 h-4" />
                      </button>
                      <button @click="openResetPassword(docente)"
                        class="p-1.5 text-slate-400 hover:text-amber-600 dark:hover:text-amber-400 hover:bg-amber-50 dark:hover:bg-amber-900/30 rounded-lg transition-colors"
                        title="Restablecer contraseña">
                        <KeyRound class="w-4 h-4" />
                      </button>
                      <button @click="deleteDocente(docente)" :disabled="docente.id === auth.user?.id"
                        class="p-1.5 text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        title="Eliminar">
                        <Trash2 class="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              </template>
              <tr v-if="docentes.length === 0">
                <td colspan="10" class="text-center py-12 text-slate-400 dark:text-slate-500">
                  No hay usuarios registrados.
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination Controls -->
        <div v-if="!loading && totalPages > 1"
          class="px-6 py-4 bg-slate-50 dark:bg-slate-700/30 border-t border-slate-100 dark:border-slate-700 flex flex-col md:flex-row items-center justify-between gap-4">

          <div class="text-xs text-slate-500 dark:text-slate-400">
            Mostrando <span class="font-bold text-slate-700 dark:text-slate-200">{{ Math.min((currentPage - 1) *
              pageSize + 1, totalCount) }}</span>
            a <span class="font-bold text-slate-700 dark:text-slate-200">{{ Math.min(currentPage * pageSize, totalCount)
            }}</span>
            de <span class="font-bold text-slate-700 dark:text-slate-200">{{ totalCount }}</span> usuarios
          </div>

          <div class="flex items-center gap-1">
            <!-- Prev -->
            <button @click="prevPage" :disabled="currentPage === 1"
              class="p-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
              <ChevronLeft class="w-4 h-4" />
            </button>

            <!-- Pages -->
            <div class="flex items-center gap-1 mx-1">
              <button v-for="p in totalPages" :key="p" @click="setPage(p)" :class="[
                'w-8 h-8 rounded-lg text-xs font-bold transition-all',
                currentPage === p
                  ? 'bg-gradient-to-r from-teal-500 to-indigo-600 text-white shadow-md scale-110'
                  : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700'
              ]">
                {{ p }}
              </button>
            </div>

            <!-- Next -->
            <button @click="nextPage" :disabled="currentPage === totalPages"
              class="p-2 rounded-lg border border-slate-200 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal -->
    <Teleport to="body">
      <Transition enter-active-class="transition ease-out duration-200" enter-from-class="opacity-0"
        enter-to-class="opacity-100" leave-active-class="transition ease-in duration-150" leave-from-class="opacity-100"
        leave-to-class="opacity-0">
        <div v-if="showModal"
          class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          @click.self="closeModal">
          <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">

            <!-- Modal Header -->
            <div class="flex items-center justify-between p-6 border-b border-slate-100 dark:border-slate-700">
              <h2 class="text-lg font-bold text-slate-800 dark:text-white">
                {{ editingId ? 'Editar Usuario' : 'Nuevo Usuario' }}
              </h2>
              <button @click="closeModal"
                class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Modal Body -->
            <div class="p-6 space-y-4">

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
              <div class="grid grid-cols-2 gap-3">
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
                <select v-model="nivel_educativo"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all">
                  <option value="">— Sin especificar —</option>
                  <option value="inicial">Inicial</option>
                  <option value="primaria">Primaria</option>
                  <option value="secundaria">Secundaria</option>
                </select>
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
              <div class="grid grid-cols-2 gap-3">
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
            <div class="flex justify-end gap-3 px-6 py-4 border-t border-slate-100 dark:border-slate-700">
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
      <Transition enter-active-class="transition ease-out duration-200" enter-from-class="opacity-0"
        enter-to-class="opacity-100" leave-active-class="transition ease-in duration-150" leave-from-class="opacity-100"
        leave-to-class="opacity-0">
        <div v-if="showResetModal"
          class="fixed inset-0 z-[200] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
          @click.self="showResetModal = false">
          <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-sm">

            <!-- Header -->
            <div class="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-700">
              <div class="flex items-center gap-2.5">
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
            <div class="p-5 space-y-4">

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
            <div class="flex justify-end gap-2 px-5 py-4 border-t border-slate-100 dark:border-slate-700">
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

    <!-- Botón Inicio (móvil/fixed) -->
    <button @click="router.push('/')"
      class="fixed bottom-6 left-6 z-[100] bg-white/90 dark:bg-slate-800/90 backdrop-blur-md text-slate-700 dark:text-slate-200 px-5 py-3 rounded-full shadow-2xl border-2 border-slate-100 dark:border-slate-600 font-bold text-sm hover:scale-105 hover:bg-white dark:hover:bg-slate-700 transition-all duration-300 flex items-center gap-2 md:hidden">
      <Home class="w-4 h-4" />
      Inicio
    </button>

  </div>
</template>
