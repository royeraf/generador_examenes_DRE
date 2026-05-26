<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, watch, onMounted, onUnmounted, computed } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { adminUsuariosService, ubigeoService, organizacionService, rolesConfigService, type DocenteCreatePayload, type DocenteUpdatePayload, type RolConfig } from '../../shared/services/api'
import type { Docente, Provincia, Distrito, Ugel, InstitucionEducativa } from '../../shared/types'
import {
  Plus, Edit2, Trash2,
  Shield, X, Eye, EyeOff, AlertCircle, KeyRound, CheckCircle,
  ChevronLeft, ChevronRight, Loader2, MoreVertical, Search, MapPin, Save, RotateCcw,
  Users, User
} from 'lucide-vue-next'
import ComboBox from '../../shared/components/ComboBox.vue'
import Header from '../../shared/components/Header.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import Swal from 'sweetalert2'
import { useForm, useField } from 'vee-validate'
import * as yup from 'yup'

const auth = useAuthStore()

// Tabs
const activeTab = ref<'usuarios' | 'roles'>('usuarios')

// Responsive
const isDesktop = ref(window.innerWidth >= 1024)
const onResize = () => { isDesktop.value = window.innerWidth >= 1024 }
onUnmounted(() => window.removeEventListener('resize', onResize))

// Datos de roles del sistema
const ROLES_SISTEMA = [
  { codigo: 'especialista_dre_comunicacion', nombre: 'Especialista DRE Comunicación', descripcion: 'Gestiona desempeños de comunicación, administra UGELes, instituciones y usuarios a nivel regional.', nivel: 1, etiqueta: 'DRE COM', gradiente: 'from-teal-400 to-emerald-500' },
  { codigo: 'especialista_dre_matematica',   nombre: 'Especialista DRE Matemática',   descripcion: 'Gestiona desempeños de matemática, administra UGELes, instituciones y usuarios a nivel regional.',   nivel: 1, etiqueta: 'DRE MAT', gradiente: 'from-violet-400 to-purple-500' },
  { codigo: 'responsable_ugel',              nombre: 'Responsable UGEL',              descripcion: 'Supervisa las instituciones educativas de su UGEL y accede a métricas del ámbito.',                   nivel: 2, etiqueta: 'UGEL',    gradiente: 'from-blue-400 to-cyan-500'   },
  { codigo: 'director',                      nombre: 'Director IE',                   descripcion: 'Administra su institución educativa, gestiona docentes y accede a módulos de evaluación.',            nivel: 3, etiqueta: 'Director', gradiente: 'from-violet-400 to-purple-500'},
  { codigo: 'auxiliar',                      nombre: 'Auxiliar',                      descripcion: 'Genera y gestiona evaluaciones dentro de la institución educativa.',                                  nivel: 4, etiqueta: 'Auxiliar', gradiente: 'from-amber-400 to-orange-500' },
  { codigo: 'docente',                       nombre: 'Docente',                       descripcion: 'Genera evaluaciones para sus estudiantes usando los módulos disponibles.',                            nivel: 5, etiqueta: 'Docente',  gradiente: 'from-rose-400 to-pink-500'   },
  { codigo: 'estudiante',                    nombre: 'Estudiante',                    descripcion: 'Accede al portal estudiantil para tomar evaluaciones asignadas por su docente.',                      nivel: 6, etiqueta: 'Alumno',   gradiente: 'from-slate-400 to-slate-500' },
]

// Roles config desde backend
const rolesConfig = ref<RolConfig[]>([])
const loadingRoles = ref(false)
// Estado de edición por rol: { [codigo]: string[] }
const rolesEditDraft = ref<Record<string, string[]>>({})
const rolesEditMode = ref<Record<string, boolean>>({})
const savingRol = ref<Record<string, boolean>>({})

async function loadRolesConfig() {
  loadingRoles.value = true
  try {
    rolesConfig.value = await rolesConfigService.getAll()
  } catch (e) {
    console.error('Error cargando roles config:', e)
  } finally {
    loadingRoles.value = false
  }
}

function modulosDelRol(codigo: string): string[] {
  const rc = rolesConfig.value.find(r => r.codigo === codigo)
  if (rc) return rc.modulos_efectivos
  return ROLE_MODULOS_DEFAULT[codigo] ?? []
}

function startEditRol(codigo: string) {
  rolesEditDraft.value[codigo] = [...modulosDelRol(codigo)]
  rolesEditMode.value[codigo] = true
}

function cancelEditRol(codigo: string) {
  rolesEditMode.value[codigo] = false
  delete rolesEditDraft.value[codigo]
}

function toggleRolModulo(rolCodigo: string, moduloId: string) {
  const draft = rolesEditDraft.value[rolCodigo] ?? []
  const idx = draft.indexOf(moduloId)
  if (idx >= 0) draft.splice(idx, 1)
  else draft.push(moduloId)
  rolesEditDraft.value[rolCodigo] = [...draft]
}

async function saveRolConfig(codigo: string) {
  savingRol.value[codigo] = true
  try {
    const updated = await rolesConfigService.update(codigo, rolesEditDraft.value[codigo] ?? null)
    const idx = rolesConfig.value.findIndex(r => r.codigo === codigo)
    if (idx >= 0) rolesConfig.value[idx] = updated
    else rolesConfig.value.push(updated)
    rolesEditMode.value[codigo] = false
    delete rolesEditDraft.value[codigo]
    Swal.fire({ icon: 'success', title: 'Permisos actualizados', showConfirmButton: false, timer: 1800 })
  } catch (e: any) {
    Swal.fire({ icon: 'error', title: 'Error', text: e.response?.data?.detail || 'No se pudo guardar', confirmButtonColor: '#6366f1' })
  } finally {
    savingRol.value[codigo] = false
  }
}

function usuariosPorRol(codigo: string): number {
  return docentes.value.filter(d => d.rol_codigo === codigo).length
}

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
const showStats = ref(localStorage.getItem('adminShowStats') !== 'false')

watch(showStats, (newVal) => {
  localStorage.setItem('adminShowStats', String(newVal))
})

let searchTimeout: any = null

// Ubigeo
const provincias = ref<Provincia[]>([])
const distritos = ref<Distrito[]>([])
const loadingDistritos = ref(false)
let isInitialLoad = false

// Organización
const ugeles = ref<Ugel[]>([])
const instituciones = ref<InstitucionEducativa[]>([])
const loadingOrganizacion = ref(false)
const ugelFiltroIE = ref<number | null>(null)

const institucionesFiltradas = computed(() =>
  ugelFiltroIE.value
    ? instituciones.value.filter(ie => ie.ugel_id === ugelFiltroIE.value)
    : []
)


// Módulos
const TODOS_MODULOS = [
  { id: 'lectosistem',          label: 'LectoSistem' },
  { id: 'matsistem',            label: 'MatSistem' },
  { id: 'asignaciones',         label: 'Asignaciones' },
  { id: 'codigos_clase',        label: 'Aulas' },
  { id: 'metricas',             label: 'Métricas' },
  { id: 'admin_desempenos_comunicacion', label: 'Curricular — Comunicación' },
  { id: 'admin_desempenos_matematica',  label: 'Curricular — Matemática' },
  { id: 'admin_desempenos',             label: 'Curricular — Ambas áreas' },
  { id: 'admin_ugeles',         label: 'Gestión UGELes' },
  { id: 'admin_instituciones',  label: 'Gestión Instituciones' },
  { id: 'admin_usuarios',       label: 'Gestión Usuarios' },
]
const ROLE_MODULOS_DEFAULT: Record<string, string[]> = {
  especialista_dre_comunicacion: ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_desempenos_comunicacion', 'admin_ugeles', 'admin_instituciones', 'admin_usuarios'],
  especialista_dre_matematica:   ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_desempenos_matematica',   'admin_ugeles', 'admin_instituciones', 'admin_usuarios'],
  responsable_ugel:              ['metricas', 'admin_instituciones', 'admin_usuarios'],
  director:                      ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas', 'admin_usuarios'],
  auxiliar:                      ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas'],
  docente:                       ['lectosistem', 'matsistem', 'asignaciones', 'codigos_clase', 'metricas'],
  estudiante:                    [],
}
// null = usar defaults del rol; array = override explícito
const modulosSeleccionados = ref<string[] | null>(null)
const usandoDefaultModulos = ref(true)

function toggleModulo(id: string) {
  // Primer click en modo default → activar personalización automáticamente
  if (usandoDefaultModulos.value) activarModulosPersonalizados()
  const idx = modulosSeleccionados.value!.indexOf(id)
  if (idx >= 0) modulosSeleccionados.value!.splice(idx, 1)
  else modulosSeleccionados.value!.push(id)
}

function resetModulosADefault() {
  usandoDefaultModulos.value = true
  modulosSeleccionados.value = null
}

