<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { organizacionService, type IECreatePayload } from '../services/api'
import type { InstitucionEducativa, Ugel } from '../types'
import Header from '../components/Header.vue'
import { Plus, Edit2, Trash2, Home, Loader2, AlertCircle, Search } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import Swal from 'sweetalert2'

const router = useRouter()
const instituciones = ref<InstitucionEducativa[]>([])
const ugeles = ref<Ugel[]>([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const serverError = ref('')
const searchQuery = ref('')

const nivelOptions = [
  { value: 'inicial', label: 'Inicial' },
  { value: 'primaria', label: 'Primaria' },
  { value: 'secundaria', label: 'Secundaria' },
]

const nivelLabel: Record<string, string> = { inicial: 'Inicial', primaria: 'Primaria', secundaria: 'Secundaria' }
const nivelColors: Record<string, string> = {
  inicial: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
  primaria: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
  secundaria: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
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

onMounted(load)

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
  })
  if (!confirm.isConfirmed) return
  try {
    await organizacionService.deleteInstitucion(ie.id)
    instituciones.value = instituciones.value.filter(i => i.id !== ie.id)
  } catch (e: any) {
    Swal.fire('Error', e.response?.data?.detail ?? 'No se pudo eliminar', 'error')
  }
}

</script>

<template>
  <div>
    <Header title="Instituciones Educativas" subtitle="">
    <template #actions-before>
      <button @click="router.push('/')"
        class="p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300"
        title="Inicio">
        <Home class="w-4 h-4" />
      </button>
    </template>
  </Header>

  <main class="max-w-6xl mx-auto px-4 py-8">
    <div class="flex items-center justify-between mb-6 gap-4 flex-wrap">
      <h2 class="text-lg font-bold text-slate-800 dark:text-white">Instituciones Educativas</h2>
      <div class="flex items-center gap-3">
        <div class="relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input v-model="searchQuery" type="text" placeholder="Buscar..."
            class="pl-9 pr-4 py-2 text-sm text-slate-900 dark:text-white bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl outline-none focus:ring-2 focus:ring-teal-500/50 w-48" />
        </div>
        <button @click="openCreate"
          class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all">
          <Plus class="w-4 h-4" /> Nueva IE
        </button>
      </div>
    </div>

    <div v-if="loading" class="flex justify-center py-16">
      <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
    </div>

    <div v-else class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 overflow-hidden shadow-sm">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 dark:bg-slate-700/50 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          <tr>
            <th class="px-4 py-3 text-left">Cód. Modular</th>
            <th class="px-4 py-3 text-left">Nombre</th>
            <th class="px-4 py-3 text-left">Niveles</th>
            <th class="px-4 py-3 text-left">UGEL</th>
            <th class="px-4 py-3 text-center">Estado</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
          <tr v-for="ie in filtradas" :key="ie.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
            <td class="px-4 py-3 font-mono text-xs text-slate-500">{{ ie.codigo_modular }}</td>
            <td class="px-4 py-3 font-medium text-slate-800 dark:text-white">{{ ie.nombre }}</td>
            <td class="px-4 py-3">
              <div class="flex flex-wrap gap-1">
                <span v-for="niv in (Array.isArray(ie.nivel_educativo) ? ie.nivel_educativo : [ie.nivel_educativo])" :key="niv"
                  :class="['px-2 py-0.5 rounded-full text-xs font-semibold', nivelColors[niv] ?? 'bg-slate-100 text-slate-600']">
                  {{ nivelLabel[niv] ?? niv }}
                </span>
              </div>
            </td>
            <td class="px-4 py-3 text-slate-500 dark:text-slate-400">{{ ie.ugel_nombre || `#${ie.ugel_id}` }}</td>
            <td class="px-4 py-3 text-center">
              <span :class="ie.is_active
                ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400'"
                class="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold">
                {{ ie.is_active ? 'Activa' : 'Inactiva' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <div class="flex items-center justify-end gap-2">
                <button @click="openEdit(ie)" class="text-slate-400 hover:text-indigo-500 transition-colors"><Edit2 class="w-4 h-4" /></button>
                <button @click="eliminar(ie)" class="text-slate-400 hover:text-red-500 transition-colors"><Trash2 class="w-4 h-4" /></button>
              </div>
            </td>
          </tr>
          <tr v-if="filtradas.length === 0">
            <td colspan="6" class="px-4 py-8 text-center text-slate-400 dark:text-slate-500">No hay instituciones registradas</td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>

  <!-- Modal -->
  <Teleport to="body">
    <Transition enter-active-class="transition ease-out duration-200" enter-from-class="opacity-0" enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150" leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="showModal = false">
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md max-h-[90vh] overflow-y-auto">
          <div class="p-5 border-b border-slate-100 dark:border-slate-700 sticky top-0 bg-white dark:bg-slate-800">
            <h2 class="text-base font-bold text-slate-800 dark:text-white">{{ editingId ? 'Editar Institución' : 'Nueva Institución' }}</h2>
          </div>
          <div class="p-5 space-y-4">
            <div v-if="serverError" class="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 text-xs p-3 rounded-xl border border-red-100">
              <AlertCircle class="w-3.5 h-3.5 shrink-0 mt-0.5" /> {{ serverError }}
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Código Modular</label>
              <input v-model="form.codigo_modular" type="text" placeholder="Ej: 1234567"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Nombre</label>
              <input v-model="form.nombre" type="text" placeholder="Nombre de la institución"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
            </div>
            <!-- Niveles educativos — multi-selección -->
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-2">
                Nivel(es) Educativo(s)
                <span class="font-normal text-slate-400">(puede seleccionar varios)</span>
              </label>
              <div class="flex gap-2 flex-wrap">
                <label v-for="n in nivelOptions" :key="n.value"
                  :class="['flex items-center gap-2 px-3 py-2 rounded-xl border text-sm font-medium cursor-pointer transition-colors',
                    form.nivel_educativo.includes(n.value)
                      ? (nivelColors[n.value] ?? '') + ' border-current'
                      : 'bg-slate-50 dark:bg-slate-700/50 border-slate-200 dark:border-slate-600 text-slate-500 dark:text-slate-400']">
                  <input type="checkbox" class="sr-only"
                    :checked="form.nivel_educativo.includes(n.value)"
                    @change="toggleNivel(n.value)" />
                  <span :class="['w-3.5 h-3.5 rounded border flex-shrink-0 flex items-center justify-center transition-colors',
                    form.nivel_educativo.includes(n.value) ? 'bg-current border-current' : 'bg-white dark:bg-slate-700 border-slate-300']">
                    <svg v-if="form.nivel_educativo.includes(n.value)" class="w-2 h-2 text-white" viewBox="0 0 10 8" fill="none">
                      <path d="M1 4l3 3 5-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </span>
                  {{ n.label }}
                </label>
              </div>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">UGEL</label>
              <select v-model="form.ugel_id"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50">
                <option v-for="u in ugeles" :key="u.id" :value="u.id">{{ u.nombre }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Dirección <span class="font-normal text-slate-400">(opcional)</span></label>
              <input v-model="form.direccion" type="text"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
            </div>
            <label class="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" v-model="form.is_active" class="rounded" />
              <span class="text-sm text-slate-600 dark:text-slate-300">Activa</span>
            </label>
          </div>
          <div class="flex justify-end gap-2 px-5 py-4 border-t border-slate-100 dark:border-slate-700">
            <button @click="showModal = false" class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">Cancelar</button>
            <button @click="guardar" :disabled="saving"
              class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-70">
              <Loader2 v-if="saving" class="w-3.5 h-3.5 animate-spin" /> Guardar
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
  </div>
</template>
