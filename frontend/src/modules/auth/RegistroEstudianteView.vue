<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { registroService, type RegistroEstudiantePayload } from '../../shared/services/api'
import { Eye, EyeOff, AlertCircle, CheckCircle, GraduationCap, Loader2, ArrowRight, ArrowLeft, Sparkles } from 'lucide-vue-next'
import ThemeToggle from '../../shared/components/ThemeToggle.vue'

const router = useRouter()
const route = useRoute()

const step = ref<'codigo' | 'datos'>('codigo')
const codigoInput = ref('')

// Pre-llenar y validar el código desde la query string (?code=XXXXXXXX)
onMounted(async () => {
  const code = route.query.code as string | undefined
  if (code) {
    codigoInput.value = code.trim().toUpperCase()
    await validarCodigo()
  }
})

const codigoInfo = ref<{ grado: string | null; seccion: string | null; institucion: string | null } | null>(null)
const validandoCodigo = ref(false)
const codigoError = ref('')

const form = ref({
  nombres: '',
  apellidos: '',
  dni: '',
  password: '',
  confirm: '',
})

const showPass = ref(false)
const showConfirm = ref(false)
const saving = ref(false)
const serverError = ref('')
const success = ref<{ codigo: string } | null>(null)

const formError = computed(() => {
  if (!form.value.nombres.trim() || !form.value.apellidos.trim()) return 'Nombres y apellidos son requeridos'
  if (form.value.password.length < 4) return 'Contraseña muy corta (mín. 4)'
  if (form.value.password !== form.value.confirm) return 'Las contraseñas no coinciden'
  return ''
})

async function validarCodigo() {
  codigoError.value = ''
  if (!codigoInput.value.trim()) {
    codigoError.value = 'Ingresa el código de tu aula'
    return
  }
  validandoCodigo.value = true
  try {
    const info = await registroService.validarCodigo(codigoInput.value.trim())
    codigoInfo.value = info
    step.value = 'datos'
  } catch (e: any) {
    codigoError.value = e.response?.data?.detail ?? 'Código inválido'
  } finally {
    validandoCodigo.value = false
  }
}

