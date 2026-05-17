<script setup lang="ts">
import { GraduationCap } from 'lucide-vue-next';
import logoDre from '../../assets/logo.png';
import UserBadge from './UserBadge.vue';

interface Props {
    title: string;
    subtitle?: string;
    // Mantenidos por compatibilidad, ya no afectan el estilo visual
    showResults?: boolean;
    hasResultado?: boolean;
    loading?: boolean;
    activeTab?: string;
    gradientClass?: string;
    subtitleClass?: string;
}

withDefaults(defineProps<Props>(), {
    subtitle: '',
    showResults: false,
    hasResultado: false,
    loading: false,
    activeTab: 'generador',
    gradientClass: '',
    subtitleClass: '',
});

defineEmits(['toggleTheme', 'toggleResults']);
</script>

<template>
    <header class="sticky top-0 z-50 bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm border-b border-slate-200/80 dark:border-slate-800 transition-colors duration-300">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">

            <!-- Izquierda: Logo + Título -->
            <div class="flex items-center gap-3 min-w-0">
                <div class="relative w-8 h-8 shrink-0">
                    <div class="absolute -inset-0.5 bg-gradient-to-r from-teal-500 to-indigo-600 rounded-lg blur opacity-20"></div>
                    <div class="absolute inset-0 flex items-center justify-center p-1.5 bg-white dark:bg-slate-800 rounded-lg border border-slate-100 dark:border-slate-700 overflow-hidden">
                        <GraduationCap class="absolute w-4 h-4 text-teal-600 dark:text-teal-400 animate-logo-cycle-1" />
                        <div class="absolute logo-gradient-display-static w-4 h-4 animate-logo-cycle-2"
                            :style="{ 'mask-image': `url(${logoDre})`, '-webkit-mask-image': `url(${logoDre})` }"></div>
                    </div>
                </div>
                <div class="min-w-0">
                    <h1 class="text-sm font-bold text-slate-800 dark:text-white tracking-tight truncate">
                        {{ title }}
                    </h1>
                    <p v-if="subtitle" class="text-[10px] text-slate-400 dark:text-slate-500 truncate leading-tight">
                        {{ subtitle }}
                    </p>
                </div>
            </div>

            <!-- Derecha: Acciones -->
            <div class="flex items-center gap-2 shrink-0">
                <slot name="actions-before"></slot>
                <UserBadge />
                <slot name="actions-after"></slot>
            </div>

        </div>
    </header>
</template>

<style scoped>
@keyframes logoCycle1 {
    0%, 42%  { opacity: 1; transform: scale(1) rotate(0deg); }
    48%, 92% { opacity: 0; transform: scale(0.5) rotate(-15deg); }
    98%, 100%{ opacity: 1; transform: scale(1) rotate(0deg); }
}
@keyframes logoCycle2 {
    0%, 42%  { opacity: 0; transform: scale(0.5) rotate(15deg); }
    48%, 92% { opacity: 1; transform: scale(1) rotate(0deg); }
    98%, 100%{ opacity: 0; transform: scale(0.5) rotate(-15deg); }
}
.animate-logo-cycle-1 { animation: logoCycle1 10s infinite; }
.animate-logo-cycle-2 { animation: logoCycle2 10s infinite; }

.logo-gradient-display-static {
    background: linear-gradient(135deg, #14b8a6, #4f46e5);
    mask-size: contain; -webkit-mask-size: contain;
    mask-repeat: no-repeat; -webkit-mask-repeat: no-repeat;
    mask-position: center; -webkit-mask-position: center;
}
.dark .logo-gradient-display-static {
    background: linear-gradient(135deg, #5eead4, #818cf8);
}
</style>
