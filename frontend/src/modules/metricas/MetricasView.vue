<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../../shared/services/api'
import Navbar from '../../shared/components/Navbar.vue'
import Footer from '../../shared/components/Footer.vue'
import {
  Users, BookOpen, Calculator,
  Clock, BarChart3, RefreshCw,
  Building2, CheckCircle2, ClipboardList,
  TrendingUp, Activity, Medal
} from 'lucide-vue-next'
import { useTheme } from '../../shared/composables/useTheme'

useTheme()

interface Reciente {
  id: number
  titulo: string
  grado: string
  area: 'lectura' | 'matematica'
  fecha: string | null
}

interface ResumenData {
  total_examenes_lectura: number
  total_examenes_matematica: number
  total_examenes: number
  total_usuarios: number
  total_ugeles: number
  total_instituciones: number
  total_asignaciones: number
  total_completados: number
  recientes: Reciente[]
  rol: string
}

const resumen = ref<ResumenData | null>(null)
const loading = ref(true)
const error = ref('')

async function fetchMetricas() {
  loading.value = true
  error.value = ''
  try {
    const res = await apiClient.get('/metricas/resumen')
    resumen.value = res.data
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar métricas'
  } finally {
    loading.value = false
  }
}

onMounted(fetchMetricas)

const completadosPct = computed(() => {
  if (!resumen.value || !resumen.value.total_asignaciones) return 0
  return Math.min(100, Math.round((resumen.value.total_completados / resumen.value.total_asignaciones) * 100))
})

const lecturaPct = computed(() => {
  if (!resumen.value || !resumen.value.total_examenes) return 0
  return Math.round((resumen.value.total_examenes_lectura / resumen.value.total_examenes) * 100)
})

const matematicaPct = computed(() => {
  if (!resumen.value || !resumen.value.total_examenes) return 0
  return Math.round((resumen.value.total_examenes_matematica / resumen.value.total_examenes) * 100)
})

