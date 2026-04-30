<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useTheme } from '../../shared/composables/useTheme'
import { BookOpen, GraduationCap, BarChart3, ChevronRight, Sun, Moon } from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const { isDark, toggleTheme } = useTheme()

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Buenos días'
  if (hour < 18) return 'Buenas tardes'
  return 'Buenas noches'
})
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-teal-50 to-indigo-50 dark:from-slate-900 dark:to-slate-800">
    <!-- Header simple para estudiantes -->
    <header class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-700 sticky top-0 z-40">
      <div class="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center">
            <GraduationCap class="w-4 h-4 text-white" />
          </div>
          <span class="font-bold text-slate-800 dark:text-white text-sm">LectoSistem</span>
        </div>
        <div class="flex items-center gap-3">
          <span class="text-xs text-slate-500 dark:text-slate-400 font-mono">{{ auth.user?.codigo_estudiante }}</span>
          <button @click="toggleTheme()"
            class="p-1.5 rounded-xl text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
            <Sun v-if="isDark" class="w-4 h-4" />
            <Moon v-else class="w-4 h-4" />
          </button>
          <button @click="auth.logout(); router.push('/login')"
            class="text-xs text-slate-500 hover:text-red-500 transition-colors">
            Salir
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8">
      <!-- Bienvenida -->
      <div class="mb-8">
        <p class="text-slate-500 dark:text-slate-400 text-sm">{{ greeting }},</p>
        <h1 class="text-2xl font-bold text-slate-800 dark:text-white mt-0.5">{{ auth.displayName || auth.user?.codigo_estudiante }}</h1>
        <p v-if="auth.displayName && auth.user?.codigo_estudiante" class="text-sm font-mono text-slate-500 dark:text-slate-400 mt-1">
          Código: {{ auth.user.codigo_estudiante }}
        </p>
        <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
          {{ auth.user?.institucion_nombre }}
        </p>
        <p v-if="auth.user?.grado_nombre || auth.user?.seccion" class="text-xs text-slate-400 dark:text-slate-500 mt-0.5 flex items-center gap-1.5">
          <GraduationCap class="w-3 h-3" />
          <span v-if="auth.user?.grado_nombre">{{ auth.user.grado_nombre }}</span>
          <span v-if="auth.user?.grado_nombre && auth.user?.seccion">—</span>
          <span v-if="auth.user?.seccion">Sección {{ auth.user.seccion }}</span>
        </p>
      </div>

      <!-- Tarjetas de acceso rápido -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <button
          @click="router.push('/estudiante/examenes')"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm hover:shadow-md transition-all text-left group"
        >
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center mb-4">
            <BookOpen class="w-6 h-6 text-white" />
          </div>
          <h3 class="font-bold text-slate-800 dark:text-white text-lg">Mis Exámenes</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Ver y rendir los exámenes asignados por tu docente</p>
          <div class="flex items-center gap-1 mt-4 text-teal-600 dark:text-teal-400 text-sm font-semibold group-hover:gap-2 transition-all">
            Ver exámenes <ChevronRight class="w-4 h-4" />
          </div>
        </button>

        <button
          @click="router.push('/estudiante/progreso')"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm hover:shadow-md transition-all text-left group"
        >
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center mb-4">
            <BarChart3 class="w-6 h-6 text-white" />
          </div>
          <h3 class="font-bold text-slate-800 dark:text-white text-lg">Mi Progreso</h3>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">Revisa tus resultados y nivel de logro actual</p>
          <div class="flex items-center gap-1 mt-4 text-indigo-600 dark:text-indigo-400 text-sm font-semibold group-hover:gap-2 transition-all">
            Ver progreso <ChevronRight class="w-4 h-4" />
          </div>
        </button>
      </div>


    </main>
  </div>
</template>
