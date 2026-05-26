<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../../shared/services/api'
import EstudianteNavbar from './components/EstudianteNavbar.vue'
import { isSidebarCollapsed } from './composables/useStudentLayout'
import {
  Loader2, AlertCircle, BarChart3,
  BookOpen, Calculator, Target, TrendingUp, Calendar, Award
} from 'lucide-vue-next'

const router = useRouter()

interface ProgresoArea {
  area: string
  total_examenes_completados: number
  puntaje_promedio: number
  nivel_logro_actual: string | null
  ultima_actividad: string | null
}

const progreso = ref<ProgresoArea[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await apiClient.get('/estudiante/progreso')
    progreso.value = Array.isArray(res.data) ? res.data : [res.data]
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar progreso'
  } finally {
    loading.value = false
  }
})

const nivelColors: Record<string, string> = {
  pre_inicio: 'text-red-500 bg-red-50 dark:bg-red-500/10 border-red-100 dark:border-red-500/20',
  inicio: 'text-orange-500 bg-orange-50 dark:bg-orange-500/10 border-orange-100 dark:border-orange-500/20',
  proceso: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-500/10 border-yellow-100 dark:border-yellow-500/20',
  satisfactorio: 'text-emerald-500 bg-emerald-50 dark:bg-emerald-500/10 border-emerald-100 dark:border-emerald-500/20',
  destacado: 'text-teal-500 bg-teal-50 dark:bg-emerald-500/10 border-teal-100 dark:border-emerald-100/20',
}