const rolLabel = computed(() => {
  const labels: Record<string, string> = {
    especialista_dre_comunicacion: 'Especialista DRE — Comunicación',
    especialista_dre_matematica: 'Especialista DRE — Matemática',
    responsable_ugel: 'Responsable UGEL',
    director: 'Director',
    auxiliar: 'Auxiliar',
    docente: 'Docente',
  }
  return labels[resumen.value?.rol ?? ''] ?? resumen.value?.rol ?? ''
})
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0f111a] transition-colors font-sans">
    
    <Navbar title="Dashboard de Métricas" subtitle="Analítica y estadísticas en tiempo real" :show-home="true" />

    <main class="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-10 space-y-8 md:space-y-12">
      
      <!-- Top Actions & Welcome -->
      <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div class="space-y-1">
          <div class="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-bold text-sm tracking-wider uppercase">
            <TrendingUp class="w-4 h-4" />
            <span>Métricas en tiempo real</span>
          </div>
          <h2 class="text-3xl md:text-4xl font-black text-slate-800 dark:text-white tracking-tight">
            Dashboard Global
          </h2>
          <p class="text-slate-500 dark:text-slate-400 text-sm md:text-base max-w-2xl">
            Estadísticas consolidadas para el rol <span class="text-indigo-600 dark:text-indigo-400 font-bold border-b-2 border-indigo-500/20">{{ rolLabel }}</span>.
          </p>
        </div>
        <button @click="fetchMetricas" :disabled="loading"
          class="group flex items-center justify-center gap-2 px-6 py-3 text-sm font-bold text-white bg-slate-900 dark:bg-white dark:text-slate-900 rounded-2xl hover:scale-105 active:scale-95 transition-all shadow-xl shadow-slate-900/10 dark:shadow-white/5 disabled:opacity-50">
          <RefreshCw class="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" :class="{'animate-spin': loading}" />
          <span>Actualizar Datos</span>
        </button>
      </div>

      <!-- Error state -->
      <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="transform -translate-y-4 opacity-0" enter-to-class="transform translate-y-0 opacity-100">
        <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-2xl p-5 text-red-600 dark:text-red-400 text-sm flex items-center justify-between shadow-lg">
          <span class="flex items-center gap-3 font-medium">
            <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div> 
            {{ error }}
          </span>
          <button @click="fetchMetricas" class="px-4 py-1.5 bg-red-100 dark:bg-red-500/20 rounded-xl font-bold hover:bg-red-200 dark:hover:bg-red-500/30 transition-colors">
            Reintentar
          </button>
        </div>
      </Transition>

      <!-- Loading state -->
      <div v-if="loading && !resumen" class="flex flex-col items-center justify-center py-24 md:py-32">
        <div class="relative w-20 h-20">
          <div class="absolute inset-0 rounded-full border-4 border-slate-300 dark:border-slate-800"></div>
          <div class="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
          <div class="absolute inset-4 rounded-full border-4 border-teal-400 border-b-transparent animate-spin-reverse"></div>
        </div>
        <p class="text-slate-500 dark:text-slate-400 font-bold mt-6 tracking-widest uppercase text-xs">Analizando Datos...</p>
      </div>

      <template v-if="resumen">
        
        <!-- KPI Grid: Dynamic and Interactive -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6">
          
          <!-- Exámenes Totales -->
          <div class="bg-white dark:bg-slate-900/40 backdrop-blur-xl border border-slate-300/60 dark:border-slate-800/60 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300 group overflow-hidden relative">
            <div class="absolute -right-10 -top-10 w-32 h-32 bg-indigo-500/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
            <div class="flex justify-between items-start mb-6">
              <div class="w-14 h-14 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400 transform group-hover:rotate-12 transition-transform">
                <BarChart3 class="w-7 h-7" />
              </div>
              <div class="flex flex-col items-end">
                <span class="text-[10px] font-black text-slate-400 uppercase tracking-wider">Histórico</span>
                <span class="text-xs font-bold text-emerald-500 flex items-center gap-1">
                  <TrendingUp class="w-3 h-3" /> +12%
                </span>
              </div>
            </div>
            <h3 class="text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-widest mb-1">Exámenes Generados</h3>
            <p class="text-4xl md:text-5xl font-black text-slate-800 dark:text-white tracking-tighter">{{ resumen.total_examenes }}</p>
          </div>

          <!-- Total Usuarios -->
          <div class="bg-white dark:bg-slate-900/40 backdrop-blur-xl border border-slate-300/60 dark:border-slate-800/60 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:shadow-blue-500/10 transition-all duration-300 group overflow-hidden relative">
            <div class="absolute -right-10 -top-10 w-32 h-32 bg-blue-500/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
            <div class="flex justify-between items-start mb-6">
              <div class="w-14 h-14 rounded-2xl bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400 transform group-hover:-rotate-12 transition-transform">
                <Users class="w-7 h-7" />
              </div>
            </div>
            <h3 class="text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-widest mb-1">Comunidad Activa</h3>
            <p class="text-4xl md:text-5xl font-black text-slate-800 dark:text-white tracking-tighter">{{ resumen.total_usuarios }}</p>
          </div>

          <!-- Asignaciones -->
          <div class="bg-white dark:bg-slate-900/40 backdrop-blur-xl border border-slate-300/60 dark:border-slate-800/60 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:shadow-amber-500/10 transition-all duration-300 group overflow-hidden relative">
            <div class="absolute -right-10 -top-10 w-32 h-32 bg-amber-500/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
            <div class="flex justify-between items-start mb-6">
              <div class="w-14 h-14 rounded-2xl bg-amber-50 dark:bg-amber-500/10 flex items-center justify-center text-amber-600 dark:text-amber-400 transform group-hover:scale-110 transition-transform">
                <ClipboardList class="w-7 h-7" />
              </div>
            </div>
            <h3 class="text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-widest mb-1">Evaluaciones</h3>
            <p class="text-4xl md:text-5xl font-black text-slate-800 dark:text-white tracking-tighter">{{ resumen.total_asignaciones }}</p>
          </div>

          <!-- Instituciones -->
          <div class="bg-white dark:bg-slate-900/40 backdrop-blur-xl border border-slate-300/60 dark:border-slate-800/60 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:shadow-emerald-500/10 transition-all duration-300 group overflow-hidden relative">
            <div class="absolute -right-10 -top-10 w-32 h-32 bg-emerald-500/10 rounded-full blur-3xl group-hover:scale-150 transition-transform duration-700"></div>
            <div class="flex justify-between items-start mb-6">
              <div class="w-14 h-14 rounded-2xl bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center text-emerald-600 dark:text-emerald-400 transform group-hover:rotate-6 transition-transform">
                <Building2 class="w-7 h-7" />
              </div>
            </div>
            <h3 class="text-slate-500 dark:text-slate-400 text-xs font-bold uppercase tracking-widest mb-1">Red Educativa</h3>
            <p class="text-4xl md:text-5xl font-black text-slate-800 dark:text-white tracking-tighter">{{ resumen.total_instituciones }}</p>
          </div>

        </div>

        <!-- Detailed Analytics Section -->
        <div class="grid grid-cols-1 lg:grid-cols-12 gap-6 md:gap-8">
          
          <!-- Left Wing: Completion Gauge -->
          <div class="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl p-8 shadow-sm flex flex-col relative overflow-hidden">
            <div class="absolute top-0 right-0 p-8 opacity-10">
              <CheckCircle2 class="w-32 h-32 text-emerald-500 rotate-12" />
            </div>
            
            <h3 class="text-lg font-black text-slate-800 dark:text-white mb-8 flex items-center gap-3">
              <span class="w-2 h-8 bg-emerald-500 rounded-full"></span>
              Progreso de Evaluación
            </h3>
            
            <div class="flex-1 flex flex-col items-center justify-center py-6">
              <div class="relative w-56 h-56 md:w-64 md:h-64">
                <svg viewBox="0 0 36 36" class="w-full h-full transform -rotate-90 filter drop-shadow-lg">
                  <circle class="text-slate-100 dark:text-slate-800" stroke-width="2.5" stroke="currentColor" fill="none" r="15.9155" cx="18" cy="18" />
                  <circle class="text-emerald-500 transition-all duration-[1500ms] cubic-bezier(0.34, 1.56, 0.64, 1)" 
                    stroke-width="2.5" 
                    :stroke-dasharray="`${completadosPct}, 100`" 
                    stroke-linecap="round" 
                    stroke="currentColor" 
                    fill="none" 
                    r="15.9155" cx="18" cy="18" />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center">
                  <span class="text-5xl md:text-6xl font-black text-slate-800 dark:text-white leading-none">{{ completadosPct }}%</span>
                  <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-[0.2em] mt-3">Completados</span>
                </div>
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mt-4">
              <div class="bg-slate-50 dark:bg-slate-800/40 rounded-2xl p-4 border border-slate-300 dark:border-slate-700/50">
                <p class="text-[10px] font-bold text-slate-400 uppercase mb-1">Asignados</p>
                <p class="text-xl font-black text-slate-800 dark:text-white">{{ resumen.total_asignaciones }}</p>
              </div>
              <div class="bg-emerald-50/50 dark:bg-emerald-500/10 rounded-2xl p-4 border border-emerald-100 dark:border-emerald-500/20">
                <p class="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 uppercase mb-1">Resueltos</p>
                <p class="text-xl font-black text-emerald-600 dark:text-emerald-400">{{ resumen.total_completados }}</p>
              </div>
            </div>
          </div>

          <!-- Middle Section: Distribution Bars -->
          <div class="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl p-8 shadow-sm flex flex-col">
            <h3 class="text-lg font-black text-slate-800 dark:text-white mb-8 flex items-center gap-3">
              <span class="w-2 h-8 bg-indigo-500 rounded-full"></span>
              Distribución Regional
            </h3>
            
            <div class="space-y-10 flex-1 flex flex-col justify-center">
              <!-- Comunicación -->
              <div class="group">
                <div class="flex justify-between items-center mb-4">
                  <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-2xl bg-teal-50 dark:bg-teal-500/10 flex items-center justify-center border border-teal-100 dark:border-teal-500/20 group-hover:scale-110 transition-transform">
                      <BookOpen class="w-6 h-6 text-teal-600 dark:text-teal-400" />
                    </div>
                    <div>
                      <p class="text-sm font-black text-slate-800 dark:text-white uppercase tracking-tight">LectoSistem</p>
                      <p class="text-xs font-bold text-slate-400">Comprensión Lectora</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <p class="text-2xl font-black text-slate-800 dark:text-white leading-none">{{ resumen.total_examenes_lectura }}</p>
                    <p class="text-xs font-black text-teal-500 mt-1">{{ lecturaPct }}%</p>
                  </div>
                </div>
                <div class="h-4 w-full bg-slate-100 dark:bg-slate-800/50 rounded-full p-1 border border-slate-300 dark:border-slate-700/30">
                  <div class="h-full bg-gradient-to-r from-teal-400 to-emerald-500 rounded-full transition-all duration-1000 shadow-sm" :style="`width: ${lecturaPct}%`"></div>
                </div>
              </div>

              <!-- Matemática -->
              <div class="group">
                <div class="flex justify-between items-center mb-4">
                  <div class="flex items-center gap-4">
                    <div class="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center border border-indigo-100 dark:border-indigo-500/20 group-hover:scale-110 transition-transform">
                      <Calculator class="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <div>
                      <p class="text-sm font-black text-slate-800 dark:text-white uppercase tracking-tight">MatSistem</p>
                      <p class="text-xs font-bold text-slate-400">Pensamiento Lógico</p>
                    </div>
                  </div>
                  <div class="text-right">
                    <p class="text-2xl font-black text-slate-800 dark:text-white leading-none">{{ resumen.total_examenes_matematica }}</p>
                    <p class="text-xs font-black text-indigo-500 mt-1">{{ matematicaPct }}%</p>
                  </div>
                </div>
                <div class="h-4 w-full bg-slate-100 dark:bg-slate-800/50 rounded-full p-1 border border-slate-300 dark:border-slate-700/30">
                  <div class="h-full bg-gradient-to-r from-indigo-400 to-purple-500 rounded-full transition-all duration-1000 shadow-sm" :style="`width: ${matematicaPct}%`"></div>
                </div>
              </div>
            </div>

            <div class="mt-8 p-4 bg-slate-50 dark:bg-slate-800/20 rounded-2xl border border-slate-300 dark:border-slate-700/30">
               <div class="flex items-center gap-3">
                 <Activity class="w-4 h-4 text-indigo-500" />
                 <p class="text-[11px] font-bold text-slate-500 dark:text-slate-400 leading-tight">
                   El sistema prioriza la equidad en el despliegue de evaluaciones por área.
                 </p>
               </div>
            </div>
          </div>

          <!-- Right Wing: Recent Activity -->
          <div class="lg:col-span-4 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl p-0 shadow-sm flex flex-col overflow-hidden">
            <div class="p-8 border-b border-slate-300 dark:border-slate-800">
              <h3 class="text-lg font-black text-slate-800 dark:text-white flex items-center gap-3">
                <span class="w-2 h-8 bg-amber-500 rounded-full"></span>
                Actividad Reciente
              </h3>
            </div>
            
            <div class="flex-1 overflow-y-auto p-4 md:p-6 space-y-4 max-h-[600px] custom-scrollbar">
              <div v-if="resumen.recientes.length === 0" class="h-full flex flex-col items-center justify-center text-center px-6 py-12">
                <div class="w-20 h-20 bg-slate-50 dark:bg-slate-800/50 rounded-full flex items-center justify-center mb-4">
                  <Medal class="w-10 h-10 text-slate-200 dark:text-slate-700" />
                </div>
                <p class="text-sm font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Sin actividad</p>
                <p class="text-xs text-slate-400 mt-2">Los nuevos exámenes aparecerán aquí instantáneamente.</p>
              </div>
              
              <div v-for="item in resumen.recientes" :key="`${item.area}-${item.id}`"
                class="flex items-center gap-4 p-4 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800/80 transition-all duration-300 border border-transparent hover:border-slate-300 dark:hover:border-slate-700/50 cursor-pointer group active:scale-95">
                
                <div :class="item.area === 'lectura'
                  ? 'bg-teal-50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400 group-hover:bg-teal-500 group-hover:text-white'
                  : 'bg-indigo-50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white'"
                  class="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0 transition-all duration-500 shadow-sm">
                  <BookOpen v-if="item.area === 'lectura'" class="w-6 h-6" />
                  <Calculator v-else class="w-6 h-6" />
                </div>
                
                <div class="min-w-0 flex-1">
                  <div class="flex items-center gap-2 mb-0.5">
                    <p class="text-sm font-black text-slate-800 dark:text-slate-200 truncate">{{ item.titulo }}</p>
                  </div>
                  <div class="flex items-center gap-3">
                    <span class="text-[10px] font-black uppercase tracking-wider" :class="item.area === 'lectura' ? 'text-teal-500' : 'text-indigo-500'">
                      {{ item.grado }}
                    </span>
                    <span class="w-1 h-1 rounded-full bg-slate-300 dark:bg-slate-700"></span>
                    <span class="text-[10px] font-bold text-slate-400 flex items-center gap-1">
                      <Clock class="w-3 h-3" />
                      {{ formatFecha(item.fecha) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="p-6 bg-slate-50 dark:bg-slate-800/30 text-center">
              <p class="text-[10px] font-black text-slate-400 uppercase tracking-[0.3em]">LectoSistem DRE Engine</p>
            </div>
          </div>

        </div>

      </template>
    </main>

    <Footer />
  </div>
</template>

<style scoped>
.animate-spin-reverse {
  animation: spin-reverse 3s linear infinite;
}

@keyframes spin-reverse {
  from { transform: rotate(360deg); }
  to { transform: rotate(0deg); }
}

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
