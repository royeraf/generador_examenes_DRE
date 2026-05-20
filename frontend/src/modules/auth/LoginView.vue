<script setup lang="ts">
import { shallowRef } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import { LogIn, User, Lock, Loader2, AlertCircle, Eye, EyeOff, Sparkles } from 'lucide-vue-next';
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
const passwordFieldType = shallowRef('password');

const loginSchema = yup.object({
    identifier: yup.string()
        .required('El usuario es obligatorio')
        .min(4, 'Ingresa tu DNI o código'),
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
        await auth.login(formValues.identifier, formValues.password);
        router.push(auth.homeRoute);
    } catch (e: any) {
        const detail = e.response?.data?.detail ?? ''
        if (detail === 'Usuario inactivo') {
            Swal.fire({
                icon: 'warning',
                title: 'Cuenta desactivada',
                text: 'Tu cuenta ha sido desactivada. Comunícate con un administrador.',
                confirmButtonColor: '#14b8a6',
                confirmButtonText: 'Entendido',
            })
        } else {
            error.value = e.response?.status === 400
                ? 'Credenciales incorrectas'
                : 'Error de conexión. Intente nuevamente.'
        }
    } finally {
        loading.value = false;
    }
});
</script>

<template>
    <div class="min-h-screen flex items-stretch bg-slate-50 dark:bg-slate-950 transition-colors duration-500 overflow-hidden font-sans">
        
        <!-- ═══ Left: Visual Side (Desktop) ═══ -->
        <div class="hidden lg:flex lg:w-[50%] xl:w-[60%] relative flex-col justify-between p-12 overflow-hidden">
            <!-- Animated Background -->
            <div class="absolute inset-0 bg-slate-900 dark:bg-black">
                <div class="absolute inset-0 hero-grid opacity-20"></div>
                <div class="absolute top-0 right-0 w-[800px] h-[800px] bg-teal-500/10 rounded-full blur-[120px] animate-pulse"></div>
                <div class="absolute bottom-0 left-0 w-[600px] h-[600px] bg-indigo-500/10 rounded-full blur-[120px] animate-pulse" style="animation-delay: 2s"></div>
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
                <div class="inline-flex items-center gap-2 px-3 py-1 bg-teal-500/10 border border-teal-500/20 rounded-full mb-6">
                    <Sparkles class="w-3.5 h-3.5 text-teal-400" />
                    <span class="text-[10px] font-bold text-teal-400 uppercase tracking-widest">Plataforma Inteligente</span>
                </div>
                <h1 class="text-5xl xl:text-7xl font-bold text-white leading-[1.1] tracking-tight mb-8">
                    <span class="block text-2xl xl:text-3xl text-teal-400 font-black tracking-[0.3em] mb-4 uppercase">SIEVA</span>
                    Potencia el <span class="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-400">aprendizaje</span> con IA.
                </h1>
                <p class="text-lg text-white/50 leading-relaxed max-w-lg mb-10">
                    Genera evaluaciones precisas, gestiona el progreso de tus estudiantes y toma decisiones basadas en datos.
                </p>
                
                <!-- Stats Row (Numbers use font-black as per DESIGN.md) -->
                <div class="flex items-center gap-12">
                    <div>
                        <p class="text-3xl font-black text-white">100%</p>
                        <p class="text-xs text-white/40 uppercase font-bold tracking-wider">Automatizado</p>
                    </div>
                    <div class="w-px h-10 bg-white/10"></div>
                    <div>
                        <p class="text-3xl font-black text-white">Huánuco</p>
                        <p class="text-xs text-white/40 uppercase font-bold tracking-wider">Región Educativa</p>
                    </div>
                </div>
            </div>

            <!-- Footer -->
            <div class="relative z-10">
                <p class="text-[10px] text-white/30 font-bold uppercase tracking-widest">© 2026 DIRECCIÓN REGIONAL DE EDUCACIÓN HUÁNUCO</p>
            </div>

            <!-- Floating Illustration -->
            <div class="absolute right-[-5%] top-[25%] w-[450px] opacity-20 pointer-events-none grayscale contrast-125">
                <img :src="teachingSvg" alt="Visual" class="w-full h-full object-contain" />
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
                    <div class="mb-10 text-center lg:text-left">
                        <h2 class="text-3xl font-bold text-slate-900 dark:text-white tracking-tight mb-2">Bienvenido a SIEVA</h2>
                        <p class="text-slate-500 dark:text-slate-400 font-medium">Ingresa a tu cuenta para continuar</p>
                    </div>

                    <!-- Error Alert -->
                    <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="transform -translate-y-2 opacity-0" enter-to-class="transform translate-y-0 opacity-100">
                        <div v-if="error" class="mb-6 flex items-center gap-3 p-4 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-2xl text-red-600 dark:text-red-400 text-sm font-bold animate-shake">
                            <AlertCircle class="w-5 h-5 shrink-0" />
                            <span>{{ error }}</span>
                        </div>
                    </Transition>

                    <!-- Form -->
                    <form @submit="onSubmit" class="space-y-6" autocomplete="off">
                        <!-- Fields -->
                        <div class="space-y-2">
                            <label class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">Identificador</label>
                            <div class="relative group">
                                <User class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-teal-500 transition-colors" />
                                <input 
                                    v-model="identifierValue"
                                    type="text" 
                                    placeholder="DNI o Código"
                                    class="w-full bg-slate-50 dark:bg-slate-900/50 border-2 border-slate-300 dark:border-slate-800 focus:border-teal-500/50 dark:focus:border-teal-500/30 rounded-xl py-4 pl-12 pr-4 text-sm font-bold text-slate-900 dark:text-white outline-none transition-all"
                                    :class="{'border-red-500/50': identifierError}"
                                />
                            </div>
                            <p v-if="identifierError" class="text-[10px] font-bold text-red-500 ml-1">{{ identifierError }}</p>
                        </div>

                        <div class="space-y-2">
                            <label class="text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest ml-1">Contraseña</label>
                            <div class="relative group">
                                <Lock class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-teal-500 transition-colors" />
                                <input 
                                    v-model="passwordValue"
                                    :type="passwordFieldType" 
                                    placeholder="••••••••"
                                    class="w-full bg-slate-50 dark:bg-slate-900/50 border-2 border-slate-300 dark:border-slate-800 focus:border-teal-500/50 dark:focus:border-teal-500/30 rounded-xl py-4 pl-12 pr-12 text-sm font-bold text-slate-900 dark:text-white outline-none transition-all"
                                    :class="{'border-red-500/50': passwordError}"
                                />
                                <button type="button" @click="passwordFieldType = passwordFieldType === 'password' ? 'text' : 'password'" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors">
                                    <Eye v-if="passwordFieldType === 'password'" class="w-5 h-5" />
                                    <EyeOff v-else class="w-5 h-5" />
                                </button>
                            </div>
                            <p v-if="passwordError" class="text-[10px] font-bold text-red-500 ml-1">{{ passwordError }}</p>
                        </div>

                        <!-- Action Button -->
                        <button type="submit" :disabled="loading" 
                            class="w-full bg-slate-900 dark:bg-white text-white dark:text-slate-950 font-bold py-4 rounded-xl shadow-xl shadow-slate-950/10 dark:shadow-white/5 hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-3 disabled:opacity-50">
                            <Loader2 v-if="loading" class="w-5 h-5 animate-spin" />
                            <template v-else>
                                <span>Acceder al Sistema</span>
                                <LogIn class="w-5 h-5" />
                            </template>
                        </button>
                    </form>

                    <!-- Student Registration Link -->
                    <div class="mt-10 pt-8 border-t border-slate-300 dark:border-slate-900 text-center">
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

@keyframes blob {
    0% { transform: translate(0px, 0px) scale(1); }
    33% { transform: translate(30px, -50px) scale(1.1); }
    66% { transform: translate(-20px, 20px) scale(0.9); }
    100% { transform: translate(0px, 0px) scale(1); }
}
</style>
