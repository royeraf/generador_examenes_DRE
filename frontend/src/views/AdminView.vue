<script setup lang="ts">
import { ref, shallowRef, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { adminService } from '../services/api';
import type { Grado, Capacidad, DesempenoItem } from '../types';
import { Trash2, Edit, Plus, Save, X, Home } from 'lucide-vue-next';

const router = useRouter();
import Header from '../components/Header.vue';
import EduBackground from '../components/EduBackground.vue';
import { useTheme } from '../composables/useTheme';
import { showError, showSuccess, showDeleteConfirm } from '../utils/swal';

const { isDark, toggleTheme } = useTheme();

// State
const activeTab = shallowRef<'grados' | 'capacidades' | 'desempenos'>('desempenos');
const loading = shallowRef(false);

const grados = ref<Grado[]>([]);
const capacidades = ref<Capacidad[]>([]);
const desempenos = ref<DesempenoItem[]>([]);

// Filter for Desempeños
const selectedGradoId = shallowRef<number | null>(null);

// Forms State
const isEditing = shallowRef(false);
const editItem = ref<any>(null); // Holds the item being edited or created
const showModal = shallowRef(false);

// Fetch Data
const fetchData = async () => {
    loading.value = true;
    try {
        const [g, c] = await Promise.all([
            adminService.getGrados(),
            adminService.getCapacidades()
        ]);
        grados.value = g;
        capacidades.value = c;

        if (g.length > 0 && !selectedGradoId.value) {
            selectedGradoId.value = g[0] ? g[0].id : null;
        }

        if (selectedGradoId.value) {
            await fetchDesempenos();
        }
    } catch (e) {
        console.error("Error fetching data", e);
    } finally {
        loading.value = false;
    }
};

const fetchDesempenos = async () => {
    if (!selectedGradoId.value) return;
    try {
        const d = await adminService.getDesempenos(selectedGradoId.value);
        desempenos.value = d;
    } catch (e) {
        console.error("Error fetching desenpenos", e);
    }
};

onMounted(() => {
    fetchData();
});

// CRUD Actions
const openModal = (item: any = null) => {
    isEditing.value = !!item;
    if (item) {
        editItem.value = { ...item };
    } else {
        // Defaults for new items
        if (activeTab.value === 'grados') {
            editItem.value = { nombre: '', numero: 1, nivel: 'primaria', orden: 0 };
        } else if (activeTab.value === 'capacidades') {
            editItem.value = { nombre: '', tipo: 'literal', descripcion: '' };
        } else {
            editItem.value = { codigo: '', descripcion: '', grado_id: selectedGradoId.value, capacidad_id: capacidades.value[0]?.id };
        }
    }
    showModal.value = true;
};

const saveItem = async () => {
    try {
        if (activeTab.value === 'grados') {
            if (isEditing.value) await adminService.updateGrado(editItem.value.id, editItem.value);
            else await adminService.createGrado(editItem.value);
            await fetchData();
        } else if (activeTab.value === 'capacidades') {
            if (isEditing.value) await adminService.updateCapacidad(editItem.value.id, editItem.value);
            else await adminService.createCapacidad(editItem.value);
            const c = await adminService.getCapacidades();
            capacidades.value = c;
        } else {
            if (isEditing.value) await adminService.updateDesempeno(editItem.value.id, editItem.value);
            else await adminService.createDesempeno(editItem.value);
            await fetchDesempenos();
        }
        showModal.value = false;
        showSuccess('Guardado', 'El registro se guardó correctamente');
    } catch (e) {
        showError('Error al guardar', String(e));
    }
};

const deleteItem = async (id: number) => {
    const confirmed = await showDeleteConfirm('¿Eliminar este elemento?', 'Esta acción no se puede deshacer');
    if (!confirmed) return;
    try {
        if (activeTab.value === 'grados') {
            await adminService.deleteGrado(id);
            await fetchData();
        } else if (activeTab.value === 'capacidades') {
            await adminService.deleteCapacidad(id);
            const c = await adminService.getCapacidades();
            capacidades.value = c;
        } else {
            await adminService.deleteDesempeno(id);
            await fetchDesempenos();
        }
        showSuccess('Eliminado', 'El registro fue eliminado');
    } catch (e) {
        showError('Error al eliminar', String(e));
    }
};

// Computed/Watchers
</script>

<template>
    <div class="min-h-screen bg-slate-50 dark:bg-slate-900 p-4 sm:p-8 font-sans relative">
        <EduBackground variant="emerald" />
        <div class="max-w-6xl mx-auto relative z-10">
            <Header title="Admin" subtitle="Gestión de Comunicación" :is-dark="isDark"
                gradient-class="from-teal-600 via-teal-500 to-emerald-600 shadow-teal-500/20"
                class="rounded-xl sm:rounded-2xl mb-6 sticky top-0" @toggle-theme="toggleTheme">
              <template #actions-before>
                <button @click="router.push('/')"
                  class="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300"
                  title="Inicio">
                  <Home class="w-5 h-5" />
                </button>
              </template>
            </Header>

            <!-- Tab Navigation -->
            <div class="mb-8 flex justify-center">
                <div
                    class="flex bg-white dark:bg-slate-800 p-1.5 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
                    <button v-for="tab in ['grados', 'capacidades', 'desempenos']" :key="tab"
                        @click="activeTab = tab as any"
                        class="px-5 py-2.5 rounded-lg text-sm font-medium capitalize transition-all"
                        :class="activeTab === tab ? 'bg-teal-500 text-white shadow-md' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'">
                        {{ tab }}
                    </button>
                </div>
            </div>

            <!-- Tool Bar -->
            <div
                class="flex flex-wrap items-center justify-between gap-4 mb-6 bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
                <div v-if="activeTab === 'desempenos'" class="flex items-center gap-2">
                    <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Grado:</span>
                    <select v-model="selectedGradoId" @change="fetchDesempenos"
                        class="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-teal-500">
                        <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
                    </select>
                </div>
                <div v-else></div>

                <button @click="openModal()"
                    class="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-bold flex items-center gap-2 transition-colors shadow-lg shadow-teal-500/20">
                    <Plus class="w-4 h-4" /> Nuevo {{ activeTab.slice(0, -1) }}
                </button>
            </div>

            <!-- Content -->
            <div
                class="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr
                                class="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                                <th class="p-4 text-xs font-bold text-slate-500 uppercase">ID</th>

                                <!-- Dynamic Headers -->
                                <template v-if="activeTab === 'grados'">
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Nombre</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Número</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Nivel</th>
                                </template>

                                <template v-else-if="activeTab === 'capacidades'">
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Nombre</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Tipo</th>
                                </template>

                                <template v-else>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Código</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Descripción</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Capacidad</th>
                                </template>

                                <th class="p-4 text-xs font-bold text-slate-500 uppercase text-right">Acciones</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                            <tr v-for="item in (activeTab === 'grados' ? grados : activeTab === 'capacidades' ? capacidades : desempenos)"
                                :key="item.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                <td class="p-4 text-sm text-slate-400 font-mono">#{{ item.id }}</td>

                                <!-- Dynamic Body -->
                                <template v-if="activeTab === 'grados'">
                                    <td class="p-4 text-sm font-medium text-slate-800 dark:text-slate-200">{{ (item as
                                        Grado).nombre }}</td>
                                    <td class="p-4 text-sm text-slate-600 dark:text-slate-400">{{ (item as Grado).numero
                                        }}</td>
                                    <td class="p-4 text-sm capitalize"><span
                                            class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-bold">{{
                                                (item as Grado).nivel }}</span></td>
                                </template>

                                <template v-else-if="activeTab === 'capacidades'">
                                    <td class="p-4 text-sm font-medium text-slate-800 dark:text-slate-200">{{ (item as
                                        Capacidad).nombre }}</td>
                                    <td class="p-4 text-sm capitalize">
                                        <span
                                            class="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-bold">{{
                                                (item as Capacidad).tipo }}</span>
                                    </td>
                                </template>

                                <template v-else>
                                    <td class="p-4 text-sm font-mono font-bold text-teal-600">{{ (item as
                                        DesempenoItem).codigo }}</td>
                                    <td class="p-4 text-sm text-slate-600 dark:text-slate-300 max-w-md">{{ (item as
                                        DesempenoItem).descripcion }}</td>
                                    <td class="p-4 text-sm text-slate-500">{{ (item as DesempenoItem).capacidad_nombre
                                        || (item as DesempenoItem).capacidad_tipo }}</td>
                                </template>

                                <td class="p-4 text-right space-x-2">
                                    <button @click="openModal(item)"
                                        class="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                                        <Edit class="w-4 h-4" />
                                    </button>
                                    <button @click="deleteItem(item.id)"
                                        class="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                                        <Trash2 class="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                            <tr
                                v-if="!loading && (activeTab === 'grados' ? grados : activeTab === 'capacidades' ? capacidades : desempenos).length === 0">
                                <td colspan="100" class="p-8 text-center text-slate-400">
                                    No hay registros encontrados
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- Modal Form -->
        <div v-if="showModal"
            class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full overflow-hidden border border-slate-200 dark:border-slate-700">
                <div
                    class="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-slate-50 dark:bg-slate-900/50">
                    <h3 class="font-bold text-lg text-slate-800 dark:text-white">
                        {{ isEditing ? 'Editar' : 'Nuevo' }} {{ activeTab.slice(0, -1) }}
                    </h3>
                    <button @click="showModal = false"
                        class="text-slate-400 hover:text-slate-600 dark:hover:text-white">
                        <X class="w-5 h-5" />
                    </button>
                </div>

                <div class="p-6 space-y-4">
                    <!-- Grados Fields -->
                    <template v-if="activeTab === 'grados'">
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Nombre</label>
                            <input v-model="editItem.nombre" type="text"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white">
                        </div>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <label class="block text-xs font-bold text-slate-500 mb-1">Número</label>
                                <input v-model.number="editItem.numero" type="number"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white">
                            </div>
                            <div>
                                <label class="block text-xs font-bold text-slate-500 mb-1">Orden</label>
                                <input v-model.number="editItem.orden" type="number"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white">
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Nivel</label>
                            <select v-model="editItem.nivel"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white">
                                <option value="primaria">Primaria</option>
                                <option value="secundaria">Secundaria</option>
                            </select>
                        </div>
                    </template>

                    <!-- Capacidades Fields -->
                    <template v-if="activeTab === 'capacidades'">
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Nombre</label>
                            <input v-model="editItem.nombre" type="text"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white">
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Tipo</label>
                            <select v-model="editItem.tipo"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white">
                                <option value="literal">Literal</option>
                                <option value="inferencial">Inferencial</option>
                                <option value="critico">Crítico</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Descripción</label>
                            <textarea v-model="editItem.descripcion" rows="3"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white"></textarea>
                        </div>
                    </template>

                    <!-- Desempenos Fields -->
                    <template v-if="activeTab === 'desempenos'">
                        <div class="grid grid-cols-3 gap-4">
                            <div class="col-span-1">
                                <label class="block text-xs font-bold text-slate-500 mb-1">Código</label>
                                <input v-model="editItem.codigo" type="text" placeholder="Ej: 01"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white">
                            </div>
                            <div class="col-span-2">
                                <label class="block text-xs font-bold text-slate-500 mb-1">Capacidad</label>
                                <select v-model="editItem.capacidad_id"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white">
                                    <option v-for="c in capacidades" :key="c.id" :value="c.id">{{ c.nombre }} ({{ c.tipo
                                        }})</option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Descripción</label>
                            <textarea v-model="editItem.descripcion" rows="4"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white"></textarea>
                        </div>
                        <!-- Hidden Grado ID stored in state -->
                    </template>

                </div>

                <div
                    class="px-6 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex justify-end gap-3">
                    <button @click="showModal = false"
                        class="px-4 py-2 text-slate-600 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-700 rounded-lg font-bold text-sm transition-colors">Cancelar</button>
                    <button @click="saveItem"
                        class="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg font-bold text-sm flex items-center gap-2 shadow-lg shadow-teal-500/20 transition-all transform hover:scale-105">
                        <Save class="w-4 h-4" /> Guardar
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
