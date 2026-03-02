<script setup lang="ts">
import { shallowRef } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { LogIn, User, Lock, Loader2, AlertCircle, BrainCircuit, Users, Sparkles } from 'lucide-vue-next';
import { useForm, useField } from 'vee-validate';
import * as yup from 'yup';
import logoDre from '../assets/logo.png';
import teachingSvg from '../assets/undraw_visual-explanation_vd4l.svg';
import ThemeToggle from '../components/ThemeToggle.vue';

const router = useRouter();
const auth = useAuthStore();

const loading = shallowRef(false);
const error = shallowRef('');
const passwordFieldType = shallowRef('text');

const loginSchema = yup.object({
    dni: yup.string()
        .required('El DNI es obligatorio')
        .matches(/^\d{8}$/, 'El DNI debe tener 8 dígitos numéricos'),
    password: yup.string()
        .required('La contraseña es obligatoria')
        .max(72, 'La contraseña no puede exceder los 72 caracteres'),
});

const { handleSubmit } = useForm({
    validationSchema: loginSchema,
    initialValues: { dni: '', password: '' }
});

const { value: dniValue, errorMessage: dniError, handleChange: handleDniChange } = useField<string>('dni');
const { value: passwordValue, errorMessage: passwordError } = useField<string>('password');

const onSubmit = handleSubmit(async (formValues) => {
    loading.value = true;
    error.value = '';
    try {
        await auth.login(formValues.dni, formValues.password);
        router.push('/');
    } catch (e: any) {
        console.error(e);
        error.value = e.response?.status === 400
            ? 'DNI o contraseña incorrectos'
            : 'Error al iniciar sesión. Intente nuevamente.';
    } finally {
        loading.value = false;
    }
});

const handleDniKeyPress = (e: KeyboardEvent) => {
    if (!/^\d$/.test(e.key) && !['Backspace', 'Delete', 'ArrowLeft', 'ArrowRight', 'Tab', 'Enter'].includes(e.key)) {
        e.preventDefault();
    }
};

const handleDniInput = (e: Event) => {
    const target = e.target as HTMLInputElement;
    const val = target.value.replace(/\D/g, '').slice(0, 8);
    target.value = val;
    handleDniChange(val);
};
</script>

