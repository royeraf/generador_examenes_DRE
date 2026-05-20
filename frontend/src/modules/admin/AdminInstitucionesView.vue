<script setup lang="ts">
import { ref, onMounted, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { organizacionService, type IECreatePayload } from '../../shared/services/api'
import type { InstitucionEducativa, Ugel } from '../../shared/types'
import Header from '../../shared/components/Header.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import { useTheme } from '../../shared/composables/useTheme'
import { Plus, Edit2, Trash2, Loader2, AlertCircle, Search, X, Home, Building2, MapPin, ChevronDown } from 'lucide-vue-next'
import Swal from 'sweetalert2'

const router = useRouter()
const { isDark, toggleTheme } = useTheme()

// State
const instituciones = ref<InstitucionEducativa[]>([])
const ugeles = ref<Ugel[]>([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const serverError = ref('')
const searchQuery = ref('')

// Responsive State
const isDesktop = ref(window.innerWidth >= 1024)
const onResize = () => { isDesktop.value = window.innerWidth >= 1024 }

const nivelOptions = [
  { value: 'inicial', label: 'Inicial' },
  { value: 'primaria', label: 'Primaria' },
  { value: 'secundaria', label: 'Secundaria' },
]

const nivelLabel: Record<string, string> = { inicial: 'Inicial', primaria: 'Primaria', secundaria: 'Secundaria' }
const nivelColors: Record<string, string> = {
  inicial: 'bg-amber-50 text-amber-600 border-amber-200',
  primaria: 'bg-indigo-50 text-indigo-600 border-indigo-200',
  secundaria: 'bg-teal-50 text-teal-600 border-teal-200',
}

type FormType = Omit<IECreatePayload, 'nivel_educativo'> & { nivel_educativo: string[], is_active: boolean }

const emptyForm = (): FormType => ({
  codigo_modular: '',
  nombre: '',
  nivel_educativo: ['primaria'],
  direccion: '',
  ugel_id: 0,
  distrito_id: null,
  is_active: true,
})

const form = ref<FormType>(emptyForm())

function toggleNivel(nivel: string) {
  const idx = form.value.nivel_educativo.indexOf(nivel)
  if (idx >= 0) {
    if (form.value.nivel_educativo.length > 1) {
      form.value.nivel_educativo.splice(idx, 1)
    }
  } else {
    form.value.nivel_educativo.push(nivel)
  }
}

const filtradas = computed(() =>
  searchQuery.value
    ? instituciones.value.filter(ie =>
        ie.nombre.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
        ie.codigo_modular.includes(searchQuery.value)
      )
    : instituciones.value
)

async function load() {
  loading.value = true
  try {
    const [ies, us] = await Promise.all([
      organizacionService.getInstituciones(),
      organizacionService.getUgeles(),
    ])
    instituciones.value = ies
    ugeles.value = us
  } catch (e) {
    console.error('Error cargando instituciones:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', onResize)
  load()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})

function openCreate() {
  editingId.value = null
  form.value = emptyForm()
  form.value.ugel_id = ugeles.value[0]?.id ?? 0
  serverError.value = ''
  showModal.value = true
}

async function openEdit(ie: InstitucionEducativa) {
  editingId.value = ie.id
  form.value = {
    codigo_modular: ie.codigo_modular,
    nombre: ie.nombre,
    nivel_educativo: Array.isArray(ie.nivel_educativo) ? [...ie.nivel_educativo] : [ie.nivel_educativo],
    direccion: ie.direccion ?? '',
    ugel_id: ie.ugel_id,
    distrito_id: ie.distrito_id,
    is_active: ie.is_active,
  }
  serverError.value = ''
  showModal.value = true
}

async function guardar() {
  if (!form.value.codigo_modular.trim() || !form.value.nombre.trim() || !form.value.ugel_id) {
    serverError.value = 'Código modular, nombre y UGEL son requeridos'
    return
  }
  if (form.value.nivel_educativo.length === 0) {
    serverError.value = 'Selecciona al menos un nivel educativo'
    return
  }
  serverError.value = ''
  saving.value = true
  try {
    if (editingId.value) {
      const updated = await organizacionService.updateInstitucion(editingId.value, form.value)
      const idx = instituciones.value.findIndex(i => i.id === editingId.value)
      if (idx !== -1) instituciones.value[idx] = updated
    } else {
      const nuevo = await organizacionService.createInstitucion(form.value)
      instituciones.value.unshift(nuevo)
    }
    showModal.value = false
  } catch (e: any) {
    serverError.value = e.response?.data?.detail ?? 'Error al guardar'
  } finally {
    saving.value = false
  }
}

async function eliminar(ie: InstitucionEducativa) {
  const confirm = await Swal.fire({
    title: '¿Eliminar institución?',
    text: `La IE "${ie.nombre}" será eliminada permanentemente.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#94a3b8',
    confirmButtonText: 'Eliminar',
    cancelButtonText: 'Cancelar',
    customClass: {
      popup: 'rounded-2xl',
      confirmButton: 'rounded-xl font-bold px-6 py-3',
      cancelButton: 'rounded-xl font-bold px-6 py-3'
    }
  })
  if (!confirm.isConfirmed) return
  try {
    await organizacionService.deleteInstitucion(ie.id)
    instituciones.value = instituciones.value.filter(i => i.id !== ie.id)
    Swal.fire({
      title: 'Eliminado',
      text: 'La institución fue eliminada.',
      icon: 'success',
      timer: 1500,
      showConfirmButton: false,
      customClass: { popup: 'rounded-2xl' }
    })
  } catch (e: any) {
    Swal.fire('Error', e.response?.data?.detail ?? 'No se pudo eliminar', 'error')
  }
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 sm:p-8 font-sans relative flex flex-col overflow-x-hidden">
    <EduBackground variant="teal" />
    
    <div class="max-w-7xl mx-auto w-full relative z-10 flex-1 flex flex-col">
      <Header title="Gestión" subtitle="Instituciones Educativas" :is-dark="isDark"
        gradient-class="from-indigo-600 via-indigo-500 to-teal-500 shadow-indigo-500/20"
        class="rounded-2xl mb-8 sticky top-0" @toggle-theme="toggleTheme">
        <template #actions-before>
          <button @click="router.push('/')"
            class="p-2.5 rounded-xl bg-slate-100 dark:bg-white/20 text-slate-600 dark:text-white border border-slate-200 dark:border-white/30 hover:bg-slate-200 dark:hover:bg-white/30 transition-all duration-300"
            title="Inicio">
            <Home class="w-5 h-5" />
          </button>
        </template>
      </Header>

      <!-- Main Action Bar -->
      <div class="flex flex-col lg:flex-row items-center justify-between gap-4 mb-8 bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm animate-in fade-in slide-in-from-top-2 duration-500">
        <div class="relative w-full lg:w-96">
          <Search class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
          <input v-model="searchQuery" type="text" placeholder="Buscar por nombre o código..."
            class="w-full pl-12 pr-4 py-2.5 bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all" />
        </div>
        
        <button @click="openCreate"
          class="w-full lg:w-auto flex items-center justify-center gap-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-black px-8 py-4 rounded-2xl shadow-xl hover:-translate-y-1 transition-all active:scale-95 text-xs uppercase tracking-widest">
          <Plus class="w-5 h-5" />
          <span>Nueva Institución</span>
        </button>
      </div>

      <div v-if="loading" class="flex-1 flex flex-col items-center justify-center py-20">
        <Loader2 class="w-12 h-12 animate-spin text-indigo-500 mb-4" />
        <p class="text-xs font-black text-slate-400 uppercase tracking-[0.2em]">Cargando Instituciones...</p>
      </div>

      <div v-else class="flex-1 flex flex-col">
        <!-- Desktop Table View -->
        <div v-if="isDesktop" class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden flex flex-col">
          <div class="overflow-x-auto custom-scrollbar">
            <table class="w-full text-left border-collapse text-sm">
              <thead>
                <tr class="bg-slate-50 dark:bg-slate-900 border-b-2 border-slate-100 dark:border-slate-700">
                  <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Cód. Modular</th>
                  <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Institución</th>
                  <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Niveles</th>
                  <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">UGEL</th>
                  <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest text-center">Estado</th>
                  <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest text-right"></th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                <tr v-for="ie in filtradas" :key="ie.id" class="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors group">
                  <td class="p-5 font-mono font-black text-indigo-600 dark:text-indigo-400">{{ ie.codigo_modular }}</td>
                  <td class="p-5">
                    <div class="font-black text-slate-800 dark:text-white text-base tracking-tight">{{ ie.nombre }}</div>
                    <div v-if="ie.direccion" class="flex items-center gap-1 mt-1 text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                      <MapPin class="w-3 h-3" /> {{ ie.direccion }}
                    </div>
                  </td>
                  <td class="p-5">
                    <div class="flex flex-wrap gap-1.5">
                      <span v-for="niv in (Array.isArray(ie.nivel_educativo) ? ie.nivel_educativo : [ie.nivel_educativo])" :key="niv"
                        :class="['px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border shadow-sm', nivelColors[niv] || 'bg-slate-100 text-slate-600']">
                        {{ nivelLabel[niv] || niv }}
                      </span>
                    </div>
                  </td>
                  <td class="p-5">
                    <span class="inline-flex items-center gap-2 px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-[10px] font-black uppercase tracking-widest text-slate-500 dark:text-slate-300">
                      <Building2 class="w-3 h-3" />
                      {{ ie.ugel_nombre || 'S/N' }}
                    </span>
                  </td>
                  <td class="p-5 text-center">
                    <div :class="ie.is_active ? 'text-emerald-500 bg-emerald-50 dark:bg-emerald-900/20' : 'text-slate-400 bg-slate-50'"
                         class="inline-flex items-center justify-center w-24 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border-2 border-current border-opacity-10">
                      {{ ie.is_active ? 'Activa' : 'Inactiva' }}
                    </div>
                  </td>
                  <td class="p-5 text-right">
                    <div class="flex items-center justify-end gap-1 sm:opacity-0 group-hover:opacity-100 transition-all transform group-hover:translate-x-0 translate-x-2">
                      <button @click="openEdit(ie)" class="p-3 rounded-2xl text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-all"><Edit2 class="w-5 h-5" /></button>
                      <button @click="eliminar(ie)" class="p-3 rounded-2xl text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 transition-all"><Trash2 class="w-5 h-5" /></button>
                    </div>
                  </td>
                </tr>
                <tr v-if="filtradas.length === 0">
                  <td colspan="6" class="p-20 text-center">
                    <div class="flex flex-col items-center">
                      <Building2 class="w-16 h-16 text-slate-200 dark:text-slate-700 mb-4" />
                      <p class="text-sm font-black text-slate-400 uppercase tracking-widest">No se encontraron instituciones</p>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Mobile Card View -->
        <div v-else class="space-y-4 pb-20">
          <div v-for="ie in filtradas" :key="ie.id" 
               class="bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-500">
            <div class="flex justify-between items-start mb-4">
              <div class="space-y-1">
                <div class="text-[9px] font-mono font-black text-indigo-500 uppercase tracking-widest">Modular: {{ ie.codigo_modular }}</div>
                <h3 class="font-black text-slate-800 dark:text-white tracking-tight text-xl leading-tight">{{ ie.nombre }}</h3>
              </div>
              <div class="flex gap-2">
                <button @click="openEdit(ie)" class="p-3 bg-slate-50 dark:bg-slate-700 rounded-2xl text-slate-400 transition-all active:scale-95"><Edit2 class="w-5 h-5" /></button>
                <button @click="eliminar(ie)" class="p-3 bg-red-50 dark:bg-red-900/20 rounded-2xl text-red-400 transition-all active:scale-95"><Trash2 class="w-5 h-5" /></button>
              </div>
            </div>

            <div class="flex flex-wrap gap-1.5 mb-5">
              <span v-for="niv in (Array.isArray(ie.nivel_educativo) ? ie.nivel_educativo : [ie.nivel_educativo])" :key="niv"
                :class="['px-3 py-1 rounded-lg text-[9px] font-black uppercase tracking-widest border shadow-sm', nivelColors[niv] || 'bg-slate-100 text-slate-600']">
                {{ nivelLabel[niv] || niv }}
              </span>
            </div>

            <div class="pt-5 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between">
              <div class="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                <Building2 class="w-3.5 h-3.5" />
                {{ ie.ugel_nombre || 'SIN UGEL' }}
              </div>
              <span :class="ie.is_active ? 'text-emerald-500' : 'text-slate-400'" class="text-[10px] font-black uppercase tracking-widest">
                {{ ie.is_active ? 'Activa' : 'Inactiva' }}
              </span>
            </div>
          </div>
          <div v-if="filtradas.length === 0" class="py-20 text-center">
             <Building2 class="w-16 h-16 text-slate-200 dark:text-slate-700 mx-auto mb-4" />
             <p class="text-xs font-black text-slate-400 uppercase tracking-widest">Sin instituciones</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Premium Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center sm:items-center justify-center items-end bg-slate-900/60 backdrop-blur-sm" @click.self="showModal = false">
          <div class="bg-white dark:bg-slate-800 rounded-t-2xl sm:rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden relative">
            <!-- Mobile handle -->
            <div class="sm:hidden flex justify-center pt-4 pb-1" @click="showModal = false"><div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-slate-700"></div></div>
            
            <div class="flex items-center justify-between p-8 border-b border-slate-100 dark:border-slate-700">
              <div class="flex items-center gap-5">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-teal-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
                  <Building2 class="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 class="text-xl font-black text-slate-800 dark:text-white tracking-tight leading-tight">
                    {{ editingId ? 'Editar Institución' : 'Nueva Institución' }}
                  </h2>
                  <p class="text-[10px] text-slate-400 font-black uppercase tracking-widest mt-0.5">Sistemas DRE Huánuco</p>
                </div>
              </div>
              <button @click="showModal = false" class="p-3 rounded-2xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all"><X class="w-6 h-6" /></button>
            </div>

            <div class="p-8 space-y-6 max-h-[70vh] overflow-y-auto custom-scrollbar">
              <div v-if="serverError" class="flex items-center gap-3 bg-red-50 text-red-600 text-xs font-bold p-4 rounded-2xl border-2 border-red-100 animate-shake">
                <AlertCircle class="w-5 h-5 shrink-0" /> {{ serverError }}
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div class="space-y-2">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Código Modular</label>
                  <input v-model="form.codigo_modular" type="text" placeholder="7 dígitos" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all" />
                </div>
                <div class="space-y-2">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre IE</label>
                  <input v-model="form.nombre" type="text" placeholder="Nombre completo" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all" />
                </div>
              </div>

              <div class="space-y-3">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Niveles Educativos</label>
                <div class="flex gap-2 flex-wrap">
                  <button v-for="n in nivelOptions" :key="n.value" @click="toggleNivel(n.value)"
                    :class="[form.nivel_educativo.includes(n.value) ? 'bg-indigo-600 text-white border-indigo-600 shadow-lg shadow-indigo-500/20' : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 text-slate-500']"
                    class="px-5 py-3 rounded-2xl border-2 text-[10px] font-black uppercase tracking-widest transition-all active:scale-95">
                    {{ n.label }}
                  </button>
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">UGEL</label>
                <div class="relative">
                  <select v-model="form.ugel_id" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all appearance-none cursor-pointer">
                    <option :value="null" class="text-slate-400">— Seleccionar UGEL —</option>
                    <option v-for="u in ugeles" :key="u.id" :value="u.id">{{ u.nombre }}</option>
                  </select>
                  <ChevronDown class="absolute right-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                </div>
              </div>

              <div class="space-y-2">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Dirección</label>
                <input v-model="form.direccion" type="text" placeholder="Dirección física" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all" />
              </div>

              <button @click="form.is_active = !form.is_active" class="flex items-center gap-4 p-2 w-fit">
                <div :class="form.is_active ? 'bg-emerald-500 border-emerald-500' : 'bg-slate-200 border-slate-200 dark:bg-slate-700 dark:border-slate-700'"
                     class="w-12 h-6 rounded-full border-2 transition-all relative">
                  <div :class="form.is_active ? 'translate-x-6' : 'translate-x-0'"
                       class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-all shadow-sm"></div>
                </div>
                <span class="text-xs font-black text-slate-600 dark:text-slate-300 uppercase tracking-widest">Institución Activa</span>
              </button>
            </div>

            <div class="p-8 bg-slate-50 dark:bg-slate-900/50 flex flex-col sm:flex-row gap-4">
              <button @click="showModal = false" class="flex-1 px-8 py-4 text-xs font-black uppercase tracking-widest text-slate-500 bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 transition-all hover:bg-slate-50">Cancelar</button>
              <button @click="guardar" :disabled="saving" class="flex-1 flex items-center justify-center gap-3 py-4 bg-gradient-to-r from-indigo-600 to-teal-600 text-white font-black text-xs rounded-2xl shadow-xl shadow-indigo-500/20 transition-all transform active:scale-95 disabled:opacity-70">
                <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
                <span class="uppercase tracking-widest">{{ saving ? 'Guardando...' : 'Guardar Cambios' }}</span>
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

.custom-scrollbar::-webkit-scrollbar { width: 4px; height: 4px; }
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 10px; }

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-4px); }
  75% { transform: translateX(4px); }
}
.animate-shake { animation: shake 0.2s ease-in-out 0s 2; }
</style>
