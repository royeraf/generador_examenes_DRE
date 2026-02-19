<script setup lang="ts">
import { BookOpen, Calculator, Sparkles, GraduationCap, ShieldCheck, Users } from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import UserBadge from '../components/UserBadge.vue';
import ThemeToggle from '../components/ThemeToggle.vue';
import logoDre from '../assets/logo.png';

const router = useRouter();
const auth = useAuthStore();
</script>

<template>
    <div
        class="min-h-screen flex flex-col justify-center items-center bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-950 p-4 relative overflow-hidden transition-colors duration-500">

        <!-- Background Decoration -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none">
            <div
                class="absolute top-[-10%] left-[-10%] w-96 h-96 bg-teal-200/30 dark:bg-teal-500/10 rounded-full blur-3xl animate-blob">
            </div>
            <div
                class="absolute bottom-[-10%] right-[-10%] w-96 h-96 bg-indigo-200/30 dark:bg-indigo-500/10 rounded-full blur-3xl animate-blob animation-delay-2000">
            </div>
            <div
                class="absolute top-[20%] right-[20%] w-72 h-72 bg-amber-200/20 dark:bg-amber-500/10 rounded-full blur-3xl animate-blob animation-delay-4000">
            </div>
        </div>

        <!-- Controles fijos superiores -->
        <div class="fixed top-6 right-6 z-[100] flex items-center gap-2">
            <ThemeToggle />
            <UserBadge />
        </div>

        <!-- Content -->
        <div class="relative z-10 max-w-5xl w-full">

            <!-- Header -->
            <div class="text-center mb-12 space-y-4">

                <div class="flex items-center justify-center gap-6 mb-8">
                    <div class="relative">
                        <div
                            class="absolute -inset-1 bg-gradient-to-r from-teal-500 to-indigo-600 rounded-2xl blur opacity-20">
                        </div>
                        <div
                            class="relative flex items-center justify-center p-4 bg-white dark:bg-slate-800 rounded-2xl shadow-xl dark:shadow-none border border-slate-100 dark:border-slate-700">
                            <GraduationCap class="w-10 h-10 text-teal-600 dark:text-teal-400" />
                        </div>
                    </div>

                    <div class="relative">
                        <div
                            class="absolute -inset-1 bg-gradient-to-r from-indigo-600 to-teal-500 rounded-2xl blur opacity-20">
                        </div>
                        <div
                            class="relative flex items-center justify-center p-4 bg-white dark:bg-slate-800 rounded-2xl shadow-xl dark:shadow-none border border-slate-100 dark:border-slate-700">
                            <div class="logo-gradient-display-static" :style="{
                                'mask-image': `url(${logoDre})`,
                                '-webkit-mask-image': `url(${logoDre})`
                            }">
                            </div>
                        </div>
                    </div>
                </div>

                <h1
                    class="text-3xl md:text-5xl lg:text-6xl font-black text-slate-800 dark:text-white tracking-tight animate-fade-in-down delay-100 leading-tight">
                    <span class="bg-gradient-to-r from-teal-500 to-indigo-600 bg-clip-text text-transparent">SISTEMA
                        INTEGRADO</span>
                    <br class="hidden sm:block" />
                    <span class="bg-gradient-to-r from-indigo-500 to-teal-500 bg-clip-text text-transparent">DE
                        EVALUACIÓN DE AULA</span>
                </h1>
                <p
                    class="text-xl md:text-2xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto animate-fade-in-down delay-200 font-semibold">
                    Bienvenido a <span
                        class="bg-gradient-to-r from-teal-500 to-indigo-600 bg-clip-text text-transparent font-bold">SIEVA</span>
                </p>
                <p
                    class="text-lg md:text-xl text-slate-600 dark:text-slate-400 max-w-2xl mx-auto animate-fade-in-down delay-200">
                    Selecciona el módulo educativo para comenzar a generar evaluaciones inteligentes con IA.
                </p>
            </div>

            <!-- Selection Cards -->
            <div class="grid md:grid-cols-2 gap-6 md:gap-10 px-4">

                <!-- LectoSistem Card -->
                <button @click="router.push('/lectosistem')"
                    class="group relative bg-white dark:bg-slate-800 rounded-3xl p-8 transition-all duration-500 shadow-2xl shadow-slate-900/12 dark:shadow-black/40 hover:shadow-[0_30px_60px_-12px_rgba(20,184,166,0.35)] dark:hover:shadow-[0_30px_60px_-12px_rgba(20,184,166,0.4)] hover:-translate-y-2 border-2 border-transparent hover:border-teal-400 dark:hover:border-teal-500 text-left animate-fade-in-up delay-300 flex flex-col h-full">
                    <div class="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
                        <BookOpen class="w-32 h-32 text-teal-600 dark:text-teal-400 transform rotate-12" />
                    </div>

                    <div
                        class="w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center mb-6 shadow-lg shadow-teal-500/30 group-hover:scale-110 transition-transform duration-300">
                        <BookOpen class="w-8 h-8 text-white" />
                    </div>

                    <h2
                        class="text-2xl md:text-3xl font-bold text-slate-800 dark:text-white mb-3 group-hover:text-teal-600 dark:group-hover:text-teal-400 transition-colors">
                        LectoSistem
                    </h2>
                    <p class="text-slate-500 dark:text-slate-400 mb-6 flex-grow">
                        Generador de exámenes de comprensión lectora. Evaluación de niveles literal, inferencial y
                        crítico.
                    </p>

                    <div
                        class="flex items-center font-bold text-teal-600 dark:text-teal-400 gap-2 group-hover:gap-4 transition-all">
                        Ingresar al módulo <span class="text-xl">→</span>
                    </div>
                </button>

                <!-- MatSistem Card -->
                <button @click="router.push('/matsistem')"
                    class="group relative bg-white dark:bg-slate-800 rounded-3xl p-8 transition-all duration-500 shadow-2xl shadow-slate-900/12 dark:shadow-black/40 hover:shadow-[0_30px_60px_-12px_rgba(79,70,229,0.35)] dark:hover:shadow-[0_30px_60px_-12px_rgba(79,70,229,0.4)] hover:-translate-y-2 border-2 border-transparent hover:border-indigo-400 dark:hover:border-indigo-500 text-left animate-fade-in-up delay-400 flex flex-col h-full">
                    <div class="absolute top-0 right-0 p-6 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Calculator class="w-32 h-32 text-indigo-600 dark:text-indigo-400 transform -rotate-12" />
                    </div>

                    <div
                        class="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center mb-6 shadow-lg shadow-indigo-500/30 group-hover:scale-110 transition-transform duration-300">
                        <Calculator class="w-8 h-8 text-white" />
                    </div>

                    <h2
                        class="text-2xl md:text-3xl font-bold text-slate-800 dark:text-white mb-3 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                        MatSistem
                    </h2>
                    <p class="text-slate-500 dark:text-slate-400 mb-6 flex-grow">
                        Generador de prácticas matemáticas. Ejercicios personalizados por grado y competencia.
                    </p>

                    <div
                        class="flex items-center font-bold text-indigo-600 dark:text-indigo-400 gap-2 group-hover:gap-4 transition-all">
                        Ingresar al módulo <span class="text-xl">→</span>
                    </div>
                </button>

            </div>

            <!-- Admin Links (solo para admins) -->
            <div v-if="auth.isAdmin" class="mt-12 animate-fade-in delay-500">

                <div class="flex items-center justify-center gap-2 mb-5">
                    <div
                        class="h-px flex-1 max-w-[80px] bg-gradient-to-r from-transparent to-slate-200 dark:to-slate-700">
                    </div>
                    <span
                        class="flex items-center gap-1.5 text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest px-2">
                        <ShieldCheck class="w-3.5 h-3.5" /> Panel de Administración
                    </span>
                    <div
                        class="h-px flex-1 max-w-[80px] bg-gradient-to-l from-transparent to-slate-200 dark:to-slate-700">
                    </div>
                </div>

                <div class="grid grid-cols-3 gap-3 max-w-xl mx-auto px-4">

                    <!-- Admin Comunicación -->
                    <button @click="router.push('/admin')"
                        class="group relative bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/80 rounded-2xl p-4 flex flex-col items-center gap-2.5 transition-all duration-300 hover:-translate-y-1 shadow-xl shadow-slate-900/10 dark:shadow-black/20 hover:shadow-2xl hover:shadow-teal-500/25 hover:border-teal-400/60 dark:hover:border-teal-500/60 text-center">
                        <div
                            class="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-md shadow-teal-500/30 group-hover:scale-110 transition-transform duration-300">
                            <BookOpen class="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <p class="text-xs font-bold text-slate-700 dark:text-slate-200 leading-tight">Admin</p>
                            <p class="text-[10px] text-slate-400 dark:text-slate-500 leading-tight">Comunicación</p>
                        </div>
                    </button>

                    <!-- Admin Matemática -->
                    <button @click="router.push('/admin/mat')"
                        class="group relative bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/80 rounded-2xl p-4 flex flex-col items-center gap-2.5 transition-all duration-300 hover:-translate-y-1 shadow-xl shadow-slate-900/10 dark:shadow-black/20 hover:shadow-2xl hover:shadow-indigo-500/25 hover:border-indigo-400/60 dark:hover:border-indigo-500/60 text-center">
                        <div
                            class="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/30 group-hover:scale-110 transition-transform duration-300">
                            <Calculator class="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <p class="text-xs font-bold text-slate-700 dark:text-slate-200 leading-tight">Admin</p>
                            <p class="text-[10px] text-slate-400 dark:text-slate-500 leading-tight">Matemática</p>
                        </div>
                    </button>

                    <!-- Gestión de Usuarios -->
                    <button @click="router.push('/admin/usuarios')"
                        class="group relative bg-white/70 dark:bg-slate-800/70 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/80 rounded-2xl p-4 flex flex-col items-center gap-2.5 transition-all duration-300 hover:-translate-y-1 shadow-lg shadow-slate-900/5 dark:shadow-black/20 hover:shadow-xl hover:shadow-violet-500/20 hover:border-violet-400/60 dark:hover:border-violet-500/60 text-center">
                        <div
                            class="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-400 to-pink-500 flex items-center justify-center shadow-md shadow-violet-500/30 group-hover:scale-110 transition-transform duration-300">
                            <Users class="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <p class="text-xs font-bold text-slate-700 dark:text-slate-200 leading-tight">Gestión de</p>
                            <p class="text-[10px] text-slate-400 dark:text-slate-500 leading-tight">Usuarios</p>
                        </div>
                    </button>

                </div>

                <p
                    class="text-center text-xs text-slate-400 dark:text-slate-600 flex items-center justify-center gap-1.5 mt-5">
                    <Sparkles class="w-3.5 h-3.5" /> Desarrollado para la Dirección Regional de Educación Huanuco
                </p>
            </div>

            <div v-else class="mt-12 text-center">
                <p
                    class="text-sm text-slate-400 dark:text-slate-500 flex items-center justify-center gap-2 animate-fade-in delay-500">
                    <Sparkles class="w-4 h-4" /> Desarrollado para la Dirección Regional de Educación Huanuco
                </p>
            </div>

        </div>
    </div>
