<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  docenteEstudiantesService,
  organizacionService,
  type EstudianteDocente,
  type RegistrarEstudianteDirectoPayload,
} from '../services/api'
import type { Grado } from '../types'
import Header from '../components/Header.vue'
import Swal from 'sweetalert2'
import {
  Plus, Edit2, Trash2, Home, Search, X, Eye, EyeOff,
  GraduationCap, Loader2, AlertCircle, CheckCircle, Users
} from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()

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

// Filtros
const filtroQ = ref('')
const filtroGrado = ref<number | null>(null)
const filtroSeccion = ref('')

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

// Secciones únicas de la lista actual
const seccionesDisponibles = computed(() => {
  const set = new Set(estudiantes.value.map(e => e.seccion).filter(Boolean))
  return Array.from(set).sort()
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

// ── Lifecycle ────────────────────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([cargarEstudiantes(), cargarGrados()])
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
  editingId.value = null
  serverError.value = ''
  showPass.value = false
  form.value = { nombres: '', apellidos: '', dni: '', password: '', grado_id: grados.value[0]?.id || 0, seccion: '' }
  showModal.value = true
}

function openEdit(e: EstudianteDocente) {
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

function closeModal() { showModal.value = false }

// ── CRUD ─────────────────────────────────────────────────────────────────────
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

async function eliminar(est: EstudianteDocente) {
  const nombre = [est.nombres, est.apellidos].filter(Boolean).join(' ') || est.codigo_estudiante || `#${est.id}`
  const result = await Swal.fire({
    title: '¿Eliminar estudiante?',
    html: `¿Seguro de eliminar a <strong>${nombre}</strong>? Esta acción no se puede deshacer.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#94a3b8',
    confirmButtonText: 'Sí, eliminar',
    cancelButtonText: 'Cancelar',
  })
  if (!result.isConfirmed) return
  try {
    await docenteEstudiantesService.eliminar(est.id)
    await cargarEstudiantes()
    Swal.fire({ icon: 'success', title: 'Eliminado', showConfirmButton: false, timer: 1600 })
  } catch (e: any) {
    Swal.fire('Error', e.response?.data?.detail ?? 'No se pudo eliminar', 'error')
  }
}

function nombreGrado(id: number | null) {
  if (!id) return '—'
  return grados.value.find(g => g.id === id)?.nombre ?? `Grado ${id}`
}

function formatFecha(f: string | null) {
  if (!f) return '—'
  return new Date(f).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 to-teal-50 dark:from-slate-900 dark:to-slate-950">

    <Header
      title="Mis Estudiantes"
      subtitle="Gestión de Aula"
      :has-resultado="false"
      gradient-class="from-teal-500 via-emerald-500 to-cyan-600 shadow-teal-500/20"
      subtitle-class="text-teal-100 dark:text-slate-400"
    >
      <template #actions-before>
        <button @click="router.push('/')"
          class="p-2 sm:p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 transition-all mr-1 sm:mr-2"
          title="Inicio">
          <Home class="w-3.5 h-3.5 sm:w-4 sm:h-4" />
        </button>
      </template>
    </Header>

    <div class="flex-1 w-full max-w-6xl mx-auto p-4 md:p-8">

      <!-- Toolbar -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
        <button @click="openCreate"
          class="flex items-center gap-2 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-600 hover:to-emerald-700 text-white font-bold px-5 py-2.5 rounded-xl shadow-lg transition-all hover:-translate-y-0.5 text-sm">
          <Plus class="w-4 h-4" />
          Registrar Estudiante
        </button>

        <!-- Filtros -->
        <div class="flex flex-wrap gap-2 w-full sm:w-auto">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            <input v-model="filtroQ" type="text" placeholder="Buscar..."
              class="pl-9 pr-4 py-2 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-sm outline-none focus:ring-2 focus:ring-teal-400/40 w-44" />
          </div>
          <select v-model="filtroGrado"
            class="px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-sm outline-none focus:ring-2 focus:ring-teal-400/40">
            <option :value="null">Todos los grados</option>
            <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
          </select>
          <select v-model="filtroSeccion"
            class="px-3 py-2 border border-slate-200 dark:border-slate-700 rounded-xl bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-200 text-sm outline-none focus:ring-2 focus:ring-teal-400/40">
            <option value="">Todas las secciones</option>
            <option v-for="s in seccionesDisponibles" :key="s" :value="s">{{ s }}</option>
          </select>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <Loader2 class="w-8 h-8 text-teal-500 animate-spin" />
      </div>

      <!-- Empty State -->
      <div v-else-if="estudiantes.length === 0"
        class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 p-12 text-center">
        <div class="w-16 h-16 rounded-2xl bg-teal-100 dark:bg-teal-900/30 flex items-center justify-center mx-auto mb-4">
          <Users class="w-8 h-8 text-teal-500" />
        </div>
        <h3 class="text-lg font-bold text-slate-700 dark:text-white mb-2">Sin estudiantes registrados</h3>
        <p class="text-slate-500 dark:text-slate-400 text-sm mb-5">
          Registra estudiantes directamente o comparte un código de clase para auto-registro.
        </p>
        <button @click="openCreate"
          class="inline-flex items-center gap-2 bg-gradient-to-r from-teal-500 to-emerald-600 text-white font-bold px-5 py-2.5 rounded-xl shadow transition-all hover:-translate-y-0.5 text-sm">
          <Plus class="w-4 h-4" /> Registrar primer estudiante
        </button>
      </div>

      <!-- Tabla -->
      <div v-else class="bg-white dark:bg-slate-800 rounded-2xl shadow border border-slate-100 dark:border-slate-700 overflow-hidden">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-slate-50 dark:bg-slate-900/40 border-b border-slate-100 dark:border-slate-700">
                <th class="text-left px-4 py-3 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Estudiante</th>
                <th class="text-left px-4 py-3 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Código</th>
                <th class="text-left px-4 py-3 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">DNI</th>
                <th class="text-left px-4 py-3 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Grado</th>
                <th class="text-left px-4 py-3 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Sección</th>
                <th class="text-left px-4 py-3 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Registro</th>
                <th class="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
              <tr v-for="est in estudiantesFiltrados" :key="est.id"
                class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                <td class="px-4 py-3">
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shrink-0">
                      <GraduationCap class="w-4 h-4 text-white" />
                    </div>
                    <div>
                      <p class="font-semibold text-slate-800 dark:text-white">
                        {{ [est.apellidos, est.nombres].filter(Boolean).join(', ') || '—' }}
                      </p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-3">
                  <span class="font-mono text-xs bg-teal-50 dark:bg-teal-900/20 text-teal-700 dark:text-teal-300 px-2 py-1 rounded-lg">
                    {{ est.codigo_estudiante || '—' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-slate-600 dark:text-slate-300">{{ est.dni || '—' }}</td>
                <td class="px-4 py-3 text-slate-600 dark:text-slate-300 text-xs">{{ est.grado_nombre || nombreGrado(est.grado_id) }}</td>
                <td class="px-4 py-3">
                  <span class="bg-indigo-50 dark:bg-indigo-900/20 text-indigo-700 dark:text-indigo-300 text-xs font-bold px-2 py-0.5 rounded-lg">
                    {{ est.seccion || '—' }}
                  </span>
                </td>
                <td class="px-4 py-3 text-slate-500 dark:text-slate-400 text-xs">{{ formatFecha(est.fecha_creacion) }}</td>
                <td class="px-4 py-3">
                  <div class="flex items-center gap-1 justify-end">
                    <button @click="openEdit(est)"
                      class="p-1.5 rounded-lg text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 transition-colors" title="Editar">
                      <Edit2 class="w-4 h-4" />
                    </button>
                    <button @click="eliminar(est)"
                      class="p-1.5 rounded-lg text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors" title="Eliminar">
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="estudiantesFiltrados.length === 0">
                <td colspan="7" class="px-4 py-8 text-center text-slate-500 dark:text-slate-400 text-sm">
                  Sin resultados para los filtros seleccionados
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="px-4 py-3 border-t border-slate-100 dark:border-slate-700 text-xs text-slate-400 dark:text-slate-500">
          {{ estudiantesFiltrados.length }} de {{ estudiantes.length }} estudiante(s)
        </div>
      </div>
    </div>

    <!-- ── Modal: Crear / Editar ── -->
    <Teleport to="body">
      <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0"
        enter-to-class="opacity-100" leave-active-class="transition duration-150" leave-from-class="opacity-100"
        leave-to-class="opacity-0">
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="closeModal">
          <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            <!-- Header del modal -->
            <div class="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-700">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center">
                  <GraduationCap class="w-5 h-5 text-white" />
                </div>
                <h2 class="text-base font-bold text-slate-800 dark:text-white">
                  {{ editingId ? 'Editar Estudiante' : 'Registrar Estudiante' }}
                </h2>
              </div>
              <button @click="closeModal" class="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 transition-colors">
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- Formulario -->
            <div class="p-5 space-y-4">
              <!-- Error servidor -->
              <div v-if="serverError" class="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-xs border border-red-100 dark:border-red-900/50">
                <AlertCircle class="w-3.5 h-3.5 shrink-0 mt-0.5" />
                {{ serverError }}
              </div>

              <!-- Nombres y Apellidos -->
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Nombres <span class="text-red-400">*</span></label>
                  <input v-model="form.nombres" type="text" placeholder="Ej: María"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition-all" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Apellidos <span class="text-red-400">*</span></label>
                  <input v-model="form.apellidos" type="text" placeholder="Ej: García López"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition-all" />
                </div>
              </div>

              <!-- DNI -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">DNI <span class="text-slate-400 font-normal">(opcional)</span></label>
                <input v-model="form.dni" type="text" placeholder="12345678" maxlength="8"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition-all" />
              </div>

              <!-- Grado y Sección -->
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Grado <span class="text-red-400">*</span></label>
                  <select v-model="form.grado_id"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition-all">
                    <option :value="0" disabled>Seleccionar...</option>
                    <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Sección <span class="text-red-400">*</span></label>
                  <input v-model="form.seccion" type="text" placeholder="Ej: A"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3 text-sm outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition-all" />
                </div>
              </div>

              <!-- Contraseña -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">
                  Contraseña <span v-if="editingId" class="text-slate-400 font-normal">(dejar vacío para no cambiar)</span><span v-else class="text-red-400">*</span>
                </label>
                <div class="relative">
                  <input v-model="form.password" :type="showPass ? 'text' : 'password'" placeholder="Mínimo 4 caracteres"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 pl-3 pr-9 text-sm outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500 transition-all" />
                  <button type="button" @click="showPass = !showPass" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                    <Eye v-if="!showPass" class="w-3.5 h-3.5" /><EyeOff v-else class="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <!-- Error de formulario -->
              <p v-if="formError" class="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400">
                <AlertCircle class="w-3.5 h-3.5 shrink-0" /> {{ formError }}
              </p>
            </div>

            <!-- Acciones -->
            <div class="flex gap-2 px-5 pb-5">
              <button @click="closeModal" class="px-4 py-2.5 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
                Cancelar
              </button>
              <button @click="guardar" :disabled="saving || !!formError"
                class="flex-1 flex items-center justify-center gap-2 py-2.5 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-600 hover:to-emerald-700 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-60">
                <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
                {{ editingId ? 'Guardar Cambios' : 'Registrar' }}
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </Teleport>

    <!-- ── Modal: Código generado ── -->
    <Teleport to="body">
      <Transition enter-active-class="transition duration-200" enter-from-class="opacity-0" enter-to-class="opacity-100"
        leave-active-class="transition duration-150" leave-from-class="opacity-100" leave-to-class="opacity-0">
        <div v-if="showSuccessModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-sm p-6 text-center space-y-4">
            <div class="w-14 h-14 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto">
              <CheckCircle class="w-7 h-7 text-green-500" />
            </div>
            <h2 class="text-lg font-bold text-slate-800 dark:text-white">Estudiante Registrado</h2>
            <p class="text-slate-500 dark:text-slate-400 text-sm">El código de acceso del estudiante es:</p>
            <div class="bg-slate-100 dark:bg-slate-700 rounded-xl py-3 px-6">
              <span class="text-2xl font-mono font-black text-teal-600 dark:text-teal-400 tracking-widest">{{ successCodigo }}</span>
            </div>
            <p class="text-xs text-slate-500 dark:text-slate-400">Comparte este código con el estudiante. Lo necesitará junto con su contraseña para iniciar sesión.</p>
            <button @click="showSuccessModal = false"
              class="w-full py-2.5 bg-gradient-to-r from-teal-500 to-emerald-600 text-white font-bold rounded-xl shadow hover:from-teal-600 hover:to-emerald-700 transition-all">
              Entendido
            </button>
          </div>
        </div>
      </Transition>
    </Teleport>

  </div>
</template>
