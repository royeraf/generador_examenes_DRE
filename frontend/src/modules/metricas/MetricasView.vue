<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../../shared/services/api'
import Header from '../../shared/components/Header.vue'
import Footer from '../../shared/components/Footer.vue'
import {
  Home, Users, BookOpen, Calculator,
  Clock, BarChart3, RefreshCw, Loader2,
  Building2, MapPin, CheckCircle2, ClipboardList
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

// formatFecha importado de shared/utils/dateUtils

const completadosPct = computed(() => {
  if (!resumen.value || !resumen.value.total_asignaciones) return 0
  return Math.min(100, Math.round((resumen.value.total_completados / resumen.value.total_asignaciones) * 100))
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
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-indigo-50/20 to-sky-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-colors">

    <Header
      title="Métricas"
      subtitle="Panel de uso y actividad"
      gradient-class="from-violet-600 via-indigo-600 to-blue-600 shadow-indigo-500/20"
      subtitle-class="text-indigo-100 dark:text-slate-400"
    >
      <template #actions-before>
        <button @click="router.push(auth.homeRoute)"
          class="p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 transition-all duration-300"
          title="Inicio">
          <Home class="w-5 h-5" />
        </button>
      </template>
    </Header>

    <main class="flex-1 max-w-5xl mx-auto px-4 sm:px-6 py-6 w-full space-y-6">

      <!-- Error -->
      <div v-if="error" class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-700 rounded-xl p-4 text-red-600 dark:text-red-400 text-sm flex items-center gap-2">
        {{ error }}
        <button @click="fetchMetricas" class="ml-auto text-xs underline">Reintentar</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex flex-col items-center justify-center py-24 gap-4">
        <Loader2 class="w-10 h-10 text-indigo-500 animate-spin" />
        <p class="text-slate-500 dark:text-slate-400 text-sm">Cargando métricas...</p>
      </div>

      <template v-if="!loading && resumen">

        <!-- Scope label + refresh -->
        <div class="flex items-center justify-between">
          <p class="text-xs text-slate-500 dark:text-slate-400">
            Mostrando datos para: <span class="font-semibold text-indigo-600 dark:text-indigo-400">{{ rolLabel }}</span>
          </p>
          <button @click="fetchMetricas"
            class="flex items-center gap-2 px-3 py-1.5 text-xs font-bold text-indigo-600 dark:text-indigo-400 bg-white dark:bg-slate-800 border border-indigo-200 dark:border-slate-700 rounded-xl hover:bg-indigo-50 dark:hover:bg-slate-700 transition-all shadow-sm">
            <RefreshCw class="w-3.5 h-3.5" />
            Actualizar
          </button>
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">

          <!-- Exámenes Lectura -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-md shadow-teal-500/20">
              <BookOpen class="w-4 h-4 text-white" />
            </div>
            <p class="text-3xl font-black text-slate-800 dark:text-white">{{ resumen.total_examenes_lectura }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Exámenes Lectura</p>
          </div>

          <!-- Exámenes Matemática -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Calculator class="w-4 h-4 text-white" />
            </div>
            <p class="text-3xl font-black text-slate-800 dark:text-white">{{ resumen.total_examenes_matematica }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Exámenes Matemática</p>
          </div>

          <!-- Usuarios en scope -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-400 to-pink-500 flex items-center justify-center shadow-md shadow-violet-500/20">
              <Users class="w-4 h-4 text-white" />
            </div>
            <p class="text-3xl font-black text-slate-800 dark:text-white">{{ resumen.total_usuarios }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Usuarios</p>
          </div>

          <!-- Total exámenes -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-md shadow-amber-500/20">
              <BarChart3 class="w-4 h-4 text-white" />
            </div>
            <p class="text-3xl font-black text-slate-800 dark:text-white">{{ resumen.total_examenes }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Total exámenes</p>
          </div>

        </div>

        <!-- Segunda fila: DRE muestra UGELes + IEs; UGEL muestra IEs; todos muestran asignaciones/completados -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">

          <!-- UGELes (solo DRE) -->
          <div v-if="resumen.total_ugeles > 0 || (auth.isEspecialista)"
            class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-cyan-400 to-teal-500 flex items-center justify-center shadow-md shadow-cyan-500/20">
              <MapPin class="w-4 h-4 text-white" />
            </div>
            <p class="text-3xl font-black text-slate-800 dark:text-white">{{ resumen.total_ugeles }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">UGELes activas</p>
          </div>

          <!-- Instituciones (DRE + UGEL + Director) -->
          <div v-if="resumen.total_instituciones > 0 || auth.isEspecialista || auth.isResponsableUGEL || auth.isDirector"
            class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center shadow-md shadow-sky-500/20">
              <Building2 class="w-4 h-4 text-white" />
            </div>
            <p class="text-3xl font-black text-slate-800 dark:text-white">{{ resumen.total_instituciones }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Instituciones</p>
          </div>

          <!-- Asignaciones -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-400 to-pink-500 flex items-center justify-center shadow-md shadow-rose-500/20">
              <ClipboardList class="w-4 h-4 text-white" />
            </div>
            <p class="text-3xl font-black text-slate-800 dark:text-white">{{ resumen.total_asignaciones }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Asignaciones</p>
          </div>

          <!-- Completados -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-green-500 flex items-center justify-center shadow-md shadow-emerald-500/20">
              <CheckCircle2 class="w-4 h-4 text-white" />
            </div>
            <p class="text-3xl font-black text-slate-800 dark:text-white">{{ resumen.total_completados }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Completados</p>
          </div>

        </div>

        <!-- Progreso de completados -->
        <div v-if="resumen.total_asignaciones > 0"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-5">
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-bold text-slate-800 dark:text-white">Tasa de completado</h3>
            <span class="text-sm font-black text-emerald-600 dark:text-emerald-400">{{ completadosPct }}%</span>
          </div>
          <div class="w-full bg-slate-100 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
            <div
              class="bg-gradient-to-r from-emerald-400 to-teal-500 h-3 rounded-full transition-all duration-700"
              :style="{ width: completadosPct + '%' }"
            ></div>
          </div>
          <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-2">
            {{ resumen.total_completados }} de {{ resumen.total_asignaciones }} exámenes asignados completados
          </p>
        </div>

        <!-- Exámenes recientes -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-5">
          <div class="flex items-center gap-2 mb-4">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
              <Clock class="w-4 h-4 text-white" />
            </div>
            <h3 class="text-sm font-bold text-slate-800 dark:text-white">Exámenes recientes</h3>
          </div>
          <div class="space-y-2">
            <div v-for="item in resumen.recientes" :key="`${item.area}-${item.id}`"
              class="flex items-center gap-3 p-2.5 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
              <div :class="item.area === 'lectura'
                ? 'bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400'
                : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'"
                class="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0">
                <BookOpen v-if="item.area === 'lectura'" class="w-4 h-4" />
                <Calculator v-else class="w-4 h-4" />
              </div>
              <div class="min-w-0 flex-1">
                <p class="text-xs font-semibold text-slate-700 dark:text-slate-200 truncate">{{ item.titulo }}</p>
                <p class="text-[10px] text-slate-400 dark:text-slate-500">{{ item.grado }} — {{ item.area === 'lectura' ? 'Comunicación' : 'Matemática' }}</p>
              </div>
              <span class="text-[10px] text-slate-400 dark:text-slate-500 flex-shrink-0">{{ formatFecha(item.fecha) }}</span>
            </div>
            <p v-if="resumen.recientes.length === 0" class="text-xs text-slate-400 text-center py-6">Sin actividad reciente</p>
          </div>
        </div>

      </template>
    </main>

    <Footer />
  </div>
</template>
