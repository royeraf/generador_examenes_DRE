<script setup lang="ts">
import { Sun, Moon, Star, GraduationCap, Eye, EyeOff } from 'lucide-vue-next';
import logoDre from '../assets/logo.png';
import mascotaLectosistem from '../assets/mascota_lectosistem.png';

interface Props {
    title: string;
    subtitle: string;
    version?: string;
    isDark: boolean;
    showResults?: boolean;
    hasResultado?: boolean;
    loading?: boolean;
    activeTab?: string;
    gradientClass?: string;
    versionBadgeClass?: string;
    subtitleClass?: string;
    mascotaBubbleClass?: string;
    mascotaTextClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
    version: 'DRE',
    showResults: false,
    hasResultado: false,
    loading: false,
    activeTab: 'generador',
    gradientClass: 'from-teal-600 via-teal-500 to-sky-500 shadow-teal-500/20',
    versionBadgeClass: 'bg-amber-400 text-amber-900',
    subtitleClass: 'text-teal-100 dark:text-slate-400',
    mascotaBubbleClass: 'border-amber-300 dark:border-amber-500',
    mascotaTextClass: 'text-amber-600 dark:text-amber-400'
});

const emit = defineEmits(['toggleTheme', 'toggleResults']);
</script>

<template>
    <header :class="[
        'bg-gradient-to-r dark:from-slate-800 dark:via-slate-800 dark:to-slate-800 border-b dark:border-slate-700 sticky top-0 z-50 shadow-lg dark:shadow-none transition-all duration-300',
        gradientClass,
        'border-white/20'
    ]">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
            <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2 sm:gap-4">
                    <!-- Logo con icono de libro -->
                    <div class="relative flex-shrink-0">
                        <div
                            class="w-10 h-10 sm:w-14 sm:h-14 bg-white/90 backdrop-blur-sm rounded-xl sm:rounded-2xl flex items-center justify-center shadow-lg border border-white/30 p-1">
                            <img :src="logoDre" alt="Logo DRE" class="w-full h-full object-contain" />
                        </div>
                        <!-- Estrella decorativa -->
                        <div
                            class="absolute -top-1 -right-1 w-4 h-4 sm:w-5 sm:h-5 bg-amber-400 rounded-full flex items-center justify-center shadow-md animate-pulse">
                            <Star class="w-2 h-2 sm:w-3 sm:h-3 text-white fill-white" />
                        </div>
                    </div>
                    <div class="min-w-0">
                        <h1
                            class="text-lg sm:text-2xl font-bold text-white tracking-tight flex items-center gap-2 truncate">
                            {{ title }}
                            <span
                                :class="['text-[10px] sm:text-xs px-2 py-0.5 rounded-full font-semibold', versionBadgeClass]">
                                {{ version }}
                            </span>
                        </h1>
                        <p
                            :class="['text-[10px] sm:text-sm font-medium flex items-center gap-1 truncate', subtitleClass]">
                            <GraduationCap class="w-3 h-3 sm:w-4 sm:h-4" />
                            <span class="truncate">{{ subtitle }}</span>
                        </p>
                    </div>
                </div>

                <!-- Mascot (Optional) -->
                <div class="hidden md:flex items-center">
                    <div class="relative group">
                        <img :src="mascotaLectosistem" alt="Mascota"
                            class="h-16 w-auto object-contain drop-shadow-lg transition-all duration-500 group-hover:scale-110 group-hover:drop-shadow-2xl animate-mascota-float" />
                        <!-- Burbuja de diálogo -->
                        <div
                            class="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100 transition-all duration-300 transform group-hover:translate-y-0 translate-y-2">
                            <div
                                :class="['bg-white dark:bg-slate-700 rounded-full px-2 py-1 shadow-lg border-2', mascotaBubbleClass]">
                                <span :class="['text-[10px] font-bold whitespace-nowrap', mascotaTextClass]">¡Hola!
                                    👋</span>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="flex items-center gap-2 sm:gap-3">
                    <!-- Right Actions Slot -->
                    <slot name="actions-before"></slot>

                    <button v-if="hasResultado && !loading && activeTab === 'generador'" @click="emit('toggleResults')"
                        class="px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg sm:rounded-xl font-medium text-[10px] sm:text-sm flex items-center gap-1.5 sm:gap-2 transition-all duration-300 bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30">
                        <Eye v-if="showResults" class="w-3 h-3 sm:w-4 sm:h-4" />
                        <EyeOff v-else class="w-3 h-3 sm:w-4 sm:h-4" />
                        <span class="hidden sm:inline">{{ showResults ? 'Ocultar' : 'Ver Resultado' }}</span>
                        <span class="sm:hidden">{{ showResults ? 'Cerrar' : 'Ver' }}</span>
                    </button>

                    <button @click="emit('toggleTheme')"
                        class="p-2.5 rounded-xl bg-white/20 backdrop-blur-sm text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300">
                        <Sun v-if="isDark" class="w-5 h-5" />
                        <Moon v-else class="w-5 h-5" />
                    </button>

                    <slot name="actions-after"></slot>
                </div>
            </div>
        </div>
    </header>
</template>

<style scoped>
@keyframes float {

    0%,
    100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-10px);
    }
}

.animate-mascota-float {
    animation: float 3s ease-in-out infinite;
}
</style>
