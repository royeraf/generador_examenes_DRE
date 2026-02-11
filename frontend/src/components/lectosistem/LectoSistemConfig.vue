<script setup lang="ts">
import { computed } from 'vue';
import { Signal, Sprout, Leaf, TreeDeciduous, Check, GraduationCap, Hash, FileUp, CloudUpload, Loader2, FileText, X, AlertTriangle, BookOpen, LayoutGrid } from 'lucide-vue-next';
import ComboBox from '../ComboBox.vue';
import Checkbox from '../Checkbox.vue';
import type { NivelDificultadOption } from '../../composables/useLectoSistem';

// Define Props
interface FilesMetadata {
    archivos: { filename: string; palabras: number; caracteres: number }[];
    total_palabras: number;
    total_caracteres: number;
}

const props = defineProps<{
    nivelesDificultad: NivelDificultadOption[];
    modeloNivelDificultad: string;
    gradoOptions: { id: number; label: string; group: string }[];
    modeloGradoId: number | null;
    modeloCantidadPreguntas: number;
    modeloUseTextoBase: boolean;
    selectedFiles: File[];
    filesMetadata: FilesMetadata | null;
    uploadingFile: boolean;
    uploadError: string | null;
    // New props for textual diversity
    tipoTextualOptions?: { id: string; label: string }[];
    modeloTipoTextual?: string | null;
    formatoTextualOptions?: { id: string; label: string }[];
    modeloFormatoTextual?: string | null;
}>();

// Define Emits
const emit = defineEmits<{
    (e: 'update:modeloNivelDificultad', value: string): void;
    (e: 'update:modeloGradoId', value: number | null): void;
    (e: 'update:modeloCantidadPreguntas', value: number): void;
    (e: 'update:modeloUseTextoBase', value: boolean): void;
    (e: 'file-upload', event: Event): void;
    (e: 'clear-files'): void;
    (e: 'update:modeloTipoTextual', value: string | null): void;
    (e: 'update:modeloFormatoTextual', value: string | null): void;
}>();

// Computed for v-models
const selectedNivelDificultad = computed({
    get: () => props.modeloNivelDificultad,
    set: (val) => emit('update:modeloNivelDificultad', val)
});

const selectedGradoId = computed({
    get: () => props.modeloGradoId,
    set: (val) => emit('update:modeloGradoId', val)
});

const quantity = computed({
    get: () => props.modeloCantidadPreguntas,
    set: (val) => emit('update:modeloCantidadPreguntas', val)
});

const useTextoBase = computed({
    get: () => props.modeloUseTextoBase,
    set: (val) => emit('update:modeloUseTextoBase', val)
});

const selectedTipoTextual = computed({
    get: () => props.modeloTipoTextual ?? null,
    set: (val) => emit('update:modeloTipoTextual', val)
});

const selectedFormatoTextual = computed({
    get: () => props.modeloFormatoTextual ?? null,
    set: (val) => emit('update:modeloFormatoTextual', val)
});
</script>

