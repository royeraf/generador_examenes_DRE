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
        class="min-h-screen flex flex-col lg:flex-row bg-gradient-to-br from-teal-500 via-teal-600 to-indigo-700 lg:bg-none lg:bg-white lg:dark:bg-slate-900 relative overflow-hidden transition-colors duration-300">

        <!-- Mobile/Tablet background blobs (visible below lg) -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none lg:hidden">
            <div class="absolute top-[-15%] left-[-15%] w-72 h-72 md:w-96 md:h-96 bg-white/10 rounded-full blur-3xl animate-blob will-change-transform"></div>
            <div class="absolute bottom-[-10%] right-[-10%] w-64 h-64 md:w-80 md:h-80 bg-indigo-400/20 rounded-full blur-3xl animate-blob animation-delay-2000 will-change-transform"></div>
            <div class="absolute top-[40%] right-[-5%] w-48 h-48 md:w-64 md:h-64 bg-teal-300/15 rounded-full blur-3xl animate-blob animation-delay-4000 will-change-transform"></div>
        </div>

        <!-- Theme Toggle (top right global) -->
        <div class="fixed top-3 right-3 sm:top-5 sm:right-5 z-[100]">
            <ThemeToggle />
        </div>

        <!-- LEFT PANEL: Hero & Illustration (DESKTOP lg+ ONLY) -->
        <div class="hidden lg:flex w-full lg:w-3/5 bg-gradient-to-br from-teal-500 via-teal-600 to-indigo-700 relative overflow-hidden flex-col justify-between lg:min-h-screen lg:px-16 lg:py-10 xl:px-20 xl:py-12">
            <!-- Background decorative elements for Left Panel -->
            <div class="absolute top-0 left-0 w-full h-full overflow-hidden pointer-events-none">
                <div class="absolute top-[-20%] left-[-10%] w-96 h-96 bg-white/10 rounded-full blur-3xl animate-blob will-change-transform"></div>
                <div class="absolute bottom-[-20%] right-[-10%] w-96 h-96 bg-indigo-400/20 rounded-full blur-3xl animate-blob animation-delay-2000 will-change-transform"></div>
            </div>

            <!-- DESKTOP: original vertical layout -->
            <div class="relative z-10 pt-4">
                <div
                    class="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white/10 border border-white/20 text-white/90 text-xs font-semibold uppercase tracking-wider mb-6 backdrop-blur-md">
                    <Sparkles class="w-4 h-4" />
                    Plataforma Educativa
                </div>
                <h1 class="text-5xl xl:text-6xl font-black text-white leading-tight tracking-tight mb-4">
                    SISTEMA INTEGRADO<br />
                    <span class="text-teal-200">DE EVALUACIÓN DE AULA</span>
                </h1>
                <p class="text-xl text-teal-50 font-medium">Bienvenido a SIEVA</p>
                <p class="text-white/70 mt-4 max-w-lg lg:text-base xl:text-lg leading-relaxed">
                    Potenciando la enseñanza a través de la inteligencia artificial. Analiza, genera y sistematiza
                    evaluaciones con precisión humana y velocidad de máquina.
                </p>
            </div>

            <!-- Teaching SVG Illustration (desktop only) -->
            <div
                class="relative z-10 mt-auto flex items-center justify-center pb-8 pt-4">
                <div class="relative lg:w-64 lg:h-64 xl:w-72 xl:h-72 shrink-0">
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
                        class="absolute -top-2 lg:-left-12 xl:-left-14 z-20 bg-white/15 backdrop-blur-md border border-white/25 rounded-2xl lg:px-4 lg:py-3 shadow-[0_8px_32px_rgba(0,0,0,0.2)] flex items-center gap-3 animate-float-y">
                        <div class="relative p-2 bg-teal-400/30 rounded-xl shrink-0">
                            <Users class="w-5 h-5 text-teal-100" />
                            <span
                                class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-teal-300 rounded-full ring-2 ring-white/20">
                                <span class="absolute inset-0 rounded-full bg-teal-300 animate-ping opacity-75"></span>
                            </span>
                        </div>
                        <div>
                            <p class="text-[10px] text-teal-200 uppercase font-black tracking-widest leading-none mb-1">
                                Pedagogía</p>
                            <p class="text-sm font-bold text-white leading-tight">Evaluación<br /> Humana</p>
                        </div>
                    </div>

                    <!-- Floating Glass Card 2 - IA -->
                    <div class="absolute -bottom-2 lg:-right-12 xl:-right-14 z-20 bg-white/15 backdrop-blur-md border border-white/25 rounded-2xl lg:px-4 lg:py-3 shadow-[0_8px_32px_rgba(0,0,0,0.2)] flex items-center gap-3 animate-float-y"
                        style="animation-delay: 2s;">
                        <div class="relative p-2 bg-indigo-400/30 rounded-xl shrink-0">
                            <BrainCircuit class="w-5 h-5 text-indigo-100" />
                            <span
                                class="absolute -top-1 -right-1 w-2.5 h-2.5 bg-indigo-300 rounded-full ring-2 ring-white/20">
                                <span
                                    class="absolute inset-0 rounded-full bg-indigo-300 animate-ping opacity-75"></span>
                            </span>
                        </div>
                        <div>
                            <p class="text-[10px] text-indigo-200 uppercase font-black tracking-widest leading-none mb-1">
                                IA Generativa</p>
                            <p class="text-sm font-bold text-white leading-tight">Exámenes<br /> al Instante</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- RIGHT PANEL: Login Form -->
        <div class="w-full lg:w-2/5 flex flex-col justify-center relative lg:min-h-screen lg:bg-white lg:dark:bg-slate-900 p-4 sm:p-6 md:p-8 lg:px-12 xl:px-16">

            <!-- Mobile/Tablet branding header (below lg) -->
            <div class="relative z-10 flex flex-col items-center text-center mb-6 md:mb-8 lg:hidden animate-mobile-fade-in">
                <!-- Tablet: illustration with glass cards -->
                <div class="relative w-14 h-14 md:w-28 md:h-28 mb-3 md:mb-5">
                    <div class="absolute inset-0 bg-teal-300/20 blur-xl rounded-full"></div>
                    <div class="w-full h-full relative z-10 border-2 border-white/30 shadow-xl overflow-hidden animate-morph bg-indigo-900/40 flex items-center justify-center p-1.5 md:p-3">
                        <img :src="teachingSvg" alt="SIEVA" class="w-full h-full object-contain" />
                    </div>
                    <!-- Tablet-only floating glass pills -->
                    <div class="hidden md:flex absolute -left-24 top-1 z-20 bg-white/15 backdrop-blur-md border border-white/25 rounded-xl px-2.5 py-1.5 shadow-lg items-center gap-2 animate-float-y">
                        <div class="p-1 bg-teal-400/30 rounded-lg">
                            <Users class="w-3.5 h-3.5 text-teal-100" />
                        </div>
                        <span class="text-[10px] font-bold text-white">Pedagogía</span>
                    </div>
                    <div class="hidden md:flex absolute -right-24 bottom-1 z-20 bg-white/15 backdrop-blur-md border border-white/25 rounded-xl px-2.5 py-1.5 shadow-lg items-center gap-2 animate-float-y" style="animation-delay: 2s;">
                        <div class="p-1 bg-indigo-400/30 rounded-lg">
                            <BrainCircuit class="w-3.5 h-3.5 text-indigo-100" />
                        </div>
                        <span class="text-[10px] font-bold text-white">IA Generativa</span>
                    </div>
                </div>
                <div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 border border-white/20 text-white/90 text-[10px] md:text-xs font-semibold uppercase tracking-wider backdrop-blur-md mb-2">
                    <Sparkles class="w-3 h-3 md:w-3.5 md:h-3.5" />
                    Plataforma Educativa
                </div>
                <h1 class="text-xl md:text-3xl font-black text-white leading-tight tracking-tight">
                    SIEVA
                </h1>
                <p class="text-teal-100/80 text-xs md:text-sm mt-0.5 md:mt-1">Sistema Integrado de Evaluación de Aula</p>
                <p class="hidden md:block text-white/60 text-sm mt-2 max-w-md leading-relaxed">
                    Potenciando la enseñanza con inteligencia artificial
                </p>
            </div>

            <div class="max-w-md w-full mx-auto flex flex-col justify-center h-full lg:py-0 relative z-10">
              <div class="relative rounded-3xl p-px bg-gradient-to-br from-white/40 via-white/10 to-indigo-300/40 lg:from-teal-400/60 lg:via-transparent lg:to-indigo-400/60 dark:from-teal-500/40 dark:via-transparent dark:to-indigo-500/40 shadow-2xl shadow-black/15 lg:shadow-xl lg:shadow-slate-900/5 dark:shadow-black/20">
                <div class="rounded-3xl bg-white/95 dark:bg-slate-900/95 lg:bg-white lg:dark:bg-slate-900 backdrop-blur-xl lg:backdrop-blur-none px-5 py-7 sm:px-8 sm:py-10">
                <div class="flex flex-col items-center mb-5 lg:mb-10">
                    <div
                        class="relative w-14 h-14 sm:w-16 sm:h-16 lg:w-20 lg:h-20 bg-slate-50 dark:bg-slate-800 rounded-2xl flex items-center justify-center shadow-lg border border-slate-100 dark:border-slate-700 mb-3 lg:mb-6">
                        <div class="w-10 h-10 sm:w-12 sm:h-12 logo-display" :style="{
                            'mask-image': `url(${logoDre})`,
                            '-webkit-mask-image': `url(${logoDre})`
                        }"></div>
                    </div>
                    <h2
                        class="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-800 dark:text-white tracking-tight text-center">
                        Iniciar Sesión
                    </h2>
                    <p class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm mt-1.5 sm:mt-2 text-center">
                        Ingresa tus credenciales para continuar
                    </p>
                </div>

                <!-- Form -->
                <form @submit="onSubmit" class="space-y-4 lg:space-y-6" autocomplete="off">
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
                                class="w-full bg-slate-50 dark:bg-slate-800/50 border rounded-xl py-4 pl-11 pr-4 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-slate-700 dark:text-slate-200 text-sm sm:text-base font-medium sm:tracking-[0.15em]"
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
                                class="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-teal-500 transition-colors">
                                <Lock class="w-5 h-5" />
                            </div>
                            <input v-model="passwordValue" :type="passwordFieldType" placeholder="Ingresa tu contraseña"
                                autocomplete="new-password" readonly
                                @focus="($event.target as HTMLInputElement).removeAttribute('readonly'); passwordFieldType = 'password'"
                                @input="passwordFieldType = 'password'"
                                class="w-full bg-slate-50 dark:bg-slate-800/50 border rounded-xl py-4 pl-11 pr-4 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-slate-700 dark:text-slate-200 text-sm sm:text-base font-medium"
                                :class="passwordError ? 'border-red-500' : 'border-slate-200 dark:border-slate-700'" />
                        </div>
                        <p v-if="passwordError"
                            class="text-red-500 text-[11px] font-medium ml-1 flex items-center gap-1 mt-1">
                            <AlertCircle class="w-3.5 h-3.5" /> {{ passwordError }}
                        </p>
                    </div>

                    <button type="submit" :disabled="loading"
                        class="w-full bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 dark:from-teal-600 dark:to-indigo-700 dark:hover:from-teal-500 dark:hover:to-indigo-600 text-white font-bold py-3.5 lg:py-4 rounded-xl shadow-lg shadow-teal-500/20 dark:shadow-teal-500/30 transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-3 mt-4 lg:mt-6">
                        <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
                        <span class="text-sm sm:text-base tracking-wide">{{ loading ? 'Ingresando...' : 'Iniciar Sesión' }}</span>
                        <LogIn v-if="!loading" class="w-5 h-5" />
                    </button>

                </form>
                </div>
              </div>

                <p class="text-center text-white/50 lg:text-slate-400 lg:dark:text-slate-500 text-xs mt-6 lg:mt-12 pb-2 lg:pb-4">
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

.animation-delay-4000 {
    animation-delay: 4s;
}

@keyframes mobileFadeIn {
    from {
        opacity: 0;
        transform: translateY(-12px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-mobile-fade-in {
    animation: mobileFadeIn 0.6s ease-out forwards;
}

.logo-display {
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
</style>
