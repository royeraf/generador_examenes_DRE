<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { organizacionService, ubigeoService, type UgelCreatePayload } from '../../shared/services/api'
import type { Ugel, Provincia } from '../../shared/types'
import Header from '../../shared/components/Header.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import { Plus, Edit2, Trash2, Loader2, AlertCircle, X, Building, MapPin, ChevronDown } from 'lucide-vue-next'
import Swal from 'sweetalert2'

const ugeles = ref<Ugel[]>([])
const provincias = ref<Provincia[]>([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const serverError = ref('')

// Responsive State
const isDesktop = ref(window.innerWidth >= 1024)
const onResize = () => { isDesktop.value = window.innerWidth >= 1024 }

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

onMounted(() => {
  window.addEventListener('resize', onResize)
  load()
})

onUnmounted(() => {
  window.removeEventListener('resize', onResize)
})

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
    customClass: {
      popup: 'rounded-2xl',
      confirmButton: 'rounded-xl font-bold px-6 py-3',
      cancelButton: 'rounded-xl font-bold px-6 py-3'
    }
  })
  if (!confirm.isConfirmed) return
  try {
    await organizacionService.deleteUgel(ugel.id)
    ugeles.value = ugeles.value.filter(u => u.id !== ugel.id)
    Swal.fire({
      title: 'Eliminado',
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
  <div class="min-h-screen bg-surface font-sans relative flex flex-col overflow-x-hidden">
    <EduBackground variant="indigo" />
    <Header title="Gestión" subtitle="UGELes Regionales" :show-home="true" />

    <div class="max-w-6xl mx-auto w-full relative z-10 flex-1 flex flex-col p-4 sm:p-8">

      <!-- Action Bar -->
      <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-8 bg-surface-card p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm animate-in fade-in slide-in-from-top-2 duration-500">
        <h2 class="text-lg font-black text-text tracking-tight uppercase">Unidades Ejecutoras</h2>
        <button @click="openCreate"
          class="w-full sm:w-auto flex items-center justify-center gap-3 bg-slate-900 dark:bg-white text-white dark:text-text-inverse font-black px-8 py-4 rounded-2xl shadow-xl hover:-translate-y-1 transition-all active:scale-95 text-xs uppercase tracking-widest cursor-pointer">
          <Plus class="w-5 h-5" />
          <span>Nueva UGEL</span>
        </button>
      </div>

      <div v-if="loading" class="flex-1 flex flex-col items-center justify-center py-20">
        <Loader2 class="w-12 h-12 animate-spin text-emerald-500 mb-4" />
        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Sincronizando UGELes...</p>
      </div>

      <div v-else class="flex-1 flex flex-col">
        <!-- Desktop Table -->
        <div v-if="isDesktop" class="bg-surface-card rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden">
          <table class="w-full text-left border-collapse text-sm">
            <thead>
              <tr class="bg-surface border-b-2 border-slate-100 dark:border-slate-700">
                <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Código</th>
                <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Nombre</th>
                <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Provincia</th>
                <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest text-center">Estado</th>
                <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest text-right"></th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
              <tr v-for="ugel in ugeles" :key="ugel.id" class="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors group">
                <td class="p-5 font-mono font-black text-emerald-600 dark:text-primary">{{ ugel.codigo }}</td>
                <td class="p-5 font-black text-text text-base">{{ ugel.nombre }}</td>
                <td class="p-5">
                  <span class="inline-flex items-center gap-2 px-3 py-1 bg-surface-input rounded-full text-[10px] font-black uppercase tracking-widest text-slate-500">
                    <MapPin class="w-3 h-3" />
                    {{ ugel.provincia_nombre || 'No asignada' }}
                  </span>
                </td>
                <td class="p-5 text-center">
                   <div :class="ugel.is_active ? 'text-emerald-500 bg-emerald-50 border-emerald-100' : 'text-slate-400 bg-slate-50 border-slate-100'"
                         class="inline-flex items-center justify-center w-24 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border-2">
                      {{ ugel.is_active ? 'Activa' : 'Inactiva' }}
                    </div>
                </td>
                <td class="p-5 text-right">
                   <div class="flex items-center justify-end gap-1 sm:opacity-0 group-hover:opacity-100 transition-all">
                      <button @click="openEdit(ugel)" class="p-3 rounded-2xl text-slate-400 hover:text-emerald-600 hover:bg-emerald-50 transition-all cursor-pointer"><Edit2 class="w-5 h-5" /></button>
                      <button @click="eliminar(ugel)" class="p-3 rounded-2xl text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all cursor-pointer"><Trash2 class="w-5 h-5" /></button>
                    </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Mobile Cards -->
        <div v-else class="space-y-4 pb-20">
          <div v-for="ugel in ugeles" :key="ugel.id" class="bg-surface-card p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm">
            <div class="flex justify-between items-start mb-4">
              <div class="space-y-1">
                <div class="text-[9px] font-mono font-black text-emerald-500 uppercase tracking-widest">{{ ugel.codigo }}</div>
                <h3 class="font-black text-text tracking-tight text-xl leading-tight">{{ ugel.nombre }}</h3>
              </div>
              <div class="flex gap-2">
                <button @click="openEdit(ugel)" class="p-3 bg-surface-input rounded-2xl text-slate-400 active:scale-95 transition-all cursor-pointer"><Edit2 class="w-5 h-5" /></button>
                <button @click="eliminar(ugel)" class="p-3 bg-red-50 dark:bg-red-900/20 rounded-2xl text-red-400 active:scale-95 transition-all cursor-pointer"><Trash2 class="w-5 h-5" /></button>
              </div>
            </div>
            <div class="pt-5 border-t border-slate-100 dark:border-slate-700 flex items-center justify-between">
              <div class="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                <MapPin class="w-3.5 h-3.5" />
                {{ ugel.provincia_nombre || 'SIN PROVINCIA' }}
              </div>
              <span :class="ugel.is_active ? 'text-emerald-500' : 'text-slate-400'" class="text-[10px] font-black uppercase tracking-widest">
                {{ ugel.is_active ? 'Activa' : 'Inactiva' }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Premium Modal -->
    <Teleport to="body">
      <Transition name="modal">
        <div v-if="showModal" class="fixed inset-0 z-50 flex items-center sm:items-center justify-center items-end bg-slate-900/60 backdrop-blur-sm cursor-pointer" @click.self="showModal = false">
          <div class="bg-surface-card rounded-t-2xl sm:rounded-2xl shadow-2xl w-full max-w-md overflow-hidden relative">
            <div class="sm:hidden flex justify-center pt-4 pb-1 cursor-pointer" @click="showModal = false"><div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-surface-input"></div></div>
            <div class="flex items-center justify-between p-8 border-b border-slate-100 dark:border-slate-700">
              <div class="flex items-center gap-5">
                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-emerald-700 flex items-center justify-center shadow-lg shadow-emerald-500/20">
                  <Building class="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 class="text-xl font-black text-text tracking-tight leading-tight">
                    {{ editingId ? 'Editar UGEL' : 'Nueva UGEL' }}
                  </h2>
                  <p class="text-[10px] text-slate-400 font-black uppercase tracking-widest mt-0.5">Sistemas DRE Huánuco</p>
                </div>
              </div>
              <button @click="showModal = false" class="p-3 rounded-2xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all cursor-pointer"><X class="w-6 h-6" /></button>
            </div>
            
            <div class="p-8 space-y-6">
              <div v-if="serverError" class="flex items-center gap-3 bg-red-50 text-red-600 text-xs font-bold p-4 rounded-2xl border-2 border-red-100 animate-shake">
                <AlertCircle class="w-5 h-5 shrink-0" /> {{ serverError }}
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Código</label>
                  <input v-model="form.codigo" type="text" placeholder="Ej: 210001" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all" />
                </div>
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre</label>
                  <input v-model="form.nombre" type="text" placeholder="Ej: UGEL Huánuco" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all" />
                </div>
              </div>
              <div class="space-y-1.5">
                <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Provincia</label>
                <div class="relative">
                  <select v-model="form.provincia_id" class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all appearance-none cursor-pointer">
                    <option :value="null" class="text-slate-400">— Seleccionar Provincia —</option>
                    <option v-for="p in provincias" :key="p.id" :value="p.id">{{ p.nombre }}</option>
                  </select>
                  <ChevronDown class="absolute right-5 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
                </div>
              </div>
              <button @click="form.is_active = !form.is_active" class="flex items-center gap-4 p-1 cursor-pointer">
                <div :class="form.is_active ? 'bg-emerald-500 border-emerald-500' : 'bg-slate-200 border-slate-200 dark:bg-surface-input dark:border-slate-700'"
                     class="w-12 h-6 rounded-full border-2 transition-all relative">
                  <div :class="form.is_active ? 'translate-x-6' : 'translate-x-0'"
                       class="absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full transition-all shadow-sm"></div>
                </div>
                <span class="text-xs font-black text-slate-600 dark:text-text-muted uppercase tracking-widest">UGEL Activa</span>
              </button>
            </div>

            <div class="p-8 bg-surface/50 flex flex-col sm:flex-row gap-4">
              <button @click="showModal = false" class="flex-1 px-8 py-4 text-xs font-black uppercase tracking-widest text-slate-500 bg-surface-card rounded-2xl border-2 border-slate-200 dark:border-slate-700 transition-all hover:bg-slate-50 cursor-pointer">Cancelar</button>
              <button @click="guardar" :disabled="saving" class="flex-1 flex items-center justify-center gap-3 py-4 bg-gradient-to-r from-violet-600 to-emerald-800 text-white font-black text-xs rounded-2xl shadow-xl shadow-emerald-500/20 transition-all transform active:scale-95 disabled:opacity-70 cursor-pointer">
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
.custom-scrollbar::-webkit-scrollbar { width: 4px; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 10px; }
</style>
