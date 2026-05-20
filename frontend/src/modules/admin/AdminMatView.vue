<script setup lang="ts">
import { ref, shallowRef, onMounted, onUnmounted, computed, watch } from 'vue';
import { useRouter } from 'vue-router';
import { matematicaService } from '../../shared/services/api';
import type {
    CompetenciaMatematica,
    CapacidadMatConCompetencia,
    DesempenoMatCompleto,
    GradoMatematica
} from '../../shared/types/matematica';
import { 
    Trash2, Edit, Plus, X, Calculator, Target, Layers, BookOpen, Home, Loader2 
} from 'lucide-vue-next';

const router = useRouter();
import Swal from 'sweetalert2';
import Header from '../../shared/components/Header.vue';
import EduBackground from '../../shared/components/EduBackground.vue';
import ComboBox from '../../shared/components/ComboBox.vue';
import { useTheme } from '../../shared/composables/useTheme';

const { isDark, toggleTheme } = useTheme();

// Responsive State
const isDesktop = ref(window.innerWidth >= 1024);
const onResize = () => { isDesktop.value = window.innerWidth >= 1024; };

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

// ComboBox options
const gradoOptions = computed(() =>
    grados.value.map(g => ({ id: g.id, label: g.nombre }))
);

const competenciaOptions = computed(() =>
    competencias.value.map(c => ({ id: c.id, label: c.nombre }))
);

// Wrapper for capacidades tab filter (supports "Todas" = null)
const capFilterCompetenciaId = computed({
    get: () => selectedCompetenciaId.value ?? '__all__',
    set: (val: number | string | null) => {
        selectedCompetenciaId.value = val === '__all__' ? null : val as number;
    }
});

const competenciaOptionsConTodas = computed(() => [
    { id: '__all__' as string | number, label: 'Todas' },
    ...competencias.value.map(c => ({ id: c.id as string | number, label: c.nombre }))
]);

const capacidadModalOptions = computed(() =>
    capacidadesFiltradas.value.map(c => ({ id: c.id, label: `Cap. ${c.orden}: ${c.nombre}` }))
);

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
    window.addEventListener('resize', onResize);
    fetchData();
});

