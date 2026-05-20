<script setup lang="ts">
import { GraduationCap, Home } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import logoDre from '../../assets/logo.png';
import UserBadge from './UserBadge.vue';

interface Props {
  title: string;
  subtitle?: string;
  showHome?: boolean;
}

withDefaults(defineProps<Props>(), {
  subtitle: '',
  showHome: false,
});

const router = useRouter();
</script>

<template>
  <header class="sticky top-0 z-50 h-14 flex items-center justify-between px-4 sm:px-6 gap-3
    bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm
    border-b border-slate-300/80 dark:border-slate-800
    transition-colors duration-300">

    <!-- Izquierda: Logo + Título -->
    <div class="flex items-center gap-3 shrink-0">
      <div class="relative w-8 h-8 shrink-0">
        <div class="absolute -inset-0.5 bg-gradient-to-r from-teal-500 to-indigo-600 rounded-lg blur opacity-20"></div>
        <div class="absolute inset-0 flex items-center justify-center p-1.5 bg-white dark:bg-slate-800
          rounded-lg border border-slate-300 dark:border-slate-700 overflow-hidden">
          <GraduationCap class="absolute w-4 h-4 text-teal-600 dark:text-teal-400 nav-logo-1" />
          <div class="absolute nav-logo-img w-4 h-4 nav-logo-2"
            :style="{ 'mask-image': `url(${logoDre})`, '-webkit-mask-image': `url(${logoDre})` }"></div>
        </div>
      </div>
      <div class="hidden sm:block min-w-0">
        <h1 class="text-sm font-bold text-slate-800 dark:text-white tracking-tight truncate">{{ title }}</h1>
        <p v-if="subtitle" class="text-[10px] text-slate-400 dark:text-slate-500 truncate leading-tight">{{ subtitle }}</p>
      </div>
    </div>

    <!-- Centro: slot para tabs u otro contenido -->
    <div class="flex-1 flex justify-center min-w-0 overflow-hidden">
      <slot name="center" />
    </div>

    <!-- Derecha: acciones + UserBadge -->
    <div class="flex items-center gap-2 shrink-0">
      <slot name="actions" />
      <button v-if="showHome" @click="router.push('/')"
        class="p-2 sm:px-3 sm:py-1.5 rounded-full bg-slate-200/60 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700
          border border-slate-300 dark:border-slate-700 transition-colors
          text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5"
        title="Inicio">
        <Home class="w-3.5 h-3.5" />
        <span class="hidden sm:inline">Inicio</span>
      </button>
      <UserBadge />
    </div>

  </header>
</template>

<style scoped>
@keyframes navLogoCycle1 {
  0%, 42%  { opacity: 1; transform: scale(1) rotate(0deg); }
  48%, 92% { opacity: 0; transform: scale(0.5) rotate(-15deg); }
  98%, 100%{ opacity: 1; transform: scale(1) rotate(0deg); }
}
@keyframes navLogoCycle2 {
  0%, 42%  { opacity: 0; transform: scale(0.5) rotate(15deg); }
  48%, 92% { opacity: 1; transform: scale(1) rotate(0deg); }
  98%, 100%{ opacity: 0; transform: scale(0.5) rotate(-15deg); }
}
.nav-logo-1 { animation: navLogoCycle1 10s infinite; }
.nav-logo-2 { animation: navLogoCycle2 10s infinite; }
.nav-logo-img {
  background: linear-gradient(135deg, #14b8a6, #4f46e5);
  mask-size: contain; -webkit-mask-size: contain;
  mask-repeat: no-repeat; -webkit-mask-repeat: no-repeat;
  mask-position: center; -webkit-mask-position: center;
}
:root.dark .nav-logo-img,
.dark .nav-logo-img { background: linear-gradient(135deg, #5eead4, #818cf8); }
</style>
