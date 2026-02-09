<script setup lang="ts">
import { BookOpen, Calculator, Sparkles, GraduationCap } from 'lucide-vue-next';
import { useTheme } from '../composables/useTheme';
import logoDre from '../assets/logo.png';

useTheme(); // Initialize theme but we don't need isDark ref here since valid classes handle it

const emit = defineEmits<{
    (e: 'select-module', module: 'lectosistem' | 'matsistem' | 'admin' | 'adminmat'): void
}>();

const selectModule = (module: 'lectosistem' | 'matsistem' | 'admin' | 'adminmat') => {
    emit('select-module', module);
};
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
                                '--logo-url': `url(${logoDre})`,
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
                <button @click="selectModule('lectosistem')"
                    class="group relative bg-white dark:bg-slate-800 rounded-3xl p-8 transition-all duration-300 hover:shadow-2xl hover:shadow-teal-500/20 hover:-translate-y-2 border-2 border-transparent hover:border-teal-400 dark:hover:border-teal-500 text-left animate-fade-in-up delay-300 flex flex-col h-full">
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
                <button @click="selectModule('matsistem')"
                    class="group relative bg-white dark:bg-slate-800 rounded-3xl p-8 transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/20 hover:-translate-y-2 border-2 border-transparent hover:border-indigo-400 dark:hover:border-indigo-500 text-left animate-fade-in-up delay-400 flex flex-col h-full">
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

            <div class="mt-12 text-center">
                <p
                    class="text-sm text-slate-400 dark:text-slate-600 flex items-center justify-center gap-2 animate-fade-in delay-500">
                    <Sparkles class="w-4 h-4" /> Desarrollado para la Dirección Regional de Educación Huanuco
                </p>
                <div class="flex items-center justify-center gap-4 flex-wrap">
                    <button @click="selectModule('admin')"
                        class="mt-4 text-xs text-slate-500 dark:text-slate-400 hover:text-teal-600 dark:hover:text-teal-300 font-medium transition-colors underline decoration-slate-300 dark:decoration-slate-600 underline-offset-4 animate-fade-in delay-500">
                        📚 Admin Comunicación
                    </button>
                    <span class="mt-4 text-slate-300 dark:text-slate-600">|</span>
                    <button @click="selectModule('adminmat')"
                        class="mt-4 text-xs text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-indigo-300 font-medium transition-colors underline decoration-slate-300 dark:decoration-slate-600 underline-offset-4 animate-fade-in delay-500">
                        🔢 Admin Matemática
                    </button>
                </div>
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

.logo-gradient-display {
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #14b8a6, #4f46e5);
    mask-size: contain;
    -webkit-mask-size: contain;
    mask-repeat: no-repeat;
    -webkit-mask-repeat: no-repeat;
    mask-position: center;
    -webkit-mask-position: center;
    transition: all 0.3s ease;
}

.dark .logo-gradient-display {
    background: linear-gradient(135deg, #5eead4, #818cf8);
    filter: drop-shadow(0 0 8px rgba(94, 234, 212, 0.3));
}

.group:hover .logo-gradient-display {
    transform: scale(1.1);
    filter: drop-shadow(0 0 12px rgba(94, 234, 212, 0.5));
}

/* Versión estática sin animaciones */
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
