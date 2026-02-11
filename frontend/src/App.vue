<script setup lang="ts">
import { shallowRef } from 'vue';
import LoginView from './views/LoginView.vue';
import HomeView from './views/HomeView.vue';
import LectoSistemView from './views/LectoSistemView.vue';
import MatSistemView from './views/MatSistemView.vue';
import AdminView from './views/AdminView.vue';
import AdminMatView from './views/AdminMatView.vue';
import { Home, LogOut } from 'lucide-vue-next';
import { authService } from './services/auth';

type Module = 'login' | 'home' | 'lectosistem' | 'matsistem' | 'admin' | 'adminmat';

// Check auth synchronously (localStorage is sync) to avoid login flash
const initialModule: Module = authService.isAuthenticated() ? 'home' : 'login';
const currentModule = shallowRef<Module>(initialModule);

const handleModuleSelection = (module: 'lectosistem' | 'matsistem' | 'admin' | 'adminmat') => {
    currentModule.value = module;
};

const handleLoginSuccess = () => {
    currentModule.value = 'home';
};

const handleLogout = () => {
    authService.logout();
    currentModule.value = 'login';
};

const goHome = () => {
    currentModule.value = 'home';
};
</script>

<template>
    <div class="antialiased">
        <!-- View Switcher -->
        <Transition name="fade" mode="out-in">
            <LoginView v-if="currentModule === 'login'" @login-success="handleLoginSuccess" />
            <HomeView v-else-if="currentModule === 'home'" @select-module="handleModuleSelection"
                @logout="handleLogout" />
            <LectoSistemView v-else-if="currentModule === 'lectosistem'" />
            <MatSistemView v-else-if="currentModule === 'matsistem'" />
            <AdminView v-else-if="currentModule === 'admin'" />
            <AdminMatView v-else-if="currentModule === 'adminmat'" />
        </Transition>

        <!-- Global Back Button (Visible when not on Home and not on Login) -->
        <button v-if="currentModule !== 'home' && currentModule !== 'login'" @click="goHome"
            class="fixed bottom-6 left-6 z-[100] bg-white/90 dark:bg-slate-800/90 backdrop-blur-md text-slate-700 dark:text-slate-200 px-5 py-3 rounded-full shadow-2xl border-2 border-slate-100 dark:border-slate-600 font-bold text-sm hover:scale-105 hover:bg-white dark:hover:bg-slate-700 transition-all duration-300 flex items-center gap-2 group">
            <div
                class="w-6 h-6 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center group-hover:bg-slate-200 dark:group-hover:bg-slate-600 transition-colors">
                <Home class="w-3.5 h-3.5" />
            </div>
            Inicio
        </button>

        <!-- Logout Button (Visible ONLY on Home) -->
        <button v-if="currentModule === 'home'" @click="handleLogout"
            class="fixed top-6 right-6 z-[100] bg-white/90 dark:bg-slate-800/90 backdrop-blur-md text-slate-700 dark:text-slate-200 px-4 py-2 rounded-full shadow-xl border border-slate-100 dark:border-slate-700 font-bold text-xs hover:scale-105 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 hover:border-red-200 dark:hover:border-red-800 transition-all duration-300 flex items-center gap-2">
            <LogOut class="w-4 h-4" />
            Cerrar Sesión
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
