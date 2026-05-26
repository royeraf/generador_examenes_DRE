<script setup lang="ts">
import { ref, computed, onMounted, type Component } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { apiClient } from '../../shared/services/api'
import EstudianteNavbar from './components/EstudianteNavbar.vue'
import { isSidebarCollapsed } from './composables/useStudentLayout'
import {
  Trophy, Flame, Target, Sparkles,
  BookOpen, Star, Zap,
  GraduationCap, Sprout,
  ChevronRight, BarChart3, Library,
} from 'lucide-vue-next'

const router = useRouter()
const auth = useAuthStore()

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
    color: 'text-emerald-600 dark:text-primary',
    bg: 'from-emerald-400 to-teal-500',
    bar: 'bg-emerald-500',
  },
  destacado: {
    label: 'Destacado', icon: Trophy, msg: '¡Eres un lector de élite, increíble!',
    color: 'text-primary',
    bg: 'from-teal-400 to-emerald-500',
    bar: 'bg-teal-500',
  },
}

const nivelSteps = ['pre_inicio', 'inicio', 'proceso', 'satisfactorio', 'destacado']
const nivelIdx = computed(() => nivelLogro.value ? nivelSteps.indexOf(nivelLogro.value) : -1)
const nivelActual = computed(() => nivelLogro.value ? nivelConfig[nivelLogro.value] : null)
</script>

