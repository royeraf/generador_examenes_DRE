<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ShieldAlert, Edit, Save, X } from 'lucide-vue-next'
import { adminService } from '../../../../shared/services/api'
import { showError, showSuccess } from '../../../../shared/utils/swal'
import type { Grado } from '../../../../shared/types'

const grados = ref<Grado[]>([])
const loading = ref(false)
const editingId = ref<number | null>(null)
const editDraft = ref<Partial<Grado>>({})

const NIVEL_BADGE: Record<string, string> = {
  inicial:    'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-primary',
  primaria:   'bg-sky-100 text-sky-700 dark:bg-emerald-900/30 dark:text-primary',
  secundaria: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-primary',
}

async function load() {
  loading.value = true
  try {
    grados.value = await adminService.getGrados()
  } catch (e) {
    showError('Error', 'No se pudieron cargar los grados')
  } finally {
    loading.value = false
  }
}

function startEdit(g: Grado) {
  editingId.value = g.id
  editDraft.value = { ...g }
}

function cancelEdit() {
  editingId.value = null
  editDraft.value = {}
}

async function saveEdit() {
  if (!editingId.value) return
  try {
    await adminService.updateGrado(editingId.value, editDraft.value)
    await load()
    cancelEdit()
    showSuccess('Guardado', 'Grado actualizado')
  } catch (e) {
    showError('Error', 'No se pudo guardar el grado')
  }
}

onMounted(load)
</script>

<template>
  <div class="flex flex-col h-full min-h-0 gap-4">

    <!-- Aviso -->
    <div class="shrink-0 flex items-start gap-2.5 px-4 py-3 rounded-xl bg-amber-50 dark:bg-amber-900/10 border border-amber-200 dark:border-amber-800/50">
      <ShieldAlert class="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
      <p class="text-xs text-amber-700 dark:text-amber-400 leading-relaxed">
        Los grados son datos estructurales compartidos por todas las áreas. Solo edita si hay un error tipográfico; no elimines ni crees grados salvo que sea estrictamente necesario.
      </p>
    </div>

    <!-- Tabla -->
    <div class="flex-1 min-h-0 overflow-y-auto bg-surface-card rounded-xl border border-slate-300 dark:border-slate-700 overflow-x-auto custom-scrollbar">
      <table class="w-full text-sm min-w-[500px] sm:min-w-0">
        <thead class="sticky top-0 bg-surface">
          <tr class="border-b border-slate-300 dark:border-slate-700">
            <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Orden</th>
            <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Nombre</th>
            <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">N°</th>
            <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Nivel</th>
            <th class="px-4 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wide">Editar</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50">

          <template v-if="loading">
            <tr v-for="n in 12" :key="n" class="animate-pulse">
              <td class="px-4 py-3"><div class="h-3 w-6 bg-slate-200 dark:bg-surface-input rounded" /></td>
              <td class="px-4 py-3"><div class="h-3 w-48 bg-slate-200 dark:bg-surface-input rounded" /></td>
              <td class="px-4 py-3"><div class="h-3 w-6 bg-slate-200 dark:bg-surface-input rounded" /></td>
              <td class="px-4 py-3"><div class="h-5 w-16 bg-slate-200 dark:bg-surface-input rounded-full" /></td>
              <td class="px-4 py-3" />
            </tr>
          </template>

          <template v-else>
            <tr v-for="g in grados" :key="g.id"
              class="hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors group">

              <!-- Modo lectura -->
              <template v-if="editingId !== g.id">
                <td class="px-4 py-3 text-xs font-mono text-slate-400">{{ g.orden }}</td>
                <td class="px-4 py-3 font-medium text-slate-800 dark:text-text">{{ g.nombre }}</td>
                <td class="px-4 py-3 text-slate-500">{{ g.numero }}</td>
                <td class="px-4 py-3">
                  <span class="px-2 py-0.5 rounded-full text-xs font-bold capitalize"
                    :class="NIVEL_BADGE[g.nivel] ?? 'bg-slate-100 text-slate-600'">
                    {{ g.nivel }}
                  </span>
                </td>
                <td class="px-4 py-3">
                  <div class="flex justify-end sm:opacity-0 group-hover:opacity-100 transition-opacity">
                    <button @click="startEdit(g)"
                      class="p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-emerald-900/20 text-slate-400 hover:text-blue-600 transition-colors">
                      <Edit class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </template>

              <!-- Modo edición inline -->
              <template v-else>
                <td class="px-4 py-2">
                  <input v-model.number="editDraft.orden" type="number"
                    class="curriculum-field w-16 text-center" />
                </td>
                <td class="px-4 py-2">
                  <input v-model="editDraft.nombre" type="text"
                    class="curriculum-field w-full min-w-[120px]" />
                </td>
                <td class="px-4 py-2">
                  <input v-model.number="editDraft.numero" type="number"
                    class="curriculum-field w-14 text-center" />
                </td>
                <td class="px-4 py-2">
                  <select v-model="editDraft.nivel" class="curriculum-field">
                    <option value="inicial">Inicial</option>
                    <option value="primaria">Primaria</option>
                    <option value="secundaria">Secundaria</option>
                  </select>
                </td>
                <td class="px-4 py-2">
                  <div class="flex justify-end gap-1">
                    <button @click="saveEdit"
                      class="p-1.5 rounded-lg bg-teal-50 dark:bg-emerald-900/20 text-teal-600 hover:bg-teal-100 dark:hover:bg-emerald-900/40 transition-colors">
                      <Save class="w-3.5 h-3.5" />
                    </button>
                    <button @click="cancelEdit"
                      class="p-1.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-400 transition-colors">
                      <X class="w-3.5 h-3.5" />
                    </button>
                  </div>
                </td>
              </template>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <p class="shrink-0 text-center text-xs text-slate-400 dark:text-text-subtle">
      {{ grados.length }} grados registrados · Solo lectura — edición disponible por fila
    </p>
  </div>
</template>
