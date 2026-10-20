<script setup lang="ts">
import { shallowRef } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import { LogIn, User, Lock, AlertCircle, Eye, EyeOff } from 'lucide-vue-next';
import { useForm, useField } from 'vee-validate';
import * as yup from 'yup';
import logoDre from '../../assets/logo.png';
import teachingSvg from '../../assets/undraw_visual-explanation_vd4l.svg';
import ThemeToggle from '../../shared/components/ThemeToggle.vue';
import BaseButton from '../../shared/components/BaseButton.vue';

const router = useRouter();
const auth = useAuthStore();

const loading = shallowRef(false);
const error = shallowRef('');
const passwordFieldType = shallowRef('password');

const loginSchema = yup.object({
    identifier: yup.string()
        .required('El usuario es obligatorio')
        .min(4, 'Ingresa tu DNI o código')
        .max(20, 'Máximo 20 caracteres'),
    password: yup.string()
        .required('La contraseña es obligatoria')
        .max(72, 'Contraseña demasiado larga'),
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
        const cleanIdentifier = formValues.identifier.toUpperCase().trim();
        await auth.login(cleanIdentifier, formValues.password);
        router.push(auth.homeRoute);
    } catch (e: any) {
        const status = e.response?.status
        if (status === 429) {
            error.value = 'Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.'
        } else if (status === 400) {
            // Mismo mensaje para credenciales inválidas y cuentas inactivas:
            // no se revela si el identificador existe.
            error.value = 'Credenciales incorrectas'
        } else {
            error.value = 'Error de conexión. Intente nuevamente.'
        }
    } finally {
        loading.value = false;
    }
});

const handleSwitchUser = () => {
    auth.logout();
    error.value = '';
    identifierValue.value = '';
    passwordValue.value = '';
};
</script>