function activarModulosPersonalizados() {
  usandoDefaultModulos.value = false
  const defaultsRol = ROLE_MODULOS_DEFAULT[rol_codigo.value ?? ''] ?? []
  modulosSeleccionados.value = [...defaultsRol]
}

function moduloActivo(id: string): boolean {
  if (usandoDefaultModulos.value) {
    return (ROLE_MODULOS_DEFAULT[rol_codigo.value ?? ''] ?? []).includes(id)
  }
  return modulosSeleccionados.value?.includes(id) ?? false
}

// Role display helpers
const ROL_LABELS: Record<string, string> = {
  especialista_dre_comunicacion: 'Esp. DRE Comunicación',
  especialista_dre_matematica: 'Esp. DRE Matemática',
  responsable_ugel: 'Responsable UGEL',
  director: 'Director',
  auxiliar: 'Auxiliar',
  docente: 'Docente',
  estudiante: 'Estudiante',
}
const ROL_COLORS: Record<string, string> = {
  especialista_dre_comunicacion: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-primary-light',
  especialista_dre_matematica: 'bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-300',
  responsable_ugel: 'bg-sky-100 text-sky-700 dark:bg-emerald-900/30 dark:text-primary-light',
  director: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300',
  auxiliar: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-300',
  docente: 'bg-teal-100 text-teal-700 dark:bg-emerald-900/30 dark:text-primary-light',
  estudiante: 'bg-slate-100 text-slate-700 dark:bg-surface-input dark:text-text-muted',
}
function rolLabel(codigo?: string | null) {
  return ROL_LABELS[codigo ?? ''] ?? codigo ?? '—'
}
function rolColor(codigo?: string | null) {
  return ROL_COLORS[codigo ?? ''] ?? 'bg-slate-100 text-slate-600 dark:bg-surface-input dark:text-text-muted'
}

// ComboBox options

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
  const admins = docentes.value.filter(d => d.rol_codigo?.includes('dre')).length
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
  rol_codigo: yup.string().required('El rol es obligatorio'),
  ugel_id: yup.number().nullable().optional(),
  institucion_educativa_id: yup.number().nullable().optional(),
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
}))

const ROLES_OPTIONS = [
  { value: 'especialista_dre_comunicacion', label: 'Especialista DRE — Comunicación' },
  { value: 'especialista_dre_matematica', label: 'Especialista DRE — Matemática' },
  { value: 'responsable_ugel', label: 'Responsable UGEL' },
  { value: 'director', label: 'Director' },
  { value: 'auxiliar', label: 'Auxiliar' },
  { value: 'docente', label: 'Docente' },
]

const { handleSubmit, resetForm, setValues } = useForm({
  validationSchema: schema,
  initialValues: {
    dni: '',
    nombres: '',
    apellidos: '',
    profesion: '',
    rol_codigo: 'docente',
    ugel_id: null as number | null,
    institucion_educativa_id: null as number | null,
    provincia_id: null as number | null,
    distrito_id: null as number | null,
    password: '',
    is_active: true,
  },
})

const { value: dni, errorMessage: dniError } = useField<string>('dni')
const { value: nombres, errorMessage: nombresError } = useField<string>('nombres')
const { value: apellidos, errorMessage: apellidosError } = useField<string>('apellidos')
const { value: profesion } = useField<string>('profesion')
const { value: rol_codigo, errorMessage: rolError } = useField<string>('rol_codigo')
const { value: ugel_id } = useField<number | null>('ugel_id')
const { value: institucion_educativa_id } = useField<number | null>('institucion_educativa_id')
const { value: provincia_id } = useField<number | null>('provincia_id')
const { value: distrito_id } = useField<number | null>('distrito_id')
const { value: password, errorMessage: passwordError } = useField<string>('password')
const { value: is_active } = useField<boolean>('is_active')

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
  window.addEventListener('resize', onResize)
  loadDocentes()
  loadRolesConfig()
  try {
    provincias.value = await ubigeoService.getProvincias()
  } catch (e) {
    console.error('Error cargando provincias:', e)
  }
  // Load UGELes e IEs para los selectores del formulario
  loadingOrganizacion.value = true
  try {
    const [ugelesData, iesData] = await Promise.all([
      organizacionService.getUgeles(true),
      organizacionService.getInstituciones(undefined, true),
    ])
    ugeles.value = ugelesData
    instituciones.value = iesData
  } catch (e) {
    console.error('Error cargando organización:', e)
  } finally {
    loadingOrganizacion.value = false
  }
})