onUnmounted(() => {
    window.removeEventListener('resize', onResize);
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

</script>

<template>
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950 p-4 sm:p-8 font-sans relative flex flex-col overflow-x-hidden">
        <EduBackground variant="violet" />
        <div class="max-w-7xl mx-auto w-full relative z-10 flex-1 flex flex-col">
            <Header title="Gestión" subtitle="Matemática" :is-dark="isDark"
                gradient-class="from-violet-600 via-purple-600 to-indigo-600 shadow-violet-500/20"
                class="rounded-2xl mb-8 sticky top-0" @toggle-theme="toggleTheme">
                <template #actions-before>
                    <button @click="router.push('/')"
                        class="p-2.5 rounded-xl bg-slate-100 dark:bg-white/20 text-slate-600 dark:text-white border border-slate-200 dark:border-white/30 hover:bg-slate-200 dark:hover:bg-white/30 transition-all duration-300 cursor-pointer"
                        title="Inicio">
                        <Home class="w-5 h-5" />
                    </button>
                </template>
            </Header>

            <!-- Mobile Navigation Tabs (Premium Style) -->
            <div v-if="!isDesktop" class="shrink-0 flex items-center justify-around bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-1.5 mb-8 shadow-sm">
                <button v-for="tab in [
                    { id: 'competencias', label: 'Competencias', icon: Target },
                    { id: 'capacidades', label: 'Capacidades', icon: Layers },
                    { id: 'desempenos', label: 'Desempeños', icon: BookOpen }
                ]" :key="tab.id" @click="activeTab = tab.id as any"
                    class="flex-1 py-2.5 flex flex-col items-center justify-center gap-1 rounded-xl transition-all cursor-pointer" 
                    :class="activeTab === tab.id ? 'text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-900/30' : 'text-slate-500'">
                    <component :is="tab.icon" class="w-5 h-5" />
                    <span class="text-[10px] font-black uppercase tracking-widest">{{ tab.label }}</span>
                </button>
            </div>

            <!-- Desktop Navigation Tabs -->
            <div v-else class="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div class="flex items-center gap-1 bg-white/50 dark:bg-slate-800/50 backdrop-blur-md p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700 w-fit shadow-sm">
                    <button v-for="tab in [
                        { id: 'competencias', label: 'Competencias', icon: Target },
                        { id: 'capacidades', label: 'Capacidades', icon: Layers },
                        { id: 'desempenos', label: 'Desempeños', icon: BookOpen }
                    ]" :key="tab.id" @click="activeTab = tab.id as any"
                        class="px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all cursor-pointer"
                        :class="activeTab === tab.id ? 'bg-gradient-to-r from-violet-500 to-purple-600 text-white shadow-lg shadow-violet-500/20' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700'">
                        {{ tab.label }}
                    </button>
                </div>

                <div class="grid grid-cols-4 gap-3 bg-white/50 dark:bg-slate-800/50 p-2 rounded-2xl backdrop-blur-sm border-2 border-slate-200 dark:border-slate-700">
                    <div v-for="stat in [
                        { label: 'Comp.', value: stats.competencias, color: 'text-violet-600' },
                        { label: 'Cap.', value: stats.capacidades, color: 'text-purple-600' },
                        { label: 'Des.', value: stats.desempenos, color: 'text-indigo-600' },
                        { label: 'Grados', value: stats.grados, color: 'text-teal-600' }
                    ]" :key="stat.label" class="px-4 py-1 flex flex-col items-center">
                        <span :class="['text-base font-black', stat.color]">{{ stat.value }}</span>
                        <span class="text-[9px] uppercase font-black text-slate-400 tracking-widest">{{ stat.label }}</span>
                    </div>
                </div>
            </div>

            <!-- Tool Bar -->
            <div class="flex flex-col lg:flex-row items-center justify-between gap-6 mb-8 bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm">
                <div v-if="activeTab === 'desempenos'" class="w-full flex flex-col sm:flex-row gap-6">
                    <div class="flex-1 space-y-2">
                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Grado</label>
                        <ComboBox v-model="selectedGradoId" :options="gradoOptions" placeholder="Seleccionar grado..." />
                    </div>
                    <div class="flex-1 space-y-2">
                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Competencia</label>
                        <ComboBox v-model="selectedCompetenciaId" :options="competenciaOptions" placeholder="Seleccionar competencia..." />
                    </div>
                </div>
                <div v-else-if="activeTab === 'capacidades'" class="w-full sm:w-80 space-y-2">
                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Filtrar por Competencia</label>
                    <ComboBox v-model="capFilterCompetenciaId" :options="competenciaOptionsConTodas" placeholder="Todas..." />
                </div>
                <div v-else></div>

                <button @click="openModal()"
                    class="w-full lg:w-auto flex items-center justify-center gap-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-black px-8 py-4 rounded-2xl shadow-xl hover:-translate-y-1 transition-all active:scale-95 text-xs uppercase tracking-widest cursor-pointer">
                    <Plus class="w-5 h-5" />
                    <span>Nuevo {{ activeTab.slice(0, -1) }}</span>
                </button>
            </div>

            <!-- Content Area -->
            <div class="flex-1 flex flex-col min-h-0">
                <!-- Desktop Table -->
                <div v-if="isDesktop" class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden">
                    <div class="overflow-x-auto custom-scrollbar">
                        <table class="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr class="bg-slate-50 dark:bg-slate-900 border-b-2 border-slate-100 dark:border-slate-700">
                                    <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">ID</th>
                                    <template v-if="activeTab === 'competencias'">
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Cód</th>
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Nombre</th>
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Descripción</th>
                                    </template>
                                    <template v-else-if="activeTab === 'capacidades'">
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Orden</th>
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Nombre</th>
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Competencia</th>
                                    </template>
                                    <template v-else>
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Código</th>
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Descripción</th>
                                        <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest">Capacidad</th>
                                    </template>
                                    <th class="p-5 text-xs font-black text-slate-500 uppercase tracking-widest text-right"></th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                                <tr v-if="loading" v-for="n in 5" :key="n" class="animate-pulse">
                                    <td class="p-5"><div class="h-4 w-8 bg-slate-200 dark:bg-slate-700 rounded"></div></td>
                                    <td colspan="3" class="p-5"><div class="h-4 w-3/4 bg-slate-200 dark:bg-slate-700 rounded"></div></td>
                                    <td class="p-5 text-right"><div class="h-8 w-16 bg-slate-200 dark:bg-slate-700 rounded ml-auto"></div></td>
                                </tr>
                                <template v-else>
                                    <tr v-for="item in (activeTab === 'competencias' ? competencias : activeTab === 'capacidades' ? capacidadesFiltradas : desempenos)" :key="item.id" class="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors group">
                                        <td class="p-5 text-xs text-slate-400 font-mono font-bold">#{{ item.id }}</td>
                                        
                                        <template v-if="activeTab === 'competencias'">
                                            <td class="p-5"><span class="px-3 py-1 bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-400 rounded-lg text-xs font-black">{{ (item as any).codigo }}</span></td>
                                            <td class="p-5 text-sm font-black text-slate-800 dark:text-white leading-tight">{{ (item as any).nombre }}</td>
                                            <td class="p-5 text-xs text-slate-500 dark:text-slate-400 max-w-md truncate">{{ (item as any).descripcion }}</td>
                                        </template>

                                        <template v-else-if="activeTab === 'capacidades'">
                                            <td class="p-5"><span class="px-3 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-400 rounded-lg text-xs font-black">{{ (item as any).orden }}</span></td>
                                            <td class="p-5 text-sm font-black text-slate-800 dark:text-white leading-tight">{{ (item as any).nombre }}</td>
                                            <td class="p-5"><span class="px-3 py-1 bg-slate-100 dark:bg-slate-700 rounded-full text-[10px] font-black text-slate-500 uppercase">{{ (item as any).competencia_nombre }}</span></td>
                                        </template>

                                        <template v-else>
                                            <td class="p-5 font-mono font-black text-indigo-600 dark:text-indigo-400">{{ (item as any).codigo }}</td>
                                            <td class="p-5 text-sm font-bold text-slate-600 dark:text-slate-300 max-w-lg leading-relaxed">{{ (item as any).descripcion }}</td>
                                            <td class="p-5">
                                                <div class="text-[10px] font-black text-purple-600 uppercase tracking-widest mb-1">Cap. {{ (item as any).capacidad_orden }}</div>
                                                <div class="text-[10px] font-bold text-slate-400 uppercase leading-tight">{{ (item as any).capacidad_nombre }}</div>
                                            </td>
                                        </template>

                                        <td class="p-5 text-right">
                                            <div class="flex items-center justify-end gap-1 sm:opacity-0 group-hover:opacity-100 transition-all">
                                                <button @click="openModal(item)" class="p-2.5 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/30 transition-all cursor-pointer"><Edit class="w-5 h-5" /></button>
                                                <button @click="deleteItem(item.id)" class="p-2.5 rounded-xl text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/30 transition-all cursor-pointer"><Trash2 class="w-5 h-5" /></button>
                                            </div>
                                        </td>
                                    </tr>
                                </template>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Mobile Cards -->
                <div v-else class="space-y-4 pb-24">
                    <div v-if="loading" v-for="n in 3" :key="n" class="bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 animate-pulse">
                        <div class="h-4 w-1/2 bg-slate-200 dark:bg-slate-700 rounded mb-4"></div>
                        <div class="h-3 w-3/4 bg-slate-200 dark:bg-slate-700 rounded mb-2"></div>
                    </div>
                    <div v-else v-for="item in (activeTab === 'competencias' ? competencias : activeTab === 'capacidades' ? capacidadesFiltradas : desempenos)" :key="item.id" 
                        class="bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm">
                        <div class="flex justify-between items-start mb-4">
                            <div class="space-y-1">
                                <div class="text-[9px] font-mono font-black text-violet-500 uppercase tracking-widest">ID #{{ item.id }}</div>
                                <h3 class="font-black text-slate-800 dark:text-white tracking-tight text-lg leading-tight">
                                    {{ activeTab === 'desempenos' ? (item as any).codigo : (item as any).nombre }}
                                </h3>
                            </div>
                            <div class="flex gap-1">
                                <button @click="openModal(item)" class="p-2.5 bg-slate-50 dark:bg-slate-700 rounded-xl text-slate-400 active:scale-95 transition-all cursor-pointer"><Edit class="w-5 h-5" /></button>
                                <button @click="deleteItem(item.id)" class="p-2.5 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-400 active:scale-95 transition-all cursor-pointer"><Trash2 class="w-5 h-5" /></button>
                            </div>
                        </div>
                        <div v-if="activeTab === 'desempenos'" class="space-y-3">
                            <p class="text-xs font-bold text-slate-600 dark:text-slate-400 leading-relaxed">{{ (item as any).descripcion }}</p>
                            <div class="pt-4 border-t border-slate-100 dark:border-slate-700">
                                <div class="text-[9px] font-black text-purple-600 uppercase tracking-widest">Capacidad {{ (item as any).capacidad_orden }}</div>
                                <div class="text-[10px] font-bold text-slate-400 uppercase leading-tight mt-1">{{ (item as any).capacidad_nombre }}</div>
                            </div>
                        </div>
                        <div v-else class="flex flex-wrap gap-2 mt-2">
                             <span class="px-3 py-1 bg-violet-50 dark:bg-violet-900/30 text-violet-700 dark:text-violet-400 rounded-lg text-[10px] font-black uppercase tracking-widest border border-violet-100">{{ activeTab === 'competencias' ? 'Cód ' + (item as any).codigo : 'Orden ' + (item as any).orden }}</span>
                             <span v-if="activeTab === 'capacidades'" class="px-3 py-1 bg-slate-50 dark:bg-slate-700 text-slate-500 rounded-lg text-[10px] font-black uppercase tracking-widest border border-slate-100">{{ (item as any).competencia_nombre }}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Premium Modal -->
        <Teleport to="body">
            <Transition name="modal">
                <div v-if="showModal" class="fixed inset-0 z-50 flex items-center sm:items-center justify-center items-end bg-slate-900/60 backdrop-blur-sm cursor-pointer" @click.self="showModal = false">
                    <div class="bg-white dark:bg-slate-800 rounded-t-2xl sm:rounded-2xl shadow-2xl w-full max-w-lg overflow-hidden relative">
                        <!-- Mobile handle -->
                        <div class="sm:hidden flex justify-center pt-4 pb-1 cursor-pointer" @click="showModal = false"><div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-slate-700"></div></div>
                        
                        <div class="flex items-center justify-between p-8 border-b border-slate-100 dark:border-slate-700">
                            <div class="flex items-center gap-5">
                                <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-violet-500/20">
                                    <Calculator class="w-6 h-6 text-white" />
                                </div>
                                <div>
                                    <h2 class="text-xl font-black text-slate-800 dark:text-white tracking-tight leading-tight">
                                        {{ isEditing ? 'Ver' : 'Nuevo' }} {{ activeTab.slice(0, -1) }}
                                    </h2>
                                    <p class="text-[10px] text-slate-400 font-black uppercase tracking-widest mt-0.5">Gestión Matemática</p>
                                </div>
                            </div>
                            <button @click="showModal = false" class="p-3 rounded-2xl text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 transition-all cursor-pointer"><X class="w-6 h-6" /></button>
                        </div>

                        <div class="p-8 space-y-6 max-h-[70vh] overflow-y-auto custom-scrollbar">
                            <template v-if="activeTab === 'competencias'">
                                <div class="grid grid-cols-4 gap-4">
                                    <div class="space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Código</label>
                                        <input v-model.number="editItem.codigo" type="number" :disabled="isEditing" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all placeholder-slate-400" />
                                    </div>
                                    <div class="col-span-3 space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre</label>
                                        <input v-model="editItem.nombre" type="text" :disabled="isEditing" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all placeholder-slate-400" />
                                    </div>
                                </div>
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Descripción</label>
                                    <textarea v-model="editItem.descripcion" rows="4" :disabled="isEditing" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all placeholder-slate-400"></textarea>
                                </div>
                            </template>

                            <template v-if="activeTab === 'capacidades'">
                                <div class="grid grid-cols-4 gap-4">
                                    <div class="space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Orden</label>
                                        <input v-model.number="editItem.orden" type="number" :disabled="isEditing" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all placeholder-slate-400" />
                                    </div>
                                    <div class="col-span-3 space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Competencia</label>
                                        <ComboBox v-if="!isEditing" v-model="editItem.competencia_id" :options="competenciaOptions" placeholder="Seleccionar..." />
                                        <div v-else class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-400 opacity-60">{{ editItem?.competencia_nombre }}</div>
                                    </div>
                                </div>
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre</label>
                                    <input v-model="editItem.nombre" type="text" :disabled="isEditing" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all placeholder-slate-400" />
                                </div>
                            </template>

                            <template v-if="activeTab === 'desempenos'">
                                <div class="grid grid-cols-3 gap-4">
                                    <div class="space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Código</label>
                                        <input v-model="editItem.codigo" type="text" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all placeholder-slate-400" />
                                    </div>
                                    <div class="col-span-2 space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Capacidad</label>
                                        <ComboBox v-model="editItem.capacidad_id" :options="capacidadModalOptions" placeholder="Seleccionar..." />
                                    </div>
                                </div>
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Descripción</label>
                                    <textarea v-model="editItem.descripcion" rows="6" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all placeholder-slate-400"></textarea>
                                </div>
                            </template>
                        </div>

                        <div class="p-8 bg-slate-50 dark:bg-slate-900/50 flex flex-col sm:flex-row gap-4">
                            <button @click="showModal = false" class="flex-1 px-8 py-4 text-xs font-black uppercase tracking-widest text-slate-500 bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 transition-all hover:bg-slate-50 cursor-pointer">Cerrar</button>
                            <button v-if="activeTab === 'desempenos'" @click="saveItem" :disabled="saving" class="flex-1 flex items-center justify-center gap-3 py-4 bg-gradient-to-r from-violet-600 to-purple-700 text-white font-black text-xs rounded-2xl shadow-xl shadow-violet-500/20 transition-all transform active:scale-95 disabled:opacity-70 cursor-pointer">
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
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 10px; }
</style>