async function registrar() {
  if (formError.value) return
  serverError.value = ''
  saving.value = true
  try {
    const payload: RegistroEstudiantePayload = {
      codigo_clase: codigoInput.value.trim().toUpperCase(),
      nombres: form.value.nombres.trim(),
      apellidos: form.value.apellidos.trim(),
      password: form.value.password,
    }
    if (form.value.dni.trim()) payload.dni = form.value.dni.trim()
    const res = await registroService.registrarEstudiante(payload)
    success.value = { codigo: res.codigo_estudiante }
  } catch (e: any) {
    serverError.value = e.response?.data?.detail ?? 'Error al registrarse'
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-surface transition-colors duration-500 flex flex-col items-center justify-center p-6 relative overflow-hidden font-sans">
    
    <!-- Background Orbs -->
    <div class="absolute inset-0 pointer-events-none overflow-hidden">
        <div class="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-teal-500/5 dark:bg-emerald-500/10 rounded-full blur-[120px]"></div>
        <div class="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-emerald-500/5 dark:bg-emerald-500/10 rounded-full blur-[100px]"></div>
    </div>

    <!-- Theme Toggle -->
    <div class="absolute top-6 right-6 z-50">
        <ThemeToggle />
    </div>

    <div class="w-full max-w-md relative z-10">
      
      <!-- Top Branding -->
      <div class="text-center mb-10">
        <h1 class="text-3xl font-bold text-text tracking-tight">Registro SIEVA</h1>
        <p class="text-slate-500 dark:text-text-muted font-medium">Crea tu cuenta para rendir evaluaciones</p>
      </div>

      <!-- Main Container with Transition -->
      <Transition mode="out-in" enter-active-class="transition duration-500 ease-out" enter-from-class="transform scale-95 opacity-0" enter-to-class="transform scale-100 opacity-100">
        
        <!-- Success Card -->
        <div v-if="success" key="success" class="bg-surface rounded-2xl shadow-2xl border border-slate-300 dark:border-slate-800 p-10 text-center space-y-6">
          <div class="w-20 h-20 rounded-full bg-green-50 dark:bg-green-500/10 flex items-center justify-center mx-auto">
            <CheckCircle class="w-10 h-10 text-green-500" />
          </div>
          <div class="space-y-2">
            <h2 class="text-2xl font-bold text-text">¡Registro Exitoso!</h2>
            <p class="text-slate-500 dark:text-text-muted text-sm">Tu código de estudiante es:</p>
          </div>
          <div class="bg-surface border-2 border-dashed border-teal-500/30 rounded-2xl py-5 px-8 relative overflow-hidden group">
            <div class="absolute inset-0 bg-teal-500/5 translate-y-full group-hover:translate-y-0 transition-transform duration-500"></div>
            <span class="text-4xl font-mono font-black text-primary tracking-[0.2em] relative z-10">{{ success.codigo }}</span>
          </div>
          <div class="flex items-start gap-3 p-4 bg-amber-50 dark:bg-amber-500/10 rounded-2xl text-left border border-amber-100 dark:border-amber-500/20">
            <AlertCircle class="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <p class="text-[11px] font-bold text-amber-700 dark:text-amber-400 leading-normal uppercase">
              IMPORTANTE: Guarda este código. Lo usarás siempre para entrar al sistema.
            </p>
          </div>
          <button @click="router.push('/login')" class="w-full bg-slate-900 dark:bg-white text-white dark:text-text-inverse font-bold py-4 rounded-xl shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2">
            Ir al Inicio de Sesión
            <ArrowRight class="w-5 h-5" />
          </button>
        </div>

        <!-- Form Card -->
        <div v-else key="form" class="bg-surface rounded-2xl shadow-2xl border border-slate-300 dark:border-slate-800 overflow-hidden">
          
          <Transition mode="out-in" enter-active-class="transition duration-300 ease-out" enter-from-class="transform translate-x-8 opacity-0" enter-to-class="transform translate-x-0 opacity-100" leave-active-class="transition duration-200 ease-in" leave-from-class="transform translate-x-0 opacity-100" leave-to-class="transform -translate-x-8 opacity-0">
            
            <!-- Step: Código -->
            <div v-if="step === 'codigo'" key="step-codigo" class="p-8 sm:p-10 space-y-6">
              <div class="flex items-center gap-3 px-4 py-2 bg-emerald-500/5 border border-emerald-500/10 rounded-full w-fit">
                <Sparkles class="w-3.5 h-3.5 text-emerald-500" />
                <span class="text-[10px] font-bold text-emerald-600 dark:text-primary uppercase tracking-widest">Paso 1 de 2</span>
              </div>
              
              <div class="space-y-4">
                <div class="space-y-2">
                  <label class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest ml-1">Código de Aula</label>
                  <div class="relative group">
                    <GraduationCap class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-teal-500 transition-colors" />
                    <input
                      v-model="codigoInput"
                      @keyup.enter="validarCodigo"
                      type="text"
                      placeholder="Ej: AB3K7X2Q"
                      class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-4 pl-12 pr-4 text-sm font-bold text-slate-700 dark:text-text font-mono uppercase outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all"
                    />
                  </div>
                  <Transition enter-active-class="animate-shake">
                    <p v-if="codigoError" class="text-[10px] font-bold text-red-500 ml-1 flex items-center gap-1.5">
                      <AlertCircle class="w-3.5 h-3.5" /> {{ codigoError }}
                    </p>
                  </Transition>
                </div>
              </div>

              <button
                @click="validarCodigo"
                :disabled="validandoCodigo"
                class="w-full bg-slate-900 dark:bg-white text-white dark:text-text-inverse font-bold py-4 rounded-xl shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
              >
                <Loader2 v-if="validandoCodigo" class="w-5 h-5 animate-spin" />
                <span>Continuar Registro</span>
                <ArrowRight v-if="!validandoCodigo" class="w-5 h-5" />
              </button>

              <div class="pt-6 border-t border-slate-300 dark:border-slate-800 text-center">
                <p class="text-xs text-slate-500 dark:text-text-muted font-medium">
                  ¿Ya tienes una cuenta?
                  <button @click="router.push('/login')" class="text-primary font-bold hover:underline ml-1">Inicia sesión</button>
                </p>
              </div>
            </div>

            <!-- Step: Datos personales -->
            <div v-else key="step-datos" class="p-8 sm:p-10 space-y-6">
              <!-- Class Info Header -->
              <div v-if="codigoInfo" class="bg-gradient-to-br from-teal-500/10 to-emerald-500/10 border border-teal-500/20 rounded-2xl p-5 space-y-1">
                <p class="text-[10px] font-bold text-primary uppercase tracking-widest">Aula Identificada</p>
                <p class="text-sm font-bold text-text leading-tight">{{ codigoInfo.institucion }}</p>
                <p class="text-xs font-medium text-slate-500 dark:text-text-muted">{{ codigoInfo.grado }} — Sección {{ codigoInfo.seccion }}</p>
              </div>

              <div v-if="serverError" class="flex items-center gap-3 p-4 bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20 rounded-xl text-red-600 dark:text-red-400 text-xs font-bold animate-shake">
                <AlertCircle class="w-4 h-4 shrink-0" />
                {{ serverError }}
              </div>

              <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                  <div class="space-y-1.5">
                    <label class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest ml-1">Nombres</label>
                    <input v-model="form.nombres" type="text" placeholder="Ej: Juan"
                      class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-3 px-4 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
                  </div>
                  <div class="space-y-1.5">
                    <label class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest ml-1">Apellidos</label>
                    <input v-model="form.apellidos" type="text" placeholder="Ej: Perez"
                      class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-3 px-4 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
                  </div>
                </div>

                <div class="space-y-1.5">
                  <label class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest ml-1">DNI <span class="text-slate-300 font-medium tracking-normal capitalize">(Opcional)</span></label>
                  <input v-model="form.dni" type="text" placeholder="Ocho dígitos" maxlength="8"
                    class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-3 px-4 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div class="space-y-1.5">
                    <label class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest ml-1">Contraseña</label>
                    <div class="relative">
                      <input v-model="form.password" :type="showPass ? 'text' : 'password'" placeholder="••••"
                        class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-3 pl-4 pr-10 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
                      <button type="button" @click="showPass = !showPass" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors">
                        <Eye v-if="!showPass" class="w-4 h-4" /><EyeOff v-else class="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div class="space-y-1.5">
                    <label class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest ml-1">Confirmar</label>
                    <div class="relative">
                      <input v-model="form.confirm" :type="showConfirm ? 'text' : 'password'" placeholder="••••"
                        class="w-full bg-surface-input border border-slate-300 dark:border-slate-600 rounded-xl py-3 pl-4 pr-10 text-sm font-bold text-slate-700 dark:text-text outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
                      <button type="button" @click="showConfirm = !showConfirm" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors">
                        <Eye v-if="!showConfirm" class="w-4 h-4" /><EyeOff v-else class="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
                
                <Transition enter-active-class="animate-shake">
                  <p v-if="formError" class="text-[10px] font-bold text-red-500 ml-1 flex items-center gap-1.5">
                    <AlertCircle class="w-3.5 h-3.5" /> {{ formError }}
                  </p>
                </Transition>
              </div>

              <div class="flex flex-col sm:flex-row gap-3 pt-4">
                <button @click="step = 'codigo'" class="w-full sm:w-1/3 py-3 text-sm font-bold text-slate-500 dark:text-text-muted bg-slate-50 dark:bg-surface-card rounded-xl hover:bg-slate-100 dark:hover:bg-slate-700 transition-all flex items-center justify-center gap-2">
                  <ArrowLeft class="w-4 h-4" />
                  Atrás
                </button>
                <button
                  @click="registrar"
                  :disabled="saving || !!formError"
                  class="w-full sm:flex-1 py-3 bg-slate-900 dark:bg-white text-white dark:text-text-inverse font-bold text-sm rounded-xl shadow-xl hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
                  <span>Finalizar Registro</span>
                </button>
              </div>
            </div>
          </Transition>
        </div>
      </Transition>

      <p class="text-center text-[10px] text-slate-400 dark:text-text-subtle font-bold uppercase tracking-[0.2em] mt-10">
        © 2026 DIRECCIÓN REGIONAL DE EDUCACIÓN HUÁNUCO
      </p>
    </div>
  </div>
</template>

<style scoped>
@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
    20%, 40%, 60%, 80% { transform: translateX(2px); }
}
.animate-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }
</style>
