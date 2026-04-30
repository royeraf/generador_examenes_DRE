<script setup lang="ts">
import { GraduationCap, Eye, EyeOff, Bot } from 'lucide-vue-next';
import logoDre from '../../assets/logo.png';
import UserBadge from './UserBadge.vue';

interface Props {
    title: string;
    subtitle: string;
    showResults?: boolean;
    hasResultado?: boolean;
    loading?: boolean;
    activeTab?: string;
    gradientClass?: string;
    subtitleClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
    showResults: false,
    hasResultado: false,
    loading: false,
    activeTab: 'generador',
    gradientClass: 'from-teal-600 via-teal-500 to-sky-500 shadow-teal-500/20',
    subtitleClass: 'text-teal-100 dark:text-slate-400',
});

const emit = defineEmits(['toggleTheme', 'toggleResults']);
</script>

<template>
    <header :class="[
        'bg-gradient-to-r dark:from-slate-800 dark:via-slate-800 dark:to-slate-800 border-b border-white/20 dark:border-slate-700 sticky top-0 z-50 shadow-lg dark:shadow-none transition-all duration-300',
        gradientClass,
    ]">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
            <div class="flex items-center justify-between gap-3">

                <!-- Izquierda: Logo + Título -->
                <div class="flex items-center gap-3 min-w-0">
                    <div class="w-10 h-10 sm:w-12 sm:h-12 bg-white/90 rounded-xl flex items-center justify-center shadow-md border border-white/30 p-1 flex-shrink-0">
                        <img :src="logoDre" alt="Logo DRE" class="w-full h-full object-contain" />
                    </div>
                    <div class="min-w-0">
                        <h1 class="text-base sm:text-xl font-bold text-white tracking-tight flex items-center gap-2 truncate">
                            {{ title }}
                            <Bot class="w-5 h-5 sm:w-6 sm:h-6 text-teal-100 dark:text-sky-300 animate-robot flex-shrink-0" />
                        </h1>
                        <p :class="['text-[10px] sm:text-xs font-medium flex items-center gap-1 truncate', subtitleClass]">
                            <GraduationCap class="w-3 h-3 flex-shrink-0" />
                            <span class="truncate">{{ subtitle }}</span>
                        </p>
                    </div>
                </div>

                <!-- Derecha: Acciones -->
                <div class="flex items-center gap-2 sm:gap-3 flex-shrink-0">
                    <slot name="actions-before"></slot>

                    <div class="flex items-center gap-2">
                        <button v-if="hasResultado && !loading && activeTab === 'generador'" @click="emit('toggleResults')"
                            class="px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg sm:rounded-xl font-medium text-[10px] sm:text-sm flex items-center gap-1.5 transition-all duration-300 bg-white/20 text-white border border-white/30 hover:bg-white/30">
                            <Eye v-if="showResults" class="w-3.5 h-3.5" />
                            <EyeOff v-else class="w-3.5 h-3.5" />
                            <span class="hidden sm:inline">{{ showResults ? 'Ocultar' : 'Ver Resultado' }}</span>
                        </button>
                    </div>

                    <div class="hidden sm:block w-px h-8 bg-white/30 dark:bg-slate-600 mx-0.5"></div>

                    <UserBadge />

                    <slot name="actions-after"></slot>
                </div>

            </div>
        </div>
    </header>
</template>

<style scoped>
@keyframes robot-float {
  0%, 100% {
    transform: translateY(0) rotate(0deg) scale(1);
    filter: drop-shadow(0 0 2px rgba(255, 255, 255, 0.2));
    color: currentColor;
  }
  25% {
    transform: translateY(-2px) rotate(-8deg) scale(1.1);
    filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.8));
    color: #fff;
  }
  75% {
    transform: translateY(-2px) rotate(8deg) scale(1.1);
    filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.8));
    color: #fff;
  }
}

.animate-robot {
  animation: robot-float 4s ease-in-out infinite;
  transform-origin: center bottom;
}
</style>
