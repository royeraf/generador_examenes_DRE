<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { useTheme } from '../../shared/composables/useTheme'
import { apiClient } from '../../shared/services/api'
import {
  BookOpen, BarChart3, Sun, Moon, LogOut, Zap, Star,
  Trophy, Flame, Target, ChevronRight, Sparkles, Medal,
  Rocket, GraduationCap, Sprout, Library,
} from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()
const { isDark, toggleTheme } = useTheme()

interface ProgresoArea {
  area: string
  total_examenes_completados: number
  puntaje_promedio: number
  nivel_logro_actual: string | null
}

const progreso = ref<ProgresoArea[]>([])
const examensPendientes = ref(0)
const loadingStats = ref(true)

onMounted(async () => {
  try {
    const [progresoRes, examenesRes] = await Promise.all([
      apiClient.get('/estudiante/progreso').catch(() => ({ data: [] })),
      apiClient.get('/estudiante/examenes').catch(() => ({ data: [] })),
    ])
    progreso.value = Array.isArray(progresoRes.data) ? progresoRes.data : []
    const examenes = Array.isArray(examenesRes.data) ? examenesRes.data : []
    examensPendientes.value = examenes.filter((e: any) => !e.completado).length
  } finally {
    loadingStats.value = false
  }
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '¡Buenos días'
  if (h < 18) return '¡Buenas tardes'
  return '¡Buenas noches'
})

const firstName = computed(() => {
  const name = auth.user?.nombres || auth.user?.codigo_estudiante || 'estudiante'
  return name.split(' ')[0] ?? name
})

const nivelLogro = computed(() => {
  if (!progreso.value.length) return null
  // Tomar el mejor nivel entre todas las áreas
  const niveles = ['pre_inicio', 'inicio', 'proceso', 'satisfactorio', 'destacado']
  let best = ''
  for (const p of progreso.value) {
    if (!p.nivel_logro_actual) continue
    if (!best || niveles.indexOf(p.nivel_logro_actual) > niveles.indexOf(best)) {
      best = p.nivel_logro_actual
    }
  }
  return best || null
})

const promedioGeneral = computed(() => {
  if (!progreso.value.length) return null
  const sum = progreso.value.reduce((a, p) => a + p.puntaje_promedio, 0)
  return Math.round(sum / progreso.value.length)
})

const totalExamenes = computed(() =>
  progreso.value.reduce((a, p) => a + p.total_examenes_completados, 0)
)

const nivelConfig: Record<string, { label: string; icon: Component; color: string; bg: string; bar: string; msg: string }> = {
  pre_inicio: {
    label: 'Pre Inicio', icon: Sprout, msg: '¡Cada gran lector empezó desde cero!',
    color: 'text-red-600 dark:text-red-400',
    bg: 'from-red-400 to-orange-400',
    bar: 'bg-red-400',
  },
  inicio: {
    label: 'Inicio', icon: Flame, msg: '¡Vas agarrando el ritmo, sigue así!',
    color: 'text-orange-600 dark:text-orange-400',
    bg: 'from-orange-400 to-amber-400',
    bar: 'bg-orange-400',
  },
  proceso: {
    label: 'En Proceso', icon: Zap, msg: '¡Estás creciendo, casi llegas al nivel esperado!',
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'from-yellow-400 to-lime-400',
    bar: 'bg-yellow-400',
  },
  satisfactorio: {
    label: 'Satisfactorio', icon: Star, msg: '¡Excelente trabajo, estás donde debes estar!',
    color: 'text-emerald-600 dark:text-emerald-400',
    bg: 'from-emerald-400 to-teal-500',
    bar: 'bg-emerald-500',
  },
  destacado: {
    label: 'Destacado', icon: Trophy, msg: '¡Eres un lector de élite, increíble!',
    color: 'text-teal-600 dark:text-teal-400',
    bg: 'from-teal-400 to-indigo-500',
    bar: 'bg-teal-500',
  },
}

