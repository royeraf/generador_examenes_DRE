<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../services/api'
import Header from '../components/Header.vue'
import Footer from '../components/Footer.vue'
import {
  Home, Users, BookOpen, Calculator, TrendingUp,
  Award, Clock, BarChart3, RefreshCw, Loader2,
  UserCheck, UserX, FileText, GraduationCap
} from 'lucide-vue-next'
import { useTheme } from '../composables/useTheme'

const router = useRouter()
const { isDark, toggleTheme } = useTheme()

interface Resumen {
  total_docentes: number
  docentes_activos: number
  docentes_inactivos: number
  total_examenes: number
  examenes_lectura: number
  examenes_matematica: number
}

interface MesData {
  mes: string
  label: string
  lectura: number
  matematica: number
}

interface TopDocente {
  id: number
  nombre: string
  dni: string
  institucion: string
  lectura: number
  matematica: number
  total: number
}

interface GradoData {
  grado: string
  total: number
  area: string
}

interface Reciente {
  id: number
  titulo: string
  grado: string
  docente: string
  fecha: string | null
  area: 'lectura' | 'matematica'
}

interface Metricas {
  resumen: Resumen
  por_mes: MesData[]
  top_docentes: TopDocente[]
  por_grado_lectura: GradoData[]
  por_grado_matematica: GradoData[]
  recientes: Reciente[]
}

const metricas = ref<Metricas | null>(null)
const loading = ref(true)
const error = ref('')

async function fetchMetricas() {
  loading.value = true
  error.value = ''
  try {
    const res = await apiClient.get('/admin/metricas')
    metricas.value = res.data
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar métricas'
  } finally {
    loading.value = false
  }
}

onMounted(fetchMetricas)

const maxMes = computed(() => {
  if (!metricas.value) return 1
  return Math.max(1, ...metricas.value.por_mes.map(m => m.lectura + m.matematica))
})

const maxGradoLec = computed(() => {
  if (!metricas.value) return 1
  return Math.max(1, ...metricas.value.por_grado_lectura.map(g => g.total))
})

const maxGradoMat = computed(() => {
  if (!metricas.value) return 1
  return Math.max(1, ...metricas.value.por_grado_matematica.map(g => g.total))
})

function formatFecha(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })
}