// Modal
function openCreate() {
  editingId.value = null
  showPassword.value = false
  serverError.value = ''
  distritos.value = []
  modulosSeleccionados.value = null
  usandoDefaultModulos.value = true
  ugelFiltroIE.value = null
  resetForm()
  if (auth.isDirector && auth.user?.institucion_educativa_id) {
    ugelFiltroIE.value = auth.user.ugel_id ?? null
    setValues({ institucion_educativa_id: auth.user.institucion_educativa_id, ugel_id: auth.user.ugel_id ?? null })
  }
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

  // Pre-populate módulos
  if (docente.permisos_modulos !== null && docente.permisos_modulos !== undefined) {
    usandoDefaultModulos.value = false
    modulosSeleccionados.value = [...docente.permisos_modulos]
  } else {
    usandoDefaultModulos.value = true
    modulosSeleccionados.value = null
  }

  // Pre-populate UGEL filter for IE cascade
  if (docente.institucion_educativa_id) {
    const ie = instituciones.value.find(i => i.id === docente.institucion_educativa_id)
    ugelFiltroIE.value = ie?.ugel_id ?? null
  } else {
    ugelFiltroIE.value = null
  }

  isInitialLoad = true
  setValues({
    dni: docente.dni ?? '',
    nombres: docente.nombres ?? '',
    apellidos: docente.apellidos ?? '',
    profesion: docente.profesion ?? '',
    rol_codigo: docente.rol_codigo ?? 'docente',
    ugel_id: docente.ugel_id ?? null,
    institucion_educativa_id: docente.institucion_educativa_id ?? null,
    provincia_id: docente.provincia_id ?? null,
    distrito_id: docente.distrito_id ?? null,
    password: '',
    is_active: docente.is_active,
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

// Resetear IE al cambiar UGEL en el selector cascadeado
watch(ugelFiltroIE, (newVal, oldVal) => {
  if (!isInitialLoad && oldVal !== undefined && newVal !== oldVal) {
    institucion_educativa_id.value = null
  }
})

// Save — vee-validate handleSubmit valida antes de ejecutar
const saveDocente = handleSubmit(
  async (values) => {
    serverError.value = ''
    saving.value = true
    try {
      const permisosPayload = usandoDefaultModulos.value ? null : (modulosSeleccionados.value ?? [])
      if (editingId.value) {
        const payload: DocenteUpdatePayload = {
          nombres: values.nombres || undefined,
          apellidos: values.apellidos || undefined,
          profesion: values.profesion || undefined,
          rol_codigo: values.rol_codigo,
          ugel_id: values.ugel_id || null,
          institucion_educativa_id: values.institucion_educativa_id || null,
          provincia_id: values.provincia_id || null,
          distrito_id: values.distrito_id || null,
          is_active: values.is_active,
          permisos_modulos: permisosPayload,
        }
        if (values.password) payload.password = values.password
        await adminUsuariosService.update(editingId.value, payload)
        await loadDocentes()
        closeModal()
        Swal.fire({ icon: 'success', title: 'Cambios guardados', showConfirmButton: false, timer: 2000 })
      } else {
        const payload: DocenteCreatePayload = {
          dni: values.dni || null,
          nombres: values.nombres,
          apellidos: values.apellidos,
          profesion: values.profesion,
          rol_codigo: values.rol_codigo,
          ugel_id: values.ugel_id || null,
          institucion_educativa_id: values.institucion_educativa_id || null,
          provincia_id: values.provincia_id || null,
          distrito_id: values.distrito_id || null,
          is_active: values.is_active ?? true,
          password: values.password!,
          permisos_modulos: permisosPayload,
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

function creadorNombre(creado_por_id: number): string {
  const creador = docentes.value.find(d => d.id === creado_por_id)
  if (!creador) return `#${creado_por_id}`
  return [creador.nombres, creador.apellidos].filter(Boolean).join(' ') || creador.dni || `#${creado_por_id}`
}

// formatFecha importado de shared/utils/dateUtils

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
    class="min-h-screen flex flex-col bg-surface font-sans relative overflow-x-hidden">
    <EduBackground variant="indigo" />
    
    <Header title="Gestión" subtitle="Usuarios del Sistema" :show-home="true" />

    <div class="max-w-7xl mx-auto w-full relative z-10 flex-1 flex flex-col p-4 md:p-8">

    <!-- Main Container Content -->

      <!-- Stats Cards -->
      <Transition
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 -translate-y-4"
        enter-to-class="opacity-100 translate-y-0"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100 translate-y-0"
        leave-to-class="opacity-0 -translate-y-4"
      >
        <div v-show="showStats" class="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">

          <!-- Total -->
          <div
            class="bg-surface-card rounded-2xl shadow border border-slate-300 dark:border-slate-700 p-3 md:p-4 flex items-center gap-3 md:gap-4">
            <div
              class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-lg shrink-0">
              <svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-text-subtle uppercase tracking-wide truncate">Total</p>
              <p class="text-xl md:text-2xl font-black text-text leading-none mt-0.5">
                <span v-if="loading"
                  class="inline-block w-6 md:w-8 h-5 md:h-6 bg-slate-200 dark:bg-surface-input rounded animate-pulse"></span>
                <span v-else>{{ stats.total }}</span>
              </p>
              <p class="text-[10px] md:text-xs text-slate-400 dark:text-text-subtle mt-0.5 hidden xs:block truncate">registrados</p>
            </div>
          </div>

          <!-- Activos -->
          <div
            class="bg-surface-card rounded-2xl shadow border border-slate-300 dark:border-slate-700 p-3 md:p-4 flex items-center gap-3 md:gap-4">
            <div
              class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center shadow-lg shrink-0">
              <svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-text-subtle uppercase tracking-wide truncate">Activos</p>
              <p class="text-xl md:text-2xl font-black text-text leading-none mt-0.5">
                <span v-if="loading"
                  class="inline-block w-6 md:w-8 h-5 md:h-6 bg-slate-200 dark:bg-surface-input rounded animate-pulse"></span>
                <span v-else>{{ stats.active }}</span>
              </p>
              <p class="text-[10px] md:text-xs text-slate-400 dark:text-text-subtle mt-0.5 hidden xs:block truncate">con acceso</p>
            </div>
          </div>

          <!-- Inactivos -->
          <div
            class="bg-surface-card rounded-2xl shadow border border-slate-300 dark:border-slate-700 p-3 md:p-4 flex items-center gap-3 md:gap-4">
            <div
              class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-red-400 to-rose-500 flex items-center justify-center shadow-lg shrink-0">
              <svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-text-subtle uppercase tracking-wide truncate">Inactivos</p>
              <p class="text-xl md:text-2xl font-black text-text leading-none mt-0.5">
                <span v-if="loading"
                  class="inline-block w-6 md:w-8 h-5 md:h-6 bg-slate-200 dark:bg-surface-input rounded animate-pulse"></span>
                <span v-else>{{ stats.inactive }}</span>
              </p>
              <p class="text-[10px] md:text-xs text-slate-400 dark:text-text-subtle mt-0.5 hidden xs:block truncate">sin acceso</p>
            </div>
          </div>

          <!-- Administradores -->
          <div
            class="bg-surface-card rounded-2xl shadow border border-slate-300 dark:border-slate-700 p-3 md:p-4 flex items-center gap-3 md:gap-4">
            <div
              class="w-10 h-10 md:w-11 md:h-11 rounded-xl bg-gradient-to-br from-violet-400 to-violet-500 flex items-center justify-center shadow-lg shrink-0">
              <svg class="w-4 h-4 md:w-5 md:h-5 text-white" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round"
                  d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div class="min-w-0">
              <p class="text-[10px] md:text-xs font-semibold text-slate-400 dark:text-text-subtle uppercase tracking-wide truncate">Admins</p>
              <p class="text-xl md:text-2xl font-black text-text leading-none mt-0.5">
                <span v-if="loading"
                  class="inline-block w-6 md:w-8 h-5 md:h-6 bg-slate-200 dark:bg-surface-input rounded animate-pulse"></span>
                <span v-else>{{ stats.admins }}</span>
              </p>
              <p class="text-[10px] md:text-xs text-slate-400 dark:text-text-subtle mt-0.5 hidden xs:block truncate">especialistas DRE</p>
            </div>
          </div>

        </div>
      </Transition>

      <!-- Mobile Navigation Tabs (Premium Style) -->
      <div v-if="!isDesktop" class="shrink-0 flex items-center justify-around bg-surface-card rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-1.5 mb-6 shadow-sm">
        <button @click="activeTab = 'usuarios'" 
          class="flex-1 py-2.5 flex flex-col items-center justify-center gap-1 rounded-xl transition-all cursor-pointer" 
          :class="activeTab === 'usuarios' ? 'text-primary bg-teal-50 dark:bg-emerald-900/30' : 'text-slate-500'">
          <Users class="w-5 h-5" />
          <span class="text-[10px] font-black uppercase tracking-widest">Usuarios</span>
        </button>
        <button @click="activeTab = 'roles'" 
          class="flex-1 py-2.5 flex flex-col items-center justify-center gap-1 rounded-xl transition-all cursor-pointer" 
          :class="activeTab === 'roles' ? 'text-primary bg-teal-50 dark:bg-emerald-900/30' : 'text-slate-500'">
          <KeyRound class="w-5 h-5" />
          <span class="text-[10px] font-black uppercase tracking-widest">Roles</span>
        </button>
      </div>

      <!-- Desktop Navigation Tabs -->
      <div v-if="isDesktop" class="flex items-center gap-1 bg-surface-card p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700 mb-8 w-fit shadow-sm">
        <button @click="activeTab = 'usuarios'"
          :class="['flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all cursor-pointer',
            activeTab === 'usuarios'
              ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white shadow-lg shadow-teal-500/20'
              : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700']">
          <Users class="w-4 h-4" />
          Usuarios
        </button>
        <button @click="activeTab = 'roles'"
          :class="['flex items-center gap-2 px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all cursor-pointer',
            activeTab === 'roles'
              ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white shadow-lg shadow-teal-500/20'
              : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700']">
          <KeyRound class="w-4 h-4" />
          Roles y Permisos
        </button>
      </div>

      <!-- Toolbar -->
      <div v-if="activeTab === 'usuarios'" class="mb-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        
        <!-- Action Buttons -->
        <div class="flex items-center gap-2 sm:gap-3 flex-wrap">
          <button @click="openCreate"
            class="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-600 hover:to-emerald-700 text-white font-bold px-4 md:px-5 py-2 md:py-2.5 rounded-xl shadow-lg transition-all duration-200 hover:-translate-y-0.5 text-xs sm:text-sm cursor-pointer">
            <Plus class="w-4 h-4" />
            <span>Nuevo Usuario</span>
          </button>

          <button @click="showStats = !showStats"
            class="flex-1 sm:flex-none flex items-center justify-center gap-2 bg-surface-card text-slate-600 dark:text-text-muted font-bold px-4 md:px-5 py-2 md:py-2.5 rounded-xl shadow-sm border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all duration-200 text-xs sm:text-sm cursor-pointer">
            <EyeOff v-if="showStats" class="w-4 h-4 text-slate-400" />
            <Eye v-else class="w-4 h-4 text-slate-400" />
            <span class="hidden sm:inline">{{ showStats ? 'Ocultar Estadísticas' : 'Ver Estadísticas' }}</span>
            <span class="sm:hidden">{{ showStats ? 'Ocultar' : 'Ver Estadísticas' }}</span>
          </button>
        </div>

        <!-- Search Bar -->
        <div class="relative w-full md:w-96">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search class="h-5 w-5 text-slate-400 dark:text-text-subtle" />
          </div>
          <input type="text" v-model="searchQuery" @input="handleSearch"
            class="block w-full pl-10 pr-4 py-2.5 bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl leading-5 text-slate-900 dark:text-text placeholder-slate-400 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all shadow-sm font-bold text-sm"
            placeholder="Buscar por DNI, Nombres o Apellidos...">
          <div class="absolute inset-y-0 right-0 pr-3 flex items-center" v-if="searchQuery">
            <button @click="searchQuery = ''; handleSearch()" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 cursor-pointer">
              <X class="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <!-- User List Container -->
      <div v-if="activeTab === 'usuarios'" class="bg-surface-card md:rounded-2xl shadow-xl md:border border-slate-300 dark:border-slate-700 -mx-4 md:mx-0">
        
        <!-- Mobile Cards View -->
        <div class="md:hidden">
          <Transition name="table-content" mode="out-in">
          <div v-if="loading" key="loading" class="divide-y divide-slate-100 dark:divide-slate-700/50">
            <div v-for="n in 5" :key="n" class="p-4 animate-pulse">
              <div class="flex justify-between mb-3">
                <div class="space-y-2 w-1/2">
                   <div class="h-3 w-16 bg-slate-200 dark:bg-surface-input rounded"></div>
                   <div class="h-4 w-full bg-slate-200 dark:bg-surface-input rounded"></div>
                </div>
                <div class="space-y-2 items-end flex flex-col">
                   <div class="h-4 w-12 bg-slate-200 dark:bg-surface-input rounded-full"></div>
                   <div class="h-4 w-16 bg-slate-200 dark:bg-surface-input rounded-full"></div>
                </div>
              </div>
              <div class="space-y-2 pt-2 border-t border-slate-50 dark:border-slate-700/30">
                <div class="h-3 w-3/4 bg-slate-200 dark:bg-surface-input rounded"></div>
                <div class="h-3 w-1/2 bg-slate-200 dark:bg-surface-input rounded"></div>
              </div>
              <div class="flex justify-end gap-2 mt-3 pt-3 border-t border-slate-50 dark:border-slate-700/30">
                 <div class="h-7 w-20 bg-slate-200 dark:bg-surface-input rounded-lg"></div>
                 <div class="h-7 w-20 bg-slate-200 dark:bg-surface-input rounded-lg"></div>
                 <div class="h-7 w-10 bg-slate-200 dark:bg-surface-input rounded-lg"></div>
              </div>
            </div>
          </div>

          <div v-else key="data" class="space-y-4 p-4">
            <div v-if="docentes.length === 0" class="text-center py-12 text-slate-400 dark:text-text-subtle font-bold uppercase tracking-widest text-xs">
              Sin usuarios registrados
            </div>
            <div v-else v-for="docente in docentes" :key="docente.id"
              class="bg-surface-card p-5 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm transition-all"
              :class="{ 'opacity-60 grayscale-[0.5]': !docente.is_active }">
              
              <div class="flex items-start justify-between mb-4">
                <div class="flex items-center gap-4">
                  <div class="w-12 h-12 rounded-2xl bg-surface-input flex items-center justify-center font-black text-primary text-lg">
                    {{ (docente.nombres || '?').charAt(0) }}{{ (docente.apellidos || '?').charAt(0) }}
                  </div>
                  <div>
                    <h3 class="font-black text-text leading-tight">
                      {{ [docente.nombres, docente.apellidos].filter(Boolean).join(' ') || '—' }}
                      <span v-if="docente.id === auth.user?.id" 
                        class="ml-1 text-[9px] font-black uppercase tracking-tighter text-teal-600 bg-teal-50 px-1.5 py-0.5 rounded-full border border-teal-200">tú</span>
                    </h3>
                    <div class="flex items-center gap-2 mt-1">
                      <span class="inline-flex items-center gap-1 text-[9px] font-black px-2 py-0.5 rounded-lg uppercase tracking-widest" :class="rolColor(docente.rol_codigo)">
                        <Shield class="w-2.5 h-2.5" />
                        {{ rolLabel(docente.rol_codigo) }}
                      </span>
                      <span v-if="!docente.is_active" class="px-2 py-0.5 bg-red-50 text-red-500 rounded-lg text-[9px] font-black uppercase tracking-widest">Inactivo</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Actions Area (Premium Card Pattern) -->
              <div class="grid grid-cols-2 gap-3 pt-4 border-t border-slate-100 dark:border-slate-700">
                <div class="flex items-center gap-2">
                  <button @click="openDetails(docente)" 
                    class="flex-1 flex items-center justify-center p-2.5 bg-surface-input rounded-xl text-slate-500 hover:text-emerald-600 transition-all cursor-pointer">
                    <Eye class="w-4 h-4" />
                  </button>
                  <button @click="openEdit(docente)" 
                    class="flex-1 flex items-center justify-center p-2.5 bg-surface-input rounded-xl text-slate-500 hover:text-teal-600 transition-all cursor-pointer">
                    <Edit2 class="w-4 h-4" />
                  </button>
                  <button @click="openResetPassword(docente)" 
                    class="flex-1 flex items-center justify-center p-2.5 bg-surface-input rounded-xl text-slate-500 hover:text-amber-600 transition-all cursor-pointer">
                    <KeyRound class="w-4 h-4" />
                  </button>
                </div>

                <div class="flex items-center gap-2 justify-end">
                   <button @click="toggleActive(docente)" 
                    class="px-3 py-2 text-[10px] font-black uppercase tracking-widest rounded-xl transition-all cursor-pointer"
                    :class="docente.is_active ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-400'">
                    {{ docente.is_active ? 'Activo' : 'Pausado' }}
                  </button>
                  <button @click="deleteDocente(docente)" :disabled="docente.id === auth.user?.id"
                    class="p-2.5 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-400 transition-all disabled:opacity-30 cursor-pointer">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div class="mt-4 pt-3 border-t border-slate-50 dark:border-slate-700 flex items-center justify-between">
                <div class="text-[10px] font-mono text-slate-400 dark:text-text-subtle">DNI: {{ docente.dni }}</div>
                <div class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{{ formatFecha(docente.fecha_creacion) }}</div>
              </div>
            </div>
          </div>
          </Transition>
        </div>

        <!-- Desktop Table View -->
        <div class="hidden md:block overflow-x-auto">
          <table class="w-full text-sm">
            <thead>
              <tr class="bg-surface-input/50 border-b border-slate-300 dark:border-slate-700">
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-text-muted">DNI</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-text-muted">Nombre Completo</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-text-muted hidden xl:table-cell">
                  Creado por</th>
                <th class="text-left px-4 py-3 font-semibold text-slate-600 dark:text-text-muted hidden xl:table-cell">
                  Fecha</th>
                <th class="text-center px-4 py-3 font-semibold text-slate-600 dark:text-text-muted">Rol</th>
                <th class="text-right px-4 py-3 font-semibold text-slate-600 dark:text-text-muted w-[204px] xl:w-[252px]">Acciones</th>
              </tr>
            </thead>
            <Transition name="table-content" mode="out-in">
              <tbody v-if="loading" key="loading" class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr v-for="n in 5" :key="n" class="animate-pulse">
                  <td class="px-4 py-3">
                    <div class="h-4 w-16 bg-slate-200 dark:bg-surface-input rounded"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-4 w-40 bg-slate-200 dark:bg-surface-input rounded"></div>
                  </td>
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <div class="h-4 w-20 bg-slate-200 dark:bg-surface-input rounded"></div>
                  </td>
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <div class="h-4 w-24 bg-slate-200 dark:bg-surface-input rounded"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-6 w-16 bg-slate-200 dark:bg-surface-input rounded-full mx-auto"></div>
                  </td>
                  <td class="px-4 py-3">
                    <div class="h-8 w-20 bg-slate-200 dark:bg-surface-input rounded ml-auto"></div>
                  </td>
                </tr>
              </tbody>
              <tbody v-else key="data" class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr v-for="docente in docentes" :key="docente.id"
                  class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors"
                  :class="{ 'opacity-60': !docente.is_active }">
                  <td class="px-4 py-3 font-mono text-slate-700 dark:text-text-muted">{{ docente.dni }}</td>
                  <td class="px-4 py-3">
                    <span class="font-medium text-text">
                      {{ [docente.nombres, docente.apellidos].filter(Boolean).join(' ') || '—' }}
                    </span>
                    <span v-if="docente.id === auth.user?.id"
                      class="ml-2 text-[10px] text-primary font-bold bg-teal-50 dark:bg-emerald-900/30 px-1.5 py-0.5 rounded-full">tú</span>
                  </td>
                  <!-- Creado por -->
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <span v-if="docente.creado_por_id" class="text-xs text-slate-600 dark:text-text-muted">
                      {{ creadorNombre(docente.creado_por_id) }}
                    </span>
                    <span v-else class="text-slate-400 text-xs">—</span>
                  </td>
                  <!-- Fecha de creación -->
                  <td class="px-4 py-3 hidden xl:table-cell">
                    <span v-if="docente.fecha_creacion" class="text-xs text-slate-500 dark:text-text-muted">
                      {{ formatFecha(docente.fecha_creacion) }}
                    </span>
                    <span v-else class="text-slate-400 text-xs">—</span>
                  </td>
                  <td class="px-4 py-3 text-center">
                    <span class="inline-flex items-center gap-1 text-xs font-bold px-2 py-0.5 rounded-full" :class="rolColor(docente.rol_codigo)">
                      <Shield class="w-3 h-3" />
                      {{ rolLabel(docente.rol_codigo) }}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex items-center justify-end h-[44px] w-[172px] xl:w-[220px] ml-auto">
                      
                      <!-- Default Actions -->
                      <div v-if="showDeleteFor !== docente.id" class="flex items-center gap-2">
                        <button @click.stop="openDetails(docente)"
                          class="has-tooltip relative flex items-center justify-center w-8 h-8 md:w-9 md:h-9 bg-slate-50 text-slate-400 hover:bg-emerald-500 hover:text-white dark:bg-surface-card/80 dark:text-text-muted dark:hover:bg-emerald-500 dark:hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md hover:shadow-emerald-500/20 transform hover:-translate-y-0.5 cursor-pointer">
                          <Eye class="w-4 h-4 md:w-[18px] md:h-[18px]" />
                          <span class="tooltip-top">Ver detalles del usuario</span>
                        </button>
                        <button @click.stop="openEdit(docente)"
                          class="has-tooltip relative flex items-center justify-center w-8 h-8 md:w-9 md:h-9 bg-slate-50 text-slate-400 hover:bg-teal-500 hover:text-white dark:bg-surface-card/80 dark:text-text-muted dark:hover:bg-emerald-500 dark:hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md hover:shadow-teal-500/20 transform hover:-translate-y-0.5 cursor-pointer">
                          <Edit2 class="w-4 h-4 md:w-[18px] md:h-[18px]" />
                          <span class="tooltip-top">Editar información del usuario</span>
                        </button>
                        <button @click.stop="openResetPassword(docente)"
                          class="has-tooltip relative flex items-center justify-center w-8 h-8 md:w-9 md:h-9 bg-slate-50 text-slate-400 hover:bg-amber-500 hover:text-white dark:bg-surface-card/80 dark:text-text-muted dark:hover:bg-amber-500 dark:hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md hover:shadow-amber-500/20 transform hover:-translate-y-0.5 cursor-pointer">
                          <KeyRound class="w-4 h-4 md:w-[18px] md:h-[18px]" />
                          <span class="tooltip-top">Restablecer contraseña mediante PIN</span>
                        </button>
                        <button @click.stop="showDeleteFor = docente.id" :disabled="docente.id === auth.user?.id"
                          class="has-tooltip relative flex items-center justify-center w-8 h-8 md:w-9 md:h-9 bg-slate-50 text-slate-400 hover:bg-slate-700 hover:text-white dark:bg-surface-card/80 dark:text-text-muted dark:hover:bg-slate-600 dark:hover:text-white rounded-xl transition-all duration-300 shadow-sm hover:shadow-md disabled:opacity-40 disabled:hover:bg-slate-50 disabled:hover:text-slate-400 disabled:hover:-translate-y-0 disabled:hover:shadow-sm transform hover:-translate-y-0.5 active:scale-95 cursor-pointer">
                          <MoreVertical class="w-4 h-4 md:w-[18px] md:h-[18px]" />
                          <span class="tooltip-top">Desplegar opciones avanzadas</span>
                        </button>
                      </div>

                      <!-- Expanded Actions Toolbar -->
                      <div v-else class="flex items-center gap-1 xl:gap-1.5 bg-slate-50 dark:bg-surface-card/80 p-1 rounded-xl border border-slate-300 dark:border-slate-700 shadow-sm animate-pop-in">
                        <button @click.stop="toggleActive(docente)"
                          class="flex items-center gap-2 px-2.5 py-1.5 cursor-pointer rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700/50 transition-colors">
                          <div class="relative w-11 h-6 rounded-full transition-colors flex items-center shrink-0"
                              :class="docente.is_active ? 'bg-teal-500' : 'bg-slate-300 dark:bg-surface-elevated'">
                            <div class="absolute w-5 h-5 bg-white rounded-full transition-transform duration-200 flex justify-center items-center shadow-sm"
                                :class="docente.is_active ? 'translate-x-5' : 'translate-x-0.5'">
                                <Loader2 v-if="togglingId === docente.id" class="w-3.5 h-3.5 text-slate-500 animate-spin" />
                            </div>
                          </div>
                          <span class="text-xs font-semibold" :class="docente.is_active ? 'text-primary' : 'text-slate-500 dark:text-text-muted'">
                            {{ docente.is_active ? 'Activo' : 'Inactivo' }}
                          </span>
                        </button>
                        
                        <div class="w-px h-4 bg-slate-200 dark:bg-surface-input"></div>

                        <button @click.stop="deleteDocente(docente)"
                          class="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-semibold text-red-600 hover:text-white dark:text-red-400 hover:bg-red-500 rounded-xl transition-colors cursor-pointer">
                          <Trash2 class="w-3.5 h-3.5 shrink-0" />
                          <span class="hidden xl:inline">Eliminar</span>
                        </button>
                        
                        <div class="w-px h-4 bg-slate-200 dark:bg-surface-input"></div>

                        <button @click.stop="showDeleteFor = null"
                          class="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-200 dark:hover:bg-slate-700 dark:text-text-muted dark:hover:text-slate-200 rounded-xl transition-colors cursor-pointer"
                          title="Cancelar">
                          <X class="w-3.5 h-3.5 shrink-0" />
                        </button>
                      </div>

                    </div>
                  </td>
                </tr>
                <tr v-if="docentes.length === 0">
                  <td colspan="6" class="text-center py-12 text-slate-400 dark:text-text-subtle">
                    No hay usuarios registrados.
                  </td>
                </tr>
              </tbody>
            </Transition>
          </table>
        </div>

        <!-- Pagination Controls -->
        <div v-if="!loading && totalPages > 1"
          class="px-4 py-4 bg-surface-input/30 border-t border-slate-300 dark:border-slate-700 flex flex-col sm:flex-row items-center justify-between gap-4">

          <div class="text-[11px] md:text-xs text-slate-500 dark:text-text-muted">
            Mostrando <span class="font-bold text-slate-700 dark:text-text">{{ Math.min((currentPage - 1) *
              pageSize + 1, totalCount) }}</span>
            a <span class="font-bold text-slate-700 dark:text-text">{{ Math.min(currentPage * pageSize, totalCount)
            }}</span>
            de <span class="font-bold text-slate-700 dark:text-text">{{ totalCount }}</span>
          </div>

          <div class="flex items-center gap-1">
            <!-- Prev -->
            <button @click="prevPage" :disabled="currentPage === 1"
              class="p-1.5 sm:p-2 rounded-xl border border-slate-300 dark:border-slate-600 bg-surface-card text-slate-600 dark:text-text-muted hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
              <ChevronLeft class="w-4 h-4" />
            </button>

            <!-- Pages -->
            <div class="flex items-center gap-1 mx-1">
              <button v-for="p in totalPages" :key="p" @click="setPage(p)" :class="[
                'w-7 h-7 sm:w-8 sm:h-8 rounded-lg text-xs font-bold transition-all cursor-pointer',
                currentPage === p
                  ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white shadow-md scale-110'
                  : 'text-slate-600 dark:text-text-muted hover:bg-slate-100 dark:hover:bg-slate-700'
              ]">
                {{ p }}
              </button>
            </div>

            <!-- Next -->
            <button @click="nextPage" :disabled="currentPage === totalPages"
              class="p-1.5 sm:p-2 rounded-xl border border-slate-300 dark:border-slate-600 bg-surface-card text-slate-600 dark:text-text-muted hover:bg-slate-50 dark:hover:bg-slate-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors cursor-pointer">
              <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
      <!-- Roles y Permisos Section -->
      <div v-if="activeTab === 'roles'" class="space-y-6">

        <div v-if="loadingRoles" class="flex justify-center py-12">
          <Loader2 class="w-6 h-6 animate-spin text-teal-500" />
        </div>

        <template v-else>
          <!-- Role Cards con edición inline -->
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <div v-for="rol in ROLES_SISTEMA" :key="rol.codigo"
              class="bg-surface-card rounded-2xl border border-slate-300 dark:border-slate-700 shadow overflow-hidden flex flex-col">
              <div :class="['h-1.5 bg-gradient-to-r shrink-0', rol.gradiente]"></div>
              <div class="p-4 sm:p-5 flex flex-col flex-1 gap-3">
                <!-- Header -->
                <div class="flex items-start justify-between gap-2">
                  <div>
                    <div class="flex items-center gap-2 mb-0.5">
                      <span :class="['text-[9px] font-black px-2 py-0.5 rounded-full text-white bg-gradient-to-r', rol.gradiente]">
                        Nivel {{ rol.nivel }}
                      </span>
                    </div>
                    <h3 class="text-sm font-bold text-text leading-tight">{{ rol.nombre }}</h3>
                  </div>
                  <div class="flex flex-col items-end gap-1.5 shrink-0">
                    <span class="text-[10px] font-semibold bg-surface-input text-slate-500 dark:text-text-muted px-2 py-0.5 rounded-full whitespace-nowrap">
                      {{ usuariosPorRol(rol.codigo) }} usuarios
                    </span>
                    <button v-if="!rolesEditMode[rol.codigo]"
                      @click="startEditRol(rol.codigo)"
                      class="flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-primary hover:underline cursor-pointer">
                      <Edit2 class="w-2.5 h-2.5" /> Editar
                    </button>
                  </div>
                </div>
                <!-- Descripción -->
                <p class="text-[11px] text-slate-500 dark:text-text-muted leading-relaxed flex-1">{{ rol.descripcion }}</p>

                <!-- Módulos — Vista o Edición -->
                <div>
                  <p class="text-[9px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest mb-1.5">
                    Módulos por defecto
                  </p>

                  <!-- Vista (no editable) -->
                  <div v-if="!rolesEditMode[rol.codigo]" class="flex flex-wrap gap-1">
                    <span v-if="modulosDelRol(rol.codigo).length === 0"
                      class="text-[10px] italic text-slate-400 dark:text-text-subtle">Sin acceso a módulos</span>
                    <span v-for="mId in modulosDelRol(rol.codigo)" :key="mId"
                      class="text-[10px] font-medium px-2 py-0.5 rounded-full bg-teal-50 dark:bg-emerald-900/20 text-teal-700 dark:text-primary-light border border-teal-100 dark:border-emerald-800/50 leading-tight">
                      {{ TODOS_MODULOS.find(m => m.id === mId)?.label ?? mId }}
                    </span>
                  </div>

                  <!-- Edición -->
                  <div v-else class="space-y-2">
                    <div class="grid grid-cols-1 gap-1.5">
                      <label v-for="m in TODOS_MODULOS" :key="m.id"
                        :class="['flex items-center gap-2 px-2 py-1.5 rounded-xl border text-[11px] font-medium transition-colors cursor-pointer',
                          (rolesEditDraft[rol.codigo] ?? []).includes(m.id)
                            ? 'bg-teal-50 dark:bg-emerald-900/20 border-teal-300 dark:border-emerald-700 text-teal-700 dark:text-primary-light'
                            : 'bg-surface-input/50 border-slate-300 dark:border-slate-600 text-slate-500 dark:text-text-muted']">
                        <input type="checkbox" class="sr-only"
                          :checked="(rolesEditDraft[rol.codigo] ?? []).includes(m.id)"
                          @change="toggleRolModulo(rol.codigo, m.id)" />
                        <span :class="['w-3 h-3 rounded-sm border flex-shrink-0 flex items-center justify-center transition-colors',
                          (rolesEditDraft[rol.codigo] ?? []).includes(m.id)
                            ? 'bg-teal-500 border-teal-500'
                            : 'bg-surface-input border-slate-300 dark:border-slate-500']">
                          <svg v-if="(rolesEditDraft[rol.codigo] ?? []).includes(m.id)" class="w-2 h-2 text-white" viewBox="0 0 10 8" fill="none">
                            <path d="M1 4l3 3 5-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                        </span>
                        {{ m.label }}
                      </label>
                    </div>
                    <!-- Acciones -->
                    <div class="flex items-center gap-2 pt-1">
                      <button @click="saveRolConfig(rol.codigo)" :disabled="savingRol[rol.codigo]"
                        :class="['flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-bold transition-all cursor-pointer',
                          savingRol[rol.codigo]
                            ? 'bg-surface-input text-slate-400 cursor-not-allowed'
                            : 'bg-teal-500 hover:bg-teal-600 text-white']">
                        <Loader2 v-if="savingRol[rol.codigo]" class="w-3 h-3 animate-spin" />
                        <Save v-else class="w-3 h-3" />
                        Guardar
                      </button>
                      <button @click="cancelEditRol(rol.codigo)" :disabled="savingRol[rol.codigo]"
                        class="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-bold bg-surface-input text-slate-600 dark:text-text-muted hover:bg-slate-200 dark:hover:bg-slate-600 transition-all cursor-pointer">
                        <RotateCcw class="w-3 h-3" />
                        Cancelar
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Module Access Matrix (read-only overview) -->
          <div class="bg-surface-card rounded-2xl border border-slate-300 dark:border-slate-700 shadow overflow-hidden">
            <div class="px-5 py-4 border-b border-slate-300 dark:border-slate-700">
              <h3 class="text-sm font-bold text-text">Matriz de Acceso a Módulos</h3>
              <p class="text-[11px] text-slate-400 dark:text-text-subtle mt-0.5">Resumen actual — edita cada tarjeta arriba para cambiar permisos</p>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="border-b border-slate-300 dark:border-slate-700 bg-slate-50/60 dark:bg-surface-card/60">
                    <th class="text-left px-4 py-3 font-semibold text-slate-500 dark:text-text-muted min-w-[180px]">Módulo</th>
                    <th v-for="rol in ROLES_SISTEMA" :key="rol.codigo" class="px-3 py-3 text-center">
                      <div class="flex flex-col items-center gap-1.5">
                        <div :class="['w-6 h-6 rounded-lg bg-gradient-to-br flex items-center justify-center text-white font-black text-[8px]', rol.gradiente]">
                          {{ rol.etiqueta.slice(0, 2) }}
                        </div>
                        <span class="text-[9px] font-semibold text-slate-500 dark:text-text-muted whitespace-nowrap leading-tight max-w-[56px]">{{ rol.etiqueta }}</span>
                      </div>
                    </th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-slate-50 dark:divide-slate-700/40">
                  <tr v-for="modulo in TODOS_MODULOS" :key="modulo.id"
                    class="hover:bg-slate-50/70 dark:hover:bg-slate-700/20 transition-colors">
                    <td class="px-4 py-3 font-medium text-slate-700 dark:text-text-muted">{{ modulo.label }}</td>
                    <td v-for="rol in ROLES_SISTEMA" :key="rol.codigo" class="px-3 py-3 text-center">
                      <span v-if="modulosDelRol(rol.codigo).includes(modulo.id)"
                        class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-teal-100 dark:bg-emerald-900/40 mx-auto">
                        <svg class="w-3 h-3 text-primary" viewBox="0 0 10 8" fill="none">
                          <path d="M1 4l3 3 5-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </span>
                      <span v-else class="inline-flex items-center justify-center w-5 h-5 mx-auto">
                        <div class="w-1.5 h-1.5 rounded-full bg-slate-200 dark:bg-surface-elevated"></div>
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>

      </div><!-- /roles tab -->

    </div>

    <!-- Modal -->
    <Teleport to="body">
      <Transition name="details-modal">
        <div v-if="showModal"
          class="fixed inset-0 z-[200] flex items-end sm:items-center justify-center sm:p-4 bg-slate-900/60 backdrop-blur-sm">
          
          <!-- Backdrop -->
          <div class="absolute inset-0 cursor-pointer" @click="closeModal"></div>

          <!-- Bottom Sheet (Mobile) / Card (Desktop) -->
          <div class="relative bg-surface w-full sm:max-w-2xl max-h-[92dvh] sm:max-h-[90vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10 transition-transform duration-500 ease-out translate-y-0">
            
            <!-- Drag handle (mobile) -->
            <div class="sm:hidden flex justify-center pt-4 pb-2 shrink-0 cursor-pointer" @click="closeModal">
                <div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-surface-card"></div>
            </div>

            <!-- Modal Header -->
            <div class="flex items-center justify-between px-8 py-6 border-b border-slate-300 dark:border-slate-800 shrink-0">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center text-white shadow-lg shadow-teal-500/20">
                  <User v-if="editingId" class="w-6 h-6" />
                  <Plus v-else class="w-6 h-6" />
                </div>
                <div>
                  <h2 class="text-xl font-bold text-text leading-tight">
                    {{ editingId ? 'Editar Usuario' : 'Nuevo Usuario' }}
                  </h2>
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mt-0.5">Gestión de Cuenta</p>
                </div>
              </div>
              <button @click="closeModal"
                class="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all cursor-pointer">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Modal Body -->
            <div class="flex-1 min-h-0 p-4 sm:p-6 space-y-4 overflow-y-auto">

              <!-- Error del servidor -->
              <div v-if="serverError"
                class="flex items-center gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-sm border border-red-100 dark:border-red-900/50">
                <AlertCircle class="w-4 h-4 shrink-0" />
                {{ serverError }}
              </div>

              <!-- DNI -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">DNI <span
                    class="text-red-500">*</span></label>
                <input v-model="dni" type="text" maxlength="8" placeholder="12345678" :disabled="!!editingId" :class="[
                  'w-full bg-surface-input border rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-text outline-none focus:ring-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed font-black tracking-widest placeholder-slate-400',
                  dniError
                    ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                    : 'border-slate-300 dark:border-slate-600 focus:ring-teal-500/50 focus:border-teal-500'
                ]" />
                <p v-if="dniError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
                  <AlertCircle class="w-3 h-3" /> {{ dniError }}
                </p>
              </div>

              <!-- Nombres + Apellidos -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">Nombres <span
                      class="text-red-500">*</span></label>
                  <input v-model="nombres" type="text" placeholder="Juan" :class="[
                    'w-full bg-surface-input border rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 transition-all placeholder-slate-400',
                    nombresError
                      ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                      : 'border-slate-300 dark:border-slate-600 focus:ring-teal-500/50 focus:border-teal-500'
                  ]" />
                  <p v-if="nombresError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle class="w-3 h-3" /> {{ nombresError }}
                  </p>
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">Apellidos <span
                      class="text-red-500">*</span></label>
                  <input v-model="apellidos" type="text" placeholder="Pérez" :class="[
                    'w-full bg-surface-input border rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 transition-all placeholder-slate-400',
                    apellidosError
                      ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                      : 'border-slate-300 dark:border-slate-600 focus:ring-teal-500/50 focus:border-teal-500'
                  ]" />
                  <p v-if="apellidosError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
                    <AlertCircle class="w-3 h-3" /> {{ apellidosError }}
                  </p>
                </div>
              </div>

              <!-- Profesión -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">Profesión</label>
                <input v-model="profesion" type="text" placeholder="Docente de Primaria"
                  class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all placeholder-slate-400" />
              </div>

              <!-- Rol -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">Rol *</label>
                <select v-model="rol_codigo"
                  class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all cursor-pointer appearance-none">
                  <option v-for="r in ROLES_OPTIONS" :key="r.value" :value="r.value">{{ r.label }}</option>
                </select>
                <p v-if="rolError" class="mt-1 text-xs text-red-500">{{ rolError }}</p>
              </div>

              <!-- UGEL (solo para responsable_ugel) -->
              <div v-if="rol_codigo === 'responsable_ugel'">
                <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">
                  UGEL
                  <Loader2 v-if="loadingOrganizacion" class="inline w-3 h-3 animate-spin ml-1" />
                </label>
                <select v-model="ugel_id"
                  class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all cursor-pointer appearance-none">
                  <option :value="null">— Sin especificar —</option>
                  <option v-for="u in ugeles" :key="u.id" :value="u.id">{{ u.nombre }}</option>
                </select>
              </div>

              <!-- IE (para director, auxiliar, docente) -->
              <template v-if="['director','auxiliar','docente'].includes(rol_codigo)">
                <!-- Director: UGEL e IE fijas, no editables -->
                <template v-if="auth.isDirector">
                  <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">UGEL</label>
                    <div class="w-full bg-slate-100 dark:bg-surface-card border border-slate-200 dark:border-slate-700 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text-muted">
                      {{ auth.user?.ugel_nombre || '—' }}
                    </div>
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">Institución Educativa</label>
                    <div class="w-full bg-slate-100 dark:bg-surface-card border border-slate-200 dark:border-slate-700 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text-muted">
                      {{ auth.user?.institucion_nombre || '—' }}
                    </div>
                  </div>
                </template>
                <!-- DRE / UGEL: selector cascadeado UGEL → IE -->
                <template v-else>
                  <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">
                      UGEL
                      <Loader2 v-if="loadingOrganizacion" class="inline w-3 h-3 animate-spin ml-1" />
                    </label>
                    <select v-model="ugelFiltroIE"
                      class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all cursor-pointer appearance-none">
                      <option :value="null">— Seleccionar UGEL primero —</option>
                      <option v-for="u in ugeles" :key="u.id" :value="u.id">{{ u.nombre }}</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">
                      Institución Educativa
                      <span v-if="ugelFiltroIE" class="text-slate-400 font-normal">({{ institucionesFiltradas.length }} disponibles)</span>
                    </label>
                    <select v-model="institucion_educativa_id" :disabled="!ugelFiltroIE"
                      class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all cursor-pointer appearance-none disabled:opacity-50 disabled:cursor-not-allowed">
                      <option :value="null">— Sin especificar —</option>
                      <option v-for="ie in institucionesFiltradas" :key="ie.id" :value="ie.id">{{ ie.nombre }}</option>
                    </select>
                  </div>
                </template>
              </template>

              <!-- Módulos -->
              <div v-if="rol_codigo !== 'estudiante'">
                <div class="flex items-center justify-between mb-1.5">
                  <label class="text-xs font-bold text-slate-600 dark:text-text-muted">Acceso a módulos</label>
                  <button type="button" @click="usandoDefaultModulos ? activarModulosPersonalizados() : resetModulosADefault()"
                    class="text-[10px] font-semibold text-emerald-600 dark:text-primary hover:underline cursor-pointer">
                    {{ usandoDefaultModulos ? 'Personalizar' : 'Restablecer defaults del rol' }}
                  </button>
                </div>
                <p v-if="usandoDefaultModulos" class="text-[10px] text-slate-400 dark:text-text-subtle mb-2">
                  Usando defaults del rol seleccionado
                </p>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-2">
                  <label v-for="m in TODOS_MODULOS" :key="m.id"
                    :class="['flex items-center gap-2 px-2.5 py-2 rounded-xl border text-xs font-medium transition-colors cursor-pointer',
                      moduloActivo(m.id)
                        ? 'bg-teal-50 dark:bg-emerald-900/20 border-teal-300 dark:border-emerald-700 text-teal-700 dark:text-primary-light'
                        : 'bg-surface-input/50 border-slate-300 dark:border-slate-600 text-slate-500 dark:text-text-muted'
                    ]">
                    <input type="checkbox" class="sr-only"
                      :checked="moduloActivo(m.id)"
                      @change="toggleModulo(m.id)" />
                    <span :class="['w-3 h-3 rounded-sm border flex-shrink-0 flex items-center justify-center transition-colors',
                      moduloActivo(m.id) ? 'bg-teal-500 border-teal-500' : 'bg-surface-input border-slate-300 dark:border-slate-500']">
                      <svg v-if="moduloActivo(m.id)" class="w-2 h-2 text-white" viewBox="0 0 10 8" fill="none">
                        <path d="M1 4l3 3 5-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                    </span>
                    {{ m.label }}
                  </label>
                </div>
              </div>

              <!-- Provincia + Distrito -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">Provincia</label>
                  <ComboBox v-model="provincia_id" :options="provinciaOptions" placeholder="— Sin especificar —" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">
                    Distrito
                    <Loader2 v-if="loadingDistritos" class="inline w-3 h-3 animate-spin ml-1" />
                  </label>
                  <ComboBox v-model="distrito_id" :options="distritoOptions" placeholder="— Sin especificar —"
                    :disabled="!provincia_id || loadingDistritos" />
                </div>
              </div>

              <!-- Contraseña -->
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">
                  Contraseña {{ editingId ? '(dejar en blanco para no cambiar)' : '*' }}
                </label>
                <div class="relative">
                   <input v-model="password" :type="showPassword ? 'text' : 'password'"
                    :placeholder="editingId ? 'Nueva contraseña (opcional)' : 'Mínimo 6 caracteres'" :class="[
                      'w-full bg-surface-input border rounded-xl py-2.5 pl-3.5 pr-10 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 transition-all placeholder-slate-400',
                      passwordError
                        ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                        : 'border-slate-300 dark:border-slate-600 focus:ring-emerald-500/50 focus:border-emerald-500'
                    ]" />
                  <button type="button" @click="showPassword = !showPassword"
                    class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer">
                    <Eye v-if="!showPassword" class="w-4 h-4" />
                    <EyeOff v-else class="w-4 h-4" />
                  </button>
                </div>
                <p v-if="passwordError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
                  <AlertCircle class="w-3 h-3" /> {{ passwordError }}
                </p>
              </div>

              <!-- Estado -->
              <div>
                <label class="flex items-center gap-2.5 cursor-pointer group">
                  <div class="relative">
                    <input type="checkbox" v-model="is_active" class="sr-only peer" />
                    <div
                      class="w-10 h-5 bg-slate-200 dark:bg-surface-elevated rounded-full peer-checked:bg-teal-500 transition-colors">
                    </div>
                    <div
                      class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform peer-checked:translate-x-5">
                    </div>
                  </div>
                  <span class="text-xs font-semibold text-slate-600 dark:text-text-muted">Activo</span>
                </label>
              </div>


            </div>

            <!-- Modal Footer -->
            <div class="flex justify-end gap-2 sm:gap-3 p-4 sm:px-6 sm:py-4 border-t border-slate-300 dark:border-slate-700 shrink-0 bg-slate-50 dark:bg-surface-card/50">
              <button @click="closeModal"
                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-text-muted hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
                Cancelar
              </button>
              <button @click="saveDocente" :disabled="saving"
                class="flex items-center gap-2 px-5 py-2 bg-gradient-to-r from-teal-500 to-emerald-600 hover:from-teal-600 hover:to-emerald-700 text-white font-bold text-sm rounded-xl shadow-lg transition-all disabled:opacity-70 disabled:cursor-not-allowed">
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
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer" @click="showResetModal = false"></div>

          <!-- Bottom Sheet (Mobile) / Card (Desktop) -->
          <div class="relative bg-surface-card w-full sm:max-w-sm max-h-[92dvh] sm:max-h-[90vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10">

            <!-- Drag handle (mobile) -->
            <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0" @click="showResetModal = false">
                <div class="w-10 h-1 rounded-full bg-slate-200 dark:bg-surface-elevated"></div>
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between p-4 sm:p-5 sm:pt-5 pt-3 border-b border-slate-300 dark:border-slate-700 shrink-0">
              <div class="flex items-center gap-2.5 max-w-[85%]">
                <div class="w-8 h-8 rounded-xl bg-amber-100 dark:bg-amber-900/30 flex items-center justify-center">
                  <KeyRound class="w-4 h-4 text-amber-600 dark:text-amber-400" />
                </div>
                <div>
                  <h2 class="text-base font-bold text-text">Restablecer Contraseña</h2>
                  <p class="text-xs text-slate-500 dark:text-text-muted truncate max-w-[200px]">
                    {{ [resetTarget?.nombres, resetTarget?.apellidos].filter(Boolean).join(' ') || resetTarget?.dni }}
                  </p>
                </div>
              </div>
              <button @click="showResetModal = false"
                class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl transition-colors">
                <X class="w-4 h-4" />
              </button>
            </div>

            <!-- Body -->
            <div class="flex-1 min-h-0 p-4 sm:p-5 space-y-4 overflow-y-auto">

              <p
                class="text-xs text-slate-500 dark:text-text-muted bg-amber-50 dark:bg-amber-900/20 border border-amber-100 dark:border-amber-800/50 rounded-xl p-3">
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
                <label class="block text-xs font-bold text-slate-600 dark:text-text-muted mb-1.5">Nueva contraseña <span
                    class="text-red-500">*</span></label>
                <div class="relative">
                  <input v-model="resetPassword" :type="showResetPass ? 'text' : 'password'"
                    placeholder="Mínimo 6 caracteres" :class="[
                      'w-full bg-surface-input border rounded-xl py-2.5 pl-3.5 pr-9 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 transition-all placeholder-slate-400',
                      resetPasswordError
                        ? 'border-red-400 dark:border-red-500 focus:ring-red-400/40 focus:border-red-400'
                        : 'border-slate-300 dark:border-slate-600 focus:ring-amber-500/50 focus:border-amber-500'
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
            <div class="flex items-center justify-end gap-2 p-4 sm:px-5 sm:py-4 border-t border-slate-300 dark:border-slate-700 shrink-0 bg-slate-50 dark:bg-surface-card/50">
              <button @click="showResetModal = false"
                class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-text-muted hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
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
          <div class="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer" @click="showDetailsModal = false"></div>

          <!-- Bottom Sheet (Mobile) / Card (Desktop) -->
          <div class="relative bg-surface-card w-full sm:max-w-lg max-h-[92dvh] sm:max-h-[90vh] flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10">
            
            <!-- Drag handle (mobile) -->
            <div class="sm:hidden absolute top-0 inset-x-0 h-4 flex justify-center items-center z-20" @click="showDetailsModal = false">
                <div class="w-10 h-1 rounded-full bg-white/40"></div>
            </div>

            <div class="bg-gradient-to-r from-teal-500 to-emerald-600 pt-7 pb-5 px-5 sm:p-6 flex items-center gap-3 sm:gap-4 text-white relative shrink-0">
               <button @click="showDetailsModal = false"
                  class="absolute top-3 right-3 sm:top-4 sm:right-4 p-1.5 bg-white/10 hover:bg-white/20 rounded-xl transition-colors">
                  <X class="w-4 h-4 sm:w-5 sm:h-5" />
                </button>
               <div class="w-14 h-14 sm:w-16 sm:h-16 shrink-0 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center font-bold text-xl sm:text-2xl border border-white/20 shadow-inner">
                 {{ detailsTarget.nombres ? detailsTarget.nombres.charAt(0) : (detailsTarget.dni?.charAt(0) || 'U') }}
               </div>
               <div class="min-w-0 pr-6">
                  <h2 class="text-lg sm:text-xl font-bold leading-tight truncate">{{ [detailsTarget.nombres, detailsTarget.apellidos].filter(Boolean).join(' ') || 'Sin Nombre' }}</h2>
                  <p class="text-emerald-100 text-xs sm:text-sm opacity-90 font-mono mt-0.5 truncate">{{ detailsTarget.dni }}</p>
               </div>
            </div>

            <div class="flex-1 min-h-0 p-4 sm:p-6 overflow-y-auto">
                <!-- Data Grid -->
                <div class="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-6">
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">DNI</p>
                        <p class="font-medium text-slate-700 dark:text-text">{{ detailsTarget.dni }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Nombres</p>
                        <p class="font-medium text-slate-700 dark:text-text">{{ detailsTarget.nombres || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Apellidos</p>
                        <p class="font-medium text-slate-700 dark:text-text">{{ detailsTarget.apellidos || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Profesión</p>
                        <p class="font-medium text-slate-700 dark:text-text">{{ detailsTarget.profesion || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Inst. Educativa</p>
                        <p class="font-medium text-slate-700 dark:text-text">{{ detailsTarget.institucion_nombre || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">UGEL</p>
                        <p class="font-medium text-slate-700 dark:text-text">{{ detailsTarget.ugel_nombre || '—' }}</p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Provincia</p>
                        <p class="font-medium text-slate-700 dark:text-text">
                          <span v-if="detailsTarget.provincia_nombre" class="inline-flex items-center gap-1">
                            <MapPin class="w-3 h-3 text-teal-500" />
                            {{ detailsTarget.provincia_nombre }}
                          </span>
                          <span v-else>—</span>
                        </p>
                    </div>
                    <div>
                        <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Distrito</p>
                        <p class="font-medium text-slate-700 dark:text-text">
                          <span v-if="detailsTarget.distrito_nombre" class="inline-flex items-center gap-1">
                            <MapPin class="w-3 h-3 text-emerald-500" />
                            {{ detailsTarget.distrito_nombre }}
                          </span>
                          <span v-else>—</span>
                        </p>
                    </div>

                    <div class="col-span-1 sm:col-span-2 pt-3 mt-3 border-t border-slate-300 dark:border-slate-700 flex flex-col sm:flex-row gap-4">
                        <div class="flex-1">
                           <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Estado</p>
                           <div class="flex items-center gap-1.5">
                             <div class="w-2.5 h-2.5 rounded-full" :class="detailsTarget.is_active ? 'bg-green-500' : 'bg-red-500'"></div>
                             <span class="font-medium text-slate-700 dark:text-text text-sm">{{ detailsTarget.is_active ? 'Activo' : 'Inactivo' }}</span>
                           </div>
                        </div>
                        <div class="flex-1">
                           <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Rol</p>
                           <div class="flex items-center gap-1.5">
                             <Shield class="w-3.5 h-3.5" :class="rolColor(detailsTarget.rol_codigo)" />
                             <span class="font-medium text-slate-700 dark:text-text text-sm">{{ rolLabel(detailsTarget.rol_codigo) }}</span>
                           </div>
                        </div>
                    </div>
                    
                    <div class="col-span-1 sm:col-span-2 pt-3 mt-1 border-t border-slate-300 dark:border-slate-700 flex flex-col sm:flex-row gap-4">
                        <div class="flex-1">
                           <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Creado por</p>
                           <p class="font-medium text-slate-700 dark:text-text text-sm">
                             {{ detailsTarget.creado_por_id ? creadorNombre(detailsTarget.creado_por_id) : 'Sistema / Desconocido' }}
                           </p>
                        </div>
                        <div class="flex-1">
                           <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-text-subtle tracking-wider mb-1">Fecha de Creación</p>
                           <p class="font-medium text-slate-700 dark:text-text text-sm">
                             {{ detailsTarget.fecha_creacion ? formatFecha(detailsTarget.fecha_creacion) : '—' }}
                           </p>
                        </div>
                    </div>

                </div>
            </div>
            
            <div class="bg-slate-50 dark:bg-surface-card/50 p-4 border-t border-slate-300 dark:border-slate-700 flex justify-end shrink-0">
               <button @click="showDetailsModal = false"
                  class="w-full sm:w-auto px-5 py-2.5 sm:py-2 text-sm font-bold text-slate-600 dark:text-text-muted bg-surface-input border border-slate-300 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600 rounded-xl transition-all shadow-sm">
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

/* Premium Bottom Sheet / Modal Animations */
.details-modal-enter-active,
.details-modal-leave-active {
    transition: opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.details-modal-enter-active .relative,
.details-modal-leave-active .relative {
    transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
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
/* Desktop scales and fades from center */
@media (min-width: 640px) {
    .details-modal-enter-from .relative,
    .details-modal-leave-to .relative {
        transform: translateY(0) scale(0.9) translateZ(0);
    }
}

/* Custom Scrollbar for Modal Body */
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.4);
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

