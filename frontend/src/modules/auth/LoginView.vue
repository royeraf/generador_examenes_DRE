<script setup lang="ts">
import { shallowRef } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import { LogIn, User, Lock, Loader2, AlertCircle, Eye, EyeOff } from 'lucide-vue-next';
import { useForm, useField } from 'vee-validate';
import * as yup from 'yup';
import logoDre from '../../assets/logo.png';
import Swal from 'sweetalert2';
import teachingSvg from '../../assets/undraw_visual-explanation_vd4l.svg';
import ThemeToggle from '../../shared/components/ThemeToggle.vue';

const router = useRouter();
const auth = useAuthStore();

const loading = shallowRef(false);
const error = shallowRef('');
const passwordFieldType = shallowRef('text');

const loginSchema = yup.object({
    identifier: yup.string()
        .required('El usuario es obligatorio')
        .min(4, 'Ingresa tu DNI (8 dígitos) o código de estudiante'),
    password: yup.string()
        .required('La contraseña es obligatoria')
        .max(72, 'La contraseña no puede exceder los 72 caracteres'),
});

const { handleSubmit } = useForm({
    validationSchema: loginSchema,
    initialValues: { identifier: '', password: '' }
});

const { value: identifierValue, errorMessage: identifierError } = useField<string>('identifier');
const { value: passwordValue, errorMessage: passwordError } = useField<string>('password');

const onSubmit = handleSubmit(async (formValues) => {
    loading.value = true;
    error.value = '';
    try {
        await auth.login(formValues.identifier, formValues.password);
        router.push(auth.homeRoute);
    } catch (e: any) {
        const detail = e.response?.data?.detail ?? ''
        if (detail === 'Usuario inactivo') {
            Swal.fire({
                icon: 'warning',
                title: 'Cuenta desactivada',
                text: 'Tu cuenta ha sido desactivada. Comunícate con un administrador para recuperar el acceso.',
                confirmButtonColor: '#6366f1',
                confirmButtonText: 'Entendido',
            })
        } else {
            error.value = e.response?.status === 400
                ? 'Credenciales incorrectas'
                : 'Error al iniciar sesión. Intente nuevamente.'
        }
    } finally {
        loading.value = false;
    }
});
</script>