const nivelLabels: Record<string, string> = {
  pre_inicio: 'Pre Inicio', inicio: 'Inicio', proceso: 'En Proceso',
  satisfactorio: 'Satisfactorio', destacado: 'Destacado',
}
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 transition-all duration-300 font-sans selection:bg-teal-500/20"
       :class="isSidebarCollapsed ? 'lg:pl-[84px]' : 'lg:pl-[280px]'">

    <!-- Unified Student Navbar -->
    <EstudianteNavbar />

    <main class="max-w-4xl mx-auto px-6 pt-8 pb-12 sm:pb-10 relative">

      <!-- Background Orbs -->
      <div class="fixed inset-0 pointer-events-none overflow-hidden opacity-40">
        <div class="absolute top-[20%] right-[-10%] w-[500px] h-[500px] bg-teal-500/5 dark:bg-emerald-500/10 rounded-full blur-[120px]"></div>
        <div class="absolute bottom-[10%] left-[-10%] w-[400px] h-[400px] bg-emerald-500/5 dark:bg-emerald-500/10 rounded-full blur-[100px]"></div>
      </div>

      <div v-if="loading" class="flex flex-col items-center justify-center py-24 gap-4 animate-pulse">
        <Loader2 class="w-10 h-10 animate-spin text-teal-500" />
        <p class="text-xs font-bold text-slate-400 uppercase tracking-widest">Cargando estadísticas...</p>
      </div>

      <div v-else-if="error" class="flex flex-col items-center justify-center py-20 text-center animate-slide-up">
        <div class="w-20 h-20 rounded-2xl bg-red-50 dark:bg-red-500/10 flex items-center justify-center mb-6">
          <AlertCircle class="w-10 h-10 text-red-500" />
        </div>
        <h2 class="text-xl font-bold text-slate-900 dark:text-white mb-2">¡Ups! Algo salió mal</h2>
        <p class="text-slate-500 dark:text-slate-400 max-w-xs">{{ error }}</p>
      </div>

      <div v-else-if="progreso.length === 0"
        class="flex flex-col items-center justify-center py-24 bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 shadow-xl text-center animate-slide-up">
        <div class="w-24 h-24 rounded-full bg-slate-50 dark:bg-slate-800 flex items-center justify-center mb-8">
          <BarChart3 class="w-12 h-12 text-slate-200 dark:text-slate-700" />
        </div>
        <h2 class="text-xl font-bold text-slate-900 dark:text-white mb-2">Sin actividad aún</h2>
        <p class="text-slate-500 dark:text-slate-400 max-w-xs">Completa al menos una evaluación para comenzar a trackear tu progreso.</p>
        <button @click="router.push('/estudiante/examenes')"
          class="mt-8 px-8 py-3 bg-slate-900 dark:bg-white text-white dark:text-slate-900 rounded-xl font-bold transition-all active:scale-95 shadow-lg">
          Ver exámenes
        </button>
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div
          v-for="(p, i) in progreso"
          :key="p.area"
          class="group bg-white dark:bg-slate-900 rounded-2xl border border-slate-300 dark:border-slate-800 p-8 shadow-xl hover:shadow-2xl transition-all duration-500 relative overflow-hidden animate-slide-up"
          :style="{ animationDelay: `${i * 100}ms` }"
        >
          <!-- Decorative Background Icon -->
          <div class="absolute top-0 right-0 p-8 opacity-[0.03] dark:opacity-[0.05] group-hover:scale-110 transition-transform duration-700 pointer-events-none">
            <BookOpen v-if="p.area === 'comunicacion'" class="w-32 h-32" />
            <Calculator v-else class="w-32 h-32" />
          </div>

          <div class="relative z-10">
            <div class="flex items-center gap-4 mb-10">
              <div :class="p.area === 'comunicacion' ? 'from-teal-400 to-emerald-500' : 'from-violet-400 to-purple-500'"
                class="w-14 h-14 rounded-2xl bg-gradient-to-br flex items-center justify-center shadow-lg transition-transform group-hover:rotate-6">
                <BookOpen v-if="p.area === 'comunicacion'" class="w-7 h-7 text-white" />
                <Calculator v-else class="w-7 h-7 text-white" />
              </div>
              <div class="min-w-0">
                <h3 class="text-xl font-bold text-slate-900 dark:text-white">
                  {{ p.area === 'comunicacion' ? 'Comunicación' : 'Matemática' }}
                </h3>
                <div class="flex items-center gap-2 mt-1">
                  <Calendar class="w-3 h-3 text-slate-400" />
                  <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                    {{ formatFecha(p.ultima_actividad) }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Nivel de Logro Badge -->
            <div class="mb-8">
              <div class="flex items-center gap-2 mb-3">
                <Award class="w-4 h-4 text-slate-400" />
                <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Nivel Actual</span>
              </div>
              <div v-if="p.nivel_logro_actual"
                :class="nivelColors[p.nivel_logro_actual] || 'bg-slate-100 text-slate-600'"
                class="inline-flex px-5 py-2 rounded-full text-xs font-black uppercase tracking-[0.15em] border border-transparent shadow-sm">
                {{ nivelLabels[p.nivel_logro_actual] ?? p.nivel_logro_actual }}
              </div>
              <div v-else class="text-xs font-bold text-slate-400 bg-slate-50 dark:bg-slate-800/50 px-4 py-2 rounded-full border border-transparent inline-block">
                Pendiente de evaluación
              </div>
            </div>

            <!-- Puntaje promedio -->
            <div class="mb-10">
              <div class="flex justify-between items-end mb-3">
                <div class="flex items-center gap-2">
                  <Target class="w-4 h-4 text-slate-400" />
                  <span class="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Dominio promedio</span>
                </div>
                <div class="text-right">
                  <span class="text-3xl font-black text-slate-900 dark:text-white tabular-nums">{{ p.puntaje_promedio.toFixed(0) }}</span>
                  <span class="text-sm font-bold text-slate-400 ml-1">%</span>
                </div>
              </div>
              <div class="h-3 bg-slate-50 dark:bg-slate-800/50 rounded-full overflow-hidden p-0.5 border border-slate-300/50 dark:border-slate-800">
                <div
                  class="h-full rounded-full transition-all duration-1000 ease-out bg-gradient-to-r"
                  :class="p.area === 'comunicacion' ? 'from-teal-400 to-emerald-500' : 'from-violet-400 to-purple-500'"
                  :style="{ width: p.puntaje_promedio + '%' }"
                ></div>
              </div>
            </div>

            <!-- Quick Stats -->
            <div class="grid grid-cols-2 gap-4">
              <div class="bg-slate-50/50 dark:bg-slate-800/30 rounded-2xl p-5 border border-slate-300/50 dark:border-slate-800/50 transition-colors group-hover:bg-white dark:group-hover:bg-slate-800/50">
                <div class="flex items-center gap-2 mb-2 text-emerald-500">
                  <BarChart3 class="w-4 h-4" />
                </div>
                <p class="text-2xl font-black text-slate-900 dark:text-white leading-none">{{ p.total_examenes_completados }}</p>
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Evaluaciones</p>
              </div>
              <div class="bg-slate-50/50 dark:bg-slate-800/30 rounded-2xl p-5 border border-slate-300/50 dark:border-slate-800/50 transition-colors group-hover:bg-white dark:group-hover:bg-slate-800/50">
                <div class="flex items-center gap-2 mb-2 text-teal-500">
                  <TrendingUp class="w-4 h-4" />
                </div>
                <p class="text-2xl font-black text-slate-900 dark:text-white leading-none">{{ p.puntaje_promedio.toFixed(0) }}%</p>
                <p class="text-[10px] font-bold text-slate-400 uppercase tracking-widest mt-1">Efectividad</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
@keyframes slide-up {
  0% { transform: translateY(30px); opacity: 0; }
  100% { transform: translateY(0); opacity: 1; }
}

.animate-slide-up {
  animation: slide-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
}
</style>
