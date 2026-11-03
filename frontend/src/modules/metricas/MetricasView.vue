<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '../../shared/services/api'
import Navbar from '../../shared/components/Navbar.vue'
import Footer from '../../shared/components/Footer.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import BaseButton from '../../shared/components/BaseButton.vue'
import AvanceChart from './components/AvanceChart.vue'
import EstudiantesTreemap from './components/EstudiantesTreemap.vue'
import MapaProvincias from './components/MapaProvincias.vue'
import type { DistribucionData, MetricaMapa } from './types'
import {
  Users, BookOpen, Calculator,
  Clock, BarChart3, RefreshCw,
  Building2, CheckCircle2, ClipboardList,
  TrendingUp, Activity, Medal,
  MapPin, GraduationCap, School, Map as MapIcon
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

const distribucion = ref<DistribucionData | null>(null)
const loadingDist = ref(true)
const errorDist = ref('')

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

async function fetchDistribucion() {
  loadingDist.value = true
  errorDist.value = ''
  try {
    const res = await apiClient.get('/metricas/distribucion')
    distribucion.value = res.data
  } catch (e: any) {
    errorDist.value = e.response?.data?.detail ?? 'Error al cargar la distribución territorial'
  } finally {
    loadingDist.value = false
  }
}

async function refrescarTodo() {
  await Promise.all([fetchMetricas(), fetchDistribucion()])
}

onMounted(refrescarTodo)

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

// ── Distribución territorial ──────────────────────────────────────────────────
const esDre = computed(() => (distribucion.value?.rol ?? '').startsWith('especialista_dre'))

const avanceItems = computed(() => {
  if (!distribucion.value) return []
  return esDre.value
    ? distribucion.value.avance_por_ugel
    : distribucion.value.avance_por_institucion
})

const avanceTitulo = computed(() => (
  esDre.value ? 'Avance SIEVA por UGEL' : 'Avance SIEVA por Institución'
))

const avanceSubtitulo = computed(() => (
  esDre.value
    ? 'Asignaciones con al menos un intento completado en cada UGEL.'
    : 'Asignaciones con al menos un intento completado en cada institución.'
))

const avanceGlobalPct = computed(() => {
  const totales = distribucion.value?.totales
  if (!totales || totales.asignaciones === 0) return 0
  return Math.min(100, Math.round((totales.completados / totales.asignaciones) * 100))
})

const institucionesConEstudiantes = computed(() => distribucion.value?.totales.instituciones ?? 0)

// ── Vista mapa por provincia ──────────────────────────────────────────────────
type VistaDistribucion = 'graficos' | 'mapa'

const vistaDistribucion = ref<VistaDistribucion>('graficos')
const mapaMetrica = ref<MetricaMapa>('avance')
const provinciaSeleccionada = ref<string | null>(null)

function normalizarProvincia(texto: string): string {
  return texto
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
}

const provinciasConDatos = computed(() => {
  if (!distribucion.value) return []

  const mapa = new Map<string, {
    nombre: string
    estudiantes: number
    asignaciones: number
    completados: number
    avancePct: number
  }>()

  const asegurar = (nombre: string) => {
    const key = normalizarProvincia(nombre)
    let item = mapa.get(key)
    if (!item) {
      item = { nombre, estudiantes: 0, asignaciones: 0, completados: 0, avancePct: 0 }
      mapa.set(key, item)
    }
    return item
  }

  for (const item of distribucion.value.avance_por_ugel) {
    if (!item.provincia) continue
    const provincia = asegurar(item.provincia)
    provincia.asignaciones += item.asignaciones
    provincia.completados += item.completados
  }

  for (const item of distribucion.value.estudiantes_por_institucion) {
    if (!item.provincia) continue
    asegurar(item.provincia).estudiantes += item.estudiantes
  }

  const lista = [...mapa.values()]
  for (const provincia of lista) {
    provincia.avancePct = provincia.asignaciones > 0
      ? Math.min(100, Math.round((provincia.completados / provincia.asignaciones) * 100))
      : 0
  }

  return lista.sort((a, b) => (
    b.estudiantes - a.estudiantes
    || b.asignaciones - a.asignaciones
    || a.nombre.localeCompare(b.nombre)
  ))
})

const provinciaActiva = computed(() => {
  if (provinciaSeleccionada.value) return provinciaSeleccionada.value
  const lista = provinciasConDatos.value
  if (!lista.length) return null
  if (mapaMetrica.value === 'avance') {
    const porAvance = [...lista].sort((a, b) => (
      b.avancePct - a.avancePct
      || b.asignaciones - a.asignaciones
      || b.estudiantes - a.estudiantes
      || a.nombre.localeCompare(b.nombre)
    ))
    return porAvance[0]?.nombre ?? null
  }
  return lista[0]?.nombre ?? null
})

const detalleProvincia = computed(() => {
  const nombre = provinciaActiva.value
  if (!nombre || !distribucion.value) return null

  const key = normalizarProvincia(nombre)
  const ugeles = distribucion.value.avance_por_ugel.filter(
    (item) => item.provincia && normalizarProvincia(item.provincia) === key,
  )
  const instituciones = distribucion.value.estudiantes_por_institucion
    .filter((item) => item.provincia && normalizarProvincia(item.provincia) === key)
    .sort((a, b) => b.estudiantes - a.estudiantes)

  const asignaciones = ugeles.reduce((acc, item) => acc + item.asignaciones, 0)
  const completados = ugeles.reduce((acc, item) => acc + item.completados, 0)
  const estudiantes = instituciones.reduce((acc, item) => acc + item.estudiantes, 0)

  // El registro "Sin UGEL asignada" es un contenedor heredado; no debe
  // contarse como una UGEL adicional en el resumen de la provincia.
  const ugelesReales = ugeles.filter((item) => !item.nombre.toLowerCase().startsWith('sin ugel'))

  return {
    nombre,
    ugelLabel: ugelesReales.length === 0
      ? 'Sin UGEL en tu ámbito'
      : ugelesReales.length === 1
        ? ugelesReales[0]?.nombre ?? 'Sin UGEL en tu ámbito'
        : `${ugelesReales.length} UGELs en la provincia`,
    asignaciones,
    completados,
    estudiantes,
    instituciones: instituciones.length,
    avancePct: asignaciones > 0 ? Math.min(100, Math.round((completados / asignaciones) * 100)) : 0,
    topInstituciones: instituciones.slice(0, 5),
  }
})

const mapaTitulo = computed(() => (
  mapaMetrica.value === 'avance' ? 'Mapa de avance por provincia' : 'Mapa de estudiantes por provincia'
))

const mapaSubtitulo = computed(() => (
  mapaMetrica.value === 'avance'
    ? 'Selecciona una provincia para ver el detalle de su avance.'
    : 'Selecciona una provincia para ver sus estudiantes por institución.'
))
</script>

<template>
  <div class="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0f111a] transition-colors font-sans">
    <EduBackground />
    <Navbar title="Dashboard de Métricas" subtitle="Analítica y estadísticas en tiempo real" :show-home="true" />

    <main class="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 md:py-10 space-y-8 md:space-y-12 relative z-10">
      
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
        <BaseButton type="button" variant="primary" size="md" class="group" :disabled="loading || loadingDist" @click="refrescarTodo">
          <template #icon>
            <RefreshCw class="w-4 h-4 group-hover:rotate-180 transition-transform duration-500" :class="{'animate-spin': loading || loadingDist}" />
          </template>
          Actualizar Datos
        </BaseButton>
      </div>

      <!-- Error state -->
      <Transition enter-active-class="transition duration-300 ease-out" enter-from-class="transform -translate-y-4 opacity-0" enter-to-class="transform translate-y-0 opacity-100">
        <div v-if="error" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-2xl p-5 text-red-600 dark:text-red-400 text-sm flex items-center justify-between shadow-lg">
          <span class="flex items-center gap-3 font-medium">
            <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div> 
            {{ error }}
          </span>
          <button @click="fetchMetricas" class="px-4 py-1.5 bg-red-100 dark:bg-red-500/20 rounded-xl font-bold hover:bg-red-200 dark:hover:bg-red-500/30 transition-colors cursor-pointer">
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
          <div class="bg-white dark:bg-slate-900 border border-slate-300/60 dark:border-slate-800 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-300 group overflow-hidden relative cursor-pointer">
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
          <div class="bg-white dark:bg-slate-900 border border-slate-300/60 dark:border-slate-800 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:shadow-blue-500/10 transition-all duration-300 group overflow-hidden relative cursor-pointer">
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
          <div class="bg-white dark:bg-slate-900 border border-slate-300/60 dark:border-slate-800 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:shadow-amber-500/10 transition-all duration-300 group overflow-hidden relative cursor-pointer">
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
          <div class="bg-white dark:bg-slate-900 border border-slate-300/60 dark:border-slate-800 rounded-2xl p-6 shadow-sm hover:shadow-xl hover:shadow-emerald-500/10 transition-all duration-300 group overflow-hidden relative cursor-pointer">
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
              <div class="group cursor-pointer active:scale-95 transition-all">
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
              <div class="group cursor-pointer active:scale-95 transition-all">
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

        <!-- ── Distribución territorial ─────────────────────────────────────── -->
        <section class="space-y-6">
          <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div class="space-y-1">
              <div class="flex items-center gap-2 text-teal-600 dark:text-teal-400 font-bold text-sm tracking-wider uppercase">
                <MapPin class="w-4 h-4" />
                <span>Cobertura territorial</span>
              </div>
              <h2 class="text-2xl md:text-3xl font-black text-slate-800 dark:text-white tracking-tight">
                Distribución SIEVA
              </h2>
              <p class="text-slate-500 dark:text-slate-400 text-sm max-w-2xl">
                Avance de las evaluaciones y estudiantes registrados según el ámbito de gestión.
              </p>
            </div>

            <div
              v-if="distribucion"
              class="inline-flex items-center gap-1 p-1 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-300 dark:border-slate-700 self-start sm:self-auto shrink-0"
            >
              <button
                type="button"
                class="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer"
                :class="vistaDistribucion === 'graficos'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
                @click="vistaDistribucion = 'graficos'"
              >
                <BarChart3 class="w-4 h-4" />
                Gráficos
              </button>
              <button
                type="button"
                class="inline-flex items-center gap-2 px-3 py-2 rounded-lg text-xs font-bold transition-colors cursor-pointer"
                :class="vistaDistribucion === 'mapa'
                  ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
                @click="vistaDistribucion = 'mapa'"
              >
                <MapIcon class="w-4 h-4" />
                Mapa
              </button>
            </div>
          </div>

          <!-- Error distribución -->
          <div v-if="errorDist" class="bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/30 rounded-2xl p-5 text-red-600 dark:text-red-400 text-sm flex items-center justify-between shadow-lg">
            <span class="flex items-center gap-3 font-medium">
              <div class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
              {{ errorDist }}
            </span>
            <button @click="fetchDistribucion" class="px-4 py-1.5 bg-red-100 dark:bg-red-500/20 rounded-xl font-bold hover:bg-red-200 dark:hover:bg-red-500/30 transition-colors cursor-pointer">
              Reintentar
            </button>
          </div>

          <!-- Loading distribución -->
          <div v-else-if="loadingDist && !distribucion" class="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8">
            <div v-for="n in 2" :key="n" class="h-96 rounded-2xl bg-white dark:bg-slate-900 border border-slate-300/60 dark:border-slate-800 animate-pulse"></div>
          </div>

          <div v-else-if="distribucion && vistaDistribucion === 'graficos'" class="grid grid-cols-1 lg:grid-cols-2 gap-6 md:gap-8 items-start">
            <!-- Avance por UGEL / institución -->
            <div class="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm flex flex-col">
              <div class="flex items-start justify-between gap-4 mb-6">
                <div class="flex items-center gap-3 min-w-0">
                  <div class="w-12 h-12 rounded-2xl bg-teal-50 dark:bg-teal-500/10 border border-teal-100 dark:border-teal-500/20 flex items-center justify-center text-teal-600 dark:text-teal-400 shrink-0">
                    <MapPin class="w-6 h-6" />
                  </div>
                  <div class="min-w-0">
                    <h3 class="text-base md:text-lg font-black text-slate-800 dark:text-white leading-tight">{{ avanceTitulo }}</h3>
                    <p class="text-xs font-semibold text-slate-400 leading-snug">{{ avanceSubtitulo }}</p>
                  </div>
                </div>
                <div class="text-right shrink-0">
                  <p class="text-2xl md:text-3xl font-black text-teal-600 dark:text-teal-400 leading-none">{{ avanceGlobalPct }}%</p>
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-wider mt-1">Avance global</p>
                </div>
              </div>

              <AvanceChart v-if="avanceItems.length" :items="avanceItems" class="flex-1" />

              <div v-else class="flex-1 flex flex-col items-center justify-center text-center px-6 py-14">
                <div class="w-16 h-16 bg-slate-50 dark:bg-slate-800/50 rounded-full flex items-center justify-center mb-4">
                  <School class="w-8 h-8 text-slate-200 dark:text-slate-700" />
                </div>
                <p class="text-sm font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Sin asignaciones</p>
                <p class="text-xs text-slate-400 mt-2 max-w-xs">Cuando se asignen evaluaciones en este ámbito, el avance aparecerá aquí.</p>
              </div>

              <div class="grid grid-cols-2 gap-3 mt-6">
                <div class="rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-300 dark:border-slate-700/50 p-3">
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Asignaciones</p>
                  <p class="text-xl font-black text-slate-800 dark:text-white leading-none">{{ distribucion.totales.asignaciones }}</p>
                </div>
                <div class="rounded-xl bg-teal-50/60 dark:bg-teal-500/10 border border-teal-100 dark:border-teal-500/20 p-3">
                  <p class="text-[10px] font-black text-teal-600 dark:text-teal-400 uppercase tracking-wider mb-1">Completadas</p>
                  <p class="text-xl font-black text-teal-600 dark:text-teal-400 leading-none">{{ distribucion.totales.completados }}</p>
                </div>
              </div>
            </div>

            <!-- Estudiantes por institución -->
            <div class="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm flex flex-col">
              <div class="flex items-start justify-between gap-4 mb-6">
                <div class="flex items-center gap-3 min-w-0">
                  <div class="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-100 dark:border-indigo-500/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400 shrink-0">
                    <GraduationCap class="w-6 h-6" />
                  </div>
                  <div class="min-w-0">
                    <h3 class="text-base md:text-lg font-black text-slate-800 dark:text-white leading-tight">Estudiantes por Institución</h3>
                    <p class="text-xs font-semibold text-slate-400 leading-snug">Estudiantes activos registrados en cada IE.</p>
                  </div>
                </div>
                <div class="text-right shrink-0">
                  <p class="text-2xl md:text-3xl font-black text-indigo-600 dark:text-indigo-400 leading-none">{{ distribucion.totales.estudiantes }}</p>
                  <p class="text-[10px] font-black text-slate-400 uppercase tracking-wider mt-1">Estudiantes</p>
                </div>
              </div>

              <EstudiantesTreemap v-if="distribucion.estudiantes_por_institucion.length" :items="distribucion.estudiantes_por_institucion" class="flex-1" />

              <div v-else class="flex-1 flex flex-col items-center justify-center text-center px-6 py-14">
                <div class="w-16 h-16 bg-slate-50 dark:bg-slate-800/50 rounded-full flex items-center justify-center mb-4">
                  <GraduationCap class="w-8 h-8 text-slate-200 dark:text-slate-700" />
                </div>
                <p class="text-sm font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Sin estudiantes</p>
                <p class="text-xs text-slate-400 mt-2 max-w-xs">Aún no hay estudiantes activos registrados en este ámbito.</p>
              </div>

              <div class="mt-6 flex items-center justify-between gap-4 rounded-xl bg-slate-50 dark:bg-slate-800/30 border border-slate-300 dark:border-slate-700/50 px-4 py-3">
                <div class="flex items-center gap-2 text-[11px] font-bold text-slate-500 dark:text-slate-400">
                  <Building2 class="w-4 h-4 text-indigo-500" />
                  {{ institucionesConEstudiantes }} instituciones con estudiantes
                </div>
                <span class="text-[10px] font-black uppercase tracking-wider text-slate-400">Área = estudiantes</span>
              </div>
            </div>
          </div>

          <!-- Vista mapa por provincia -->
          <div v-else-if="distribucion" class="grid grid-cols-1 xl:grid-cols-3 gap-6 md:gap-8 items-start">
            <div class="xl:col-span-2 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm">
              <div class="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-5">
                <div class="flex items-center gap-3 min-w-0">
                  <div class="w-12 h-12 rounded-2xl bg-teal-50 dark:bg-teal-500/10 border border-teal-100 dark:border-teal-500/20 flex items-center justify-center text-teal-600 dark:text-teal-400 shrink-0">
                    <MapIcon class="w-6 h-6" />
                  </div>
                  <div class="min-w-0">
                    <h3 class="text-base md:text-lg font-black text-slate-800 dark:text-white leading-tight">{{ mapaTitulo }}</h3>
                    <p class="text-xs font-semibold text-slate-400 leading-snug">{{ mapaSubtitulo }}</p>
                  </div>
                </div>

                <div class="inline-flex items-center gap-1 p-1 rounded-xl bg-slate-100 dark:bg-slate-800/60 border border-slate-300 dark:border-slate-700 self-start shrink-0">
                  <button
                    type="button"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer"
                    :class="mapaMetrica === 'avance'
                      ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
                    @click="mapaMetrica = 'avance'"
                  >
                    Avance
                  </button>
                  <button
                    type="button"
                    class="px-3 py-1.5 rounded-lg text-xs font-bold transition-colors cursor-pointer"
                    :class="mapaMetrica === 'estudiantes'
                      ? 'bg-white dark:bg-slate-700 text-slate-900 dark:text-white shadow-sm'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'"
                    @click="mapaMetrica = 'estudiantes'"
                  >
                    Estudiantes
                  </button>
                </div>
              </div>

              <MapaProvincias
                :avance="distribucion.avance_por_ugel"
                :estudiantes="distribucion.estudiantes_por_institucion"
                :metrica="mapaMetrica"
                :seleccionada="provinciaActiva"
                @select="provinciaSeleccionada = $event"
              />

              <p class="mt-3 text-[11px] font-semibold text-slate-400 dark:text-slate-500 flex items-center gap-2">
                <MapPin class="w-3.5 h-3.5" />
                Haz clic en una provincia para ver su detalle.
              </p>
            </div>

            <!-- Detalle de la provincia seleccionada -->
            <div class="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl p-6 md:p-8 shadow-sm">
              <template v-if="detalleProvincia">
                <div class="flex items-center gap-3 mb-6">
                  <div class="w-12 h-12 rounded-2xl bg-indigo-50 dark:bg-indigo-500/10 border border-indigo-100 dark:border-indigo-500/20 flex items-center justify-center text-indigo-600 dark:text-indigo-400 shrink-0">
                    <MapPin class="w-6 h-6" />
                  </div>
                  <div class="min-w-0">
                    <h3 class="text-lg font-black text-slate-800 dark:text-white leading-tight truncate">{{ detalleProvincia.nombre }}</h3>
                    <p class="text-xs font-semibold text-slate-400 truncate">{{ detalleProvincia.ugelLabel }}</p>
                  </div>
                </div>

                <div class="rounded-2xl bg-slate-50 dark:bg-slate-800/40 border border-slate-300 dark:border-slate-700/50 p-5 mb-5">
                  <template v-if="mapaMetrica === 'avance'">
                    <div class="flex items-end justify-between gap-3 mb-3">
                      <div>
                        <p class="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Avance de evaluaciones</p>
                        <p class="text-4xl font-black text-teal-600 dark:text-teal-400 leading-none">{{ detalleProvincia.avancePct }}%</p>
                      </div>
                      <p class="text-xs font-bold text-slate-400 shrink-0">{{ detalleProvincia.completados }} / {{ detalleProvincia.asignaciones }}</p>
                    </div>
                    <div class="h-2.5 w-full rounded-full bg-slate-200 dark:bg-slate-700/60 overflow-hidden">
                      <div
                        class="h-full rounded-full bg-gradient-to-r from-teal-400 to-emerald-500 transition-all duration-700"
                        :style="{ width: `${detalleProvincia.avancePct}%` }"
                      ></div>
                    </div>
                  </template>

                  <template v-else>
                    <p class="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Estudiantes registrados</p>
                    <p class="text-4xl font-black text-indigo-600 dark:text-indigo-400 leading-none">{{ detalleProvincia.estudiantes }}</p>
                    <p class="text-xs font-semibold text-slate-400 mt-2">
                      {{ detalleProvincia.instituciones }} instituciones educativas con estudiantes
                    </p>
                  </template>
                </div>

                <div class="grid grid-cols-2 gap-3 mb-6">
                  <div class="rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-300 dark:border-slate-700/50 p-3">
                    <p class="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Asignaciones</p>
                    <p class="text-xl font-black text-slate-800 dark:text-white leading-none">{{ detalleProvincia.asignaciones }}</p>
                  </div>
                  <div class="rounded-xl bg-teal-50/60 dark:bg-teal-500/10 border border-teal-100 dark:border-teal-500/20 p-3">
                    <p class="text-[10px] font-black text-teal-600 dark:text-teal-400 uppercase tracking-wider mb-1">Completadas</p>
                    <p class="text-xl font-black text-teal-600 dark:text-teal-400 leading-none">{{ detalleProvincia.completados }}</p>
                  </div>
                  <div class="rounded-xl bg-indigo-50/60 dark:bg-indigo-500/10 border border-indigo-100 dark:border-indigo-500/20 p-3">
                    <p class="text-[10px] font-black text-indigo-600 dark:text-indigo-400 uppercase tracking-wider mb-1">Estudiantes</p>
                    <p class="text-xl font-black text-indigo-600 dark:text-indigo-400 leading-none">{{ detalleProvincia.estudiantes }}</p>
                  </div>
                  <div class="rounded-xl bg-slate-50 dark:bg-slate-800/40 border border-slate-300 dark:border-slate-700/50 p-3">
                    <p class="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-1">Instituciones</p>
                    <p class="text-xl font-black text-slate-800 dark:text-white leading-none">{{ detalleProvincia.instituciones }}</p>
                  </div>
                </div>

                <div>
                  <h4 class="text-[10px] font-black text-slate-400 uppercase tracking-wider mb-3">Instituciones con más estudiantes</h4>
                  <ul v-if="detalleProvincia.topInstituciones.length" class="space-y-2">
                    <li
                      v-for="ie in detalleProvincia.topInstituciones"
                      :key="ie.id"
                      class="flex items-center justify-between gap-3 rounded-lg px-2 py-1.5 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors"
                    >
                      <span class="text-xs font-bold text-slate-600 dark:text-slate-300 truncate">{{ ie.nombre }}</span>
                      <span class="text-xs font-black text-indigo-600 dark:text-indigo-400 shrink-0">{{ ie.estudiantes }}</span>
                    </li>
                  </ul>
                  <p v-else class="text-xs text-slate-400 dark:text-slate-500">Sin estudiantes registrados en esta provincia.</p>
                </div>
              </template>

              <div v-else class="flex flex-col items-center justify-center text-center px-6 py-20">
                <div class="w-16 h-16 bg-slate-50 dark:bg-slate-800/50 rounded-full flex items-center justify-center mb-4">
                  <MapPin class="w-8 h-8 text-slate-200 dark:text-slate-700" />
                </div>
                <p class="text-sm font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Sin provincia</p>
                <p class="text-xs text-slate-400 mt-2 max-w-xs">Selecciona una provincia en el mapa para ver su detalle.</p>
              </div>
            </div>
          </div>
        </section>

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
