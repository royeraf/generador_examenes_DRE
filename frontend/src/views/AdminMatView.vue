<script setup lang="ts">
import { ref, shallowRef, onMounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { matematicaService } from '../services/api';
import type {
    CompetenciaMatematica,
    CapacidadMatConCompetencia,
    DesempenoMatCompleto,
    GradoMatematica
} from '../types/matematica';
import { Trash2, Edit, Plus, Save, X, Calculator, Eye, Target, Layers, BookOpen, Home } from 'lucide-vue-next';

const router = useRouter();
import Swal from 'sweetalert2';
import Header from '../components/Header.vue';
import EduBackground from '../components/EduBackground.vue';
import { useTheme } from '../composables/useTheme';

const { isDark, toggleTheme } = useTheme();

// State
const activeTab = shallowRef<'competencias' | 'capacidades' | 'desempenos'>('desempenos');
const loading = shallowRef(false);
const saving = shallowRef(false);

const grados = ref<GradoMatematica[]>([]);
const competencias = ref<CompetenciaMatematica[]>([]);
const capacidades = ref<CapacidadMatConCompetencia[]>([]);
const desempenos = ref<DesempenoMatCompleto[]>([]);

// Filters
const selectedGradoId = shallowRef<number | null>(null);
const selectedCompetenciaId = shallowRef<number | null>(null);

// Forms State
const isEditing = shallowRef(false);
const editItem = ref<any>(null);
const showModal = shallowRef(false);

// Stats
const stats = computed(() => ({
    competencias: competencias.value.length,
    capacidades: capacidades.value.length,
    desempenos: desempenos.value.length,
    grados: grados.value.length
}));

// Fetch Data
const fetchData = async () => {
    loading.value = true;
    try {
        const [g, c, cap] = await Promise.all([
            matematicaService.getGrados(),
            matematicaService.getCompetencias(),
            matematicaService.getCapacidades()
        ]);
        grados.value = g;
        competencias.value = c;
        capacidades.value = cap;

        if (g.length > 0 && !selectedGradoId.value) {
            selectedGradoId.value = g[0]?.id ?? null;
        }
        if (c.length > 0 && !selectedCompetenciaId.value) {
            selectedCompetenciaId.value = c[0]?.id ?? null;
        }

        await fetchDesempenos();
    } catch (e) {
        console.error("Error fetching data", e);
    } finally {
        loading.value = false;
    }
};

const fetchDesempenos = async () => {
    if (!selectedGradoId.value || !selectedCompetenciaId.value) return;
    try {
        const d = await matematicaService.getDesempenosPorGradoYCompetencia(
            selectedGradoId.value,
            selectedCompetenciaId.value
        );
        desempenos.value = d;
    } catch (e) {
        console.error("Error fetching desempeños", e);
    }
};

// Watch filters changes
watch([selectedGradoId, selectedCompetenciaId], () => {
    if (activeTab.value === 'desempenos') {
        fetchDesempenos();
    }
});

onMounted(() => {
    fetchData();
});

// Get capacidades for selected competencia
const capacidadesFiltradas = computed(() => {
    if (!selectedCompetenciaId.value) return capacidades.value;
    return capacidades.value.filter(c => c.competencia_id === selectedCompetenciaId.value);
});

// CRUD Actions
const openModal = (item: any = null) => {
    isEditing.value = !!item;
    if (item) {
        editItem.value = { ...item };
    } else {
        // Defaults for new items
        if (activeTab.value === 'competencias') {
            editItem.value = { codigo: competencias.value.length + 1, nombre: '', descripcion: '' };
        } else if (activeTab.value === 'capacidades') {
            editItem.value = { orden: 1, nombre: '', competencia_id: selectedCompetenciaId.value, descripcion: '' };
        } else {
            editItem.value = {
                codigo: '',
                descripcion: '',
                grado_id: selectedGradoId.value,
                capacidad_id: capacidadesFiltradas.value[0]?.id
            };
        }
    }
    showModal.value = true;
};

const saveItem = async () => {
    if (activeTab.value !== 'desempenos') {
        Swal.fire('Atención', 'Por ahora solo está habilitada la gestión de Desempeños.', 'info');
        showModal.value = false;
        return;
    }

    if (!editItem.value.codigo || !editItem.value.descripcion) {
        Swal.fire('Error', 'Por favor complete todos los campos obligatorios', 'error');
        return;
    }

    saving.value = true;
    try {
        if (isEditing.value) {
            await matematicaService.updateDesempeno(editItem.value.id, {
                codigo: editItem.value.codigo,
                descripcion: editItem.value.descripcion,
                grado_id: editItem.value.grado_id,
                capacidad_id: editItem.value.capacidad_id
            });
            Swal.fire('¡Éxito!', 'Desempeño actualizado correctamente', 'success');
        } else {
            await matematicaService.createDesempeno({
                codigo: editItem.value.codigo,
                descripcion: editItem.value.descripcion,
                grado_id: editItem.value.grado_id,
                capacidad_id: editItem.value.capacidad_id
            });
            Swal.fire('¡Éxito!', 'Desempeño creado correctamente', 'success');
        }
        await fetchDesempenos();
        showModal.value = false;
    } catch (e: any) {
        Swal.fire('Error', "Error al guardar: " + (e.response?.data?.detail || e.message), 'error');
    } finally {
        saving.value = false;
    }
};

const deleteItem = async (id: number) => {
    if (activeTab.value !== 'desempenos') {
        Swal.fire('Atención', 'Por ahora solo está habilitada la gestión de Desempeños.', 'info');
        return;
    }

    const result = await Swal.fire({
        title: '¿Estás seguro?',
        text: "No podrás revertir esto",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#3085d6',
        cancelButtonColor: '#d33',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (result.isConfirmed) {
        try {
            await matematicaService.deleteDesempeno(id);
            await fetchDesempenos();
            Swal.fire('¡Eliminado!', 'El desempeño ha sido eliminado.', 'success');
        } catch (e: any) {
            Swal.fire('Error', "Error al eliminar: " + (e.response?.data?.detail || e.message), 'error');
        }
    }
};

// Nota: El botón "Inicio" global en App.vue permite volver al home
</script>

<template>
    <div
        class="min-h-screen bg-gradient-to-br from-violet-50 via-purple-50 to-indigo-50 dark:from-slate-950 dark:via-slate-900 dark:to-violet-950/30 p-4 sm:p-8 font-sans relative">

        <EduBackground variant="violet" />

        <div class="max-w-7xl mx-auto relative z-10">

            <!-- Header -->
            <Header title="AdminMat" subtitle="Gestión Matemática" :is-dark="isDark"
                gradient-class="from-violet-600 via-purple-600 to-indigo-600 shadow-violet-500/20"
                version-badge-class="bg-violet-400 text-violet-900" subtitle-class="text-violet-100 dark:text-slate-400"
                mascota-bubble-class="border-violet-300 dark:border-violet-500"
                mascota-text-class="text-violet-600 dark:text-violet-400" class="rounded-2xl mb-8 sticky top-0"
                @toggle-theme="toggleTheme">
                <template #actions-before>
                    <button @click="router.push('/')"
                        class="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300"
                        title="Inicio">
                        <Home class="w-5 h-5" />
                    </button>
                </template>
            </Header>

            <!-- Tab Navigation & Stats -->
            <div class="space-y-6 mb-8">
                <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div
                        class="flex bg-white dark:bg-slate-800 p-1.5 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">
                        <button v-for="tab in [
                            { id: 'competencias', label: 'Competencias', icon: Target },
                            { id: 'capacidades', label: 'Capacidades', icon: Layers },
                            { id: 'desempenos', label: 'Desempeños', icon: BookOpen }
                        ]" :key="tab.id" @click="activeTab = tab.id as any"
                            class="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all"
                            :class="activeTab === tab.id
                                ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-md'
                                : 'text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'">
                            <component :is="tab.icon" class="w-4 h-4" />
                            {{ tab.label }}
                        </button>
                    </div>

                    <div
                        class="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white/50 dark:bg-slate-800/50 p-2 rounded-2xl backdrop-blur-sm border border-slate-200 dark:border-slate-700">
                        <div v-for="stat in [
                            { label: 'Comp.', value: stats.competencias, color: 'text-violet-600' },
                            { label: 'Cap.', value: stats.capacidades, color: 'text-purple-600' },
                            { label: 'Des.', value: stats.desempenos, color: 'text-indigo-600' },
                            { label: 'Grados', value: stats.grados, color: 'text-teal-600' }
                        ]" :key="stat.label" class="px-3 py-1 flex flex-col items-center">
                            <span :class="['text-lg font-bold', stat.color]">{{ stat.value }}</span>
                            <span class="text-[10px] uppercase font-bold text-slate-400">{{ stat.label }}</span>
                        </div>
                    </div>
                </div>
            </div>
            <!-- Tool Bar -->
            <div
                class="flex flex-wrap items-center justify-between gap-4 mb-6 bg-white dark:bg-slate-800 p-4 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700">

                <!-- Filters for Desempeños -->
                <div v-if="activeTab === 'desempenos'" class="flex flex-wrap items-center gap-4">
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Grado:</span>
                        <select v-model="selectedGradoId"
                            class="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-violet-500">
                            <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
                        </select>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Competencia:</span>
                        <select v-model="selectedCompetenciaId"
                            class="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-violet-500">
                            <option v-for="c in competencias" :key="c.id" :value="c.id">{{ c.nombre }}</option>
                        </select>
                    </div>
                </div>

                <!-- Filter for Capacidades -->
                <div v-else-if="activeTab === 'capacidades'" class="flex items-center gap-2">
                    <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Competencia:</span>
                    <select v-model="selectedCompetenciaId"
                        class="px-3 py-2 bg-slate-50 dark:bg-slate-900 border border-slate-300 dark:border-slate-600 rounded-lg text-sm text-slate-700 dark:text-slate-200 focus:ring-2 focus:ring-violet-500">
                        <option :value="null">Todas</option>
                        <option v-for="c in competencias" :key="c.id" :value="c.id">{{ c.nombre }}</option>
                    </select>
                </div>

                <div v-else></div>

                <button @click="openModal()"
                    class="px-4 py-2 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white rounded-lg text-sm font-bold flex items-center gap-2 transition-all shadow-lg shadow-violet-500/20">
                    <Plus class="w-4 h-4" /> Nuevo {{ activeTab.slice(0, -1) }}
                </button>
            </div>

            <!-- Content Table -->
            <div
                class="bg-white dark:bg-slate-800 rounded-xl shadow-lg border border-slate-200 dark:border-slate-700 overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="w-full text-left border-collapse">
                        <thead>
                            <tr
                                class="bg-slate-50 dark:bg-slate-900/50 border-b border-slate-200 dark:border-slate-700">
                                <th class="p-4 text-xs font-bold text-slate-500 uppercase">ID</th>

                                <!-- Dynamic Headers -->
                                <template v-if="activeTab === 'competencias'">
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Código</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Nombre</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Descripción</th>
                                </template>

                                <template v-else-if="activeTab === 'capacidades'">
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Orden</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Nombre</th>
                                    <th class="p-4 text-xs font-bold text-slate-500 uppercase">Competencia</th>
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

                            <!-- Loading State -->
                            <template v-if="loading">
                                <tr v-for="n in 5" :key="n" class="animate-pulse">
                                    <td class="p-4">
                                        <div class="h-4 w-8 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                    </td>
                                    <template v-if="activeTab === 'competencias'">
                                        <td class="p-4">
                                            <div class="h-6 w-12 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                                        </td>
                                        <td class="p-4">
                                            <div class="h-4 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                        </td>
                                        <td class="p-4">
                                            <div class="h-4 w-64 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                        </td>
                                    </template>
                                    <template v-else-if="activeTab === 'capacidades'">
                                        <td class="p-4">
                                            <div class="h-6 w-8 bg-slate-200 dark:bg-slate-700 rounded-full"></div>
                                        </td>
                                        <td class="p-4">
                                            <div class="h-4 w-32 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                        </td>
                                        <td class="p-4">
                                            <div class="h-6 w-24 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                        </td>
                                    </template>
                                    <template v-else>
                                        <td class="p-4">
                                            <div class="h-6 w-12 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                        </td>
                                        <td class="p-4">
                                            <div class="h-4 w-72 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                        </td>
                                        <td class="p-4">
                                            <div class="flex flex-col gap-2">
                                                <div class="h-3 w-12 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                                <div class="h-3 w-20 bg-slate-200 dark:bg-slate-700 rounded"></div>
                                            </div>
                                        </td>
                                    </template>
                                    <td class="p-4 text-right">
                                        <div class="h-8 w-16 bg-slate-200 dark:bg-slate-700 rounded ml-auto"></div>
                                    </td>
                                </tr>
                            </template>

                            <!-- Competencias Rows -->
                            <template v-else-if="activeTab === 'competencias'">
                                <template v-if="competencias.length > 0">
                                    <tr v-for="item in competencias" :key="item.id"
                                        class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                        <td class="p-4 text-sm text-slate-400 font-mono">#{{ item.id }}</td>
                                        <td class="p-4">
                                            <span
                                                class="px-3 py-1 bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400 rounded-full text-sm font-bold">
                                                {{ item.codigo }}
                                            </span>
                                        </td>
                                        <td class="p-4 text-sm font-medium text-slate-800 dark:text-slate-200">{{
                                            item.nombre }}</td>
                                        <td class="p-4 text-sm text-slate-600 dark:text-slate-400 max-w-md truncate">{{
                                            item.descripcion?.slice(0, 100) }}...</td>
                                        <td class="p-4 text-right space-x-2">
                                            <button @click="openModal(item)"
                                                class="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                                                <Eye class="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                </template>
                            </template>

                            <!-- Capacidades Rows -->
                            <template v-else-if="activeTab === 'capacidades'">
                                <template v-if="capacidadesFiltradas.length > 0">
                                    <tr v-for="item in capacidadesFiltradas" :key="item.id"
                                        class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                        <td class="p-4 text-sm text-slate-400 font-mono">#{{ item.id }}</td>
                                        <td class="p-4">
                                            <span
                                                class="px-3 py-1 bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400 rounded-full text-sm font-bold">
                                                {{ item.orden }}
                                            </span>
                                        </td>
                                        <td class="p-4 text-sm font-medium text-slate-800 dark:text-slate-200">{{
                                            item.nombre }}</td>
                                        <td class="p-4 text-sm text-slate-600 dark:text-slate-400">
                                            <span class="px-2 py-1 bg-slate-100 dark:bg-slate-700 rounded text-xs">
                                                {{ item.competencia_nombre }}
                                            </span>
                                        </td>
                                        <td class="p-4 text-right space-x-2">
                                            <button @click="openModal(item)"
                                                class="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors">
                                                <Eye class="w-4 h-4" />
                                            </button>
                                        </td>
                                    </tr>
                                </template>
                            </template>

                            <!-- Desempeños Rows -->
                            <template v-else-if="activeTab === 'desempenos'">
                                <template v-if="desempenos.length > 0">
                                    <tr v-for="item in desempenos" :key="item.id"
                                        class="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                                        <td class="p-4 text-sm text-slate-400 font-mono">#{{ item.id }}</td>
                                        <td class="p-4">
                                            <span
                                                class="px-2 py-1 bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400 rounded font-mono text-sm font-bold">
                                                {{ item.codigo }}
                                            </span>
                                        </td>
                                        <td class="p-4 text-sm text-slate-600 dark:text-slate-300 max-w-lg">
                                            {{ item.descripcion.slice(0, 150) }}{{ item.descripcion.length > 150 ? '...'
                                                :
                                                '' }}
                                        </td>
                                        <td class="p-4 text-sm text-slate-500">
                                            <div class="flex flex-col gap-1">
                                                <span
                                                    class="text-xs font-medium text-purple-600 dark:text-purple-400">Cap.
                                                    {{ item.capacidad_orden }}</span>
                                                <span class="text-xs text-slate-400">{{ item.capacidad_nombre.slice(0,
                                                    30)
                                                    }}...</span>
                                            </div>
                                        </td>
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
                                </template>
                            </template>

                            <!-- Empty State -->
                            <tr v-if="!loading && (
                                activeTab === 'competencias' ? competencias.length === 0 :
                                    activeTab === 'capacidades' ? capacidadesFiltradas.length === 0 :
                                        desempenos.length === 0
                            )">
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
                class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-2xl w-full overflow-hidden border border-slate-200 dark:border-slate-700">
                <div
                    class="px-6 py-4 border-b border-slate-100 dark:border-slate-700 flex justify-between items-center bg-gradient-to-r from-violet-50 to-purple-50 dark:from-slate-900/50 dark:to-slate-800">
                    <h3 class="font-bold text-lg text-slate-800 dark:text-white flex items-center gap-2">
                        <Calculator class="w-5 h-5 text-violet-600" />
                        {{ isEditing ? 'Ver' : 'Nuevo' }} {{ activeTab.slice(0, -1) }}
                    </h3>
                    <button @click="showModal = false"
                        class="text-slate-400 hover:text-slate-600 dark:hover:text-white">
                        <X class="w-5 h-5" />
                    </button>
                </div>

                <div class="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
                    <!-- Competencias Fields -->
                    <template v-if="activeTab === 'competencias'">
                        <div class="grid grid-cols-4 gap-4">
                            <div>
                                <label class="block text-xs font-bold text-slate-500 mb-1">Código</label>
                                <input v-model.number="editItem.codigo" type="number" :disabled="isEditing"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50">
                            </div>
                            <div class="col-span-3">
                                <label class="block text-xs font-bold text-slate-500 mb-1">Nombre</label>
                                <input v-model="editItem.nombre" type="text" :disabled="isEditing"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50">
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Descripción</label>
                            <textarea v-model="editItem.descripcion" rows="6" :disabled="isEditing"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50"></textarea>
                        </div>
                    </template>

                    <!-- Capacidades Fields -->
                    <template v-if="activeTab === 'capacidades'">
                        <div class="grid grid-cols-4 gap-4">
                            <div>
                                <label class="block text-xs font-bold text-slate-500 mb-1">Orden</label>
                                <input v-model.number="editItem.orden" type="number" :disabled="isEditing"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50">
                            </div>
                            <div class="col-span-3">
                                <label class="block text-xs font-bold text-slate-500 mb-1">Competencia</label>
                                <select v-model="editItem.competencia_id" :disabled="isEditing"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50">
                                    <option v-for="c in competencias" :key="c.id" :value="c.id">{{ c.nombre }}</option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Nombre</label>
                            <input v-model="editItem.nombre" type="text" :disabled="isEditing"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50">
                        </div>
                    </template>

                    <!-- Desempenos Fields -->
                    <template v-if="activeTab === 'desempenos'">
                        <div class="grid grid-cols-3 gap-4">
                            <div>
                                <label class="block text-xs font-bold text-slate-500 mb-1">Código</label>
                                <input v-model="editItem.codigo" type="text" :disabled="isEditing"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50">
                            </div>
                            <div class="col-span-2">
                                <label class="block text-xs font-bold text-slate-500 mb-1">Capacidad</label>
                                <select v-model="editItem.capacidad_id" :disabled="isEditing"
                                    class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50">
                                    <option v-for="c in capacidadesFiltradas" :key="c.id" :value="c.id">
                                        Cap. {{ c.orden }}: {{ c.nombre }}
                                    </option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label class="block text-xs font-bold text-slate-500 mb-1">Descripción</label>
                            <textarea v-model="editItem.descripcion" rows="6" :disabled="isEditing"
                                class="w-full px-3 py-2 border rounded-lg dark:bg-slate-700 dark:border-slate-600 dark:text-white disabled:opacity-50"></textarea>
                        </div>
                    </template>
                </div>

                <div
                    class="px-6 py-4 border-t border-slate-100 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/50 flex justify-end gap-3">
                    <button @click="showModal = false"
                        class="px-4 py-2 text-slate-600 hover:bg-slate-200 dark:text-slate-300 dark:hover:bg-slate-700 rounded-lg font-bold text-sm transition-colors">
                        Cancelar
                    </button>
                    <button v-if="activeTab === 'desempenos'" @click="saveItem" :disabled="saving"
                        class="px-4 py-2 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white rounded-lg font-bold text-sm flex items-center gap-2 shadow-lg shadow-violet-500/20 disabled:opacity-50 transition-all transform hover:scale-105">
                        <Save class="w-4 h-4" /> {{ saving ? 'Guardando...' : 'Guardar' }}
                    </button>
                </div>
            </div>
        </div>
    </div>
</template>
