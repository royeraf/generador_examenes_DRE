<script setup lang="ts">
import { ref, shallowRef, onMounted, onUnmounted } from 'vue';
import { adminService } from '../../shared/services/api';
import type { Grado, Capacidad, DesempenoItem } from '../../shared/types';
import {
  Trash2, Edit, Plus, Save, X, GraduationCap, Shield, BookOpen, ChevronDown
} from 'lucide-vue-next';

import Header from '../../shared/components/Header.vue';
import EduBackground from '../../shared/components/EduBackground.vue';
import BaseButton from '../../shared/components/BaseButton.vue';
import { showError, showSuccess, showDeleteConfirm } from '../../shared/utils/swal';

// Responsive State
const isDesktop = ref(window.innerWidth >= 1024);
const onResize = () => { isDesktop.value = window.innerWidth >= 1024; };

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
    window.addEventListener('resize', onResize);
    fetchData();
});

onUnmounted(() => {
    window.removeEventListener('resize', onResize);
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

</script>

<template>
    <div class="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans relative flex flex-col overflow-x-hidden">
        <EduBackground variant="emerald" />
        <Header title="Gestión" subtitle="Currículo Nacional" :show-home="true" />
        <div class="max-w-7xl mx-auto w-full relative z-10 flex-1 flex flex-col p-4 sm:p-8">

            <!-- Mobile Navigation Tabs (Premium Style) -->
            <div v-if="!isDesktop" class="shrink-0 flex items-center justify-around bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-1.5 mb-8 shadow-sm">
                <button v-for="tab in ['grados', 'capacidades', 'desempenos']" :key="tab"
                    @click="activeTab = tab as any"
                    class="flex-1 py-2.5 flex flex-col items-center justify-center gap-1 rounded-xl transition-all cursor-pointer" 
                    :class="activeTab === tab ? 'text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/30' : 'text-slate-500'">
                    <component :is="tab === 'grados' ? GraduationCap : tab === 'capacidades' ? Shield : BookOpen" class="w-5 h-5" />
                    <span class="text-[10px] font-black uppercase tracking-widest">{{ tab }}</span>
                </button>
            </div>

            <!-- Desktop Navigation Tabs -->
            <div v-else class="mb-8 flex justify-center">
                <div class="flex items-center gap-1 bg-white dark:bg-slate-800 p-1.5 rounded-2xl border border-slate-200 dark:border-slate-700 w-fit shadow-sm">
                    <button v-for="tab in ['grados', 'capacidades', 'desempenos']" :key="tab"
                        @click="activeTab = tab as any"
                        class="px-6 py-2.5 rounded-xl text-xs font-black uppercase tracking-widest transition-all cursor-pointer"
                        :class="activeTab === tab ? 'bg-gradient-to-r from-teal-500 to-emerald-600 text-white shadow-lg shadow-teal-500/20' : 'text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700'">
                        {{ tab }}
                    </button>
                </div>
            </div>

            <!-- Tool Bar -->
            <div class="flex flex-col sm:flex-row items-center justify-between gap-4 mb-8 bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm animate-in fade-in slide-in-from-top-2 duration-500">
                <div v-if="activeTab === 'desempenos'" class="w-full sm:w-auto space-y-2">
                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Grado</label>
                    <div class="relative">
                        <select v-model="selectedGradoId" @change="fetchDesempenos"
                            class="w-full sm:w-64 bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none appearance-none cursor-pointer">
                            <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
                        </select>
                        <ChevronDown class="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                    </div>
                </div>
                <div v-else></div>

                <BaseButton variant="primary" size="md" class="w-full sm:w-auto" @click="openModal()">
                    <template #icon><Plus class="w-4 h-4" /></template>
                    Nuevo {{ activeTab.slice(0, -1) }}
                </BaseButton>
            </div>

            <!-- Content Area -->
            <div class="flex-1 flex flex-col min-h-0">
                
                <!-- Desktop Table -->
                <div v-if="isDesktop" class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-xl overflow-hidden flex flex-col">
                    <div class="overflow-x-auto custom-scrollbar">
                        <table class="w-full text-left border-collapse text-sm">
                            <thead>
                                <tr class="bg-slate-50 dark:bg-slate-900 border-b-2 border-slate-100 dark:border-slate-700">
                                    <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">ID</th>
                                    <template v-if="activeTab === 'grados'">
                                        <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">Nombre</th>
                                        <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">Número</th>
                                        <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">Nivel</th>
                                    </template>
                                    <template v-else-if="activeTab === 'capacidades'">
                                        <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">Nombre</th>
                                        <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">Tipo</th>
                                    </template>
                                    <template v-else>
                                        <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">Código</th>
                                        <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">Descripción</th>
                                        <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest">Capacidad</th>
                                    </template>
                                    <th class="p-4 text-xs font-black text-slate-500 uppercase tracking-widest text-right"></th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                                <tr v-if="loading" v-for="n in 5" :key="n" class="animate-pulse">
                                    <td class="p-4"><div class="h-4 w-8 bg-slate-200 dark:bg-slate-700 rounded"></div></td>
                                    <td colspan="3" class="p-4"><div class="h-4 w-3/4 bg-slate-200 dark:bg-slate-700 rounded"></div></td>
                                    <td class="p-4 text-right"><div class="h-8 w-16 bg-slate-200 dark:bg-slate-700 rounded ml-auto"></div></td>
                                </tr>
                                <tr v-else v-for="item in (activeTab === 'grados' ? grados : activeTab === 'capacidades' ? capacidades : desempenos)" :key="item.id" class="hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors">
                                    <td class="p-4 text-xs text-slate-400 font-mono font-bold">#{{ item.id }}</td>
                                    
                                    <template v-if="activeTab === 'grados'">
                                        <td class="p-4 text-sm font-black text-slate-800 dark:text-slate-200">{{ (item as Grado).nombre }}</td>
                                        <td class="p-4 text-sm font-bold text-slate-600 dark:text-slate-400">{{ (item as Grado).numero }}</td>
                                        <td class="p-4 capitalize">
                                            <span class="px-3 py-1 bg-teal-50 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400 rounded-lg text-[10px] font-black uppercase tracking-widest">
                                                {{ (item as Grado).nivel }}
                                            </span>
                                        </td>
                                    </template>

                                    <template v-else-if="activeTab === 'capacidades'">
                                        <td class="p-4 text-sm font-black text-slate-800 dark:text-slate-200">{{ (item as Capacidad).nombre }}</td>
                                        <td class="p-4 capitalize">
                                            <span class="px-3 py-1 bg-indigo-50 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400 rounded-lg text-[10px] font-black uppercase tracking-widest">
                                                {{ (item as Capacidad).tipo }}
                                            </span>
                                        </td>
                                    </template>

                                    <template v-else>
                                        <td class="p-4 text-sm font-mono font-black text-teal-600">{{ (item as DesempenoItem).codigo }}</td>
                                        <td class="p-4 text-sm font-bold text-slate-600 dark:text-slate-300 max-w-md">{{ (item as DesempenoItem).descripcion }}</td>
                                        <td class="p-4 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                            {{ (item as DesempenoItem).capacidad_nombre || (item as DesempenoItem).capacidad_tipo }}
                                        </td>
                                    </template>

                                    <td class="p-4 text-right">
                                        <div class="flex items-center justify-end gap-1">
                                            <button @click="openModal(item)" class="p-2.5 rounded-xl text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 transition-all cursor-pointer"><Edit class="w-4 h-4" /></button>
                                            <button @click="deleteItem(item.id)" class="p-2.5 rounded-xl text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all cursor-pointer"><Trash2 class="w-4 h-4" /></button>
                                        </div>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Mobile Cards -->
                <div v-else class="space-y-4 pb-8">
                    <div v-if="loading" v-for="n in 3" :key="n" class="bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 animate-pulse">
                        <div class="h-4 w-1/2 bg-slate-200 dark:bg-slate-700 rounded mb-4"></div>
                        <div class="h-3 w-3/4 bg-slate-200 dark:bg-slate-700 rounded mb-2"></div>
                    </div>
                    <div v-else v-for="item in (activeTab === 'grados' ? grados : activeTab === 'capacidades' ? capacidades : desempenos)" :key="item.id" 
                        class="bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-slate-200 dark:border-slate-700 shadow-sm animate-in fade-in slide-in-from-bottom-2 duration-500">
                        <div class="flex justify-between items-start mb-4">
                            <div class="space-y-1">
                                <div class="text-[9px] font-mono font-bold text-slate-400 uppercase">ID #{{ item.id }}</div>
                                <h3 class="font-black text-slate-800 dark:text-white tracking-tight text-lg leading-tight">
                                    {{ activeTab === 'grados' ? (item as Grado).nombre : activeTab === 'capacidades' ? (item as Capacidad).nombre : (item as DesempenoItem).codigo }}
                                </h3>
                            </div>
                            <div class="flex gap-1">
                                <button @click="openModal(item)" class="p-2.5 bg-slate-50 dark:bg-slate-700 rounded-xl text-slate-400 transition-all cursor-pointer"><Edit class="w-4 h-4" /></button>
                                <button @click="deleteItem(item.id)" class="p-2.5 bg-red-50 dark:bg-red-900/20 rounded-xl text-red-400 transition-all cursor-pointer"><Trash2 class="w-4 h-4" /></button>
                            </div>
                        </div>
                        <div v-if="activeTab === 'grados'" class="flex items-center gap-2">
                            <span class="px-3 py-1 bg-teal-50 dark:bg-teal-900/30 text-teal-700 dark:text-teal-400 rounded-lg text-[9px] font-black uppercase tracking-widest">{{ (item as Grado).nivel }}</span>
                            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Grado {{ (item as Grado).numero }}</span>
                        </div>
                        <div v-else-if="activeTab === 'capacidades'">
                            <span class="px-3 py-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-400 rounded-lg text-[9px] font-black uppercase tracking-widest">{{ (item as Capacidad).tipo }}</span>
                        </div>
                        <div v-else class="space-y-3">
                            <p class="text-xs font-bold text-slate-600 dark:text-slate-400 leading-relaxed">{{ (item as DesempenoItem).descripcion }}</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal Form -->
        <Teleport to="body">
            <Transition name="modal">
                <div v-if="showModal" class="fixed inset-0 z-50 flex items-center sm:items-center justify-center items-end bg-slate-900/60 backdrop-blur-sm cursor-pointer" @click.self="showModal = false">
                    <div class="bg-white dark:bg-slate-800 rounded-t-2xl sm:rounded-2xl shadow-2xl w-full max-w-md overflow-hidden relative">
                        <div class="sm:hidden flex justify-center pt-4 pb-1 cursor-pointer" @click="showModal = false"><div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-slate-700"></div></div>
                        <div class="flex items-center justify-between p-6 border-b border-slate-300 dark:border-slate-700">
                            <div class="flex items-center gap-4">
                                <div class="w-10 h-10 rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-lg shadow-teal-500/20">
                                    <component :is="activeTab === 'grados' ? GraduationCap : activeTab === 'capacidades' ? Shield : BookOpen" class="w-5 h-5 text-white" />
                                </div>
                                <div>
                                    <h2 class="text-lg font-black text-slate-800 dark:text-white tracking-tight">
                                        {{ isEditing ? 'Editar' : 'Nuevo' }} {{ activeTab.slice(0, -1) }}
                                    </h2>
                                    <p class="text-xs text-slate-500 font-bold uppercase tracking-widest">Currículo Nacional</p>
                                </div>
                            </div>
                            <button @click="showModal = false" class="p-2 rounded-xl text-slate-400 hover:bg-slate-100 transition-all cursor-pointer"><X class="w-5 h-5" /></button>
                        </div>

                        <div class="p-6 space-y-5 max-h-[70vh] overflow-y-auto custom-scrollbar">
                            <template v-if="activeTab === 'grados'">
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre</label>
                                                                        <input v-model="editItem.nombre" type="text" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all placeholder-slate-400" />

                                </div>
                                <div class="grid grid-cols-2 gap-4">
                                    <div class="space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Número</label>
                                        <input v-model.number="editItem.numero" type="number" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all placeholder-slate-400" />
                                    </div>
                                    <div class="space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nivel</label>
                                        <select v-model="editItem.nivel" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none appearance-none cursor-pointer">
                                            <option value="primaria">Primaria</option>
                                            <option value="secundaria">Secundaria</option>
                                        </select>
                                    </div>
                                </div>
                            </template>

                            <template v-if="activeTab === 'capacidades'">
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Nombre</label>
                                                                        <input v-model="editItem.nombre" type="text" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all placeholder-slate-400" />

                                </div>
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Tipo</label>
                                    <select v-model="editItem.tipo" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none appearance-none cursor-pointer">
                                        <option value="literal">Literal</option>
                                        <option value="inferencial">Inferencial</option>
                                        <option value="critico">Crítico</option>
                                    </select>
                                </div>
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Descripción</label>
                                    <textarea v-model="editItem.descripcion" rows="3" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all placeholder-slate-400"></textarea>
                                </div>
                            </template>

                            <template v-if="activeTab === 'desempenos'">
                                <div class="grid grid-cols-3 gap-4">
                                    <div class="col-span-1 space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Código</label>
                                        <input v-model="editItem.codigo" type="text" placeholder="Ej: 01" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all placeholder-slate-400" />
                                    </div>
                                    <div class="col-span-2 space-y-1.5">
                                        <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Capacidad</label>
                                        <select v-model="editItem.capacidad_id" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none appearance-none cursor-pointer">
                                            <option v-for="c in capacidades" :key="c.id" :value="c.id">{{ c.nombre }} ({{ c.tipo }})</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="space-y-1.5">
                                    <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Descripción</label>
                                    <textarea v-model="editItem.descripcion" rows="4" class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all placeholder-slate-400"></textarea>
                                </div>
                            </template>
                        </div>

                        <div class="p-6 bg-slate-50 dark:bg-slate-900/50 flex flex-col sm:flex-row gap-3">
                            <BaseButton variant="secondary" size="md" class="flex-1" @click="showModal = false">Cancelar</BaseButton>
                            <BaseButton variant="primary" size="md" class="flex-1" @click="saveItem">
                                <template #icon><Save class="w-4 h-4" /></template>
                                Guardar Cambios
                            </BaseButton>
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
.custom-scrollbar::-webkit-scrollbar-track { background: transparent; }
.custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(148, 163, 184, 0.2); border-radius: 10px; }
</style>
