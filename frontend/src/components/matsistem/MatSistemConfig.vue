<script setup lang="ts">
import { computed } from 'vue';
import {
    Signal,
    Sprout,
    Leaf,
    TreeDeciduous,
    Check,
    GraduationCap,
    Target,
    Hash,
    FileUp,
    CloudUpload,
    Loader2,
    FileText,
    X,
    AlertTriangle,
    BookOpen,
    Calculator,
    RefreshCw,
    Shapes,
    BarChart3
} from 'lucide-vue-next';
import ComboBox from '../ComboBox.vue';
import Checkbox from '../Checkbox.vue';
import type { NivelDificultadOption, NivelDificultad } from '../../composables/useMatSistem';
import type { CompetenciaMatematica } from '../../types/matematica';

interface FilesMetadata {
    archivos: { filename: string; palabras: number; caracteres: number }[];
    total_palabras: number;
    total_caracteres: number;
}

const props = defineProps<{
    selectedNivelDificultad: NivelDificultad;
    nivelesDificultad: NivelDificultadOption[];
    selectedGradoId: number | null;
    gradoOptions: { id: number; label: string; group: string }[];
    loadingGrados?: boolean;
    selectedCompetenciaId: number | null;
    competencias: CompetenciaMatematica[];
    cantidadPreguntas: number;
    useTextoBase: boolean;
    contenidoTematico: string;
    selectedFiles: File[];
    filesMetadata: FilesMetadata | null;
    uploadingFile: boolean;
    uploadError: string | null;
}>();

const emit = defineEmits<{
    (e: 'update:selectedNivelDificultad', value: NivelDificultad): void;
    (e: 'update:selectedGradoId', value: number | null): void;
    (e: 'update:selectedCompetenciaId', value: number | null): void;
    (e: 'update:cantidadPreguntas', value: number): void;
    (e: 'update:useTextoBase', value: boolean): void;
    (e: 'update:contenidoTematico', value: string): void;
    (e: 'handleFileUpload', event: Event): void;
    (e: 'clearFiles'): void;
}>();

const localSelectedNivelDificultad = computed({
    get: () => props.selectedNivelDificultad,
    set: (val) => emit('update:selectedNivelDificultad', val)
});

const localSelectedGradoId = computed({
    get: () => props.selectedGradoId,
    set: (val) => emit('update:selectedGradoId', val)
});

const localSelectedCompetenciaId = computed({
    get: () => props.selectedCompetenciaId,
    set: (val) => emit('update:selectedCompetenciaId', val)
});

const localCantidadPreguntas = computed({
    get: () => props.cantidadPreguntas,
    set: (val) => emit('update:cantidadPreguntas', Number(val))
});

const localUseTextoBase = computed({
    get: () => props.useTextoBase,
    set: (val) => emit('update:useTextoBase', val)
});

const localContenidoTematico = computed({
    get: () => props.contenidoTematico,
    set: (val) => emit('update:contenidoTematico', val)
});

// Icon components per competencia
const COMP_ICONS: Record<number, typeof Calculator> = {
    1: Calculator,
    2: RefreshCw,
    3: Shapes,
    4: BarChart3
};

// Visual config for each competencia by codigo
const COMP_VISUAL: Record<number, { shortName: string; gradient: string; gradientSelected: string; border: string; ring: string; text: string; badge: string }> = {
    1: {
        shortName: 'Cantidad',
        gradient: 'from-teal-50 to-emerald-50 dark:from-teal-900/20 dark:to-emerald-900/15',
        gradientSelected: 'from-teal-100 to-emerald-100 dark:from-teal-900/40 dark:to-emerald-900/30',
        border: 'border-teal-400 dark:border-teal-600',
        ring: 'ring-2 ring-teal-200 dark:ring-teal-800',
        text: 'text-teal-700 dark:text-teal-300',
        badge: 'bg-teal-500'
    },
    2: {
        shortName: 'Regularidad y cambio',
        gradient: 'from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/15',
        gradientSelected: 'from-amber-100 to-orange-100 dark:from-amber-900/40 dark:to-orange-900/30',
        border: 'border-amber-400 dark:border-amber-600',
        ring: 'ring-2 ring-amber-200 dark:ring-amber-800',
        text: 'text-amber-700 dark:text-amber-300',
        badge: 'bg-amber-500'
    },
    3: {
        shortName: 'Forma y localización',
        gradient: 'from-violet-50 to-purple-50 dark:from-violet-900/20 dark:to-purple-900/15',
        gradientSelected: 'from-violet-100 to-purple-100 dark:from-violet-900/40 dark:to-purple-900/30',
        border: 'border-violet-400 dark:border-violet-600',
        ring: 'ring-2 ring-violet-200 dark:ring-violet-800',
        text: 'text-violet-700 dark:text-violet-300',
        badge: 'bg-violet-500'
    },
    4: {
        shortName: 'Gestión de datos',
        gradient: 'from-rose-50 to-pink-50 dark:from-rose-900/20 dark:to-pink-900/15',
        gradientSelected: 'from-rose-100 to-pink-100 dark:from-rose-900/40 dark:to-pink-900/30',
        border: 'border-rose-400 dark:border-rose-600',
        ring: 'ring-2 ring-rose-200 dark:ring-rose-800',
        text: 'text-rose-700 dark:text-rose-300',
        badge: 'bg-rose-500'
    }
};