<template>
    <div class="login-page min-h-screen flex flex-col lg:flex-row transition-colors duration-300">

        <!-- ═══ LEFT: Hero Panel (desktop lg+) ═══ -->
        <div
            class="hidden lg:flex lg:w-[55%] xl:w-3/5 relative flex-col justify-between overflow-hidden bg-slate-950">

            <!-- Grid pattern overlay -->
            <div class="absolute inset-0 hero-grid"></div>

            <!-- Gradient atmosphere -->
            <div
                class="absolute inset-0 bg-gradient-to-br from-teal-950/70 via-slate-950/30 to-emerald-950/50">
            </div>

            <!-- Animated glow blobs -->
            <div
                class="absolute top-[-10%] left-[-5%] w-[500px] h-[500px] bg-teal-500/[0.07] rounded-full blur-[120px] animate-blob">
            </div>
            <div
                class="absolute bottom-[-10%] right-[-5%] w-[400px] h-[400px] bg-emerald-500/[0.06] rounded-full blur-[100px] animate-blob animation-delay-2000">
            </div>
            <div
                class="absolute top-[50%] right-[20%] w-[300px] h-[300px] bg-teal-400/[0.04] rounded-full blur-[100px] animate-blob animation-delay-4000">
            </div>

            <!-- Vertical separator accent -->
            <div
                class="absolute top-0 right-0 w-px h-full bg-gradient-to-b from-transparent via-teal-500/20 to-transparent">
            </div>

            <!-- Top: Logo mark -->
            <div class="relative z-10 px-10 xl:px-16 pt-10 xl:pt-12">
                <div class="flex items-center gap-3">
                    <div
                        class="w-9 h-9 rounded-lg bg-white/[0.07] border border-white/[0.08] flex items-center justify-center">
                        <div class="w-5 h-5 logo-hero" :style="{
                            'mask-image': `url(${logoDre})`,
                            '-webkit-mask-image': `url(${logoDre})`
                        }"></div>
                    </div>
                    <span
                        class="text-white/55 text-xs font-bold tracking-[0.2em] uppercase">DRE
                        Huánuco</span>
                </div>
            </div>

            <!-- Center: Headline + Illustration side by side -->
            <div
                class="relative z-10 flex-1 flex items-center px-10 xl:px-16">
                <div class="flex items-center gap-10 xl:gap-14 w-full">
                    <!-- Text -->
                    <div class="flex-1 min-w-0">
                        <h1
                            class="text-[2.5rem] xl:text-[3.25rem] font-extrabold text-white leading-[1.08] tracking-tight">
                            Sistema Integrado
                            <span class="block text-teal-300">de
                                Evaluación</span>
                            <span class="block">de Aula</span>
                        </h1>
                        <div
                            class="w-14 h-1 bg-amber-400 rounded-full mt-6 mb-5">
                        </div>
                        <p
                            class="text-white/60 text-base xl:text-lg leading-relaxed max-w-md">
                            Plataforma educativa para la gestión y
                            generación
                            de evaluaciones con apoyo de inteligencia
                            artificial.
                        </p>
                    </div>

                    <!-- Illustration with morph -->
                    <div class="shrink-0 w-48 xl:w-56">
                        <div class="relative">
                            <div
                                class="absolute -inset-6 bg-teal-400/[0.10] rounded-full blur-2xl">
                            </div>
                            <div
                                class="relative w-full aspect-square border-2 border-white/20 shadow-2xl overflow-hidden animate-morph bg-emerald-900/30 backdrop-blur-sm flex items-center justify-center p-5">
                                <img :src="teachingSvg"
                                    alt="Ilustración educativa"
                                    class="w-full h-full object-contain drop-shadow-xl" />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Bottom: Copyright -->
            <div
                class="relative z-10 px-10 xl:px-16 pb-8 xl:pb-10">
                <p
                    class="text-white/35 text-[11px] leading-relaxed">
                    © 2026 Dirección Regional de Educación Huánuco
                </p>
            </div>
        </div>

        <!-- ═══ RIGHT: Login Form ═══ -->
        <div
            class="flex-1 flex flex-col relative min-h-screen lg:min-h-0">

            <!-- Theme Toggle (desktop only) -->
            <div
                class="hidden lg:block absolute top-5 right-5 z-50">
                <ThemeToggle />
            </div>

            <!-- ── Mobile: Hero Banner ── -->
            <div
                class="lg:hidden relative overflow-hidden bg-slate-950">
                <!-- Decorations -->
                <div class="absolute inset-0 hero-grid"></div>
                <div
                    class="absolute inset-0 bg-gradient-to-br from-teal-950/70 via-slate-950/30 to-emerald-950/50">
                </div>
                <div
                    class="absolute top-[-25%] left-[-15%] w-56 h-56 sm:w-72 sm:h-72 bg-teal-500/[0.08] rounded-full blur-[80px] animate-blob">
                </div>
                <div
                    class="absolute bottom-[-25%] right-[-15%] w-44 h-44 sm:w-56 sm:h-56 bg-emerald-500/[0.07] rounded-full blur-[60px] animate-blob animation-delay-2000">
                </div>

                <div
                    class="relative z-10 px-5 sm:px-7 pt-4 sm:pt-5 pb-5 sm:pb-7 animate-mobile-fade-in">

                    <!-- Top row: Logo + ThemeToggle -->
                    <div
                        class="flex items-center justify-between mb-3 sm:mb-4">
                        <div class="flex items-center gap-2">
                            <div
                                class="w-7 h-7 rounded-md bg-white/[0.07] border border-white/[0.08] flex items-center justify-center">
                                <div class="w-4 h-4 logo-hero"
                                    :style="{
                                        'mask-image': `url(${logoDre})`,
                                        '-webkit-mask-image': `url(${logoDre})`
                                    }"></div>
                            </div>
                            <span
                                class="text-white/50 text-[10px] font-bold tracking-[0.15em] uppercase">DRE
                                Huánuco</span>
                        </div>
                        <ThemeToggle />
                    </div>

                    <!-- Content row: Title + Morph Illustration -->
                    <div
                        class="flex items-center gap-4 sm:gap-6">
                        <div class="flex-1 min-w-0">
                            <h1
                                class="text-xl sm:text-2xl font-extrabold text-white leading-tight tracking-tight">
                                SIEVA
                            </h1>
                            <p
                                class="text-white/50 text-xs sm:text-sm mt-0.5 leading-snug">
                                Sistema Integrado de Evaluación
                                de Aula
                            </p>
                        </div>

                        <!-- Small morph illustration -->
                        <div
                            class="shrink-0 w-[76px] h-[76px] sm:w-24 sm:h-24">
                            <div class="relative w-full h-full">
                                <div
                                    class="absolute -inset-3 bg-teal-400/[0.08] rounded-full blur-xl">
                                </div>
                                <div
                                    class="relative w-full h-full border border-white/15 shadow-lg overflow-hidden animate-morph bg-emerald-900/30 backdrop-blur-sm flex items-center justify-center p-2 sm:p-3">
                                    <img :src="teachingSvg"
                                        alt="SIEVA"
                                        class="w-full h-full object-contain drop-shadow-lg" />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- ── Form Area ── -->
            <div
                class="flex-1 flex flex-col justify-center bg-white dark:bg-slate-900 px-5 sm:px-8 lg:px-12 xl:px-20 py-5 sm:py-6 lg:py-0">
                <div
                    class="w-full max-w-sm mx-auto lg:max-w-[26rem] animate-enter">

                    <!-- Form card with border -->
                    <div
                        class="form-card rounded-2xl border border-slate-200/80 dark:border-slate-700/60 bg-white dark:bg-slate-800/40 shadow-xl shadow-slate-900/[0.04] dark:shadow-black/20 px-5 py-6 sm:px-8 sm:py-10">

                        <!-- Desktop: logo + title -->
                        <div
                            class="hidden lg:flex flex-col items-center mb-8">
                            <div
                                class="w-16 h-16 rounded-2xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 flex items-center justify-center shadow-sm mb-5">
                                <div class="w-10 h-10 logo-display"
                                    :style="{
                                        'mask-image': `url(${logoDre})`,
                                        '-webkit-mask-image': `url(${logoDre})`
                                    }"></div>
                            </div>
                            <h2
                                class="text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                                Iniciar Sesión</h2>
                            <p
                                class="text-slate-500 dark:text-slate-400 text-sm mt-1.5">
                                Ingresa tus credenciales para
                                continuar</p>
                        </div>

                        <!-- Mobile: title -->
                        <div class="lg:hidden mb-5">
                            <h2
                                class="text-xl sm:text-2xl font-bold text-slate-900 dark:text-white tracking-tight">
                                Iniciar Sesión</h2>
                            <p
                                class="text-slate-500 dark:text-slate-400 text-xs sm:text-sm mt-1">
                                Ingresa tus credenciales</p>
                        </div>

                        <!-- Error alert -->
                        <div v-if="error"
                            class="mb-4 sm:mb-5 bg-red-50 dark:bg-red-950/30 text-red-600 dark:text-red-400 px-3.5 sm:px-4 py-2.5 sm:py-3 rounded-xl text-xs sm:text-sm font-medium border border-red-100 dark:border-red-900/40 animate-shake flex items-center gap-2">
                            <AlertCircle
                                class="w-4 h-4 shrink-0" />
                            {{ error }}
                        </div>

                        <!-- Login Form -->
                        <form @submit="onSubmit"
                            class="space-y-4 sm:space-y-5"
                            autocomplete="off">
                            <!-- Honeypots -->
                            <input type="text" name="username_fake"
                                aria-hidden="true" tabindex="-1"
                                style="position:absolute;width:1px;height:1px;opacity:0;pointer-events:none;overflow:hidden;" />
                            <input type="password"
                                name="password_fake"
                                aria-hidden="true" tabindex="-1"
                                style="position:absolute;width:1px;height:1px;opacity:0;pointer-events:none;overflow:hidden;" />

                            <!-- Identificador Field (DNI o código estudiante) -->
                            <div>
                                <label
                                    class="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider mb-1.5 sm:mb-2 ml-0.5">
                                    DNI o Código de Estudiante
                                </label>
                                <div class="relative group">
                                    <User
                                        class="absolute left-3 sm:left-3.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-slate-400 dark:text-slate-400 group-focus-within:text-teal-500 transition-colors duration-200" />
                                    <input v-model="identifierValue"
                                        type="text"
                                        placeholder="12345678 o EST0001"
                                        maxlength="10"
                                        autocomplete="username"
                                        readonly
                                        @focus="($event.target as HTMLInputElement).removeAttribute('readonly')"
                                        class="login-input w-full bg-white dark:bg-slate-700/80 border rounded-xl py-3 sm:py-3.5 pl-9 sm:pl-10 pr-4 outline-none text-slate-900 dark:text-white text-sm font-semibold tracking-[0.18em] placeholder:tracking-normal placeholder:font-normal placeholder:text-slate-400 dark:placeholder:text-slate-400 transition-all duration-200"
                                        :class="identifierError ? 'border-red-400 dark:border-red-500' : 'border-slate-300 dark:border-slate-500 focus:border-teal-500 dark:focus:border-teal-400 focus:ring-2 focus:ring-teal-500/25'" />
                                </div>
                                <p v-if="identifierError"
                                    class="text-red-500 text-[11px] font-medium mt-1.5 ml-0.5 flex items-center gap-1">
                                    <AlertCircle
                                        class="w-3 h-3 shrink-0" />
                                    {{ identifierError }}
                                </p>
                            </div>

                            <!-- Password Field -->
                            <div>
                                <label
                                    class="block text-xs font-bold text-slate-600 dark:text-slate-300 uppercase tracking-wider mb-1.5 sm:mb-2 ml-0.5">
                                    Contraseña
                                </label>
                                <div class="relative group">
                                    <Lock
                                        class="absolute left-3 sm:left-3.5 top-1/2 -translate-y-1/2 w-[18px] h-[18px] text-slate-400 dark:text-slate-400 group-focus-within:text-teal-500 transition-colors duration-200" />
                                    <input
                                        v-model="passwordValue"
                                        :type="passwordFieldType"
                                        placeholder="Tu contraseña"
                                        autocomplete="new-password"
                                        readonly
                                        @focus="($event.target as HTMLInputElement).removeAttribute('readonly'); passwordFieldType = 'password'"
                                        @input="passwordFieldType = 'password'"
                                        class="login-input w-full bg-white dark:bg-slate-700/80 border rounded-xl py-3 sm:py-3.5 pl-9 sm:pl-10 pr-10 outline-none text-slate-900 dark:text-white text-sm font-medium placeholder:text-slate-400 dark:placeholder:text-slate-400 transition-all duration-200"
                                        :class="passwordError ? 'border-red-400 dark:border-red-500' : 'border-slate-300 dark:border-slate-500 focus:border-teal-500 dark:focus:border-teal-400 focus:ring-2 focus:ring-teal-500/25'" />
                                    <button type="button"
                                        @click="passwordFieldType = passwordFieldType === 'password' ? 'text' : 'password'"
                                        class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
                                        <Eye v-if="passwordFieldType === 'password'" class="w-4 h-4" />
                                        <EyeOff v-else class="w-4 h-4" />
                                    </button>
                                </div>
                                <p v-if="passwordError"
                                    class="text-red-500 text-[11px] font-medium mt-1.5 ml-0.5 flex items-center gap-1">
                                    <AlertCircle
                                        class="w-3 h-3 shrink-0" />
                                    {{ passwordError }}
                                </p>
                            </div>

                            <!-- Submit Button -->
                            <button type="submit"
                                :disabled="loading"
                                class="login-btn w-full font-bold py-3 sm:py-3.5 rounded-xl transition-all duration-200 disabled:opacity-60 disabled:cursor-not-allowed flex items-center justify-center gap-2.5 mt-1 sm:mt-2 active:scale-[0.98]">
                                <Loader2 v-if="loading"
                                    class="w-5 h-5 animate-spin" />
                                <span
                                    class="text-sm tracking-wide">{{
                                    loading ? 'Ingresando...' :
                                    'Iniciar Sesión'
                                }}</span>
                                <LogIn v-if="!loading"
                                    class="w-4 h-4" />
                            </button>
                        </form>

                        <!-- Link registro estudiante -->
                        <p class="text-center text-xs text-slate-500 dark:text-slate-400 mt-5">
                            ¿Estudiante sin cuenta?
                            <router-link to="/registro" class="text-teal-600 dark:text-teal-400 font-semibold hover:underline">
                                Registrarse con código de clase
                            </router-link>
                        </p>
                    </div>

                    <!-- Footer -->
                    <p
                        class="lg:hidden text-center text-slate-400 dark:text-slate-500 text-[11px] mt-6">
                        © 2026 Dirección Regional de Educación
                        Huánuco
                    </p>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