<template>
    <div class="mb-6">
        <!-- Nivel de Dificultad Selector -->
        <div class="mb-6">
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-violet-100 dark:border-slate-700 shadow-sm">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-4">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-violet-400 to-purple-600 rounded-lg flex items-center justify-center">
                        <Signal class="w-4 h-4 text-white" />
                    </div>
                    Nivel de Dificultad
                </label>
                <div class="grid grid-cols-3 gap-3">
                    <button v-for="nivel in nivelesDificultad" :key="nivel.id"
                        @click="selectedNivelDificultad = nivel.id"
                        class="relative p-4 rounded-xl border-2 transition-all duration-300 text-center" :class="selectedNivelDificultad === nivel.id
                            ? nivel.id === 'basico'
                                ? 'bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/30 dark:to-green-900/20 border-emerald-400 dark:border-emerald-600 ring-2 ring-emerald-200 dark:ring-emerald-800'
                                : nivel.id === 'intermedio'
                                    ? 'bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/20 border-amber-400 dark:border-amber-600 ring-2 ring-amber-200 dark:ring-amber-800'
                                    : 'bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/20 border-red-400 dark:border-red-600 ring-2 ring-red-200 dark:ring-red-800'
                            : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600'
                            ">
                        <div class="mb-2 flex justify-center">
                            <Sprout v-if="nivel.icono === 'Sprout'" class="w-8 h-8"
                                :class="selectedNivelDificultad === nivel.id ? 'text-emerald-500' : 'text-slate-400'" />
                            <Leaf v-else-if="nivel.icono === 'Leaf'" class="w-8 h-8"
                                :class="selectedNivelDificultad === nivel.id ? 'text-amber-500' : 'text-slate-400'" />
                            <TreeDeciduous v-else class="w-8 h-8"
                                :class="selectedNivelDificultad === nivel.id ? 'text-red-500' : 'text-slate-400'" />
                        </div>
                        <span class="font-bold text-sm block" :class="selectedNivelDificultad === nivel.id
                            ? nivel.id === 'basico'
                                ? 'text-emerald-700 dark:text-emerald-400'
                                : nivel.id === 'intermedio'
                                    ? 'text-amber-700 dark:text-amber-400'
                                    : 'text-red-700 dark:text-red-400'
                            : 'text-slate-600 dark:text-slate-400'
                            ">
                            {{ nivel.nombre }}
                        </span>
                        <span class="text-xs text-slate-500 dark:text-slate-500 mt-1 block">
                            {{ nivel.descripcion }}
                        </span>
                        <div v-if="selectedNivelDificultad === nivel.id"
                            class="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center" :class="nivel.id === 'basico'
                                ? 'bg-emerald-500'
                                : nivel.id === 'intermedio'
                                    ? 'bg-amber-500'
                                    : 'bg-red-500'
                                ">
                            <Check class="w-3 h-3 text-white" />
                        </div>
                    </button>
                </div>
            </div>
        </div>



        <!-- Textual Diversity Selector -->
        <div class="grid md:grid-cols-2 gap-4 mb-6" v-if="tipoTextualOptions && formatoTextualOptions">
            <!-- Tipo Textual -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-indigo-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-300">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-indigo-400 to-indigo-600 rounded-lg flex items-center justify-center">
                        <FileText class="w-4 h-4 text-white" />
                    </div>
                    Tipo Textual
                    <span class="text-xs font-normal text-slate-400 ml-auto">(Opcional)</span>
                </label>
                <ComboBox v-model="selectedTipoTextual" :options="tipoTextualOptions"
                    placeholder="Seleccionar tipo..." />
            </div>

            <!-- Formato Textual -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-pink-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-pink-200 transition-all duration-300">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-pink-400 to-pink-600 rounded-lg flex items-center justify-center">
                        <LayoutGrid class="w-4 h-4 text-white" />
                    </div>
                    Formato Textual
                    <span class="text-xs font-normal text-slate-400 ml-auto">(Opcional)</span>
                </label>
                <ComboBox v-model="selectedFormatoTextual" :options="formatoTextualOptions"
                    placeholder="Seleccionar formato..." />
            </div>
        </div>

        <div class="grid md:grid-cols-3 gap-4 mb-6">
            <!-- Grade Selection -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-teal-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-teal-200 transition-all duration-300">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-teal-400 to-teal-600 rounded-lg flex items-center justify-center">
                        <GraduationCap class="w-4 h-4 text-white" />
                    </div>
                    Grado Escolar
                </label>
                <ComboBox v-model="selectedGradoId" :options="gradoOptions" placeholder="Seleccionar grado..." />
            </div>

            <!-- Quantity -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-amber-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-amber-200 transition-all duration-300">
                <label class="flex items-center gap-2 text-sm font-bold text-slate-700 dark:text-slate-300 mb-3">
                    <div
                        class="w-8 h-8 bg-gradient-to-br from-amber-400 to-amber-600 rounded-lg flex items-center justify-center">
                        <Hash class="w-4 h-4 text-white" />
                    </div>
                    Cantidad de Preguntas
                </label>
                <div class="flex items-center gap-4">
                    <input type="range" v-model="quantity" min="1" max="10"
                        class="flex-1 h-3 bg-gradient-to-r from-teal-100 to-amber-100 dark:bg-slate-700 rounded-full appearance-none cursor-pointer accent-teal-600" />
                    <span
                        class="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 flex items-center justify-center text-xl font-bold text-white shadow-lg shadow-teal-500/30">
                        {{ quantity }}
                    </span>
                </div>
            </div>

            <!-- File Upload -->
            <div
                class="bg-white dark:bg-slate-800 rounded-2xl p-5 border-2 border-sky-100 dark:border-slate-700 shadow-sm hover:shadow-md hover:border-sky-200 transition-all duration-300">
                <Checkbox v-model="useTextoBase" class="items-center mb-3">
                    <div class="flex items-center gap-2">
                        <div
                            class="w-8 h-8 bg-gradient-to-br from-sky-400 to-sky-600 rounded-lg flex items-center justify-center">
                            <FileUp class="w-4 h-4 text-white" />
                        </div>
                        <span class="text-sm font-bold text-slate-700 dark:text-slate-300">Usar Texto Base</span>
                    </div>
                </Checkbox>

                <div v-if="useTextoBase" class="space-y-2">
                    <div v-if="selectedFiles.length === 0 && !uploadingFile" class="relative">
                        <input type="file" accept=".pdf,.docx,.doc" multiple @change="(e) => emit('file-upload', e)"
                            class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                        <div
                            class="flex items-center justify-center py-4 px-3 bg-gradient-to-br from-sky-50 to-teal-50 dark:bg-slate-900 border-2 border-dashed border-sky-300 dark:border-slate-600 rounded-xl hover:border-teal-400 hover:bg-teal-50 transition-all duration-300">
                            <div class="text-center">
                                <CloudUpload class="w-6 h-6 text-teal-500 mx-auto mb-1" />
                                <span class="text-teal-600 dark:text-slate-400 text-xs font-medium">📄 PDF o Word</span>
                            </div>
                        </div>
                    </div>

                    <div v-if="uploadingFile"
                        class="flex items-center justify-center gap-2 py-4 bg-teal-50 dark:bg-slate-900 rounded-xl">
                        <Loader2 class="w-5 h-5 text-teal-600 animate-spin" />
                        <span class="text-teal-600 dark:text-teal-400 text-sm font-medium">Procesando...</span>
                    </div>

                    <div v-if="selectedFiles.length > 0 && !uploadingFile && filesMetadata" class="space-y-2">
                        <div v-for="(archivo, index) in filesMetadata.archivos" :key="index"
                            class="flex items-center gap-2 p-3 bg-gradient-to-r from-teal-50 to-emerald-50 dark:bg-emerald-900/20 border-2 border-teal-200 dark:border-emerald-800 rounded-xl text-xs">
                            <FileText class="w-5 h-5 text-teal-600 dark:text-emerald-400" />
                            <span class="flex-1 truncate text-slate-700 dark:text-slate-200 font-medium">{{
                                archivo.filename }}</span>
                            <span class="text-teal-600 font-bold bg-teal-100 px-2 py-0.5 rounded-full">{{
                                archivo.palabras }}p</span>
                        </div>
                        <button @click="emit('clear-files')"
                            class="text-xs text-red-500 hover:text-red-600 flex items-center gap-1 font-medium">
                            <X class="w-3 h-3" /> Quitar archivo
                        </button>
                    </div>

                    <div v-if="uploadError"
                        class="p-3 bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl">
                        <p class="text-red-600 dark:text-red-400 text-xs flex items-center gap-1 font-medium">
                            <AlertTriangle class="w-4 h-4" />
                            {{ uploadError }}
                        </p>
                    </div>
                </div>

                <p v-else class="text-slate-400 dark:text-slate-500 text-xs mt-2 flex items-center gap-1">
                    <BookOpen class="w-3 h-3" /> Activa para usar lectura personalizada
                </p>
            </div>
        </div>
    </div>
</template>
