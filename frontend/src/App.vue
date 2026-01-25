<script setup lang="ts">
import { ref } from 'vue';
import HomeView from './views/HomeView.vue';
import LectoSistemView from './views/LectoSistemView.vue';
import MatSistemView from './views/MatSistemView.vue';
import AdminView from './views/AdminView.vue';
import AdminMatView from './views/AdminMatView.vue';
import { Home } from 'lucide-vue-next';

// Simple state management for routing
const currentModule = ref<'home' | 'lectosistem' | 'matsistem' | 'admin' | 'adminmat'>('home');

const handleModuleSelection = (module: 'lectosistem' | 'matsistem' | 'admin' | 'adminmat') => {
    currentModule.value = module;
};

const goHome = () => {
    currentModule.value = 'home';
};
</script>

<template>
    <div class="antialiased">
        <!-- View Switcher -->
        <Transition name="fade" mode="out-in">
            <HomeView v-if="currentModule === 'home'" @select-module="handleModuleSelection" />
            <LectoSistemView v-else-if="currentModule === 'lectosistem'" />
            <MatSistemView v-else-if="currentModule === 'matsistem'" />
            <AdminView v-else-if="currentModule === 'admin'" />
            <AdminMatView v-else-if="currentModule === 'adminmat'" />
        </Transition>

        <!-- Global Back Button (Visible when not on Home) -->
        <button v-if="currentModule !== 'home'" @click="goHome"
            class="fixed bottom-6 left-6 z-[100] bg-white/90 dark:bg-slate-800/90 backdrop-blur-md text-slate-700 dark:text-slate-200 px-5 py-3 rounded-full shadow-2xl border-2 border-slate-100 dark:border-slate-600 font-bold text-sm hover:scale-105 hover:bg-white dark:hover:bg-slate-700 transition-all duration-300 flex items-center gap-2 group">
            <div
                class="w-6 h-6 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center group-hover:bg-slate-200 dark:group-hover:bg-slate-600 transition-colors">
                <Home class="w-3.5 h-3.5" />
            </div>
            Inicio
        </button>
    </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
    transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
    opacity: 0;
}
</style>