<template>
    <div
        class="min-h-screen flex flex-col md:flex-row bg-white dark:bg-slate-900 relative overflow-hidden transition-colors duration-300">

        <!-- Theme Toggle (top right global) -->
        <div class="fixed top-5 right-5 z-[100]">
            <ThemeToggle />
        </div>

        <!-- LEFT PANEL: Hero & Illustration -->
        <div class="w-full md:w-1/2 lg:w-3/5 bg-gradient-to-br from-teal-500 via-teal-600 to-indigo-700 relative overflow-hidden flex flex-col justify-between md:min-h-screen"
            :class="'p-5 sm:p-8 md:p-12 lg:p-20 min-h-[auto] md:min-h-screen'">
            <!-- Background decorative elements for Left Panel -->
            <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div class="absolute top-[-20%] left-[-10%] w-96 h-96 bg-white/10 rounded-full blur-3xl animate-blob">
                </div>
                <div
                    class="absolute bottom-[-20%] right-[-10%] w-96 h-96 bg-indigo-400/20 rounded-full blur-3xl animate-blob animation-delay-2000">
                </div>
            </div>

            <!-- MOBILE: horizontal strip (illustration + text side by side) -->
            <div class="relative z-10 flex md:hidden items-center gap-4 py-2">
                <!-- Mini illustration -->
                <div class="shrink-0 w-20 h-20 relative">
                    <div class="absolute inset-0 bg-teal-300/20 blur-xl rounded-full"></div>
                    <div
                        class="w-full h-full relative z-10 border-2 border-white/30 shadow-xl overflow-hidden animate-morph bg-indigo-900/40 flex items-center justify-center p-1.5">
                        <img :src="teachingSvg" alt="SIEVA" class="w-full h-full object-contain" />
                    </div>
                </div>
                <!-- Text -->
                <div class="flex-1 min-w-0">
                    <div
                        class="inline-flex items-center gap-1.5 px-2 py-1 rounded-full bg-white/10 border border-white/20 text-white/90 text-[10px] font-semibold uppercase tracking-wider mb-1.5 backdrop-blur-md">
                        <Sparkles class="w-3 h-3" />
                        Plataforma Educativa
                    </div>
                    <h1 class="text-base font-black text-white leading-tight tracking-tight">
                        SIEVA<br />
                        <span class="text-teal-200 text-sm font-bold">Sistema Integrado de<br />Evaluaci&oacute;n de
                            Aula</span>
                    </h1>
                    <p class="text-teal-100/80 text-xs mt-0.5">Potenciado por Inteligencia Artificial</p>
                </div>
            </div>

            <!-- DESKTOP: original vertical layout -->
            <div class="relative z-10 pt-4 hidden md:block">
                <div
                    class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-white/90 text-xs font-semibold uppercase tracking-wider mb-6 backdrop-blur-md">
                    <Sparkles class="w-4 h-4" />
                    Plataforma Educativa
                </div>
                <h1 class="text-3xl md:text-5xl lg:text-6xl font-black text-white leading-tight tracking-tight mb-4">
                    SISTEMA INTEGRADO<br />
                    <span class="text-teal-200">DE EVALUACIÓN DE AULA</span>
                </h1>
                <p class="text-xl text-teal-50 font-medium">Bienvenido a SIEVA</p>
                <p class="text-white/70 mt-4 max-w-lg text-base lg:text-lg leading-relaxed">
                    Potenciando la enseñanza a través de la inteligencia artificial. Analiza, genera y sistematiza
                    evaluaciones con precisión humana y velocidad de máquina.
                </p>
            </div>

            <!-- Teaching SVG Illustration (desktop only) -->
            <div
                class="relative z-10 mt-8 mb-8 md:mb-0 md:mt-auto hidden md:flex items-center justify-center pb-8 pt-4">
                <div class="relative w-72 h-72 md:w-64 md:h-64 lg:w-72 lg:h-72">
                    <!-- Background Glow -->
                    <div class="absolute inset-0 bg-teal-400/20 blur-3xl rounded-full"></div>

                    <!-- Animated Morph Container + SVG Illustration -->
                    <div
                        class="w-full h-full relative z-10 border-[3px] border-white/30 shadow-2xl overflow-hidden animate-morph bg-indigo-900/40 backdrop-blur-sm flex items-center justify-center p-4">
                        <img :src="teachingSvg" alt="Ilustración educativa"
                            class="w-full h-full object-contain drop-shadow-2xl" />
                    </div>

                    <!-- Floating Glass Card 1 - Docente -->
                    <div
                        class="absolute -top-2 -left-10 md:-left-14 z-20 bg-white/15 backdrop-blur-md border border-white/25 rounded-2xl px-3 py-2.5 md:px-4 md:py-3 shadow-[0_8px_32px_rgba(0,0,0,0.2)] flex items-center gap-3 animate-float-y">
                        <div class="relative p-2 bg-teal-400/30 rounded-xl shrink-0">
                            <Users class="w-4 h-4 md:w-5 md:h-5 text-teal-100" />
                            <!-- Active pulse dot -->
                            <span
                                class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-teal-300 rounded-full ring-2 ring-white/20">
                                <span class="absolute inset-0 rounded-full bg-teal-300 animate-ping opacity-75"></span>
                            </span>
                        </div>
                        <div>
                            <p
                                class="text-[9px] md:text-[10px] text-teal-200 uppercase font-black tracking-widest leading-none mb-1">
                                Pedagog&iacute;a</p>
                            <p class="text-xs md:text-sm font-bold text-white leading-tight">Evaluaci&oacute;n<br
                                    class="hidden md:block" /> Humana</p>
                        </div>
                    </div>

                    <!-- Floating Glass Card 2 - IA -->
                    <div class="absolute -bottom-2 -right-10 md:-right-14 z-20 bg-white/15 backdrop-blur-md border border-white/25 rounded-2xl px-3 py-2.5 md:px-4 md:py-3 shadow-[0_8px_32px_rgba(0,0,0,0.2)] flex items-center gap-3 animate-float-y"
                        style="animation-delay: 2s;">
                        <div class="relative p-2 bg-indigo-400/30 rounded-xl shrink-0">
                            <BrainCircuit class="w-4 h-4 md:w-5 md:h-5 text-indigo-100" />
                            <!-- Active pulse dot -->
                            <span
                                class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-indigo-300 rounded-full ring-2 ring-white/20">
                                <span
                                    class="absolute inset-0 rounded-full bg-indigo-300 animate-ping opacity-75"></span>
                            </span>
                        </div>
                        <div>
                            <p
                                class="text-[9px] md:text-[10px] text-indigo-200 uppercase font-black tracking-widest leading-none mb-1">
                                IA Generativa</p>
                            <p class="text-xs md:text-sm font-bold text-white leading-tight">Ex&aacute;menes<br
                                    class="hidden md:block" /> al Instante</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- RIGHT PANEL: Login Form -->
        <div class="w-full md:w-1/2 lg:w-2/5 flex flex-col justify-center bg-white dark:bg-slate-900 relative md:min-h-screen"
            :class="'p-5 sm:p-8 md:p-12 lg:p-16'">

            <div class="max-w-md w-full mx-auto flex flex-col justify-center h-full py-6 md:py-0">
                <div class="flex flex-col items-center mb-6 md:mb-10">
                    <div
                        class="relative w-14 h-14 sm:w-16 sm:h-16 md:w-20 md:h-20 bg-slate-50 dark:bg-slate-800 rounded-2xl flex items-center justify-center shadow-lg border border-slate-100 dark:border-slate-700 mb-4 md:mb-6">
                        <div class="logo-display" :style="{
                            'mask-image': `url(${logoDre})`,
                            '-webkit-mask-image': `url(${logoDre})`
                        }"></div>
                    </div>
                    <h2
                        class="text-xl sm:text-2xl md:text-3xl font-bold text-slate-800 dark:text-white tracking-tight text-center">
                        Iniciar Sesión
                    </h2>
                    <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm mt-2 text-center">
                        Ingresa tus credenciales para continuar
                    </p>
                </div>

                <!-- Form -->
                <form @submit="onSubmit" class="space-y-4 md:space-y-6" autocomplete="off">
                    <!-- Honeypot -->
                    <input type="text" name="username_fake" aria-hidden="true" tabindex="-1"
                        style="position:absolute;width:1px;height:1px;opacity:0;pointer-events:none;overflow:hidden;" />
                    <input type="password" name="password_fake" aria-hidden="true" tabindex="-1"
                        style="position:absolute;width:1px;height:1px;opacity:0;pointer-events:none;overflow:hidden;" />

                    <div v-if="error"
                        class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3.5 rounded-xl text-sm font-medium text-center border border-red-100 dark:border-red-900/50 animate-shake flex items-center justify-center gap-2">
                        <AlertCircle class="w-4 h-4" />
                        {{ error }}
                    </div>

                    <div class="space-y-2">
                        <label
                            class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider ml-1">DNI
                            (Usuario)</label>
                        <div class="relative group">
                            <div
                                class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-teal-500 transition-colors">
                                <User class="w-5 h-5" />
                            </div>
                            <input :value="dniValue" @input="handleDniInput" @keypress="handleDniKeyPress" type="text"
                                placeholder="Ingresa tu DNI" maxlength="8" autocomplete="one-time-code" readonly
                                @focus="($event.target as HTMLInputElement).removeAttribute('readonly')"
                                class="w-full bg-slate-50 dark:bg-slate-800/50 border rounded-xl py-4 pl-11 pr-4 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-slate-700 dark:text-slate-200 text-sm sm:text-base font-medium"
                                :class="dniError ? 'border-red-500' : 'border-slate-200 dark:border-slate-700'" />
                        </div>
                        <p v-if="dniError"
                            class="text-red-500 text-[11px] font-medium ml-1 flex items-center gap-1 mt-1">
                            <AlertCircle class="w-3.5 h-3.5" /> {{ dniError }}
                        </p>
                    </div>

                    <div class="space-y-2">
                        <label
                            class="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-wider ml-1">Contraseña</label>
                        <div class="relative group">
                            <div
                                class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                                <Lock class="w-5 h-5" />
                            </div>
                            <input v-model="passwordValue" :type="passwordFieldType" placeholder="Ingresa tu contraseña"
                                autocomplete="new-password" readonly
                                @focus="($event.target as HTMLInputElement).removeAttribute('readonly'); passwordFieldType = 'password'"
                                @input="passwordFieldType = 'password'"
                                class="w-full bg-slate-50 dark:bg-slate-800/50 border rounded-xl py-4 pl-11 pr-4 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all text-slate-700 dark:text-slate-200 text-sm sm:text-base font-medium"
                                :class="passwordError ? 'border-red-500' : 'border-slate-200 dark:border-slate-700'" />
                        </div>
                        <p v-if="passwordError"
                            class="text-red-500 text-[11px] font-medium ml-1 flex items-center gap-1 mt-1">
                            <AlertCircle class="w-3.5 h-3.5" /> {{ passwordError }}
                        </p>
                    </div>

                    <button type="submit" :disabled="loading"
                        class="w-full bg-slate-800 dark:bg-teal-600 hover:bg-slate-900 dark:hover:bg-teal-500 text-white font-bold py-4 rounded-xl shadow-lg transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-3 mt-6">
                        <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
                        <span v-else class="text-sm sm:text-base tracking-wide">Iniciar Sesión</span>
                        <LogIn v-if="!loading" class="w-5 h-5" />
                    </button>

                </form>

                <p class="text-center text-slate-400 dark:text-slate-500 text-xs mt-8 md:mt-12 pb-4">
                    © 2026 Dirección Regional de Educación Huánuco
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

@keyframes float-y {

    0%,
    100% {
        transform: translateY(0px);
    }

    50% {
        transform: translateY(-10px);
    }
}

.animate-float-y {
    animation: float-y 4s ease-in-out infinite;
}

@keyframes morph {
    0% {
        border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
    }

    50% {
        border-radius: 30% 60% 70% 40% / 50% 60% 30% 60%;
    }

    100% {
        border-radius: 60% 40% 30% 70% / 60% 30% 70% 40%;
    }
}

.animate-morph {
    animation: morph 8s ease-in-out infinite;
}

@keyframes shake {

    0%,
    100% {
        transform: translateX(0);
    }

    10%,
    30%,
    50%,
    70%,
    90% {
        transform: translateX(-4px);
    }

    20%,
    40%,
    60%,
    80% {
        transform: translateX(4px);
    }
}

.animate-shake {
    animation: shake 0.4s cubic-bezier(.36, .07, .19, .97) both;
}

.logo-display {
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

.dark .logo-display {
    background: linear-gradient(135deg, #5eead4, #818cf8);
}

@media (min-width: 640px) {
    .logo-display {
        width: 48px;
        height: 48px;
    }
}
</style>