<template>
    <div class="min-h-screen flex items-stretch bg-slate-50 dark:bg-slate-950 transition-colors duration-500 overflow-hidden font-sans">
        
        <!-- ═══ Left: Visual Side (Desktop) ═══ -->
        <div class="hidden lg:flex lg:w-[50%] xl:w-[60%] relative flex-col justify-between p-12 overflow-hidden">
            <!-- Animated Background -->
            <div class="absolute inset-0 bg-slate-900 dark:bg-black">
                <div class="absolute inset-0 hero-grid opacity-20"></div>
                <div class="absolute top-0 right-0 w-[800px] h-[800px] bg-teal-500/10 rounded-full blur-[120px]"></div>
                <div class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-[120px]"></div>
            </div>

            <!-- Header -->
            <div class="relative z-10 flex items-center gap-3">
                <div class="w-10 h-10 p-1.5 bg-white/10 backdrop-blur-md border border-white/20 rounded-xl flex items-center justify-center">
                    <img :src="logoDre" alt="DRE Logo" class="w-full h-full object-contain brightness-0 invert" />
                </div>
                <div class="flex flex-col">
                    <span class="text-white font-bold tracking-widest text-xs uppercase">SIEVA</span>
                    <span class="text-white/40 text-[10px] uppercase font-bold tracking-wider">DRE Huánuco</span>
                </div>
            </div>

            <!-- Content -->
            <div class="relative z-10 max-w-2xl">
                <h1 class="text-2xl xl:text-3xl text-teal-400 font-black tracking-[0.3em] mb-4 uppercase">SIEVA</h1>
                <p class="text-lg text-white/60 leading-relaxed max-w-lg">
                    Sistema Integrado de Evaluación en Aula. Un solo espacio para enseñar, aprender y crecer juntos.
                </p>
            </div>

            <!-- Footer -->
            <div class="relative z-10">
                <p class="text-[10px] text-white/30 font-bold uppercase tracking-widest">© 2026 DIRECCIÓN REGIONAL DE EDUCACIÓN HUÁNUCO</p>
            </div>

            <!-- Floating Illustration -->
            <div class="absolute right-[-5%] top-[25%] w-[450px] opacity-30 pointer-events-none">
                <img :src="teachingSvg" alt="" aria-hidden="true" class="w-full h-full object-contain animate-float" />
            </div>
        </div>

        <!-- ═══ Right: Login Side ═══ -->
        <div class="flex-1 flex flex-col relative bg-white dark:bg-slate-950">
            
            <div class="lg:hidden flex items-center justify-between p-6 shrink-0 z-20">
                <div class="flex items-center gap-2">
                    <img :src="logoDre" alt="Logo" class="w-7 h-7 object-contain dark:brightness-0 dark:invert" />
                    <span class="text-sm font-bold text-slate-800 dark:text-white tracking-tighter">SIEVA</span>
                </div>
                <ThemeToggle />
            </div>

            <!-- Theme Toggle (Desktop) -->
            <div class="hidden lg:block absolute top-10 right-10 z-50">
                <ThemeToggle />
            </div>

            <!-- Form Container -->
            <div class="flex-1 flex flex-col justify-center px-6 sm:px-12 md:px-20 lg:px-16 xl:px-24 py-12 relative">
                
                <!-- Background Accents (Mobile) -->
                <div class="lg:hidden absolute inset-0 pointer-events-none">
                    <div class="absolute top-0 right-0 w-64 h-64 bg-teal-500/5 rounded-full blur-[80px]"></div>
                    <div class="absolute bottom-0 left-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-[80px]"></div>
                </div>

                <div class="w-full max-w-md mx-auto relative z-10">
                    
                    <!-- Form Header -->
                    <div class="mb-4 text-center lg:text-left">
                        <h2 class="text-3xl font-bold text-slate-900 dark:text-white tracking-tight mb-2">Bienvenido a SIEVA</h2>
                        <p class="text-slate-500 dark:text-slate-400 font-medium">Ingresa a tu cuenta para continuar</p>
                    </div>

                    <!-- Sesión activa: equipo compartido -->
                    <div
                        v-if="auth.isAuthenticated && !loading"
                        class="mb-4 flex flex-col gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm dark:border-amber-500/30 dark:bg-amber-500/10"
                    >
                        <div class="flex items-start gap-3">
                            <User class="mt-0.5 h-5 w-5 shrink-0 text-amber-600 dark:text-amber-400" />
                            <div>
                                <p class="font-bold text-amber-800 dark:text-amber-300">
                                    Sesión activa: {{ auth.displayName || 'usuario' }}
                                </p>
                                <p class="mt-1 font-medium text-amber-700 dark:text-amber-400/80">
                                    Si este equipo es compartido, cierra la sesión antes de que otro estudiante ingrese.
                                </p>
                            </div>
                        </div>
                        <button
                            type="button"
                            @click="handleSwitchUser"
                            class="inline-flex items-center justify-center gap-2 rounded-xl border border-amber-300 bg-white px-4 py-2.5 text-xs font-bold text-amber-800 transition-colors hover:bg-amber-100 dark:border-amber-500/40 dark:bg-transparent dark:text-amber-300 dark:hover:bg-amber-500/10"
                        >
                            <LogIn class="h-4 w-4" />
                            Cerrar sesión e ingresar con otra cuenta
                        </button>
                    </div>

                    <!-- Error Alert -->
                    <div class="min-h-[76px] mb-4">
                        <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="transform -translate-y-2 opacity-0" enter-to-class="transform translate-y-0 opacity-100">
                            <div v-if="error" class="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-2xl text-red-600 dark:text-red-400 text-sm font-bold animate-shake">
                                <AlertCircle class="w-5 h-5 shrink-0" />
                                <span>{{ error }}</span>
                            </div>
                        </Transition>
                    </div>



                    <!-- Form -->
                    <form @submit="onSubmit" class="space-y-6" autocomplete="on" novalidate>
                        <!-- Fields -->
                        <div class="space-y-2">
                            <div class="relative">
                                <input
                                    id="login-identifier"
                                    v-model="identifierValue"
                                    type="text"
                                    autocomplete="username"
                                    placeholder=" "
                                    :disabled="loading"
                                    :aria-invalid="!!identifierError"
                                    aria-describedby="login-identifier-help"
                                    class="peer block w-full bg-transparent px-4 pt-4 pb-2.5 text-sm font-bold text-slate-700 dark:text-slate-200 uppercase rounded-xl border appearance-none outline-none focus:ring-0 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                                    :class="identifierError
                                        ? 'border-red-500 focus:border-red-500'
                                        : 'border-slate-300 dark:border-slate-600 focus:border-teal-500'"
                                />
                                <label
                                    for="login-identifier"
                                    class="inline-flex items-center absolute text-sm font-bold transition-all duration-300 transform -translate-y-4 scale-75 top-2 z-10 origin-[0] start-1 px-2 bg-white dark:bg-slate-950 rounded-lg cursor-text peer-focus:px-2 peer-focus:top-2 peer-focus:scale-75 peer-focus:-translate-y-4 peer-placeholder-shown:scale-100 peer-placeholder-shown:-translate-y-1/2 peer-placeholder-shown:top-1/2"
                                    :class="identifierError
                                        ? 'text-red-600 dark:text-red-400 peer-focus:text-red-600 dark:peer-focus:text-red-400'
                                        : 'text-slate-400 dark:text-slate-400 peer-focus:text-teal-500'"
                                >
                                    <User class="w-4 h-4 me-1.5 shrink-0" aria-hidden="true" />
                                    DNI o Código
                                </label>
                            </div>
                            <p
                                id="login-identifier-help"
                                aria-live="polite"
                                class="mt-2 min-h-[1rem] text-xs font-medium text-red-600 dark:text-red-400"
                            >
                                <template v-if="identifierError"><span class="font-bold">Revisa:</span> {{ identifierError }}</template>
                            </p>
                        </div>

                        <div class="space-y-2">
                            <div class="relative">
                                <input
                                    id="login-password"
                                    v-model="passwordValue"
                                    :type="passwordFieldType"
                                    autocomplete="current-password"
                                    placeholder=" "
                                    :disabled="loading"
                                    :aria-invalid="!!passwordError"
                                    aria-describedby="login-password-help"
                                    class="peer block w-full bg-transparent px-4 pr-12 pt-4 pb-2.5 text-sm font-bold text-slate-700 dark:text-slate-200 rounded-xl border appearance-none outline-none focus:ring-0 transition-all disabled:opacity-60 disabled:cursor-not-allowed"
                                    :class="passwordError
                                        ? 'border-red-500 focus:border-red-500'
                                        : 'border-slate-300 dark:border-slate-600 focus:border-teal-500'"
                                />
                                <label
                                    for="login-password"
                                    class="inline-flex items-center absolute text-sm font-bold transition-all duration-300 transform -translate-y-4 scale-75 top-2 z-10 origin-[0] start-1 px-2 bg-white dark:bg-slate-950 rounded-lg cursor-text peer-focus:px-2 peer-focus:top-2 peer-focus:scale-75 peer-focus:-translate-y-4 peer-placeholder-shown:scale-100 peer-placeholder-shown:-translate-y-1/2 peer-placeholder-shown:top-1/2"
                                    :class="passwordError
                                        ? 'text-red-600 dark:text-red-400 peer-focus:text-red-600 dark:peer-focus:text-red-400'
                                        : 'text-slate-400 dark:text-slate-400 peer-focus:text-teal-500'"
                                >
                                    <Lock class="w-4 h-4 me-1.5 shrink-0" aria-hidden="true" />
                                    Contraseña
                                </label>
                                <button type="button" @click="passwordFieldType = passwordFieldType === 'password' ? 'text' : 'password'" :aria-label="passwordFieldType === 'password' ? 'Mostrar contraseña' : 'Ocultar contraseña'" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors cursor-pointer">
                                    <Eye v-if="passwordFieldType === 'password'" class="w-5 h-5" />
                                    <EyeOff v-else class="w-5 h-5" />
                                </button>
                            </div>
                            <p
                                id="login-password-help"
                                aria-live="polite"
                                class="mt-2 min-h-[1rem] text-xs font-medium text-red-600 dark:text-red-400"
                            >
                                <template v-if="passwordError"><span class="font-bold">Revisa:</span> {{ passwordError }}</template>
                            </p>
                        </div>

                        <!-- Action Button -->
                        <BaseButton type="submit" variant="primary" size="lg" block :loading="loading">
                            <template #icon><LogIn class="w-5 h-5" /></template>
                            Acceder al Sistema
                        </BaseButton>


                    </form>

                    <!-- Student Registration Link -->
                    <div class="mt-10 pt-8 border-t border-slate-200 dark:border-slate-800 text-center">
                        <p class="text-sm text-slate-500 dark:text-slate-400 font-medium">
                            ¿Eres estudiante y no tienes cuenta?
                        </p>
                        <router-link to="/registro" class="inline-block mt-2 text-teal-600 dark:text-teal-400 font-bold hover:underline underline-offset-4">
                            Regístrate con tu código de aula
                        </router-link>
                    </div>
                </div>
            </div>

            <!-- Copyright (Mobile) -->
            <div class="lg:hidden p-8 text-center shrink-0">
                <p class="text-[10px] text-slate-400 dark:text-slate-600 font-bold uppercase tracking-widest">© 2026 DRE HUÁNUCO</p>
            </div>
        </div>

    </div>
</template>

<style scoped>
.hero-grid {
    background-image: 
        radial-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px);
    background-size: 32px 32px;
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
    20%, 40%, 60%, 80% { transform: translateX(2px); }
}
.animate-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }


</style>
