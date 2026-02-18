<script setup lang="ts">
import { shallowRef } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { LogIn, User, Lock, Loader2, AlertCircle } from 'lucide-vue-next';
import { useForm, useField } from 'vee-validate';
import * as yup from 'yup';
import logoDre from '../assets/logo.png';
import ThemeToggle from '../components/ThemeToggle.vue';

const router = useRouter();
const auth = useAuthStore();

const loading = shallowRef(false);
const error = shallowRef('');

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
        class="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-gray-200 dark:from-slate-900 dark:to-slate-950 p-4 relative overflow-hidden">

        <!-- Theme Toggle (top right) -->
        <div class="fixed top-5 right-5 z-[100]">
            <ThemeToggle />
        </div>

        <!-- Background Decoration -->
        <div class="absolute inset-0 overflow-hidden pointer-events-none">
            <div
                class="absolute top-[-20%] left-[-10%] w-[500px] h-[500px] bg-teal-400/20 dark:bg-teal-500/10 rounded-full blur-3xl animate-blob">
            </div>
            <div
                class="absolute bottom-[-20%] right-[-10%] w-[500px] h-[500px] bg-indigo-400/20 dark:bg-indigo-500/10 rounded-full blur-3xl animate-blob animation-delay-2000">
            </div>
        </div>

        <div class="w-full max-w-md relative z-10">
            <!-- Glassmorphism Card -->
            <div
                class="bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-3xl shadow-2xl p-8 border border-white/20 dark:border-slate-700/50">

                <!-- Header / Logo -->
                <div class="flex flex-col items-center mb-8">
                    <div class="relative mb-4 group">
                        <div
                            class="absolute -inset-1 bg-gradient-to-r from-teal-500 to-indigo-600 rounded-2xl blur opacity-30 group-hover:opacity-50 transition-opacity duration-500">
                        </div>
                        <div
                            class="relative w-20 h-20 bg-white dark:bg-slate-800 rounded-2xl flex items-center justify-center shadow-lg">
                            <div class="logo-display" :style="{
                                'mask-image': `url(${logoDre})`,
                                '-webkit-mask-image': `url(${logoDre})`
                            }"></div>
                        </div>
                    </div>
                    <h1 class="text-3xl font-black text-slate-800 dark:text-white tracking-tight text-center">
                        <span class="bg-gradient-to-r from-teal-500 to-indigo-600 bg-clip-text text-transparent">
                            Bienvenido
                        </span>
                    </h1>
                    <p class="text-slate-500 dark:text-slate-400 text-sm mt-2 text-center">
                        Ingresa tus credenciales para continuar
                    </p>
                </div>

                <!-- Form -->
                <form @submit="onSubmit" class="space-y-5">

                    <div v-if="error"
                        class="bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-sm font-medium text-center border border-red-100 dark:border-red-900/50 animate-shake">
                        {{ error }}
                    </div>

                    <div class="space-y-1.5">
                        <label class="text-xs font-bold text-slate-600 dark:text-slate-300 ml-1">DNI (Usuario)</label>
                        <div class="relative group">
                            <div
                                class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-teal-500 transition-colors">
                                <User class="w-5 h-5" />
                            </div>
                            <input :value="dniValue" @input="handleDniInput" @keypress="handleDniKeyPress" type="text"
                                placeholder="Ingresa tu DNI" maxlength="8"
                                class="w-full bg-slate-50 dark:bg-slate-800/50 border rounded-xl py-3 pl-10 pr-4 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all text-slate-700 dark:text-slate-200"
                                :class="dniError ? 'border-red-500' : 'border-slate-200 dark:border-slate-700'" />
                        </div>
                        <p v-if="dniError" class="text-red-500 text-[10px] font-medium ml-1 flex items-center gap-1">
                            <AlertCircle class="w-3 h-3" /> {{ dniError }}
                        </p>
                    </div>

                    <div class="space-y-1.5">
                        <label class="text-xs font-bold text-slate-600 dark:text-slate-300 ml-1">Contraseña</label>
                        <div class="relative group">
                            <div
                                class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-indigo-500 transition-colors">
                                <Lock class="w-5 h-5" />
                            </div>
                            <input v-model="passwordValue" type="password" placeholder="Ingresa tu contraseña"
                                class="w-full bg-slate-50 dark:bg-slate-800/50 border rounded-xl py-3 pl-10 pr-4 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all text-slate-700 dark:text-slate-200"
                                :class="passwordError ? 'border-red-500' : 'border-slate-200 dark:border-slate-700'" />
                        </div>
                        <p v-if="passwordError"
                            class="text-red-500 text-[10px] font-medium ml-1 flex items-center gap-1">
                            <AlertCircle class="w-3 h-3" /> {{ passwordError }}
                        </p>
                    </div>

                    <button type="submit" :disabled="loading"
                        class="w-full bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold py-3.5 rounded-xl shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/40 transform hover:-translate-y-0.5 transition-all duration-200 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2">
                        <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
                        <span v-else>Iniciar Sesión</span>
                        <LogIn v-if="!loading" class="w-5 h-5" />
                    </button>

                </form>

            </div>

            <p class="text-center text-slate-400 dark:text-slate-500 text-xs mt-6">
                © 2026 Dirección Regional de Educación Huánuco
            </p>
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
    width: 48px;
    height: 48px;
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