<template>
  <div class="min-h-screen bg-surface transition-all duration-300 overflow-x-hidden font-sans"
       :class="isSidebarCollapsed ? 'lg:pl-[84px]' : 'lg:pl-[280px]'">

    <!-- Premium Background Elements -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-[-10%] right-[-10%] w-[500px] h-[500px] bg-teal-500/5 dark:bg-emerald-500/10 rounded-full blur-[120px]"></div>
      <div class="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-emerald-500/5 dark:bg-emerald-500/10 rounded-full blur-[100px]"></div>
    </div>

    <!-- Unified Student Navbar -->
    <EstudianteNavbar />

    <main class="max-w-3xl mx-auto px-6 pt-8 pb-12 sm:pb-8 relative">

      <!-- ── Hero Section ── -->
      <section class="relative mb-8 rounded-2xl overflow-hidden bg-gradient-to-br from-teal-500 via-emerald-500 to-purple-600 p-8 sm:p-10 shadow-2xl shadow-emerald-500/20 group">
        <!-- Decoration -->
        <div class="absolute inset-0 opacity-10 bg-[radial-gradient(circle,white_1px,transparent_1px)] bg-[length:24px_24px]" />
        <div class="absolute -top-24 -right-24 w-64 h-64 bg-white/10 rounded-full blur-3xl group-hover:scale-110 transition-transform duration-1000" />
        
        <div class="relative z-10 flex flex-col sm:flex-row sm:items-center gap-6">
          <!-- Avatar -->
          <div class="w-20 h-20 rounded-2xl bg-white/20 backdrop-blur-md border-2 border-white/30 flex items-center justify-center shadow-xl shrink-0 group-hover:scale-105 transition-transform">
            <span class="text-3xl font-black text-white">{{ (firstName[0] ?? '?').toUpperCase() }}</span>
          </div>

          <div class="flex-1">
            <p class="text-white/80 text-sm font-bold uppercase tracking-widest">{{ greeting }},</p>
            <h1 class="text-3xl sm:text-4xl font-bold text-white mt-1 leading-tight">{{ firstName }}!</h1>

            <div class="flex items-center gap-2 mt-4 flex-wrap">
              <span v-if="auth.user?.matricula_activa?.grado_nombre"
                class="inline-flex items-center gap-2 bg-white/20 backdrop-blur-md text-white text-[10px] font-bold px-3 py-1.5 rounded-full border border-white/20 uppercase tracking-wider">
                <GraduationCap class="w-3.5 h-3.5" />
                {{ auth.user.matricula_activa.grado_nombre }} <span v-if="auth.user.matricula_activa.seccion" class="opacity-50 mx-1">|</span> {{ auth.user.matricula_activa.seccion }}
              </span>
              <span class="inline-flex items-center gap-2 bg-slate-900/20 backdrop-blur-md text-white/90 text-[10px] font-mono font-bold px-3 py-1.5 rounded-full border border-white/10 tracking-widest">
                ID: {{ auth.user?.codigo_estudiante }}
              </span>
            </div>
          </div>

          <!-- Motivational Badge -->
          <div v-if="nivelActual" class="hidden md:flex flex-col items-center gap-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-4 min-w-[140px]">
            <div class="w-12 h-12 rounded-full bg-white/20 flex items-center justify-center">
              <component :is="nivelActual.icon" class="w-6 h-6 text-white" />
            </div>
            <span class="text-[10px] font-bold text-white uppercase tracking-widest">{{ nivelActual.label }}</span>
          </div>
        </div>

        <p v-if="nivelActual" class="relative z-10 mt-6 text-white/90 text-sm font-bold flex items-center gap-2">
          <Sparkles class="w-4 h-4 text-yellow-300" />
          {{ nivelActual.msg }}
        </p>
      </section>

      <!-- ── Quick Stats Grid ── -->
      <section class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <!-- Stat Card Template -->
        <div class="bg-surface rounded-2xl p-5 border border-slate-300 dark:border-slate-800 shadow-sm flex items-center gap-4 group hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-teal-50 dark:bg-emerald-500/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
            <Trophy class="w-6 h-6 text-teal-500" />
          </div>
          <div>
            <p class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest">Completados</p>
            <div v-if="loadingStats" class="h-6 w-12 bg-slate-100 dark:bg-surface-card rounded animate-pulse mt-1" />
            <p v-else class="text-2xl font-black text-text tabular-nums">{{ totalExamenes }}</p>
          </div>
        </div>

        <div class="bg-surface rounded-2xl p-5 border border-slate-300 dark:border-slate-800 shadow-sm flex items-center gap-4 group hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
            <Target class="w-6 h-6 text-emerald-500" />
          </div>
          <div>
            <p class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest">Promedio</p>
            <div v-if="loadingStats" class="h-6 w-16 bg-slate-100 dark:bg-surface-card rounded animate-pulse mt-1" />
            <p v-else class="text-2xl font-black text-text tabular-nums">
              {{ promedioGeneral !== null ? promedioGeneral + '%' : '—' }}
            </p>
          </div>
        </div>

        <div class="bg-surface rounded-2xl p-5 border border-slate-300 dark:border-slate-800 shadow-sm flex items-center gap-4 group hover:shadow-md transition-all">
          <div class="w-12 h-12 rounded-xl bg-amber-50 dark:bg-amber-500/10 flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform">
            <Flame class="w-6 h-6 text-amber-500" />
          </div>
          <div>
            <p class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest">Pendientes</p>
            <div v-if="loadingStats" class="h-6 w-10 bg-slate-100 dark:bg-surface-card rounded animate-pulse mt-1" />
            <p v-else class="text-2xl font-black text-text tabular-nums">{{ examensPendientes }}</p>
          </div>
        </div>
      </section>

      <!-- ── Level Progress Bar ── -->
      <section v-if="!loadingStats && nivelLogro" class="bg-surface rounded-2xl p-6 mb-8 border border-slate-300 dark:border-slate-800 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-xs font-bold text-text uppercase tracking-widest">Nivel de Logro Actual</h3>
          <span class="inline-flex items-center gap-1.5 text-[10px] font-bold px-3 py-1 rounded-full uppercase tracking-wider"
            :class="nivelActual?.color"
            style="background: color-mix(in srgb, currentColor 10%, transparent)">
            <component :is="nivelActual?.icon" class="w-3.5 h-3.5" />
            {{ nivelActual?.label }}
          </span>
        </div>
        <div class="flex items-center gap-1.5 h-3">
          <div v-for="(step, i) in nivelSteps" :key="step"
            class="flex-1 h-full rounded-full transition-all duration-1000"
            :class="i <= nivelIdx
              ? (nivelActual?.bar ?? 'bg-teal-500')
              : 'bg-slate-100 dark:bg-surface-card'" />
        </div>
        <div class="flex justify-between mt-3 px-1">
          <span class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest">Base</span>
          <span class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest">Élite</span>
        </div>
      </section>

      <!-- ── Main Navigation CTAs ── -->
      <section class="grid grid-cols-1 md:grid-cols-2 gap-5 mb-10">
        
        <!-- Action Card: Exámenes -->
        <button @click="router.push('/estudiante/examenes')"
          class="relative overflow-hidden rounded-2xl p-6 text-left group transition-all duration-300 hover:-translate-y-1.5"
          style="background: linear-gradient(135deg, #14b8a6, #0ea5e9)">
          
          <div class="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors" />
          <div class="absolute -top-10 -right-10 w-32 h-32 bg-white/10 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700" />
          
          <div class="relative flex items-center gap-5">
            <div class="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-md flex items-center justify-center shadow-xl shrink-0 group-hover:scale-110 transition-transform">
              <BookOpen class="w-8 h-8 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <span class="text-[10px] font-bold text-white/70 uppercase tracking-widest">Evaluaciones</span>
              <h3 class="text-xl font-bold text-white mt-0.5">Mis Exámenes</h3>
              <div v-if="examensPendientes > 0 && !loadingStats" class="mt-2 inline-flex items-center gap-1.5 bg-white/20 px-2.5 py-1 rounded-lg text-[10px] font-bold text-white border border-white/20">
                <Zap class="w-3 h-3 fill-white" />
                {{ examensPendientes }} PENDIENTE{{ examensPendientes !== 1 ? 'S' : '' }}
              </div>
            </div>
            <ChevronRight class="w-6 h-6 text-white/50 group-hover:translate-x-1 transition-transform" />
          </div>
        </button>

        <!-- Action Card: Progreso -->
        <button @click="router.push('/estudiante/progreso')"
          class="relative overflow-hidden rounded-2xl p-6 text-left group transition-all duration-300 hover:-translate-y-1.5 bg-surface border border-slate-300 dark:border-slate-800 shadow-sm hover:shadow-xl hover:shadow-emerald-500/10">
          
          <div class="absolute -top-10 -right-10 w-32 h-32 bg-emerald-50 dark:bg-emerald-500/5 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-700" />
          
          <div class="relative flex items-center gap-5">
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center shadow-lg shadow-emerald-500/20 shrink-0 group-hover:scale-110 transition-transform">
              <BarChart3 class="w-8 h-8 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <span class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest">Seguimiento</span>
              <h3 class="text-xl font-bold text-text mt-0.5">Mi Progreso</h3>
              <p class="text-xs text-slate-500 dark:text-text-muted mt-1 truncate">Reporte detallado de áreas</p>
            </div>
            <ChevronRight class="w-6 h-6 text-slate-300 dark:text-text-subtle group-hover:translate-x-1 group-hover:text-emerald-500 transition-all" />
          </div>
        </button>
      </section>

      <!-- ── Area Detail Section ── -->
      <section v-if="!loadingStats && progreso.length > 0" class="mb-10">
        <div class="flex items-center gap-3 mb-5 px-1">
          <div class="w-1 h-4 bg-teal-500 rounded-full" />
          <h2 class="text-xs font-bold text-text uppercase tracking-widest">Logros por Área</h2>
        </div>
        
        <div class="space-y-4">
          <div v-for="p in progreso" :key="p.area"
            class="bg-surface rounded-2xl border border-slate-300 dark:border-slate-800 p-5 flex items-center gap-4 shadow-sm hover:border-slate-300 dark:hover:border-slate-700 transition-colors">
            
            <div class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0 shadow-lg"
              :class="p.area === 'comunicacion'
                ? 'bg-gradient-to-br from-teal-400 to-emerald-500 shadow-teal-500/20'
                : 'bg-gradient-to-br from-violet-400 to-purple-500 shadow-emerald-500/20'">
              <BookOpen v-if="p.area === 'comunicacion'" class="w-6 h-6 text-white" />
              <Zap v-else class="w-6 h-6 text-white" />
            </div>

            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between mb-2">
                <h4 class="text-sm font-bold text-text">
                  {{ p.area === 'comunicacion' ? 'Comunicación' : 'Matemática' }}
                </h4>
                <span class="text-sm font-black tabular-nums"
                  :class="nivelConfig[p.nivel_logro_actual || '']?.color ?? 'text-slate-400'">
                  {{ Math.round(p.puntaje_promedio) }}%
                </span>
              </div>
              <div class="h-2.5 bg-slate-100 dark:bg-surface-card rounded-full overflow-hidden">
                <div class="h-full rounded-full transition-all duration-1000"
                  :class="nivelConfig[p.nivel_logro_actual || '']?.bar ?? 'bg-slate-300 dark:bg-surface-input'"
                  :style="{ width: p.puntaje_promedio + '%' }" />
              </div>
            </div>

            <div v-if="p.nivel_logro_actual && nivelConfig[p.nivel_logro_actual]" class="hidden sm:flex shrink-0">
               <component :is="nivelConfig[p.nivel_logro_actual]!.icon" class="w-6 h-6" :class="nivelConfig[p.nivel_logro_actual]!.color" />
            </div>
          </div>
        </div>
      </section>

      <!-- ── Empty State ── -->
      <section v-if="!loadingStats && progreso.length === 0"
        class="bg-surface rounded-2xl border-2 border-dashed border-slate-300 dark:border-slate-800 p-12 text-center mb-10 group">
        <div class="w-20 h-20 rounded-2xl bg-slate-50 dark:bg-surface-card flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform">
          <Library class="w-10 h-10 text-slate-300 dark:text-text-subtle" />
        </div>
        <h3 class="text-xl font-bold text-text">¡Bienvenido a tu nueva etapa!</h3>
        <p class="text-sm text-slate-500 dark:text-text-muted mt-2 max-w-xs mx-auto">
          Aún no has rendido exámenes. Empieza hoy mismo y desbloquea tus primeros logros.
        </p>
        <button @click="router.push('/estudiante/examenes')" class="mt-8 px-8 py-3 bg-teal-500 text-white font-bold rounded-xl shadow-lg shadow-teal-500/25 hover:scale-105 active:scale-95 transition-all">
          Ver Exámenes Disponibles
        </button>
      </section>

      <!-- Footer Info -->
      <footer class="mt-12 pt-8 border-t border-slate-300 dark:border-slate-800 text-center pb-12">
        <p class="text-[10px] font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest leading-loose">
          {{ auth.user?.institucion_nombre }}<br/>
          Dirección Regional de Educación Huánuco
        </p>
      </footer>

    </main>
  </div>
</template>

<style scoped>
@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-15px); }
}

@keyframes shake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-2px); }
    20%, 40%, 60%, 80% { transform: translateX(2px); }
}
.animate-shake { animation: shake 0.5s cubic-bezier(.36,.07,.19,.97) both; }
</style>
