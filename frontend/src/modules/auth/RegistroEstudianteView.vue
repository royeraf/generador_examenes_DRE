<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { registroService, type RegistroEstudiantePayload } from '../../shared/services/api'
import { Eye, EyeOff, AlertCircle, CheckCircle, GraduationCap, Loader2 } from 'lucide-vue-next'

const router = useRouter()

const step = ref<'codigo' | 'datos'>('codigo')
const codigoInput = ref('')
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
  if (form.value.password.length < 4) return 'La contraseña debe tener al menos 4 caracteres'
  if (form.value.password !== form.value.confirm) return 'Las contraseñas no coinciden'
  return ''
})

async function validarCodigo() {
  codigoError.value = ''
  if (!codigoInput.value.trim()) {
    codigoError.value = 'Ingresa el código de clase'
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
  <div class="min-h-screen bg-gradient-to-br from-teal-50 to-indigo-50 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center p-4">
    <div class="w-full max-w-md">

      <!-- Logo / título -->
      <div class="text-center mb-8">
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-teal-500 to-indigo-600 mb-4 shadow-lg">
          <GraduationCap class="w-7 h-7 text-white" />
        </div>
        <h1 class="text-2xl font-bold text-slate-800 dark:text-white">Registro de Estudiante</h1>
        <p class="text-slate-500 dark:text-slate-400 text-sm mt-1">Ingresa el código de clase de tu docente</p>
      </div>

      <!-- Éxito -->
      <div v-if="success" class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl p-8 text-center space-y-4">
        <div class="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto">
          <CheckCircle class="w-8 h-8 text-green-500" />
        </div>
        <h2 class="text-xl font-bold text-slate-800 dark:text-white">Registro exitoso</h2>
        <p class="text-slate-600 dark:text-slate-300 text-sm">Tu código de estudiante es:</p>
        <div class="bg-slate-100 dark:bg-slate-700 rounded-xl py-3 px-6">
          <span class="text-2xl font-mono font-bold text-teal-600 dark:text-teal-400 tracking-widest">{{ success.codigo }}</span>
        </div>
        <p class="text-xs text-slate-500 dark:text-slate-400">Guarda este código, lo necesitarás para iniciar sesión junto con tu contraseña.</p>
        <button
          @click="router.push('/login')"
          class="w-full py-3 bg-gradient-to-r from-teal-500 to-indigo-600 text-white font-bold rounded-xl shadow hover:from-teal-600 hover:to-indigo-700 transition-all"
        >
          Iniciar sesión
        </button>
      </div>

      <!-- Formulario -->
      <div v-else class="bg-white dark:bg-slate-800 rounded-2xl shadow-xl overflow-hidden">

        <!-- Step: Código -->
        <div v-if="step === 'codigo'" class="p-8 space-y-5">
          <div>
            <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Código de clase</label>
            <input
              v-model="codigoInput"
              @keyup.enter="validarCodigo"
              type="text"
              placeholder="Ej: AB3K7X2Q"
              class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-3 px-4 text-sm text-slate-700 dark:text-slate-200 font-mono uppercase outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all"
            />
            <p v-if="codigoError" class="mt-1.5 text-xs text-red-500 flex items-center gap-1">
              <AlertCircle class="w-3 h-3" /> {{ codigoError }}
            </p>
          </div>
          <button
            @click="validarCodigo"
            :disabled="validandoCodigo"
            class="w-full py-3 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold rounded-xl shadow transition-all disabled:opacity-70 flex items-center justify-center gap-2"
          >
            <Loader2 v-if="validandoCodigo" class="w-4 h-4 animate-spin" />
            Continuar
          </button>
          <p class="text-center text-xs text-slate-500 dark:text-slate-400">
            Ya tienes cuenta?
            <button @click="router.push('/login')" class="text-teal-600 dark:text-teal-400 font-semibold hover:underline">Iniciar sesión</button>
          </p>
        </div>

        <!-- Step: Datos personales -->
        <div v-else class="p-8 space-y-4">
          <!-- Info de la clase -->
          <div v-if="codigoInfo" class="bg-teal-50 dark:bg-teal-900/20 border border-teal-200 dark:border-teal-700/50 rounded-xl p-3 text-xs text-teal-700 dark:text-teal-300">
            <p class="font-semibold">{{ codigoInfo.institucion }}</p>
            <p>{{ codigoInfo.grado }} — Sección {{ codigoInfo.seccion }}</p>
          </div>

          <div v-if="serverError" class="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-xs border border-red-100 dark:border-red-900/50">
            <AlertCircle class="w-3.5 h-3.5 shrink-0 mt-0.5" />
            {{ serverError }}
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Nombres</label>
              <input v-model="form.nombres" type="text" placeholder="Tus nombres"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-400 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Apellidos</label>
              <input v-model="form.apellidos" type="text" placeholder="Tus apellidos"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-400 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">DNI <span class="text-slate-400 font-normal">(opcional)</span></label>
            <input v-model="form.dni" type="text" placeholder="12345678" maxlength="8"
              class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-700 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-400 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Contraseña</label>
            <div class="relative">
              <input v-model="form.password" :type="showPass ? 'text' : 'password'" placeholder="Mínimo 4 caracteres"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 pl-3.5 pr-9 text-sm text-slate-700 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-400 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
              <button type="button" @click="showPass = !showPass" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                <Eye v-if="!showPass" class="w-3.5 h-3.5" /><EyeOff v-else class="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Confirmar contraseña</label>
            <div class="relative">
              <input v-model="form.confirm" :type="showConfirm ? 'text' : 'password'" placeholder="Repite tu contraseña"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 pl-3.5 pr-9 text-sm text-slate-700 dark:text-slate-200 placeholder-slate-400 dark:placeholder-slate-400 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
              <button type="button" @click="showConfirm = !showConfirm" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">
                <Eye v-if="!showConfirm" class="w-3.5 h-3.5" /><EyeOff v-else class="w-3.5 h-3.5" />
              </button>
            </div>
            <p v-if="formError" class="mt-1 text-xs text-red-500 flex items-center gap-1">
              <AlertCircle class="w-3 h-3" /> {{ formError }}
            </p>
          </div>

          <div class="flex gap-2 pt-1">
            <button @click="step = 'codigo'" class="px-4 py-2.5 text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-700 rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors">
              Volver
            </button>
            <button
              @click="registrar"
              :disabled="saving || !!formError"
              class="flex-1 py-2.5 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-70 flex items-center justify-center gap-2"
            >
              <Loader2 v-if="saving" class="w-4 h-4 animate-spin" />
              Registrarme
            </button>
          </div>
        </div>

      </div>
    </div>
  </div>
</template>