const nivelSteps = ['pre_inicio', 'inicio', 'proceso', 'satisfactorio', 'destacado']
const nivelIdx = computed(() => nivelLogro.value ? nivelSteps.indexOf(nivelLogro.value) : -1)
const nivelActual = computed(() => nivelLogro.value ? nivelConfig[nivelLogro.value] : null)
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-indigo-50 via-teal-50/40 to-purple-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-indigo-950/30 overflow-x-hidden">

    <!-- Burbujas decorativas de fondo -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-10 left-[10%] w-48 h-48 rounded-full bg-teal-300/20 dark:bg-teal-500/10 blur-3xl animate-float-slow" />
      <div class="absolute top-1/3 right-[5%] w-64 h-64 rounded-full bg-indigo-300/20 dark:bg-indigo-500/10 blur-3xl animate-float-medium" />
      <div class="absolute bottom-1/4 left-[20%] w-40 h-40 rounded-full bg-purple-300/20 dark:bg-purple-500/10 blur-3xl animate-float-fast" />
    </div>

    <!-- Header -->
    <header class="bg-white/70 dark:bg-slate-900/70 backdrop-blur-md border-b border-white/60 dark:border-slate-700/60 sticky top-0 z-40">
      <div class="max-w-2xl mx-auto px-4 h-14 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-teal-500/30">
            <Rocket class="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
          </div>
          <span class="font-black text-slate-800 dark:text-white text-sm tracking-tight">SIEVA</span>
        </div>
        <div class="flex items-center gap-2">
          <button @click="toggleTheme()"
            class="w-8 h-8 rounded-xl flex items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all">
            <Sun v-if="isDark" class="w-4 h-4" />
            <Moon v-else class="w-4 h-4" />
          </button>
          <button @click="auth.logout(); router.push('/login')"
            class="w-8 h-8 rounded-xl flex items-center justify-center text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-all">
            <LogOut class="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>

    <main class="max-w-2xl mx-auto px-4 py-6 relative">

      <!-- ── Hero / Saludo ── -->
      <div class="relative mb-5 sm:mb-6 rounded-3xl overflow-hidden bg-gradient-to-br from-teal-500 via-indigo-500 to-purple-600 p-5 sm:p-6 shadow-2xl shadow-indigo-500/25">
        <!-- Patrón de puntos -->
        <div class="absolute inset-0 opacity-10"
          style="background-image: radial-gradient(circle, white 1px, transparent 1px); background-size: 20px 20px;" />

        <!-- Estrellitas flotantes -->
        <div class="absolute top-4 right-6 sm:right-8 text-yellow-300 animate-spin-slow opacity-80">
          <Star class="w-4 h-4 sm:w-5 sm:h-5 fill-yellow-300" />
        </div>
        <div class="absolute top-10 right-16 sm:right-20 text-white animate-pulse opacity-50">
          <Sparkles class="w-3 h-3 sm:w-4 sm:h-4" />
        </div>
        <div class="absolute bottom-5 right-8 sm:right-12 text-yellow-200 animate-bounce opacity-60">
          <Star class="w-2.5 h-2.5 sm:w-3 sm:h-3 fill-yellow-200" />
        </div>

        <div class="relative z-10">
          <!-- Avatar circular con iniciales -->
          <div class="w-14 h-14 sm:w-16 sm:h-16 rounded-2xl bg-white/20 backdrop-blur-sm border-2 border-white/40 flex items-center justify-center mb-3 sm:mb-4 shadow-lg">
            <span class="text-xl sm:text-2xl font-black text-white">{{ (firstName[0] ?? '?').toUpperCase() }}</span>
          </div>

          <p class="text-white/80 text-sm font-medium">{{ greeting }},</p>
          <h1 class="text-2xl font-black text-white mt-0.5 leading-tight">{{ firstName }}!</h1>

          <div class="flex items-center gap-2 mt-2 flex-wrap">
            <span v-if="auth.user?.grado_nombre"
              class="inline-flex items-center gap-1 bg-white/20 backdrop-blur-sm text-white text-[11px] font-semibold px-2.5 py-1 rounded-full border border-white/30">
              <GraduationCap class="w-3 h-3" />
              {{ auth.user.grado_nombre }}
              <span v-if="auth.user?.seccion">· Sección {{ auth.user.seccion }}</span>
            </span>
            <span class="inline-flex items-center gap-1 bg-white/20 backdrop-blur-sm text-white/90 text-[11px] font-mono px-2.5 py-1 rounded-full border border-white/30">
              {{ auth.user?.codigo_estudiante }}
            </span>
          </div>

          <!-- Mensaje motivacional según nivel -->
          <p v-if="nivelActual" class="mt-3 text-white/90 text-sm font-medium flex items-center gap-2">
            <component :is="nivelActual.icon" class="w-4 h-4 shrink-0" />
            {{ nivelActual.msg }}
          </p>
          <p v-else-if="!loadingStats" class="mt-3 text-white/90 text-sm font-medium flex items-center gap-2">
            <Rocket class="w-4 h-4 shrink-0" />
            ¡Tu aventura de lectura comienza hoy!
          </p>
        </div>
      </div>

      <!-- ── Stats rápidas ── -->
      <div class="grid grid-cols-3 gap-2 sm:gap-3 mb-5 sm:mb-6">
        <!-- Exámenes completados -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-3 sm:p-4 text-center border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col items-center justify-center">
          <div class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 flex items-center justify-center mb-1.5 sm:mb-2 shadow-lg shadow-teal-500/25">
            <Trophy class="w-4 h-4 text-white" />
          </div>
          <template v-if="loadingStats">
            <div class="h-5 w-8 bg-slate-100 dark:bg-slate-700 rounded animate-pulse mb-1" />
          </template>
          <template v-else>
            <p class="text-lg sm:text-xl font-black text-slate-800 dark:text-white tabular-nums leading-tight">{{ totalExamenes }}</p>
          </template>
          <p class="text-[9px] sm:text-[10px] text-slate-500 dark:text-slate-400 font-medium leading-tight mt-0.5">Completados</p>
        </div>

        <!-- Promedio -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-3 sm:p-4 text-center border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col items-center justify-center">
          <div class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center mb-1.5 sm:mb-2 shadow-lg shadow-amber-500/25">
            <Target class="w-4 h-4 text-white" />
          </div>
          <template v-if="loadingStats">
            <div class="h-5 w-10 bg-slate-100 dark:bg-slate-700 rounded animate-pulse mb-1" />
          </template>
          <template v-else>
            <p class="text-lg sm:text-xl font-black tabular-nums leading-tight"
              :class="promedioGeneral === null ? 'text-slate-400' : 'text-slate-800 dark:text-white'">
              {{ promedioGeneral !== null ? promedioGeneral + '%' : '—' }}
            </p>
          </template>
          <p class="text-[9px] sm:text-[10px] text-slate-500 dark:text-slate-400 font-medium leading-tight mt-0.5">Promedio</p>
        </div>

        <!-- Pendientes -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl p-3 sm:p-4 text-center border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col items-center justify-center">
          <div class="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-br from-violet-400 to-purple-600 flex items-center justify-center mb-1.5 sm:mb-2 shadow-lg shadow-violet-500/25">
            <Flame class="w-4 h-4 text-white" />
          </div>
          <template v-if="loadingStats">
            <div class="h-5 w-6 bg-slate-100 dark:bg-slate-700 rounded animate-pulse mb-1" />
          </template>
          <template v-else>
            <p class="text-lg sm:text-xl font-black text-slate-800 dark:text-white tabular-nums leading-tight">{{ examensPendientes }}</p>
          </template>
          <p class="text-[9px] sm:text-[10px] text-slate-500 dark:text-slate-400 font-medium leading-tight mt-0.5">Pendientes</p>
        </div>
      </div>

      <!-- ── Barra de nivel de logro ── -->
      <div v-if="!loadingStats && nivelLogro"
        class="bg-white dark:bg-slate-800 rounded-2xl p-4 mb-6 border border-slate-100 dark:border-slate-700 shadow-sm">
        <div class="flex items-center justify-between mb-3">
          <span class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Tu nivel</span>
          <span class="inline-flex items-center gap-1.5 text-xs font-bold px-2.5 py-1 rounded-full"
            :class="nivelActual?.color"
            style="background: color-mix(in srgb, currentColor 12%, transparent)">
            <component :is="nivelActual?.icon" class="w-3 h-3" />
            {{ nivelActual?.label }}
          </span>
        </div>
        <!-- Pasos del camino -->
        <div class="flex items-center gap-1">
          <div v-for="(step, i) in nivelSteps" :key="step"
            class="flex-1 h-2.5 rounded-full transition-all duration-700"
            :class="i <= nivelIdx
              ? (nivelActual?.bar ?? 'bg-teal-500')
              : 'bg-slate-100 dark:bg-slate-700'" />
        </div>
        <div class="flex justify-between mt-1.5">
          <span class="text-[9px] text-slate-400">Inicio</span>
          <span class="text-[9px] text-slate-400">Destacado</span>
        </div>
      </div>

      <!-- ── Acciones principales ── -->
      <div class="space-y-3 mb-6">

        <!-- Mis Exámenes — CTA principal -->
        <button @click="router.push('/estudiante/examenes')"
          class="w-full relative overflow-hidden rounded-2xl p-4 sm:p-5 text-left shadow-xl shadow-teal-500/20 transition-all duration-300 hover:-translate-y-1 hover:shadow-2xl hover:shadow-teal-500/30 group"
          style="background: linear-gradient(135deg, #14b8a6, #6366f1)">
          <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
            style="background: linear-gradient(135deg, #0d9488, #4f46e5)" />
          <!-- Burbuja decorativa -->
          <div class="absolute -top-4 -right-4 w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-white/10 group-hover:scale-150 transition-transform duration-500" />
          <div class="absolute bottom-2 right-8 w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-white/10" />

          <div class="relative flex items-center gap-3 sm:gap-4">
            <div class="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-white/20 flex items-center justify-center shadow-lg shrink-0 group-hover:scale-110 transition-transform duration-300">
              <BookOpen class="w-6 h-6 sm:w-7 sm:h-7 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-white/70 text-[10px] sm:text-xs font-semibold mb-0.5">¡A estudiar!</p>
              <h3 class="text-white font-black text-base sm:text-lg leading-tight truncate">Mis Exámenes</h3>
              <p class="text-white/70 text-[10px] sm:text-xs mt-0.5 truncate">
                <span v-if="examensPendientes > 0 && !loadingStats"
                  class="inline-flex items-center gap-1 bg-white/20 px-2 py-0.5 rounded-full font-bold truncate">
                  <Zap class="w-3 h-3 shrink-0" /> {{ examensPendientes }} pendiente{{ examensPendientes !== 1 ? 's' : '' }}
                </span>
                <span v-else>Ver y rendir tus exámenes</span>
              </p>
            </div>
            <ChevronRight class="w-5 h-5 text-white/60 group-hover:translate-x-1 transition-transform duration-200 shrink-0 ml-1" />
          </div>
        </button>

        <!-- Mi Progreso -->
        <button @click="router.push('/estudiante/progreso')"
          class="w-full relative overflow-hidden rounded-2xl p-4 sm:p-5 text-left bg-white dark:bg-slate-800 border-2 border-slate-100 dark:border-slate-700 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 group">
          <div class="absolute -top-3 -right-3 w-16 h-16 rounded-full bg-indigo-50 dark:bg-indigo-900/20 group-hover:scale-150 transition-transform duration-500" />

          <div class="relative flex items-center gap-3 sm:gap-4">
            <div class="w-12 h-12 sm:w-14 sm:h-14 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/25 shrink-0 group-hover:scale-110 transition-transform duration-300">
              <BarChart3 class="w-6 h-6 sm:w-7 sm:h-7 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <p class="text-slate-400 dark:text-slate-500 text-[10px] sm:text-xs font-semibold mb-0.5">Seguimiento</p>
              <h3 class="font-black text-slate-800 dark:text-white text-base sm:text-lg leading-tight truncate">Mi Progreso</h3>
              <p class="text-slate-400 dark:text-slate-500 text-[10px] sm:text-xs mt-0.5 truncate">Revisa tu evolución y nivel de logro</p>
            </div>
            <ChevronRight class="w-5 h-5 text-slate-300 dark:text-slate-600 group-hover:translate-x-1 group-hover:text-indigo-500 transition-all duration-200 shrink-0 ml-1" />
          </div>
        </button>
      </div>

      <!-- ── Progreso por área (inline) ── -->
      <div v-if="!loadingStats && progreso.length > 0" class="mb-6">
        <h2 class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-3 flex items-center gap-2">
          <Medal class="w-3.5 h-3.5" /> Logros por área
        </h2>
        <div class="space-y-2.5">
          <div v-for="p in progreso" :key="p.area"
            class="bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 px-4 py-3 flex items-center gap-3 shadow-sm">
            <div class="w-9 h-9 rounded-xl flex items-center justify-center shrink-0"
              :class="p.area === 'comunicacion'
                ? 'bg-gradient-to-br from-teal-400 to-teal-600'
                : 'bg-gradient-to-br from-orange-400 to-amber-500'">
              <BookOpen v-if="p.area === 'comunicacion'" class="w-4 h-4 text-white" />
              <Zap v-else class="w-4 h-4 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-1.5">
                <span class="text-xs font-bold text-slate-700 dark:text-slate-200">
                  {{ p.area === 'comunicacion' ? 'Comunicación' : 'Matemática' }}
                </span>
                <span class="text-xs font-black tabular-nums"
                  :class="nivelConfig[p.nivel_logro_actual || '']?.color ?? 'text-slate-500'">
                  {{ Math.round(p.puntaje_promedio) }}%
                </span>
              </div>
              <div class="h-2 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-700"
                  :class="nivelConfig[p.nivel_logro_actual || '']?.bar ?? 'bg-slate-400'"
                  :style="{ width: p.puntaje_promedio + '%' }" />
              </div>
            </div>
            <component
              v-if="p.nivel_logro_actual && nivelConfig[p.nivel_logro_actual]"
              :is="nivelConfig[p.nivel_logro_actual]!.icon"
              class="w-5 h-5 shrink-0"
              :class="nivelConfig[p.nivel_logro_actual]!.color" />
          </div>
        </div>
      </div>

      <!-- ── Mensaje motivacional si no hay progreso ── -->
      <div v-if="!loadingStats && progreso.length === 0"
        class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700 p-6 text-center mb-6">
        <div class="w-12 h-12 rounded-2xl bg-slate-100 dark:bg-slate-700 flex items-center justify-center mx-auto mb-3">
          <Library class="w-6 h-6 text-slate-400 dark:text-slate-500" />
        </div>
        <p class="font-bold text-slate-700 dark:text-slate-200 text-sm">¡Aún no has rendido ningún examen!</p>
        <p class="text-xs text-slate-400 dark:text-slate-500 mt-1">Completa tu primer examen y comienza tu camino hacia el logro destacado.</p>
      </div>

      <!-- Footer -->
      <p class="text-center text-[11px] text-slate-400 dark:text-slate-600 pb-6">
        {{ auth.user?.institucion_nombre }}
      </p>

    </main>
  </div>
</template>

<style scoped>
@keyframes float-slow {
  0%, 100% { transform: translateY(0px) scale(1); }
  50% { transform: translateY(-20px) scale(1.05); }
}
@keyframes float-medium {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-14px); }
}
@keyframes float-fast {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-float-slow { animation: float-slow 7s ease-in-out infinite; }
.animate-float-medium { animation: float-medium 5s ease-in-out infinite 1s; }
.animate-float-fast { animation: float-fast 4s ease-in-out infinite 0.5s; }
.animate-spin-slow { animation: spin-slow 8s linear infinite; }
</style>
