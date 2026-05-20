<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { formatFechaLarga } from '../utils/dateUtils'
import { apiClient } from '../services/api'
import ThemeToggle from './ThemeToggle.vue'
import {
  Palette, LogOut, ChevronDown, User, Shield, KeyRound, X,
  Loader2, Eye, EyeOff, AlertCircle, CheckCircle, MapPin,
  Building2, BadgeCheck, CalendarDays, Info, Fingerprint
} from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const isOpen = ref(false)
const container = ref<HTMLElement | null>(null)

// Perfil modal
const showPerfilModal = ref(false)

const openPerfilModal = () => {
  isOpen.value = false
  showPerfilModal.value = true
}

// Password change modal
const showPasswordModal = ref(false)
const savingPassword = ref(false)
const passwordError = ref('')
const passwordSuccess = ref(false)
const showCurrent = ref(false)
const showNew = ref(false)
const showConfirm = ref(false)

const passwordForm = ref({
  current: '',
  newPass: '',
  confirm: '',
})

const ROL_LABELS: Record<string, string> = {
  especialista_dre_comunicacion: 'Esp. DRE Comunicación',
  especialista_dre_matematica: 'Esp. DRE Matemática',
  responsable_ugel: 'Responsable UGEL',
  director: 'Director',
  auxiliar: 'Auxiliar',
  docente: 'Docente',
  estudiante: 'Estudiante',
}

function rolLabel(codigo?: string | null) {
  return ROL_LABELS[codigo ?? ''] ?? codigo ?? '—'
}

const initials = computed(() => {
  const user = auth.user
  if (!user) return '?'
  const names = [user.nombres, user.apellidos].filter((n): n is string => !!n)
  if (names.length === 0) return (user.dni ?? user.codigo_estudiante ?? 'US').slice(0, 2).toUpperCase()
  return names.map(n => n.charAt(0).toUpperCase()).join('').slice(0, 2)
})

const handleLogout = () => {
  isOpen.value = false
  auth.logout()
  router.push('/login')
}

const openPasswordModal = () => {
  isOpen.value = false
  passwordForm.value = { current: '', newPass: '', confirm: '' }
  passwordError.value = ''
  passwordSuccess.value = false
  showCurrent.value = false
  showNew.value = false
  showConfirm.value = false
  showPasswordModal.value = true
}

const savePassword = async () => {
  passwordError.value = ''
  passwordSuccess.value = false

  if (!passwordForm.value.current) {
    passwordError.value = 'Ingresa tu contraseña actual'
    return
  }
  if (passwordForm.value.newPass.length < 6) {
    passwordError.value = 'La nueva contraseña debe tener al menos 6 caracteres'
    return
  }
  if (passwordForm.value.newPass !== passwordForm.value.confirm) {
    passwordError.value = 'Las contraseñas no coinciden'
    return
  }

  savingPassword.value = true
  try {
    await apiClient.put('/auth/me/password', {
      current_password: passwordForm.value.current,
      new_password: passwordForm.value.newPass,
    })
    passwordSuccess.value = true
    passwordForm.value = { current: '', newPass: '', confirm: '' }
  } catch (e: any) {
    passwordError.value = e.response?.data?.detail ?? 'Error al cambiar la contraseña'
  } finally {
    savingPassword.value = false
  }
}