const DEFAULT_COMP_VISUAL = COMP_VISUAL[1]!;
const getCompVisual = (codigo: number) => COMP_VISUAL[codigo] ?? DEFAULT_COMP_VISUAL;
</script>

<template>
    <div class="animate-fadeIn space-y-5 mb-6">

        <!-- === PASO 1: Grado y Competencia (selecciones principales) === -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-indigo-100 dark:border-slate-700 shadow-sm">

            <!-- Section Header -->
            <div class="bg-gradient-to-r from-indigo-500 to-purple-500 px-5 py-3 rounded-t-[calc(1rem-2px)]">
                <h3 class="text-sm font-bold text-white flex items-center gap-2">
                    <GraduationCap class="w-4 h-4" />
                    Grado y Competencia
                </h3>
                <p class="text-xs text-indigo-100 mt-0.5">Selecciona el grado escolar y la competencia a evaluar</p>
            </div>

            <div class="p-5 space-y-5">

                <!-- Grado + Cantidad en fila -->
                <div class="grid sm:grid-cols-2 gap-4">
                    <!-- Grado -->
                    <div>
                        <label class="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-400 mb-2 uppercase tracking-wider">
                            <GraduationCap class="w-3.5 h-3.5 text-indigo-500" />
                            Grado Escolar
                        </label>
                        <div v-if="loadingGrados" class="w-full h-[46px] bg-slate-50 dark:bg-slate-900/50 rounded-xl animate-pulse flex items-center px-4 border-2 border-slate-200/60 dark:border-slate-700/60">
                            <div class="h-4 w-1/3 bg-slate-200 dark:bg-slate-700 rounded"></div>
                        </div>
                        <ComboBox v-else v-model="localSelectedGradoId" :options="gradoOptions" placeholder="Seleccionar grado..." />
                    </div>

                    <!-- Cantidad -->
                    <div>
                        <label class="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-400 mb-2 uppercase tracking-wider">
                            <Hash class="w-3.5 h-3.5 text-indigo-500" />
                            Cantidad de Preguntas
                        </label>
                        <div class="flex items-center gap-3 h-[46px]">
                            <input type="range" v-model="localCantidadPreguntas" min="1" max="10"
                                class="flex-1 h-2 bg-slate-200 dark:bg-slate-700 rounded-full appearance-none cursor-pointer accent-indigo-600" />
                            <span class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-lg font-bold text-white shadow-lg shadow-indigo-500/30">
                                {{ localCantidadPreguntas }}
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Competencia - Tarjetas visuales -->
                <div>
                    <label class="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-400 mb-3 uppercase tracking-wider">
                        <Target class="w-3.5 h-3.5 text-indigo-500" />
                        Competencia Matemática
                    </label>
                    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
                        <button
                            v-for="comp in competencias"
                            :key="comp.id"
                            @click="localSelectedCompetenciaId = comp.id"
                            class="relative p-4 rounded-xl border-2 transition-all duration-300 text-left group"
                            :class="localSelectedCompetenciaId === comp.id
                                ? `bg-gradient-to-br ${getCompVisual(comp.codigo).gradientSelected} ${getCompVisual(comp.codigo).border} ${getCompVisual(comp.codigo).ring} shadow-md`
                                : 'bg-white dark:bg-slate-900 border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600 hover:shadow-sm'">

                            <!-- Badge C1-C4 -->
                            <div class="flex items-center gap-2 mb-2">
                                <div class="w-7 h-7 rounded-lg flex items-center justify-center"
                                    :class="localSelectedCompetenciaId === comp.id
                                        ? getCompVisual(comp.codigo).badge + ' text-white'
                                        : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'">
                                    <component :is="COMP_ICONS[comp.codigo]" class="w-4 h-4" />
                                </div>
                                <span class="text-xs font-black px-2 py-0.5 rounded-md text-white"
                                    :class="getCompVisual(comp.codigo).badge">
                                    C{{ comp.codigo }}
                                </span>
                            </div>

                            <!-- Short name -->
                            <span class="block text-sm font-bold leading-tight"
                                :class="localSelectedCompetenciaId === comp.id
                                    ? getCompVisual(comp.codigo).text
                                    : 'text-slate-700 dark:text-slate-300'">
                                {{ getCompVisual(comp.codigo).shortName }}
                            </span>

                            <!-- Full name (smaller) -->
                            <span class="block text-[10px] mt-1.5 leading-tight"
                                :class="localSelectedCompetenciaId === comp.id
                                    ? getCompVisual(comp.codigo).text + ' opacity-80'
                                    : 'text-slate-400 dark:text-slate-500'">
                                {{ comp.nombre }}
                            </span>

                            <!-- Check indicator -->
                            <div v-if="localSelectedCompetenciaId === comp.id"
                                class="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center text-white"
                                :class="getCompVisual(comp.codigo).badge">
                                <Check class="w-3 h-3" />
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        </div>

        <!-- === PASO 2: Opciones del examen (secundarias) === -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-100 dark:border-slate-700 shadow-sm">

            <!-- Section Header -->
            <div class="bg-gradient-to-r from-slate-500 to-slate-600 dark:from-slate-600 dark:to-slate-700 px-5 py-3 rounded-t-[calc(1rem-2px)]">
                <h3 class="text-sm font-bold text-white flex items-center gap-2">
                    <Signal class="w-4 h-4" />
                    Opciones del Examen
                </h3>
                <p class="text-xs text-slate-200 mt-0.5">Dificultad, tema y situación problemática base</p>
            </div>

            <div class="p-5 space-y-5">

                <!-- Nivel de Dificultad -->
                <div>
                    <label class="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-400 mb-3 uppercase tracking-wider">
                        <Signal class="w-3.5 h-3.5 text-violet-500" />
                        Nivel de Dificultad
                    </label>
                    <div class="grid grid-cols-3 gap-3">
                        <button v-for="nivel in nivelesDificultad" :key="nivel.id"
                            @click="localSelectedNivelDificultad = nivel.id"
                            class="relative p-3 sm:p-4 rounded-xl border-2 transition-all duration-300 text-center" :class="localSelectedNivelDificultad === nivel.id
                                ? nivel.id === 'basico'
                                    ? 'bg-gradient-to-br from-emerald-50 to-green-50 dark:from-emerald-900/30 dark:to-green-900/20 border-emerald-400 dark:border-emerald-600 ring-2 ring-emerald-200 dark:ring-emerald-800'
                                    : nivel.id === 'intermedio'
                                        ? 'bg-gradient-to-br from-amber-50 to-orange-50 dark:from-amber-900/30 dark:to-orange-900/20 border-amber-400 dark:border-amber-600 ring-2 ring-amber-200 dark:ring-amber-800'
                                        : 'bg-gradient-to-br from-red-50 to-rose-50 dark:from-red-900/30 dark:to-rose-900/20 border-red-400 dark:border-red-600 ring-2 ring-red-200 dark:ring-red-800'
                                : 'bg-gray-50 dark:bg-slate-900 border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600'
                                ">
                            <div class="mb-1.5 flex justify-center">
                                <Sprout v-if="nivel.icono === 'Sprout'" class="w-7 h-7"
                                    :class="localSelectedNivelDificultad === nivel.id ? 'text-emerald-500' : 'text-slate-400'" />
                                <Leaf v-else-if="nivel.icono === 'Leaf'" class="w-7 h-7"
                                    :class="localSelectedNivelDificultad === nivel.id ? 'text-amber-500' : 'text-slate-400'" />
                                <TreeDeciduous v-else class="w-7 h-7"
                                    :class="localSelectedNivelDificultad === nivel.id ? 'text-red-500' : 'text-slate-400'" />
                            </div>
                            <span class="font-bold text-sm block" :class="localSelectedNivelDificultad === nivel.id
                                ? nivel.id === 'basico'
                                    ? 'text-emerald-700 dark:text-emerald-400'
                                    : nivel.id === 'intermedio'
                                        ? 'text-amber-700 dark:text-amber-400'
                                        : 'text-red-700 dark:text-red-400'
                                : 'text-slate-600 dark:text-slate-400'
                                ">
                                {{ nivel.nombre }}
                            </span>
                            <span class="text-[11px] text-slate-500 dark:text-slate-500 mt-0.5 block hidden sm:block">
                                {{ nivel.descripcion }}
                            </span>
                            <div v-if="localSelectedNivelDificultad === nivel.id"
                                class="absolute top-2 right-2 w-4 h-4 rounded-full flex items-center justify-center" :class="nivel.id === 'basico'
                                    ? 'bg-emerald-500'
                                    : nivel.id === 'intermedio'
                                        ? 'bg-amber-500'
                                        : 'bg-red-500'
                                    ">
                                <Check class="w-2.5 h-2.5 text-white" />
                            </div>
                        </button>
                    </div>
                </div>

                <!-- Contenido Temático + Problema Base en fila -->
                <div class="grid sm:grid-cols-2 gap-4">
                    <!-- Contenido Temático -->
                    <div>
                        <label class="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-400 mb-2 uppercase tracking-wider">
                            <BookOpen class="w-3.5 h-3.5 text-teal-500" />
                            Contenido Temático
                            <span class="text-slate-400 font-normal normal-case">(opcional)</span>
                        </label>
                        <input
                            type="text"
                            v-model="localContenidoTematico"
                            placeholder="Ej: fracciones, geometría plana..."
                            class="w-full px-4 py-2.5 rounded-xl border-2 border-slate-200 dark:border-slate-600 bg-slate-50 dark:bg-slate-900 text-slate-800 dark:text-slate-100 text-sm focus:outline-none focus:border-teal-400 dark:focus:border-teal-500 transition-colors"
                        />
                    </div>

                    <!-- Problema Base -->
                    <div>
                        <Checkbox v-model="localUseTextoBase" class="items-center mb-2">
                            <span class="flex items-center gap-2 text-xs font-bold text-slate-600 dark:text-slate-400 uppercase tracking-wider">
                                <FileUp class="w-3.5 h-3.5 text-sky-500" />
                                Usar Problema Base
                            </span>
                        </Checkbox>

                        <div v-if="localUseTextoBase" class="space-y-2">
                            <div v-if="selectedFiles.length === 0 && !uploadingFile" class="relative">
                                <input type="file" accept=".pdf,.docx,.doc" multiple
                                    @change="(e) => emit('handleFileUpload', e)"
                                    class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" />
                                <div class="flex items-center justify-center py-3 px-3 bg-gradient-to-br from-sky-50 to-teal-50 dark:from-slate-900 dark:to-slate-950 border-2 border-dashed border-sky-300 dark:border-slate-600 rounded-xl hover:border-teal-400 transition-all duration-300">
                                    <div class="text-center">
                                        <CloudUpload class="w-5 h-5 text-teal-500 mx-auto mb-1" />
                                        <span class="text-teal-600 dark:text-slate-400 text-xs font-medium">PDF o Word</span>
                                    </div>
                                </div>
                            </div>

                            <div v-if="uploadingFile"
                                class="flex items-center justify-center gap-2 py-3 bg-teal-50 dark:bg-slate-900 rounded-xl">
                                <Loader2 class="w-5 h-5 text-teal-600 animate-spin" />
                                <span class="text-teal-600 dark:text-teal-400 text-sm font-medium">Procesando...</span>
                            </div>

                            <div v-if="selectedFiles.length > 0 && !uploadingFile && filesMetadata" class="space-y-2">
                                <div v-for="(archivo, index) in filesMetadata.archivos" :key="index"
                                    class="flex items-center gap-2 p-2.5 bg-gradient-to-r from-teal-50 to-emerald-50 dark:bg-emerald-900/20 border-2 border-teal-200 dark:border-emerald-800 rounded-xl text-xs">
                                    <FileText class="w-4 h-4 text-teal-600 dark:text-emerald-400 flex-shrink-0" />
                                    <span class="flex-1 truncate text-slate-700 dark:text-slate-200 font-medium">{{ archivo.filename }}</span>
                                    <span class="text-teal-600 font-bold bg-teal-100 px-2 py-0.5 rounded-full text-[10px]">{{ archivo.palabras }}p</span>
                                </div>
                                <button @click="emit('clearFiles')"
                                    class="text-xs text-red-500 hover:text-red-600 flex items-center gap-1 font-medium">
                                    <X class="w-3 h-3" /> Quitar
                                </button>
                            </div>

                            <div v-if="uploadError"
                                class="p-2.5 bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800 rounded-xl">
                                <p class="text-red-600 dark:text-red-400 text-xs flex items-center gap-1 font-medium">
                                    <AlertTriangle class="w-3.5 h-3.5" />
                                    {{ uploadError }}
                                </p>
                            </div>
                        </div>

                        <p v-else class="text-slate-400 dark:text-slate-500 text-xs mt-1">
                            Sube un PDF o Word con una situación problemática
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