</template>

<style scoped>
.animate-blob {
    animation: blob 7s infinite;
}

.animation-delay-2000 {
    animation-delay: 2s;
}

.animation-delay-4000 {
    animation-delay: 4s;
}

.animate-fade-in-down {
    animation: fadeInDown 0.8s ease-out forwards;
    opacity: 0;
}

.animate-fade-in-up {
    animation: fadeInUp 0.8s ease-out forwards;
    opacity: 0;
}

.animate-fade-in {
    animation: fadeIn 1s ease-out forwards;
    opacity: 0;
}

.delay-100 {
    animation-delay: 0.1s;
}

.delay-200 {
    animation-delay: 0.2s;
}

.delay-300 {
    animation-delay: 0.3s;
}

.delay-400 {
    animation-delay: 0.4s;
}

.delay-500 {
    animation-delay: 0.5s;
}

@keyframes blob {
    0% {
        transform: translate(0px, 0px) scale(1);
    }

    33% {
        transform: translate(30px, -50px) scale(1.1);
    }

    66% {
        transform: translate(-20px, 20px) scale(0.9);
    }

    100% {
        transform: translate(0px, 0px) scale(1);
    }
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes fadeIn {
    from {
        opacity: 0;
    }

    to {
        opacity: 1;
    }
}

.logo-gradient-display-static {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #14b8a6, #4f46e5);
    mask-size: contain;
    -webkit-mask-size: contain;
    mask-repeat: no-repeat;
    -webkit-mask-repeat: no-repeat;
    mask-position: center;
    -webkit-mask-position: center;
}

.dark .logo-gradient-display-static {
    background: linear-gradient(135deg, #5eead4, #818cf8);
    filter: drop-shadow(0 0 8px rgba(94, 234, 212, 0.3));
}
</style>