const handleClickOutside = (e: MouseEvent) => {
  if (container.value && !container.value.contains(e.target as Node)) {
    isOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', handleClickOutside))
onUnmounted(() => document.removeEventListener('click', handleClickOutside))
</script>

<template>
  <div ref="container" class="relative">
    <!-- Trigger Button -->
    <button
      @click="isOpen = !isOpen"
      class="group flex items-center gap-2 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md text-slate-700 dark:text-slate-200 pl-1.5 pr-3 py-1.5 rounded-full shadow-lg border border-slate-300 dark:border-slate-800 hover:bg-white dark:hover:bg-slate-800 transition-all duration-300 active:scale-95"
    >
      <!-- Avatar -->
      <div class="w-8 h-8 rounded-full bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center text-white text-[10px] font-black shrink-0 shadow-md group-hover:scale-105 transition-transform">
        {{ initials }}
      </div>
      <div class="hidden sm:flex flex-col items-start leading-none gap-0.5">
        <span class="max-w-[120px] truncate font-bold text-[11px]">{{ auth.displayName }}</span>
        <span class="text-[9px] font-black text-slate-400 uppercase tracking-tighter">{{ rolLabel(auth.user?.rol_codigo) }}</span>
      </div>
      <ChevronDown class="w-3.5 h-3.5 text-slate-400 transition-transform duration-300" :class="{ 'rotate-180': isOpen }" />
    </button>

    <!-- Dropdown -->
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 translate-y-2 scale-95"
      enter-to-class="opacity-100 translate-y-0 scale-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0 scale-100"
      leave-to-class="opacity-0 translate-y-2 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 top-full mt-3 w-72 bg-white dark:bg-slate-900 rounded-[2rem] shadow-2xl border border-slate-300 dark:border-slate-800 overflow-hidden z-50 animate-in fade-in zoom-in duration-200"
      >
        <!-- User info -->
        <div class="p-6 border-b border-slate-50 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/30">
          <div class="flex items-center gap-4">
            <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center text-white font-black text-sm shrink-0 shadow-xl shadow-teal-500/20">
              {{ initials }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-bold text-slate-900 dark:text-white text-sm truncate leading-tight">{{ auth.displayName }}</p>
              <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mt-1">DNI: {{ auth.user?.dni }}</p>
            </div>
          </div>
          
          <div v-if="auth.isAdmin" class="mt-4">
            <span class="inline-flex items-center gap-1.5 text-[10px] font-black text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-3 py-1 rounded-full uppercase tracking-widest border border-indigo-100 dark:border-indigo-800/50">
              <Shield class="w-3 h-3" /> Administrador
            </span>
          </div>
        </div>

        <!-- Actions -->
        <div class="p-3 space-y-1">
          <button
            @click="openPerfilModal"
            class="group w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-2xl transition-all font-bold"
          >
            <div class="w-8 h-8 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center group-hover:bg-teal-500 group-hover:text-white transition-colors">
              <User class="w-4 h-4" />
            </div>
            <span>Mis Datos Personales</span>
          </button>
          
          <button
            @click="openPasswordModal"
            class="group w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 rounded-2xl transition-all font-bold"
          >
            <div class="w-8 h-8 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center group-hover:bg-indigo-500 group-hover:text-white transition-colors">
              <KeyRound class="w-4 h-4" />
            </div>
            <span>Cambiar Contraseña</span>
          </button>

          <div class="w-full flex items-center justify-between px-4 py-2 hover:bg-slate-50 dark:hover:bg-slate-800/50 rounded-2xl transition-colors font-bold">
            <div class="flex items-center gap-3 text-sm text-slate-600 dark:text-slate-300">
              <div class="w-8 h-8 rounded-xl bg-slate-100 dark:bg-slate-800 flex items-center justify-center">
                <Palette class="w-4 h-4" />
              </div>
              <span>Tema Oscuro</span>
            </div>
            <ThemeToggle />
          </div>

          <div class="my-2 border-t border-slate-50 dark:border-slate-800/50"></div>

          <button
            @click="handleLogout"
            class="group w-full flex items-center gap-3 px-4 py-3 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-2xl transition-all font-bold"
          >
            <div class="w-8 h-8 rounded-xl bg-red-100 dark:bg-red-900/30 flex items-center justify-center group-hover:bg-red-500 group-hover:text-white transition-colors">
              <LogOut class="w-4 h-4" />
            </div>
            <span>Cerrar Sesión</span>
          </button>
        </div>
      </div>
    </Transition>
  </div>

  <!-- Perfil Modal (Bottom Sheet on Mobile) -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="showPerfilModal" class="fixed inset-0 z-[300] bg-slate-900/60 backdrop-blur-sm" @click.self="showPerfilModal = false">
        <div class="fixed inset-x-0 bottom-0 sm:inset-0 flex items-end sm:items-center justify-center sm:p-6 pointer-events-none">
          <div class="bg-white dark:bg-slate-900 w-full sm:max-w-xl max-h-[90vh] sm:max-h-none sm:h-auto flex flex-col rounded-t-[2.5rem] sm:rounded-[2.5rem] shadow-2xl overflow-hidden pointer-events-auto transform transition-transform duration-500 ease-out translate-y-0"
               :class="showPerfilModal ? 'translate-y-0' : 'translate-y-full sm:translate-y-0'">

            <!-- Drag handle mobile -->
            <div class="sm:hidden flex justify-center pt-4 pb-2 shrink-0 cursor-pointer" @click="showPerfilModal = false">
              <div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-slate-800"></div>
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between px-8 py-6 border-b border-slate-300 dark:border-slate-800">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center text-white font-black text-lg shrink-0 shadow-lg shadow-teal-500/20">
                  <User class="w-6 h-6" />
                </div>
                <div>
                  <h2 class="text-xl font-bold text-slate-900 dark:text-white leading-tight">Perfil de Usuario</h2>
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mt-0.5">Información Personal</p>
                </div>
              </div>
              <button @click="showPerfilModal = false" class="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Body -->
            <div class="overflow-y-auto p-8 space-y-8 custom-scrollbar">
              
              <!-- Aviso solo lectura -->
              <div class="flex items-start gap-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-100 dark:border-indigo-800/50 text-indigo-700 dark:text-indigo-400 p-4 rounded-[1.5rem] text-xs font-medium leading-relaxed">
                <Info class="w-4 h-4 shrink-0 mt-0.5" />
                <span>Esta es una vista informativa. Si necesitas actualizar algún dato, por favor contacta con el equipo de soporte técnico.</span>
              </div>

              <!-- Data Sections -->
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <!-- Personales -->
                <div class="space-y-6">
                  <h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                    <Fingerprint class="w-3.5 h-3.5" /> Identidad
                  </h3>
                  <div class="space-y-4">
                    <div class="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl border border-transparent hover:border-slate-300 dark:hover:border-slate-700 transition-all">
                      <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">DNI</p>
                      <p class="text-sm font-black text-slate-800 dark:text-slate-200 font-mono">{{ auth.user?.dni }}</p>
                    </div>
                    <div class="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl border border-transparent hover:border-slate-300 dark:hover:border-slate-700 transition-all">
                      <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">Nombre Completo</p>
                      <p class="text-sm font-bold text-slate-800 dark:text-slate-200">{{ [auth.user?.nombres, auth.user?.apellidos].filter(Boolean).join(' ') || '—' }}</p>
                    </div>
                  </div>
                </div>

                <!-- Institucional -->
                <div class="space-y-6">
                  <h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                    <Building2 class="w-3.5 h-3.5" /> Organización
                  </h3>
                  <div class="space-y-4">
                    <div class="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl border border-transparent hover:border-slate-300 dark:hover:border-slate-700 transition-all">
                      <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">Institución</p>
                      <p class="text-sm font-bold text-slate-800 dark:text-slate-200 truncate">{{ auth.user?.institucion_nombre || 'No asignada' }}</p>
                    </div>
                    <div class="bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl border border-transparent hover:border-slate-300 dark:hover:border-slate-700 transition-all">
                      <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest mb-1">UGEL</p>
                      <p class="text-sm font-bold text-slate-800 dark:text-slate-200">{{ auth.user?.ugel_nombre || 'No asignada' }}</p>
                    </div>
                  </div>
                </div>

                <!-- Ubicación -->
                <div class="space-y-6 sm:col-span-2">
                  <h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                    <MapPin class="w-3.5 h-3.5" /> Ubicación Geográfica
                  </h3>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div class="flex items-center gap-4 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl">
                      <div class="w-10 h-10 rounded-xl bg-white dark:bg-slate-700 flex items-center justify-center text-teal-500 shadow-sm">
                        <MapPin class="w-5 h-5" />
                      </div>
                      <div>
                        <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Provincia</p>
                        <p class="text-sm font-bold text-slate-800 dark:text-slate-200">{{ auth.user?.provincia_nombre || '—' }}</p>
                      </div>
                    </div>
                    <div class="flex items-center gap-4 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl">
                      <div class="w-10 h-10 rounded-xl bg-white dark:bg-slate-700 flex items-center justify-center text-indigo-500 shadow-sm">
                        <MapPin class="w-5 h-5" />
                      </div>
                      <div>
                        <p class="text-[9px] font-bold text-slate-400 uppercase tracking-widest">Distrito</p>
                        <p class="text-sm font-bold text-slate-800 dark:text-slate-200">{{ auth.user?.distrito_nombre || '—' }}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Cuenta -->
                <div class="space-y-6 sm:col-span-2">
                  <h3 class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] flex items-center gap-2">
                    <BadgeCheck class="w-3.5 h-3.5" /> Detalles de Cuenta
                  </h3>
                  <div class="flex flex-wrap gap-4">
                    <div class="flex items-center gap-2 px-4 py-2 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-full text-xs font-black uppercase tracking-widest border border-emerald-100 dark:border-emerald-800/50">
                      <div class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                      {{ auth.user?.is_active ? 'Usuario Activo' : 'Inactivo' }}
                    </div>
                    <div class="flex items-center gap-2 px-4 py-2 bg-indigo-50 dark:bg-indigo-900/20 text-indigo-600 dark:text-indigo-400 rounded-full text-xs font-black uppercase tracking-widest border border-indigo-100 dark:border-indigo-800/50">
                      <Shield class="w-3.5 h-3.5" />
                      {{ rolLabel(auth.user?.rol_codigo) }}
                    </div>
                    <div v-if="auth.user?.fecha_creacion" class="flex items-center gap-2 px-4 py-2 bg-slate-50 dark:bg-slate-800/50 text-slate-600 dark:text-slate-400 rounded-full text-xs font-black uppercase tracking-widest border border-slate-300 dark:border-slate-800">
                      <CalendarDays class="w-3.5 h-3.5" />
                      Miembro desde {{ formatFechaLarga(auth.user.fecha_creacion) }}
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="px-8 py-6 border-t border-slate-300 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 flex justify-end">
              <button @click="showPerfilModal = false"
                class="px-8 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-black text-sm rounded-2xl shadow-xl hover:scale-105 active:scale-95 transition-all">
                Entendido
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Password Modal (Bottom Sheet on Mobile) -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-300 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-200 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="showPasswordModal" class="fixed inset-0 z-[300] bg-slate-900/60 backdrop-blur-sm" @click.self="showPasswordModal = false">
        <div class="fixed inset-x-0 bottom-0 sm:inset-0 flex items-end sm:items-center justify-center sm:p-6 pointer-events-none">
          <div class="bg-white dark:bg-slate-900 w-full sm:max-w-md max-h-[90vh] sm:max-h-none sm:h-auto flex flex-col rounded-t-[2.5rem] sm:rounded-[2.5rem] shadow-2xl overflow-hidden pointer-events-auto transform transition-transform duration-500 ease-out translate-y-0">

            <!-- Drag handle mobile -->
            <div class="sm:hidden flex justify-center pt-4 pb-2 shrink-0 cursor-pointer" @click="showPasswordModal = false">
              <div class="w-12 h-1.5 rounded-full bg-slate-200 dark:bg-slate-800"></div>
            </div>

            <!-- Header -->
            <div class="flex items-center justify-between px-8 py-6 border-b border-slate-300 dark:border-slate-800">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-black text-lg shrink-0 shadow-lg shadow-indigo-500/20">
                  <KeyRound class="w-6 h-6" />
                </div>
                <div>
                  <h2 class="text-xl font-bold text-slate-900 dark:text-white leading-tight">Seguridad</h2>
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.2em] mt-0.5">Actualizar Contraseña</p>
                </div>
              </div>
              <button @click="showPasswordModal = false" class="p-2 text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 rounded-xl transition-all">
                <X class="w-5 h-5" />
              </button>
            </div>

            <!-- Body -->
            <div class="p-8 space-y-6">
              
              <!-- Alerts -->
              <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0">
                <div v-if="passwordError" class="flex items-start gap-3 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-4 rounded-2xl text-xs font-bold border border-red-100 dark:border-red-900/50 shadow-sm">
                  <AlertCircle class="w-4 h-4 shrink-0 mt-0.5" />
                  {{ passwordError }}
                </div>
              </Transition>

              <Transition enter-active-class="transition duration-200 ease-out" enter-from-class="opacity-0 -translate-y-2" enter-to-class="opacity-100 translate-y-0">
                <div v-if="passwordSuccess" class="flex items-center gap-3 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 p-4 rounded-2xl text-xs font-bold border border-emerald-100 dark:border-emerald-900/50 shadow-sm">
                  <CheckCircle class="w-4 h-4 shrink-0" />
                  ¡La contraseña se actualizó correctamente!
                </div>
              </Transition>

              <!-- Inputs -->
              <div class="space-y-4">
                <!-- Current password -->
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1">Contraseña Actual</label>
                  <div class="relative group">
                    <input
                      v-model="passwordForm.current"
                      :type="showCurrent ? 'text' : 'password'"
                      placeholder="••••••••"
                      class="w-full h-14 bg-slate-50 dark:bg-slate-800/50 border border-slate-300 dark:border-slate-800 rounded-2xl pl-12 pr-12 text-sm text-slate-900 dark:text-white outline-none focus:ring-4 focus:ring-teal-500/10 focus:border-teal-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-600"
                    />
                    <KeyRound class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-teal-500 transition-colors" />
                    <button type="button" @click="showCurrent = !showCurrent" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white p-1">
                      <Eye v-if="!showCurrent" class="w-4 h-4" />
                      <EyeOff v-else class="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <!-- New password -->
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1">Nueva Contraseña</label>
                  <div class="relative group">
                    <input
                      v-model="passwordForm.newPass"
                      :type="showNew ? 'text' : 'password'"
                      placeholder="Mínimo 6 caracteres"
                      class="w-full h-14 bg-slate-50 dark:bg-slate-800/50 border border-slate-300 dark:border-slate-800 rounded-2xl pl-12 pr-12 text-sm text-slate-900 dark:text-white outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-600"
                    />
                    <Shield class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    <button type="button" @click="showNew = !showNew" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white p-1">
                      <Eye v-if="!showNew" class="w-4 h-4" />
                      <EyeOff v-else class="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <!-- Confirm password -->
                <div class="space-y-1.5">
                  <label class="text-[10px] font-black text-slate-400 uppercase tracking-widest pl-1">Confirmar Contraseña</label>
                  <div class="relative group">
                    <input
                      v-model="passwordForm.confirm"
                      :type="showConfirm ? 'text' : 'password'"
                      placeholder="Repite la contraseña"
                      class="w-full h-14 bg-slate-50 dark:bg-slate-800/50 border border-slate-300 dark:border-slate-800 rounded-2xl pl-12 pr-12 text-sm text-slate-900 dark:text-white outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-slate-300 dark:placeholder:text-slate-600"
                    />
                    <BadgeCheck class="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-indigo-500 transition-colors" />
                    <button type="button" @click="showConfirm = !showConfirm" class="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-white p-1">
                      <Eye v-if="!showConfirm" class="w-4 h-4" />
                      <EyeOff v-else class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="p-8 border-t border-slate-300 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-800/50 flex gap-3">
              <button @click="showPasswordModal = false"
                class="flex-1 h-12 rounded-2xl border border-slate-300 dark:border-slate-700 text-slate-600 dark:text-slate-300 font-bold text-sm hover:bg-white dark:hover:bg-slate-700 transition-all">
                Cancelar
              </button>
              <button
                @click="savePassword"
                :disabled="savingPassword"
                class="flex-[2] h-12 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-black text-sm rounded-2xl shadow-xl shadow-teal-500/20 transition-all disabled:opacity-50 flex items-center justify-center gap-2 active:scale-95">
                <Loader2 v-if="savingPassword" class="w-4 h-4 animate-spin" />
                <span>Actualizar Contraseña</span>
              </button>
            </div>

          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}
.custom-scrollbar:hover::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.4);
}
</style>