/* ── Hero grid pattern ── */
.hero-grid {
    background-image:
        linear-gradient(rgba(255, 255, 255, 0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.025) 1px, transparent 1px);
    background-size: 48px 48px;
}

/* ── Logo masks ── */
.logo-hero {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.6), rgba(255, 255, 255, 0.3));
    mask-size: contain;
    -webkit-mask-size: contain;
    mask-repeat: no-repeat;
    -webkit-mask-repeat: no-repeat;
    mask-position: center;
    -webkit-mask-position: center;
}

.logo-mobile {
    background: linear-gradient(135deg, #0d9488, #0ea5e9);
    mask-size: contain;
    -webkit-mask-size: contain;
    mask-repeat: no-repeat;
    -webkit-mask-repeat: no-repeat;
    mask-position: center;
    -webkit-mask-position: center;
}

.logo-display {
    background: linear-gradient(135deg, #14b8a6, #0d9488);
    mask-size: contain;
    -webkit-mask-size: contain;
    mask-repeat: no-repeat;
    -webkit-mask-repeat: no-repeat;
    mask-position: center;
    -webkit-mask-position: center;
}

.dark .logo-display {
    background: linear-gradient(135deg, #5eead4, #2dd4bf);
}

/* ── Submit button ── */
.login-btn {
    background: #0f172a;
    color: white;
    box-shadow:
        0 1px 3px rgba(15, 23, 42, 0.12),
        0 6px 16px rgba(15, 23, 42, 0.08);
}

.login-btn:hover:not(:disabled) {
    background: #1e293b;
    box-shadow:
        0 1px 3px rgba(15, 23, 42, 0.16),
        0 8px 24px rgba(15, 23, 42, 0.12);
    transform: translateY(-1px);
}

.dark .login-btn {
    background: linear-gradient(135deg, #0d9488, #0f766e);
    box-shadow:
        0 1px 3px rgba(13, 148, 136, 0.2),
        0 6px 16px rgba(13, 148, 136, 0.15);
}

.dark .login-btn:hover:not(:disabled) {
    background: linear-gradient(135deg, #14b8a6, #0d9488);
    box-shadow:
        0 1px 3px rgba(13, 148, 136, 0.25),
        0 8px 24px rgba(13, 148, 136, 0.2);
}

/* ── Input focus glow ── */
.login-input:focus {
    background-color: white;
    box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.12);
}

.dark .login-input:focus {
    background-color: rgba(51, 65, 85, 0.9);
    box-shadow: 0 0 0 3px rgba(45, 212, 191, 0.15);
}

/* ── Blob animation ── */
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

.animate-blob {
    animation: blob 7s infinite;
}

.animation-delay-2000 {
    animation-delay: 2s;
}

.animation-delay-4000 {
    animation-delay: 4s;
}

/* ── Morph animation (illustration) ── */
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

/* ── Entrance animation ── */
@keyframes enter {
    from {
        opacity: 0;
        transform: translateY(12px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.animate-enter {
    animation: enter 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* ── Mobile fade-in ── */
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

/* ── Error shake ── */
@keyframes shake {

    0%,
    100% {
        transform: translateX(0);
    }

    15%,
    45%,
    75% {
        transform: translateX(-4px);
    }

    30%,
    60%,
    90% {
        transform: translateX(4px);
    }
}

.animate-shake {
    animation: shake 0.4s cubic-bezier(.36, .07, .19, .97) both;
}
</style>
