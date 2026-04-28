<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { organizacionService, ubigeoService, type UgelCreatePayload } from '../services/api'
import type { Ugel, Provincia } from '../types'
import Header from '../components/Header.vue'
import { Plus, Edit2, Trash2, Home, Loader2, AlertCircle } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import Swal from 'sweetalert2'

const router = useRouter()
const ugeles = ref<Ugel[]>([])
const provincias = ref<Provincia[]>([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const serverError = ref('')

const form = ref<UgelCreatePayload>({ codigo: '', nombre: '', provincia_id: null, is_active: true })

async function load() {
  loading.value = true
  try {
    const [u, p] = await Promise.all([organizacionService.getUgeles(), ubigeoService.getProvincias()])
    ugeles.value = u
    provincias.value = p
  } catch (e) {
    console.error('Error cargando UGELes:', e)
  } finally {
    loading.value = false
  }
}

onMounted(load)

function openCreate() {
  editingId.value = null
  form.value = { codigo: '', nombre: '', provincia_id: null, is_active: true }
  serverError.value = ''
  showModal.value = true
}

function openEdit(ugel: Ugel) {
  editingId.value = ugel.id
  form.value = { codigo: ugel.codigo, nombre: ugel.nombre, provincia_id: ugel.provincia_id ?? null, is_active: ugel.is_active }
  serverError.value = ''
  showModal.value = true
}

async function guardar() {
  if (!form.value.codigo.trim() || !form.value.nombre.trim()) {
    serverError.value = 'Código y nombre son requeridos'
    return
  }
  serverError.value = ''
  saving.value = true
  try {
    if (editingId.value) {
      const updated = await organizacionService.updateUgel(editingId.value, form.value)
      const idx = ugeles.value.findIndex(u => u.id === editingId.value)
      if (idx !== -1) ugeles.value[idx] = updated
    } else {
      const nuevo = await organizacionService.createUgel(form.value)
      ugeles.value.unshift(nuevo)
    }
    showModal.value = false
  } catch (e: any) {
    serverError.value = e.response?.data?.detail ?? 'Error al guardar'
  } finally {
    saving.value = false
  }
}

async function eliminar(ugel: Ugel) {
  const confirm = await Swal.fire({
    title: '¿Eliminar UGEL?',
    text: `La UGEL "${ugel.nombre}" será eliminada permanentemente.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#94a3b8',
    confirmButtonText: 'Eliminar',
    cancelButtonText: 'Cancelar',
  })
  if (!confirm.isConfirmed) return
  try {
    await organizacionService.deleteUgel(ugel.id)
    ugeles.value = ugeles.value.filter(u => u.id !== ugel.id)
  } catch (e: any) {
    Swal.fire('Error', e.response?.data?.detail ?? 'No se pudo eliminar', 'error')
  }
}
</script>

<template>
  <div>
    <Header title="Gestión de UGELes" subtitle="">
      <template #actions-before>
        <button @click="router.push('/')"
          class="p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300"
          title="Inicio">
          <Home class="w-4 h-4" />
        </button>
      </template>
    </Header>

    <main class="max-w-5xl mx-auto px-4 py-8">
      <div class="flex items-center justify-between mb-6">
        <h2 class="text-lg font-bold text-slate-800 dark:text-white">Unidades de Gestión Educativa Local</h2>
        <button @click="openCreate"
          class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all">
          <Plus class="w-4 h-4" /> Nueva UGEL
        </button>
      </div>

      <div v-if="loading" class="flex justify-center py-16">
        <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
      </div>

      <div v-else class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 overflow-hidden shadow-sm">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 dark:bg-slate-700/50 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            <tr>
              <th class="px-4 py-3 text-left">Código</th>
              <th class="px-4 py-3 text-left">Nombre</th>
              <th class="px-4 py-3 text-left">Provincia</th>
              <th class="px-4 py-3 text-center">Estado</th>
              <th class="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr v-for="ugel in ugeles" :key="ugel.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
              <td class="px-4 py-3 font-mono font-semibold text-slate-600 dark:text-slate-300">{{ ugel.codigo }}</td>
              <td class="px-4 py-3 font-medium text-slate-800 dark:text-white">{{ ugel.nombre }}</td>
              <td class="px-4 py-3 text-slate-500 dark:text-slate-400">{{ ugel.provincia_nombre || '—' }}</td>
              <td class="px-4 py-3 text-center">
                <span :class="ugel.is_active
                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                  : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400'"
                  class="inline-flex px-2 py-0.5 rounded-full text-xs font-semibold">
                  {{ ugel.is_active ? 'Activa' : 'Inactiva' }}
                </span>
              </td>
              <td class="px-4 py-3">
                <div class="flex items-center justify-end gap-2">
                  <button @click="openEdit(ugel)" class="text-slate-400 hover:text-indigo-500 transition-colors">
                    <Edit2 class="w-4 h-4" />
                  </button>
                  <button @click="eliminar(ugel)" class="text-slate-400 hover:text-red-500 transition-colors">
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="ugeles.length === 0">
              <td colspan="5" class="px-4 py-8 text-center text-slate-400 dark:text-slate-500">No hay UGELes registradas</td>
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
          <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-md">
            <div class="p-5 border-b border-slate-100 dark:border-slate-700">
              <h2 class="text-base font-bold text-slate-800 dark:text-white">{{ editingId ? 'Editar UGEL' : 'Nueva UGEL' }}</h2>
            </div>
            <div class="p-5 space-y-4">
              <div v-if="serverError" class="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 text-xs p-3 rounded-xl border border-red-100">
                <AlertCircle class="w-3.5 h-3.5 shrink-0 mt-0.5" /> {{ serverError }}
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Código</label>
                  <input v-model="form.codigo" type="text" placeholder="Ej: UGEL01"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
                </div>
                <div>
                  <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Nombre</label>
                  <input v-model="form.nombre" type="text" placeholder="Nombre de la UGEL"
                    class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
                </div>
              </div>
              <div>
                <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Provincia</label>
                <select v-model="form.provincia_id"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50">
                  <option :value="null">— Sin especificar —</option>
                  <option v-for="p in provincias" :key="p.id" :value="p.id">{{ p.nombre }}</option>
                </select>
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

