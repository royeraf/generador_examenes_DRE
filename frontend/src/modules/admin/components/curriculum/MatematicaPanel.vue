<script setup lang="ts">
import { Plus, Edit, Trash2, Save, X, Target, Layers, BookOpen } from 'lucide-vue-next'
import ComboBox from '../../../../shared/components/ComboBox.vue'
import { useMatematica } from '../../composables/useMatematica'
import type { CompetenciaMatematica, CapacidadMatConCompetencia, DesempenoMatCompleto } from '../../../../shared/types/matematica'

const {
  activeTab, loading, saving,
  competencias, desempenos,
  selectedGradoId, selectedCompetenciaId, filterCapCompetenciaId,
  gradoOptions, competenciaOptions, competenciaOptionsConTodas,
  capacidadesFiltradas, capacidadesPorCompetencia, capacidadModalOptions,
  showModal, isEditing, editItem,
  openModal, saveItem, deleteItem,
} = useMatematica()

const TABS = [
  { id: 'competencias' as const, label: 'Competencias', icon: Target },
  { id: 'capacidades' as const, label: 'Capacidades', icon: Layers },
  { id: 'desempenos' as const, label: 'Desempeños', icon: BookOpen },
]
</script>

<template>
  <div class="flex flex-col h-full min-h-0">

    <!-- Tabs -->
    <div class="flex gap-1 p-1 bg-slate-100 dark:bg-slate-800 rounded-xl mb-4 shrink-0 overflow-x-auto custom-scrollbar">
      <button
        v-for="tab in TABS" :key="tab.id"
        @click="activeTab = tab.id"
        class="flex items-center gap-1.5 px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all flex-1 sm:flex-initial justify-center whitespace-nowrap"
        :class="activeTab === tab.id
          ? 'bg-white dark:bg-slate-700 text-violet-600 dark:text-violet-400 shadow-sm'
          : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
      >
        <component :is="tab.icon" class="w-3.5 h-3.5" />
        {{ tab.label }}
      </button>
    </div>

    <!-- Toolbar -->
    <div class="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-4 shrink-0">
      <div class="flex flex-wrap items-center gap-3">
        <!-- Desempeños filters -->
        <template v-if="activeTab === 'desempenos'">
          <div class="flex items-center gap-2 flex-1 sm:flex-initial">
            <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Grado:</span>
            <div class="flex-1 w-28 sm:w-40 text-xs sm:text-sm">
              <ComboBox v-model="selectedGradoId" :options="gradoOptions" placeholder="Grado..." />
            </div>
          </div>
          <div class="flex items-center gap-2 flex-1 sm:flex-initial">
            <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Competencia:</span>
            <div class="flex-1 w-32 sm:w-56 text-xs sm:text-sm">
              <ComboBox v-model="selectedCompetenciaId" :options="competenciaOptions" placeholder="Competencia..." />
            </div>
          </div>
        </template>
        <!-- Capacidades filter -->
        <template v-else-if="activeTab === 'capacidades'">
          <div class="flex items-center gap-2 w-full sm:w-auto">
            <span class="text-[10px] font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wide">Competencia:</span>
            <div class="flex-1 sm:w-56 text-xs sm:text-sm">
              <ComboBox v-model="filterCapCompetenciaId" :options="competenciaOptionsConTodas" placeholder="Todas..." />
            </div>
          </div>
        </template>
      </div>

      <button
        @click="openModal()"
        class="w-full sm:w-auto flex items-center justify-center gap-1.5 px-4 py-2 bg-violet-600 hover:bg-violet-700 text-white rounded-lg text-sm font-bold transition-colors shadow-lg shadow-violet-500/20"
      >
        <Plus class="w-4 h-4" />
        Nuevo {{ activeTab === 'competencias' ? 'competencia' : activeTab === 'capacidades' ? 'capacidad' : 'desempeño' }}
      </button>
    </div>

    <!-- Table -->
    <div class="flex-1 min-h-0 overflow-y-auto bg-white dark:bg-slate-800 rounded-xl border border-slate-300 dark:border-slate-700 overflow-x-auto custom-scrollbar">
      <table class="w-full text-sm min-w-[600px] sm:min-w-0">
        <thead class="sticky top-0 bg-slate-50 dark:bg-slate-900/80 backdrop-blur-sm">
          <tr class="border-b border-slate-300 dark:border-slate-700">
            <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">ID</th>

            <template v-if="activeTab === 'competencias'">
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Cód.</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Nombre</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Descripción</th>
            </template>
            <template v-else-if="activeTab === 'capacidades'">
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Orden</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Nombre</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Competencia</th>
            </template>
            <template v-else>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Código</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Descripción</th>
              <th class="px-4 py-3 text-left text-xs font-bold text-slate-500 uppercase tracking-wide">Capacidad</th>
            </template>

            <th class="px-4 py-3 text-right text-xs font-bold text-slate-500 uppercase tracking-wide">Acciones</th>
          </tr>
        </thead>

        <tbody class="divide-y divide-slate-100 dark:divide-slate-700/50">
          <!-- Skeleton -->
          <template v-if="loading">
            <tr v-for="n in 6" :key="n" class="animate-pulse">
              <td class="px-4 py-3"><div class="h-3 w-8 bg-slate-200 dark:bg-slate-700 rounded" /></td>
              <td class="px-4 py-3"><div class="h-3 w-12 bg-slate-200 dark:bg-slate-700 rounded" /></td>
              <td class="px-4 py-3"><div class="h-3 w-40 bg-slate-200 dark:bg-slate-700 rounded" /></td>
              <td class="px-4 py-3"><div class="h-3 w-24 bg-slate-200 dark:bg-slate-700 rounded" /></td>
              <td class="px-4 py-3"><div class="h-6 w-16 bg-slate-200 dark:bg-slate-700 rounded ml-auto" /></td>
            </tr>
          </template>

          <!-- Competencias -->
          <template v-else-if="activeTab === 'competencias' && competencias.length > 0">
            <tr v-for="item in competencias" :key="item.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors group">
              <td class="px-4 py-3 text-xs text-slate-400 font-mono">#{{ item.id }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400 rounded-full text-xs font-bold">{{ (item as CompetenciaMatematica).codigo }}</span>
              </td>
              <td class="px-4 py-3 font-medium text-slate-800 dark:text-slate-100">{{ item.nombre }}</td>
              <td class="px-4 py-3 text-slate-500 text-xs max-w-xs">
                <span class="line-clamp-2">{{ (item as CompetenciaMatematica).descripcion?.slice(0, 100) }}...</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex justify-end gap-1 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click="openModal(item)" class="p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 text-slate-400 hover:text-blue-600 transition-colors">
                    <Edit class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </template>

          <!-- Capacidades -->
          <template v-else-if="activeTab === 'capacidades' && capacidadesFiltradas.length > 0">
            <tr v-for="item in capacidadesFiltradas" :key="item.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors group">
              <td class="px-4 py-3 text-xs text-slate-400 font-mono">#{{ item.id }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 rounded-full text-xs font-bold">{{ (item as CapacidadMatConCompetencia).orden }}</span>
              </td>
              <td class="px-4 py-3 font-medium text-slate-800 dark:text-slate-100">{{ item.nombre }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded text-xs text-slate-500">{{ (item as CapacidadMatConCompetencia).competencia_nombre }}</span>
              </td>
              <td class="px-4 py-3">
                <div class="flex justify-end gap-1 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click="openModal(item)" class="p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 text-slate-400 hover:text-blue-600 transition-colors">
                    <Edit class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </template>

          <!-- Desempeños -->
          <template v-else-if="activeTab === 'desempenos' && desempenos.length > 0">
            <tr v-for="item in desempenos" :key="item.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/40 transition-colors group">
              <td class="px-4 py-3 text-xs text-slate-400 font-mono">#{{ item.id }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400 rounded font-mono text-xs font-bold">{{ (item as DesempenoMatCompleto).codigo }}</span>
              </td>
              <td class="px-4 py-3 text-slate-600 dark:text-slate-300 max-w-sm">
                <span class="line-clamp-2">{{ (item as DesempenoMatCompleto).descripcion }}</span>
              </td>
              <td class="px-4 py-3 text-xs">
                <div class="flex flex-col gap-0.5">
                  <span class="text-violet-600 dark:text-violet-400 font-medium">Cap. {{ (item as DesempenoMatCompleto).capacidad_orden }}</span>
                  <span class="text-slate-400 line-clamp-1">{{ (item as DesempenoMatCompleto).capacidad_nombre?.slice(0, 30) }}...</span>
                </div>
              </td>
              <td class="px-4 py-3">
                <div class="flex justify-end gap-1 sm:opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click="openModal(item)" class="p-1.5 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/20 text-slate-400 hover:text-blue-600 transition-colors">
                    <Edit class="w-3.5 h-3.5" />
                  </button>
                  <button @click="deleteItem(item.id)" class="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-slate-400 hover:text-red-600 transition-colors">
                    <Trash2 class="w-3.5 h-3.5" />
                  </button>
                </div>
              </td>
            </tr>
          </template>

          <tr v-else-if="!loading">
            <td colspan="10" class="px-4 py-12 text-center text-sm text-slate-400">
              No hay registros para mostrar
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Modal -->
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="showModal" class="fixed inset-0 z-[200] flex items-end sm:items-center justify-center sm:p-4 bg-slate-900/60 backdrop-blur-sm" @click.self="showModal = false">
        <div class="absolute inset-0" @click="showModal = false" />
        <div class="relative z-10 w-full sm:max-w-2xl bg-white dark:bg-slate-900 rounded-t-[2.5rem] sm:rounded-[2.5rem] shadow-2xl overflow-hidden flex flex-col max-h-[92dvh] sm:max-h-[85vh] transition-transform duration-500 ease-out translate-y-0">
          
          <!-- Drag handle (mobile) -->
          <div class="sm:hidden flex justify-center pt-4 pb-2 shrink-0 cursor-pointer" @click="showModal = false">
            <div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-slate-800"></div>
          </div>

          <div class="flex items-center justify-between px-8 py-6 border-b border-slate-300 dark:border-slate-800 shrink-0 bg-slate-50/50 dark:bg-slate-800/30">
            <div class="flex items-center gap-4">
              <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-violet-500/20">
                <component :is="TABS.find(t => t.id === activeTab)?.icon || BookOpen" class="w-6 h-6" />
              </div>
              <div>
                <h3 class="text-xl font-bold text-slate-800 dark:text-white leading-tight">
                  {{ isEditing ? 'Editar' : 'Nuevo' }}
                  {{ activeTab === 'competencias' ? 'Competencia' : activeTab === 'capacidades' ? 'Capacidad' : 'Desempeño' }}
                </h3>
                <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mt-0.5">Gestión Curricular (MAT)</p>
              </div>
            </div>
            <button @click="showModal = false" class="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all">
              <X class="w-5 h-5" />
            </button>
          </div>

          <div class="p-8 space-y-6 overflow-y-auto custom-scrollbar">

            <!-- Competencia fields (read-only in some cases) -->
            <template v-if="activeTab === 'competencias'">
              <div class="space-y-4">
                <div class="grid grid-cols-4 gap-4">
                  <div>
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Código</label>
                    <input v-model.number="editItem.codigo" type="number" :disabled="isEditing" class="curriculum-field h-14 bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-800 rounded-2xl px-5 text-sm text-center font-mono" />
                  </div>
                  <div class="col-span-3">
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Nombre</label>
                    <input v-model="editItem.nombre" type="text" :disabled="isEditing" class="curriculum-field h-14 bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-800 rounded-2xl px-5 text-sm" />
                  </div>
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Descripción</label>
                  <textarea v-model="editItem.descripcion" rows="5" :disabled="isEditing" class="curriculum-field bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-800 rounded-2xl p-5 text-sm resize-none leading-relaxed" />
                </div>
              </div>
            </template>

            <!-- Capacidad fields -->
            <template v-else-if="activeTab === 'capacidades'">
              <div class="space-y-4">
                <div class="grid grid-cols-4 gap-4">
                  <div>
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Orden</label>
                    <input v-model.number="editItem.orden" type="number" :disabled="isEditing" class="curriculum-field h-14 bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-800 rounded-2xl px-5 text-sm text-center font-mono" />
                  </div>
                  <div class="col-span-3">
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Competencia</label>
                    <div v-if="isEditing" class="flex items-center h-14 bg-slate-100 dark:bg-slate-800 rounded-2xl px-5 text-xs text-slate-500 font-bold">
                      {{ competencias.find(c => c.id === editItem.competencia_id)?.nombre ?? '-' }}
                    </div>
                    <ComboBox v-else v-model="editItem.competencia_id" :options="competenciaOptions" placeholder="Seleccionar..." />
                  </div>
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Nombre</label>
                  <input v-model="editItem.nombre" type="text" :disabled="isEditing" placeholder="Ej: Usa estrategias y procedimientos de estimación" class="curriculum-field h-14 bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-800 rounded-2xl px-5 text-sm" />
                </div>
              </div>
            </template>

            <!-- Desempeño fields -->
            <template v-else>
              <div class="space-y-4">
                <div class="grid grid-cols-3 gap-4">
                  <div>
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Código</label>
                    <input v-model="editItem.codigo" type="text" placeholder="01" class="curriculum-field h-14 bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-800 rounded-2xl px-5 text-sm text-center font-mono" />
                  </div>
                  <div class="col-span-2">
                    <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Capacidad</label>
                    <div v-if="isEditing" class="flex items-center h-14 bg-slate-100 dark:bg-slate-800 rounded-2xl px-5 text-xs text-slate-500 font-bold truncate">
                      {{ capacidadesPorCompetencia.find(c => c.id === editItem.capacidad_id)?.nombre ?? '-' }}
                    </div>
                    <ComboBox v-else v-model="editItem.capacidad_id" :options="capacidadModalOptions" placeholder="Seleccionar..." />
                  </div>
                </div>
                <div>
                  <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1.5 ml-1">Descripción del Desempeño</label>
                  <textarea v-model="editItem.descripcion" rows="6" placeholder="Escribe el desempeño aquí..." class="curriculum-field bg-slate-50 dark:bg-slate-800/50 border-slate-300 dark:border-slate-800 rounded-2xl p-5 text-sm resize-none leading-relaxed" />
                </div>
              </div>
            </template>
          </div>

          <div class="px-8 py-6 border-t border-slate-300 dark:border-slate-800 flex justify-end gap-3 bg-slate-50/50 dark:bg-slate-800/50">
            <button @click="showModal = false" class="px-6 py-3 text-sm font-bold rounded-2xl bg-white dark:bg-slate-800 hover:bg-slate-50 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-300 dark:border-slate-700 transition-all">
              Cancelar
            </button>
            <button
              v-if="activeTab === 'desempenos'"
              @click="saveItem" :disabled="saving"
              class="flex items-center gap-2 px-8 py-3 text-sm font-black rounded-2xl bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white shadow-xl shadow-violet-500/20 transition-all disabled:opacity-50 active:scale-95"
            >
              <Save v-if="!saving" class="w-4 h-4" />
              <div v-else class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
              {{ saving ? 'Guardando...' : 'Guardar Cambios' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active, .modal-leave-active { transition: opacity 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-enter-active .relative, .modal-leave-active .relative { transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1); }
.modal-enter-from, .modal-leave-to { opacity: 0; }
/* Mobile slides from bottom */
.modal-enter-from .relative, .modal-leave-to .relative { transform: translateY(100%); }
/* Desktop scales and fades from center */
@media (min-width: 640px) {
    .modal-enter-from .relative, .modal-leave-to .relative { transform: translateY(0) scale(0.9) translateZ(0); }
}

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
</style>
