<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { apiClient } from '../services/api'
import { LogOut, ChevronDown, User, Shield, KeyRound, X, Loader2, Eye, EyeOff, AlertCircle, CheckCircle } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const isOpen = ref(false)
const container = ref<HTMLElement | null>(null)

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

const initials = computed(() => {
  const user = auth.user
  if (!user) return '?'
  const names = [user.nombres, user.apellidos].filter((n): n is string => !!n)
  if (names.length === 0) return user.dni.slice(0, 2).toUpperCase()
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
    <button
      @click="isOpen = !isOpen"
      class="flex items-center gap-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur-md text-slate-700 dark:text-slate-200 px-3 py-2 rounded-full shadow-xl border border-slate-100 dark:border-slate-700 hover:bg-white dark:hover:bg-slate-700 transition-all duration-200 text-sm font-medium"
    >
      <!-- Avatar -->
      <div class="w-7 h-7 rounded-full bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
        {{ initials }}
      </div>
      <span class="hidden sm:block max-w-[140px] truncate">{{ auth.displayName }}</span>
      <Shield v-if="auth.isAdmin" class="w-3.5 h-3.5 text-indigo-500 shrink-0" />
      <ChevronDown class="w-3.5 h-3.5 shrink-0 transition-transform" :class="{ 'rotate-180': isOpen }" />
    </button>

    <!-- Dropdown -->
    <Transition
      enter-active-class="transition ease-out duration-150"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition ease-in duration-100"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 top-full mt-2 w-64 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-slate-100 dark:border-slate-700 overflow-hidden z-50"
      >
        <!-- User info -->
        <div class="p-4 border-b border-slate-100 dark:border-slate-700">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-full bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center text-white font-bold shrink-0">
              {{ initials }}
            </div>
            <div class="flex-1 min-w-0">
              <p class="font-semibold text-slate-800 dark:text-white text-sm truncate">{{ auth.displayName }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">DNI: {{ auth.user?.dni }}</p>
              <span
                v-if="auth.isAdmin"
                class="inline-flex items-center gap-1 text-[10px] font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 px-2 py-0.5 rounded-full mt-1"
              >
                <Shield class="w-2.5 h-2.5" /> Administrador
              </span>
            </div>
          </div>
          <div v-if="auth.user?.profesion || auth.user?.institucion_educativa" class="mt-3 space-y-1">
            <p v-if="auth.user?.profesion" class="text-xs text-slate-600 dark:text-slate-300 flex items-center gap-1.5">
              <User class="w-3 h-3 text-slate-400 shrink-0" />
              {{ auth.user.profesion }}
            </p>
            <p v-if="auth.user?.institucion_educativa" class="text-xs text-slate-500 dark:text-slate-400 truncate pl-4">
              {{ auth.user.institucion_educativa }}
            </p>
          </div>
        </div>

        <!-- Actions -->
        <div class="p-2 space-y-0.5">
          <button
            @click="openPasswordModal"
            class="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 rounded-xl transition-colors font-medium"
          >
            <KeyRound class="w-4 h-4" />
            Cambiar Contraseña
          </button>
          <button
            @click="handleLogout"
            class="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors font-medium"
          >
            <LogOut class="w-4 h-4" />
            Cerrar Sesión
          </button>
        </div>
      </div>
    </Transition>
  </div>

  <!-- Change Password Modal -->
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="showPasswordModal"
        class="fixed inset-0 z-[300] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
        @click.self="showPasswordModal = false"
      >
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-sm">

          <!-- Header -->
          <div class="flex items-center justify-between p-5 border-b border-slate-100 dark:border-slate-700">
            <div class="flex items-center gap-2">
              <KeyRound class="w-5 h-5 text-teal-500" />
              <h2 class="text-base font-bold text-slate-800 dark:text-white">Cambiar Contraseña</h2>
            </div>
            <button @click="showPasswordModal = false" class="p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-lg transition-colors">
              <X class="w-4 h-4" />
            </button>
          </div>

          <!-- Body -->
          <div class="p-5 space-y-3.5">

            <div v-if="passwordError" class="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 p-3 rounded-xl text-xs border border-red-100 dark:border-red-900/50">
              <AlertCircle class="w-3.5 h-3.5 shrink-0 mt-0.5" />
              {{ passwordError }}
            </div>

            <div v-if="passwordSuccess" class="flex items-center gap-2 bg-green-50 dark:bg-green-900/20 text-green-600 dark:text-green-400 p-3 rounded-xl text-xs border border-green-100 dark:border-green-900/50">
              <CheckCircle class="w-3.5 h-3.5 shrink-0" />
              ¡Contraseña actualizada correctamente!
            </div>

            <!-- Current password -->
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Contraseña actual</label>
              <div class="relative">
                <input
                  v-model="passwordForm.current"
                  :type="showCurrent ? 'text' : 'password'"
                  placeholder="Tu contraseña actual"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 pl-3.5 pr-9 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all"
                />
                <button type="button" @click="showCurrent = !showCurrent" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                  <Eye v-if="!showCurrent" class="w-3.5 h-3.5" />
                  <EyeOff v-else class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <!-- New password -->
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Nueva contraseña</label>
              <div class="relative">
                <input
                  v-model="passwordForm.newPass"
                  :type="showNew ? 'text' : 'password'"
                  placeholder="Mínimo 6 caracteres"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 pl-3.5 pr-9 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all"
                />
                <button type="button" @click="showNew = !showNew" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                  <Eye v-if="!showNew" class="w-3.5 h-3.5" />
                  <EyeOff v-else class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            <!-- Confirm password -->
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5">Confirmar nueva contraseña</label>
              <div class="relative">
                <input
                  v-model="passwordForm.confirm"
                  :type="showConfirm ? 'text' : 'password'"
                  placeholder="Repite la nueva contraseña"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 pl-3.5 pr-9 text-sm text-slate-700 dark:text-slate-200 outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all"
                />
                <button type="button" @click="showConfirm = !showConfirm" class="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                  <Eye v-if="!showConfirm" class="w-3.5 h-3.5" />
                  <EyeOff v-else class="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

          </div>

          <!-- Footer -->
          <div class="flex justify-end gap-2 px-5 py-4 border-t border-slate-100 dark:border-slate-700">
            <button
              @click="showPasswordModal = false"
              class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors"
            >
              Cancelar
            </button>
            <button
              @click="savePassword"
              :disabled="savingPassword"
              class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-70 disabled:cursor-not-allowed"
            >
              <Loader2 v-if="savingPassword" class="w-3.5 h-3.5 animate-spin" />
              Actualizar
            </button>
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>