function barPct(val: number, max: number) {
  return max === 0 ? 0 : Math.round((val / max) * 100)
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 via-indigo-50/20 to-sky-50/30 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 transition-colors">

    <Header
      title="Métricas del Sistema"
      subtitle="Panel de uso y actividad"
      gradient-class="from-violet-600 via-indigo-600 to-blue-600 shadow-indigo-500/20"
      subtitle-class="text-indigo-100 dark:text-slate-400"
    >
      <template #actions-before>
        <button @click="router.push('/')"
          class="p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 transition-all duration-300"
          title="Inicio">
          <Home class="w-5 h-5" />
        </button>
      </template>
    </Header>

    <main class="flex-1 max-w-7xl mx-auto px-4 sm:px-6 py-6 w-full space-y-6">

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

      <template v-if="!loading && metricas">

        <!-- Refresh button -->
        <div class="flex justify-end">
          <button @click="fetchMetricas"
            class="flex items-center gap-2 px-4 py-2 text-xs font-bold text-indigo-600 dark:text-indigo-400 bg-white dark:bg-slate-800 border border-indigo-200 dark:border-slate-700 rounded-xl hover:bg-indigo-50 dark:hover:bg-slate-700 transition-all shadow-sm">
            <RefreshCw class="w-3.5 h-3.5" />
            Actualizar
          </button>
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">

          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-400 to-indigo-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Users class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ metricas.resumen.total_docentes }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Total docentes</p>
          </div>

          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-md shadow-teal-500/20">
              <UserCheck class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ metricas.resumen.docentes_activos }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Activos</p>
          </div>

          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-rose-400 to-red-500 flex items-center justify-center shadow-md shadow-red-500/20">
              <UserX class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ metricas.resumen.docentes_inactivos }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Inactivos</p>
          </div>

          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center shadow-md shadow-amber-500/20">
              <FileText class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ metricas.resumen.total_examenes }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">Total exámenes</p>
          </div>

          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-md shadow-teal-500/20">
              <BookOpen class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ metricas.resumen.examenes_lectura }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">LectoSistem</p>
          </div>

          <div class="bg-white dark:bg-slate-800 rounded-2xl p-4 border border-slate-100 dark:border-slate-700 shadow-sm flex flex-col gap-2">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-400 to-purple-500 flex items-center justify-center shadow-md shadow-indigo-500/20">
              <Calculator class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ metricas.resumen.examenes_matematica }}</p>
            <p class="text-[11px] text-slate-500 dark:text-slate-400 font-medium leading-tight">MatSistem</p>
          </div>

        </div>

        <!-- Actividad mensual + Recientes -->
        <div class="grid lg:grid-cols-3 gap-4">

          <!-- Gráfico mensual -->
          <div class="lg:col-span-2 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-5">
            <div class="flex items-center gap-2 mb-5">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-400 to-violet-500 flex items-center justify-center">
                <BarChart3 class="w-4 h-4 text-white" />
              </div>
              <h3 class="text-sm font-bold text-slate-800 dark:text-white">Actividad últimos 6 meses</h3>
              <div class="ml-auto flex items-center gap-3 text-[10px] text-slate-500 dark:text-slate-400">
                <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-sm bg-teal-400 inline-block"></span>Lectura</span>
                <span class="flex items-center gap-1"><span class="w-2.5 h-2.5 rounded-sm bg-indigo-400 inline-block"></span>Matemática</span>
              </div>
            </div>

            <div class="flex items-end justify-between gap-2 h-40">
              <div v-for="mes in metricas.por_mes" :key="mes.mes"
                class="flex-1 flex flex-col items-center gap-1">
                <!-- Barras apiladas -->
                <div class="w-full flex flex-col justify-end gap-0.5" style="height: 120px;">
                  <div
                    class="w-full bg-indigo-400 dark:bg-indigo-500 rounded-t-sm transition-all duration-700"
                    :style="{ height: barPct(mes.matematica, maxMes) * 1.2 + 'px' }"
                    :title="`Matemática: ${mes.matematica}`"
                  ></div>
                  <div
                    class="w-full bg-teal-400 dark:bg-teal-500 rounded-t-sm transition-all duration-700"
                    :style="{ height: barPct(mes.lectura, maxMes) * 1.2 + 'px' }"
                    :title="`Lectura: ${mes.lectura}`"
                  ></div>
                </div>
                <span class="text-[9px] text-slate-400 dark:text-slate-500 text-center leading-tight">{{ mes.label.split(' ')[0] }}</span>
                <span class="text-[9px] font-bold text-slate-600 dark:text-slate-300">{{ mes.lectura + mes.matematica }}</span>
              </div>
            </div>
          </div>

          <!-- Exámenes recientes -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center">
                <Clock class="w-4 h-4 text-white" />
              </div>
              <h3 class="text-sm font-bold text-slate-800 dark:text-white">Recientes</h3>
            </div>
            <div class="space-y-2.5 overflow-y-auto max-h-48">
              <div v-for="item in metricas.recientes" :key="`${item.area}-${item.id}`"
                class="flex items-start gap-2.5 p-2 rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                <div :class="item.area === 'lectura'
                  ? 'bg-teal-100 dark:bg-teal-900/30 text-teal-600 dark:text-teal-400'
                  : 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-600 dark:text-indigo-400'"
                  class="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0">
                  <BookOpen v-if="item.area === 'lectura'" class="w-3.5 h-3.5" />
                  <Calculator v-else class="w-3.5 h-3.5" />
                </div>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-semibold text-slate-700 dark:text-slate-200 truncate">{{ item.titulo }}</p>
                  <p class="text-[10px] text-slate-400 dark:text-slate-500 truncate">{{ item.docente }}</p>
                  <p class="text-[10px] text-slate-400 dark:text-slate-500">{{ formatFecha(item.fecha) }}</p>
                </div>
              </div>
              <p v-if="metricas.recientes.length === 0" class="text-xs text-slate-400 text-center py-4">Sin actividad aún</p>
            </div>
          </div>

        </div>

        <!-- Top docentes + Distribución por grado -->
        <div class="grid lg:grid-cols-2 gap-4">

          <!-- Top docentes -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-400 to-purple-500 flex items-center justify-center">
                <Award class="w-4 h-4 text-white" />
              </div>
              <h3 class="text-sm font-bold text-slate-800 dark:text-white">Top docentes activos</h3>
            </div>
            <div class="space-y-2">
              <div v-for="(doc, idx) in metricas.top_docentes.slice(0, 8)" :key="doc.id"
                class="flex items-center gap-3 p-2 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors">
                <span :class="[
                  'w-6 h-6 rounded-lg flex items-center justify-center text-[10px] font-black flex-shrink-0',
                  idx === 0 ? 'bg-amber-400 text-white' :
                  idx === 1 ? 'bg-slate-300 dark:bg-slate-600 text-slate-700 dark:text-slate-200' :
                  idx === 2 ? 'bg-orange-300 text-white' :
                  'bg-slate-100 dark:bg-slate-700 text-slate-500 dark:text-slate-400'
                ]">{{ idx + 1 }}</span>
                <div class="min-w-0 flex-1">
                  <p class="text-xs font-bold text-slate-700 dark:text-slate-200 truncate">{{ doc.nombre || doc.dni }}</p>
                  <p class="text-[10px] text-slate-400 dark:text-slate-500 truncate">{{ doc.institucion }}</p>
                </div>
                <div class="flex items-center gap-1.5 flex-shrink-0">
                  <span class="text-[10px] font-bold text-teal-600 dark:text-teal-400 bg-teal-50 dark:bg-teal-900/20 px-1.5 py-0.5 rounded-md">{{ doc.lectura }}</span>
                  <span class="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 bg-indigo-50 dark:bg-indigo-900/20 px-1.5 py-0.5 rounded-md">{{ doc.matematica }}</span>
                  <span class="text-[10px] font-black text-slate-600 dark:text-slate-300 w-5 text-right">{{ doc.total }}</span>
                </div>
              </div>
              <p v-if="metricas.top_docentes.length === 0" class="text-xs text-slate-400 text-center py-4">Sin datos aún</p>
            </div>
            <div class="flex items-center justify-end gap-3 mt-3 pt-3 border-t border-slate-100 dark:border-slate-700 text-[10px] text-slate-400">
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-teal-400 inline-block"></span>Lectura</span>
              <span class="flex items-center gap-1"><span class="w-2 h-2 rounded-sm bg-indigo-400 inline-block"></span>Matemática</span>
              <span class="flex items-center gap-1 font-bold text-slate-500">Total</span>
            </div>
          </div>

          <!-- Distribución por grado -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 shadow-sm p-5">
            <div class="flex items-center gap-2 mb-4">
              <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-sky-400 to-blue-500 flex items-center justify-center">
                <GraduationCap class="w-4 h-4 text-white" />
              </div>
              <h3 class="text-sm font-bold text-slate-800 dark:text-white">Exámenes por grado</h3>
            </div>

            <!-- LectoSistem -->
            <p class="text-[10px] font-bold text-teal-600 dark:text-teal-400 uppercase tracking-wider mb-2">Lectura</p>
            <div class="space-y-1.5 mb-4">
              <div v-for="g in metricas.por_grado_lectura" :key="g.grado" class="flex items-center gap-2">
                <span class="text-[10px] text-slate-500 dark:text-slate-400 w-28 flex-shrink-0 truncate" :title="g.grado">{{ g.grado }}</span>
                <div class="flex-1 bg-slate-100 dark:bg-slate-700 rounded-full h-2">
                  <div class="bg-teal-400 dark:bg-teal-500 h-2 rounded-full transition-all duration-700"
                    :style="{ width: barPct(g.total, maxGradoLec) + '%' }"></div>
                </div>
                <span class="text-[10px] font-bold text-slate-600 dark:text-slate-300 w-5 text-right">{{ g.total }}</span>
              </div>
              <p v-if="metricas.por_grado_lectura.length === 0" class="text-[10px] text-slate-400">Sin datos</p>
            </div>

            <!-- MatSistem -->
            <p class="text-[10px] font-bold text-indigo-600 dark:text-indigo-400 uppercase tracking-wider mb-2">Matemática</p>
            <div class="space-y-1.5">
              <div v-for="g in metricas.por_grado_matematica" :key="g.grado" class="flex items-center gap-2">
                <span class="text-[10px] text-slate-500 dark:text-slate-400 w-28 flex-shrink-0 truncate" :title="g.grado">{{ g.grado }}</span>
                <div class="flex-1 bg-slate-100 dark:bg-slate-700 rounded-full h-2">
                  <div class="bg-indigo-400 dark:bg-indigo-500 h-2 rounded-full transition-all duration-700"
                    :style="{ width: barPct(g.total, maxGradoMat) + '%' }"></div>
                </div>
                <span class="text-[10px] font-bold text-slate-600 dark:text-slate-300 w-5 text-right">{{ g.total }}</span>
              </div>
              <p v-if="metricas.por_grado_matematica.length === 0" class="text-[10px] text-slate-400">Sin datos</p>
            </div>
          </div>

        </div>

      </template>
    </main>

    <Footer />
  </div>
</template>
