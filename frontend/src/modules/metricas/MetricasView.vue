<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../../shared/services/api'
import Header from '../../shared/components/Header.vue'
import Footer from '../../shared/components/Footer.vue'
import {
  Home, Users, BookOpen, Calculator,
  Clock, BarChart3, RefreshCw,
  Building2, CheckCircle2, ClipboardList,
  TrendingUp, Activity, FileText, Medal
} from 'lucide-vue-next'
import { useTheme } from '../../shared/composables/useTheme'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const auth = useAuthStore()
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
    
    <Header
      title="Dashboard de Métricas"
      subtitle="Analítica y estadísticas en tiempo real"
      gradient-class="from-indigo-600 via-purple-600 to-violet-600"
      subtitle-class="text-indigo-100"
    >
      <template #actions-before>
        <button @click="router.push(auth.homeRoute)"
          class="p-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white backdrop-blur-sm border border-white/20 transition-all shadow-sm"
          title="Inicio">
          <Home class="w-5 h-5" />
        </button>
      </template>
    </Header>

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-8 w-full space-y-8">
      
      <!-- Top Actions -->
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 class="text-xl font-black text-slate-800 dark:text-white flex items-center gap-2">
            <Activity class="w-5 h-5 text-indigo-500" />
            Visión General
          </h2>
          <p class="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Datos consolidados para el rol: <span class="font-bold text-indigo-600 dark:text-indigo-400">{{ rolLabel }}</span>
          </p>
        </div>
        <button @click="fetchMetricas" :disabled="loading"
          class="flex items-center justify-center gap-2 px-4 py-2 text-sm font-bold text-white bg-slate-800 dark:bg-white dark:text-slate-900 rounded-xl hover:opacity-90 transition-opacity shadow-sm disabled:opacity-50">
          <RefreshCw class="w-4 h-4" :class="{'animate-spin': loading}" />
          Actualizar Datos
        </button>
      </div>

      <!-- Error state -->
      <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-2xl p-4 text-red-600 dark:text-red-400 text-sm flex items-center justify-between shadow-sm">
        <span class="flex items-center gap-2"><div class="w-2 h-2 rounded-full bg-red-500"></div> {{ error }}</span>
        <button @click="fetchMetricas" class="underline font-medium hover:text-red-700 dark:hover:text-red-300">Reintentar</button>
      </div>

      <!-- Loading state -->
      <div v-if="loading && !resumen" class="flex flex-col items-center justify-center py-32">
        <div class="relative w-16 h-16">
          <div class="absolute inset-0 rounded-full border-4 border-slate-100 dark:border-slate-800"></div>
          <div class="absolute inset-0 rounded-full border-4 border-indigo-500 border-t-transparent animate-spin"></div>
        </div>
        <p class="text-slate-500 dark:text-slate-400 font-medium mt-4">Sincronizando métricas...</p>
      </div>

      <template v-if="resumen">
        
        <!-- KPI Row 1: The Big Numbers -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          
          <!-- Exámenes Totales -->
          <div class="bg-white dark:bg-slate-900/50 backdrop-blur-xl border border-slate-200/60 dark:border-slate-800/60 rounded-3xl p-6 shadow-sm relative overflow-hidden group">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-gradient-to-br from-indigo-500/10 to-purple-500/10 dark:from-indigo-500/20 dark:to-purple-500/20 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
            <div class="flex justify-between items-start mb-4 relative z-10">
              <div class="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center text-indigo-600 dark:text-indigo-400">
                <BarChart3 class="w-6 h-6" />
              </div>
              <span class="px-2.5 py-1 bg-indigo-100 dark:bg-indigo-500/20 text-indigo-700 dark:text-indigo-300 text-xs font-bold rounded-lg flex items-center gap-1">
                <TrendingUp class="w-3 h-3" /> +12%
              </span>
            </div>
            <div class="relative z-10">
              <h3 class="text-slate-500 dark:text-slate-400 text-sm font-semibold mb-1">Exámenes Generados</h3>
              <p class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">{{ resumen.total_examenes }}</p>
            </div>
          </div>

          <!-- Total Usuarios -->
          <div class="bg-white dark:bg-slate-900/50 backdrop-blur-xl border border-slate-200/60 dark:border-slate-800/60 rounded-3xl p-6 shadow-sm relative overflow-hidden group">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 dark:from-blue-500/20 dark:to-cyan-500/20 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
            <div class="flex justify-between items-start mb-4 relative z-10">
              <div class="w-12 h-12 rounded-2xl bg-blue-50 dark:bg-blue-500/10 flex items-center justify-center text-blue-600 dark:text-blue-400">
                <Users class="w-6 h-6" />
              </div>
            </div>
            <div class="relative z-10">
              <h3 class="text-slate-500 dark:text-slate-400 text-sm font-semibold mb-1">Usuarios Activos</h3>
              <p class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">{{ resumen.total_usuarios }}</p>
            </div>
          </div>

          <!-- Asignaciones -->
          <div class="bg-white dark:bg-slate-900/50 backdrop-blur-xl border border-slate-200/60 dark:border-slate-800/60 rounded-3xl p-6 shadow-sm relative overflow-hidden group">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-gradient-to-br from-amber-500/10 to-orange-500/10 dark:from-amber-500/20 dark:to-orange-500/20 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
            <div class="flex justify-between items-start mb-4 relative z-10">
              <div class="w-12 h-12 rounded-2xl bg-amber-50 dark:bg-amber-500/10 flex items-center justify-center text-amber-600 dark:text-amber-400">
                <ClipboardList class="w-6 h-6" />
              </div>
            </div>
            <div class="relative z-10">
              <h3 class="text-slate-500 dark:text-slate-400 text-sm font-semibold mb-1">Total Asignaciones</h3>
              <p class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">{{ resumen.total_asignaciones }}</p>
            </div>
          </div>

          <!-- Instituciones (o UGELes) -->
          <div class="bg-white dark:bg-slate-900/50 backdrop-blur-xl border border-slate-200/60 dark:border-slate-800/60 rounded-3xl p-6 shadow-sm relative overflow-hidden group">
            <div class="absolute -right-6 -top-6 w-24 h-24 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 dark:from-emerald-500/20 dark:to-teal-500/20 rounded-full blur-2xl group-hover:scale-150 transition-transform duration-500"></div>
            <div class="flex justify-between items-start mb-4 relative z-10">
              <div class="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-500/10 flex items-center justify-center text-emerald-600 dark:text-emerald-400">
                <Building2 class="w-6 h-6" />
              </div>
            </div>
            <div class="relative z-10">
              <h3 class="text-slate-500 dark:text-slate-400 text-sm font-semibold mb-1">Instituciones Educativas</h3>
              <p class="text-4xl font-black text-slate-800 dark:text-white tracking-tight">{{ resumen.total_instituciones }}</p>
            </div>
          </div>

        </div>

        <!-- Dashboard Main Charts Row -->
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          <!-- Column 1: Performance / Completion Gauge -->
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm flex flex-col">
            <h3 class="text-base font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
              <CheckCircle2 class="w-5 h-5 text-emerald-500" />
              Tasa de Finalización
            </h3>
            
            <div class="flex-1 flex flex-col items-center justify-center relative">
              <!-- SVG Gauge Chart -->
              <div class="relative w-48 h-48">
                <!-- Background track -->
                <svg viewBox="0 0 36 36" class="w-full h-full transform -rotate-90">
                  <circle class="text-slate-100 dark:text-slate-800" stroke-width="3" stroke="currentColor" fill="none" r="15.9155" cx="18" cy="18" />
                  <!-- Progress track -->
                  <circle class="text-emerald-500 transition-all duration-1000 ease-out" 
                    stroke-width="3" 
                    :stroke-dasharray="`${completadosPct}, 100`" 
                    stroke-linecap="round" 
                    stroke="currentColor" 
                    fill="none" 
                    r="15.9155" cx="18" cy="18" />
                </svg>
                <div class="absolute inset-0 flex flex-col items-center justify-center">
                  <span class="text-4xl font-black text-slate-800 dark:text-white">{{ completadosPct }}%</span>
                  <span class="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mt-1">Completados</span>
                </div>
              </div>
              
              <div class="mt-8 w-full bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-4 flex justify-between items-center border border-slate-100 dark:border-slate-700/50">
                <div class="text-center">
                  <p class="text-xs text-slate-500 dark:text-slate-400 font-medium">Asignados</p>
                  <p class="text-lg font-black text-slate-800 dark:text-white">{{ resumen.total_asignaciones }}</p>
                </div>
                <div class="h-8 w-px bg-slate-200 dark:bg-slate-700"></div>
                <div class="text-center">
                  <p class="text-xs text-slate-500 dark:text-slate-400 font-medium">Resueltos</p>
                  <p class="text-lg font-black text-emerald-600 dark:text-emerald-400">{{ resumen.total_completados }}</p>
                </div>
              </div>
            </div>
          </div>

          <!-- Column 2: Distribution Donut -->
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-6 shadow-sm flex flex-col">
            <h3 class="text-base font-bold text-slate-800 dark:text-white mb-6 flex items-center gap-2">
              <FileText class="w-5 h-5 text-indigo-500" />
              Distribución por Área
            </h3>
            
            <div class="flex-1 flex flex-col items-center justify-center">
              
              <!-- Two overlapping bars for distribution -->
              <div class="w-full space-y-6">
                <!-- Comunicación -->
                <div>
                  <div class="flex justify-between items-end mb-2">
                    <div class="flex items-center gap-2">
                      <div class="w-8 h-8 rounded-xl bg-teal-50 dark:bg-teal-500/10 flex items-center justify-center">
                        <BookOpen class="w-4 h-4 text-teal-600 dark:text-teal-400" />
                      </div>
                      <div>
                        <p class="text-sm font-bold text-slate-800 dark:text-white">Comunicación</p>
                        <p class="text-xs text-slate-500 dark:text-slate-400">LectoSistem</p>
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="text-lg font-black text-slate-800 dark:text-white">{{ resumen.total_examenes_lectura }}</p>
                      <p class="text-xs font-bold text-teal-600 dark:text-teal-400">{{ lecturaPct }}%</p>
                    </div>
                  </div>
                  <div class="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full bg-gradient-to-r from-teal-400 to-emerald-500 rounded-full transition-all duration-1000" :style="`width: ${lecturaPct}%`"></div>
                  </div>
                </div>

                <!-- Matemática -->
                <div>
                  <div class="flex justify-between items-end mb-2">
                    <div class="flex items-center gap-2">
                      <div class="w-8 h-8 rounded-xl bg-indigo-50 dark:bg-indigo-500/10 flex items-center justify-center">
                        <Calculator class="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
                      </div>
                      <div>
                        <p class="text-sm font-bold text-slate-800 dark:text-white">Matemática</p>
                        <p class="text-xs text-slate-500 dark:text-slate-400">MatSistem</p>
                      </div>
                    </div>
                    <div class="text-right">
                      <p class="text-lg font-black text-slate-800 dark:text-white">{{ resumen.total_examenes_matematica }}</p>
                      <p class="text-xs font-bold text-indigo-600 dark:text-indigo-400">{{ matematicaPct }}%</p>
                    </div>
                  </div>
                  <div class="h-3 w-full bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                    <div class="h-full bg-gradient-to-r from-indigo-400 to-purple-500 rounded-full transition-all duration-1000" :style="`width: ${matematicaPct}%`"></div>
                  </div>
                </div>

              </div>

            </div>
          </div>

          <!-- Column 3: Recent Activity -->
          <div class="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl p-0 shadow-sm flex flex-col overflow-hidden">
            <div class="p-6 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between">
              <h3 class="text-base font-bold text-slate-800 dark:text-white flex items-center gap-2">
                <Clock class="w-5 h-5 text-amber-500" />
                Actividad Reciente
              </h3>
            </div>
            
            <div class="flex-1 overflow-y-auto p-4 space-y-3">
              <div v-if="resumen.recientes.length === 0" class="h-full flex flex-col items-center justify-center text-center px-4">
                <Medal class="w-12 h-12 text-slate-200 dark:text-slate-700 mb-3" />
                <p class="text-sm font-medium text-slate-500 dark:text-slate-400">No hay exámenes generados recientemente</p>
              </div>
              
              <div v-for="item in resumen.recientes" :key="`${item.area}-${item.id}`"
                class="flex items-center gap-4 p-3 rounded-2xl hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors border border-transparent hover:border-slate-100 dark:hover:border-slate-700/50 cursor-pointer group">
                
                <div :class="item.area === 'lectura'
                  ? 'bg-teal-100/50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400 group-hover:bg-teal-500 group-hover:text-white'
                  : 'bg-indigo-100/50 dark:bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white'"
                  class="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-colors duration-300">
                  <BookOpen v-if="item.area === 'lectura'" class="w-5 h-5" />
                  <Calculator v-else class="w-5 h-5" />
                </div>
                
                <div class="min-w-0 flex-1">
                  <p class="text-sm font-bold text-slate-800 dark:text-slate-200 truncate">{{ item.titulo }}</p>
                  <p class="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-0.5">
                    <span class="inline-block w-1.5 h-1.5 rounded-full" :class="item.area === 'lectura' ? 'bg-teal-400' : 'bg-indigo-400'"></span>
                    {{ item.grado }}
                  </p>
                </div>
                
                <div class="text-right flex-shrink-0">
                  <p class="text-[11px] font-medium text-slate-400 dark:text-slate-500">{{ formatFecha(item.fecha) }}</p>
                </div>
              </div>
            </div>
          </div>

        </div>

      </template>
    </main>

    <Footer />
  </div>
</template>
