<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import {
  Activity, RefreshCw, Users, GraduationCap, ShieldCheck, AlertTriangle,
  Monitor, Smartphone, Tablet, Loader2, Search, ChevronLeft, ChevronRight,
  Wifi, Building2, Clock, LogOut, BarChart3, Globe, CheckCircle2, XCircle,
  FileSpreadsheet, FileText,
} from 'lucide-vue-next'
import Swal from 'sweetalert2'
import Header from '../../shared/components/Header.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import BaseButton from '../../shared/components/BaseButton.vue'
import { exportToExcel, exportToPdf, type ExportColumn } from '../../shared/utils/exportUtils'
import { monitoreoService, type PaginatedResponse } from '../../shared/services/api'
import type {
  SesionAcceso, ResumenMonitoreo, EstadisticasMonitoreo,
} from '../../shared/types/monitoreo'

type Tab = 'vivo' | 'estadisticas' | 'historico'

const ROL_LABELS: Record<string, string> = {
  especialista_dre_comunicacion: 'Especialista DRE Comunicación',
  especialista_dre_matematica: 'Especialista DRE Matemática',
  responsable_ugel: 'Responsable UGEL',
  director: 'Director',
  auxiliar: 'Auxiliar',
  docente: 'Docente',
  estudiante: 'Estudiante',
}

const COLUMNAS_REPORTE: ExportColumn[] = [
  { header: 'Estado', key: 'estado' },
  { header: 'Usuario', key: 'usuario' },
  { header: 'DNI / Código', key: 'identificador' },
  { header: 'Rol', key: 'rol' },
  { header: 'Institución educativa', key: 'ie' },
  { header: 'UGEL', key: 'ugel' },
  { header: 'IP', key: 'ip' },
  { header: 'Equipo', key: 'equipo' },
  { header: 'Fecha y hora', key: 'fecha' },
  { header: 'Motivo', key: 'motivo' },
]

const tab = ref<Tab>('vivo')
const tabs: { id: Tab; label: string; icon: typeof Wifi }[] = [
  { id: 'vivo', label: 'En vivo', icon: Wifi },
  { id: 'estadisticas', label: 'Estadísticas', icon: BarChart3 },
  { id: 'historico', label: 'Histórico', icon: Clock },
]
const loading = ref(true)
const refreshing = ref(false)
const error = ref('')

const resumen = ref<ResumenMonitoreo | null>(null)
const sesionesActivas = ref<SesionAcceso[]>([])
const estadisticas = ref<EstadisticasMonitoreo | null>(null)
const historico = ref<PaginatedResponse<SesionAcceso> | null>(null)
const cargandoHistorico = ref(false)
const exportando = ref<'pdf' | 'xlsx' | ''>('')

// Filtros de sesiones activas
const buscarActiva = ref('')
const filtroRol = ref('')

// Filtros de histórico
const filtros = ref({
  page: 1,
  size: 20,
  q: '',
  rol: '',
  solo_fallidos: false,
  fecha_desde: '',
  fecha_hasta: '',
})

const rolLabel = (codigo: string | null) => (codigo ? ROL_LABELS[codigo] ?? codigo : '—')

const nombreMostrar = (s: SesionAcceso) => {
  const full = [s.nombres, s.apellidos].filter(Boolean).join(' ').trim()
  return full || s.identificador || 'Desconocido'
}

const formatFecha = (iso: string | null) => {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleString('es-PE', {
    timeZone: 'America/Lima',
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

const tiempoRelativo = (iso: string | null) => {
  if (!iso) return '—'
  const d = new Date(iso).getTime()
  if (Number.isNaN(d)) return '—'
  const seg = Math.max(0, Math.floor((Date.now() - d) / 1000))
  if (seg < 60) return 'hace instantes'
  const min = Math.floor(seg / 60)
  if (min < 60) return `hace ${min} min`
  const h = Math.floor(min / 60)
  const restM = min % 60
  if (h < 24) return restM ? `hace ${h}h ${restM}m` : `hace ${h}h`
  const dias = Math.floor(h / 24)
  return `hace ${dias} d`
}

const formatDuracion = (min: number | null) => {
  if (min === null || min === undefined) return '—'
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  const m = min % 60
  return m ? `${h}h ${m}m` : `${h}h`
}

const deviceIcon = (dispositivo: string | null) => {
  if (dispositivo === 'mobile') return Smartphone
  if (dispositivo === 'tablet') return Tablet
  return Monitor
}

const maxHora = computed(() => {
  const list = estadisticas.value?.accesos_por_hora ?? []
  return Math.max(1, ...list.map(p => p.total))
})

const maxDia = computed(() => {
  const list = estadisticas.value?.accesos_por_dia ?? []
  return Math.max(1, ...list.map(p => p.total))
})

const maxConteo = (items: { total: number }[]) => Math.max(1, ...items.map(i => i.total))

const ultimaActualizacion = computed(() => resumen.value?.ultima_actualizacion ?? null)

async function cargarResumen() {
  resumen.value = await monitoreoService.getResumen()
}

async function cargarActivas() {
  sesionesActivas.value = await monitoreoService.getSesionesActivas({
    q: buscarActiva.value || undefined,
    rol: filtroRol.value || undefined,
  })
}

async function cargarEstadisticas() {
  estadisticas.value = await monitoreoService.getEstadisticas()
}

async function cargarHistorico() {
  cargandoHistorico.value = true
  try {
    historico.value = await monitoreoService.getSesiones({
      page: filtros.value.page,
      size: filtros.value.size,
      q: filtros.value.q || undefined,
      rol: filtros.value.rol || undefined,
      solo_fallidos: filtros.value.solo_fallidos || undefined,
      fecha_desde: filtros.value.fecha_desde || undefined,
      fecha_hasta: filtros.value.fecha_hasta || undefined,
    })
  } finally {
    cargandoHistorico.value = false
  }
}

async function cargarTodo() {
  loading.value = true
  error.value = ''
  try {
    await Promise.all([cargarResumen(), cargarActivas(), cargarEstadisticas()])
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'No se pudo cargar la información de monitoreo'
  } finally {
    loading.value = false
  }
}

async function refrescar() {
  refreshing.value = true
  try {
    const tareas: Promise<unknown>[] = [cargarResumen(), cargarActivas(), cargarEstadisticas()]
    if (tab.value === 'historico') tareas.push(cargarHistorico())
    await Promise.all(tareas)
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al actualizar'
  } finally {
    refreshing.value = false
  }
}

async function cerrarSesion(s: SesionAcceso) {
  const result = await Swal.fire({
    title: '¿Cerrar esta sesión?',
    text: `${nombreMostrar(s)} (${s.identificador ?? '—'}) quedará desconectado.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonText: 'Cerrar sesión',
    cancelButtonText: 'Cancelar',
    customClass: {
      popup: 'rounded-2xl',
      confirmButton: 'rounded-xl font-bold',
      cancelButton: 'rounded-xl font-bold',
    },
  })
  if (!result.isConfirmed) return
  try {
    await monitoreoService.cerrarSesion(s.id)
    await Promise.all([cargarActivas(), cargarResumen()])
  } catch (e: any) {
    Swal.fire({
      icon: 'error',
      title: 'No se pudo cerrar',
      text: e.response?.data?.detail ?? 'Intenta nuevamente',
      customClass: { popup: 'rounded-2xl', confirmButton: 'rounded-xl font-bold' },
    })
  }
}

function aplicarFiltros() {
  filtros.value.page = 1
  void cargarHistorico()
}

const descripcionFiltros = computed(() => {
  const partes = [
    `Rol: ${filtros.value.rol ? rolLabel(filtros.value.rol) : 'Todos'}`,
  ]
  if (filtros.value.q) partes.push(`Búsqueda: ${filtros.value.q}`)
  if (filtros.value.solo_fallidos) partes.push('Solo intentos fallidos')
  partes.push(`Desde: ${filtros.value.fecha_desde || 'sin límite'}`)
  partes.push(`Hasta: ${filtros.value.fecha_hasta || 'hoy'}`)
  return partes.join('  ·  ')
})

function filaReporte(s: SesionAcceso) {
  return {
    estado: s.exito ? 'Correcto' : 'Fallido',
    usuario: nombreMostrar(s),
    identificador: s.identificador ?? '—',
    rol: rolLabel(s.rol_codigo),
    ie: s.institucion_nombre ?? '—',
    ugel: s.ugel_nombre ?? '—',
    ip: s.ip ?? '—',
    equipo: [s.sistema_operativo, s.navegador].filter(Boolean).join(' · ') || '—',
    fecha: formatFecha(s.login_at),
    motivo: s.motivo ?? (s.exito ? '—' : 'credenciales'),
  }
}

async function exportarReporte(formato: 'pdf' | 'xlsx') {
  exportando.value = formato
  try {
    const sesiones = await monitoreoService.getReporte({
      q: filtros.value.q || undefined,
      rol: filtros.value.rol || undefined,
      solo_fallidos: filtros.value.solo_fallidos || undefined,
      fecha_desde: filtros.value.fecha_desde || undefined,
      fecha_hasta: filtros.value.fecha_hasta || undefined,
    })

    if (sesiones.length === 0) {
      await Swal.fire({
        icon: 'info',
        title: 'Sin registros',
        text: 'No hay inicios de sesión que coincidan con los filtros seleccionados.',
        customClass: { popup: 'rounded-2xl', confirmButton: 'rounded-xl font-bold' },
      })
      return
    }

    const rows = sesiones.map(filaReporte)
    const stamp = new Date().toISOString().split('T')[0]
    const subtitulo = `${descripcionFiltros.value}  ·  Total: ${rows.length} registros`

    if (formato === 'pdf') {
      exportToPdf({
        title: 'Reporte de inicios de sesión',
        subtitle: subtitulo,
        columns: COLUMNAS_REPORTE,
        rows,
        filename: `reporte_inicios_sesion_${stamp}.pdf`,
        accent: [225, 29, 72],
      })
    } else {
      exportToExcel(
        COLUMNAS_REPORTE,
        rows,
        `reporte_inicios_sesion_${stamp}.xlsx`,
        'Inicios de sesión',
      )
    }
  } catch (e: any) {
    await Swal.fire({
      icon: 'error',
      title: 'No se pudo generar el reporte',
      text: e.response?.data?.detail ?? 'Intenta nuevamente',
      customClass: { popup: 'rounded-2xl', confirmButton: 'rounded-xl font-bold' },
    })
  } finally {
    exportando.value = ''
  }
}

function cambiarPagina(delta: number) {
  if (!historico.value) return
  const nueva = filtros.value.page + delta
  if (nueva < 1 || nueva > historico.value.pages) return
  filtros.value.page = nueva
  void cargarHistorico()
}

watch(tab, (nuevo) => {
  if (nuevo === 'historico' && !historico.value) void cargarHistorico()
})

onMounted(cargarTodo)
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans relative flex flex-col overflow-x-hidden">
    <EduBackground variant="indigo" />
    <Header title="Monitoreo" subtitle="Sesiones activas y estadísticas de acceso" :show-home="true" />

    <main class="max-w-6xl mx-auto w-full relative z-10 flex-1 flex flex-col p-4 sm:p-8">

      <!-- Barra superior -->
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div class="flex items-center gap-3">
          <div class="w-11 h-11 rounded-xl bg-gradient-to-br from-rose-500 to-red-600 flex items-center justify-center shadow-lg shadow-rose-500/20">
            <Activity class="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 class="text-lg font-black text-slate-800 dark:text-white tracking-tight uppercase leading-none">Panel de Monitoreo</h2>
            <p class="text-[11px] text-slate-400 dark:text-slate-500 font-semibold mt-1 flex items-center gap-1.5">
              <Clock class="w-3 h-3" />
              Actualizado: {{ formatFecha(ultimaActualizacion) }}
            </p>
          </div>
        </div>
        <BaseButton variant="primary" size="md" :loading="refreshing" @click="refrescar">
          <template #icon><RefreshCw class="w-4 h-4" /></template>
          Actualizar
        </BaseButton>
      </div>

      <!-- Error -->
      <div v-if="error" class="mb-6 flex items-start gap-3 bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800/50 rounded-2xl p-4">
        <AlertTriangle class="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
        <p class="text-sm font-semibold text-red-700 dark:text-red-300">{{ error }}</p>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="flex-1 flex flex-col items-center justify-center py-20">
        <Loader2 class="w-12 h-12 animate-spin text-rose-500 mb-4" />
        <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Cargando monitoreo...</p>
      </div>

      <template v-else>
        <!-- KPIs -->
        <div class="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4 mb-6">
          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-4 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">En línea</span>
              <Wifi class="w-4 h-4 text-emerald-500" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none">{{ resumen?.sesiones_activas ?? 0 }}</p>
            <p class="text-[10px] text-slate-400 font-semibold mt-1">últimos 15 min</p>
          </div>
          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-4 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Estudiantes</span>
              <GraduationCap class="w-4 h-4 text-indigo-500" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none">{{ resumen?.estudiantes_activos ?? 0 }}</p>
            <p class="text-[10px] text-slate-400 font-semibold mt-1">activos ahora</p>
          </div>
          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-4 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Staff</span>
              <ShieldCheck class="w-4 h-4 text-teal-500" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none">{{ resumen?.staff_activos ?? 0 }}</p>
            <p class="text-[10px] text-slate-400 font-semibold mt-1">docentes y gestores</p>
          </div>
          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-4 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Ingresos hoy</span>
              <Users class="w-4 h-4 text-violet-500" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none">{{ resumen?.logins_hoy ?? 0 }}</p>
            <p class="text-[10px] text-slate-400 font-semibold mt-1">{{ resumen?.sesiones_hoy ?? 0 }} intentos totales</p>
          </div>
          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-4 shadow-sm">
            <div class="flex items-center justify-between mb-2">
              <span class="text-[10px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest">Fallidos hoy</span>
              <AlertTriangle class="w-4 h-4 text-red-500" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white leading-none">{{ resumen?.fallidos_hoy ?? 0 }}</p>
            <p class="text-[10px] text-slate-400 font-semibold mt-1">credenciales incorrectas</p>
          </div>
        </div>

        <!-- Tabs -->
        <div class="flex items-center gap-1.5 mb-5 bg-white dark:bg-slate-800 p-1.5 rounded-2xl border-2 border-slate-200 dark:border-slate-700 w-fit">
          <button
            v-for="t in tabs"
            :key="t.id"
            class="flex items-center gap-1.5 px-4 py-2 rounded-xl text-[11px] font-black uppercase tracking-widest transition-all"
            :class="tab === t.id
              ? 'bg-gradient-to-r from-rose-500 to-red-600 text-white shadow-lg shadow-rose-500/20'
              : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700'"
            @click="tab = t.id"
          >
            <component :is="t.icon" class="w-3.5 h-3.5" />
            <span class="hidden sm:inline">{{ t.label }}</span>
          </button>
        </div>

        <!-- ── TAB EN VIVO ─────────────────────────────────────────────────── -->
        <section v-if="tab === 'vivo'" class="flex-1">
          <div class="flex flex-col sm:flex-row gap-3 mb-4">
            <div class="relative flex-1">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                v-model="buscarActiva"
                type="text"
                placeholder="Buscar por nombre, DNI o código..."
                class="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200 font-semibold focus:outline-none focus:border-rose-400 dark:focus:border-rose-500 transition-colors"
                @keyup.enter="cargarActivas"
              />
            </div>
            <select
              v-model="filtroRol"
              class="px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-sm text-slate-700 dark:text-slate-200 font-semibold focus:outline-none focus:border-rose-400"
              @change="cargarActivas"
            >
              <option value="">Todos los roles</option>
              <option v-for="(label, code) in ROL_LABELS" :key="code" :value="code">{{ label }}</option>
            </select>
            <BaseButton variant="secondary" size="md" @click="cargarActivas">
              <template #icon><Search class="w-4 h-4" /></template>
              Filtrar
            </BaseButton>
          </div>

          <div v-if="sesionesActivas.length === 0" class="flex flex-col items-center justify-center py-16 bg-white dark:bg-slate-800 rounded-2xl border-2 border-dashed border-slate-200 dark:border-slate-700">
            <Wifi class="w-10 h-10 text-slate-300 dark:text-slate-600 mb-3" />
            <p class="text-sm font-bold text-slate-500 dark:text-slate-400">No hay sesiones activas</p>
            <p class="text-[11px] text-slate-400 dark:text-slate-500 mt-1">Los usuarios aparecerán aquí al iniciar sesión</p>
          </div>

          <div v-else class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm">
            <!-- Desktop -->
            <div class="hidden lg:block overflow-x-auto">
              <table class="w-full text-left">
                <thead>
                  <tr class="border-b-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/40">
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Usuario</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Rol</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">IE / UGEL</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">IP</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Dispositivo</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Última actividad</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Duración</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest text-right">Acción</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="s in sesionesActivas"
                    :key="s.id"
                    class="border-b border-slate-100 dark:border-slate-700/60 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors"
                  >
                    <td class="px-4 py-3">
                      <div class="flex items-center gap-2.5">
                        <span class="w-2 h-2 rounded-full bg-emerald-500 shrink-0 animate-pulse"></span>
                        <div class="min-w-0">
                          <p class="text-sm font-bold text-slate-700 dark:text-slate-200 truncate">{{ nombreMostrar(s) }}</p>
                          <p class="text-[11px] text-slate-400 dark:text-slate-500 font-semibold">{{ s.identificador ?? '—' }}</p>
                        </div>
                      </div>
                    </td>
                    <td class="px-4 py-3">
                      <span class="inline-block text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-600">
                        {{ rolLabel(s.rol_codigo) }}
                      </span>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-xs font-semibold text-slate-600 dark:text-slate-300 truncate max-w-[180px]">{{ s.institucion_nombre ?? '—' }}</p>
                      <p class="text-[10px] text-slate-400 truncate max-w-[180px]">{{ s.ugel_nombre ?? '—' }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <span class="text-xs font-mono font-semibold text-slate-600 dark:text-slate-300">{{ s.ip ?? '—' }}</span>
                    </td>
                    <td class="px-4 py-3">
                      <div class="flex items-center gap-1.5">
                        <component :is="deviceIcon(s.dispositivo)" class="w-4 h-4 text-slate-400 shrink-0" />
                        <div class="min-w-0">
                          <p class="text-xs font-semibold text-slate-600 dark:text-slate-300">{{ s.sistema_operativo ?? '—' }}</p>
                          <p class="text-[10px] text-slate-400">{{ s.navegador ?? '—' }}</p>
                        </div>
                      </div>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-xs font-semibold text-slate-600 dark:text-slate-300">{{ tiempoRelativo(s.last_activity) }}</p>
                      <p class="text-[10px] text-slate-400">Ingresó {{ formatFecha(s.login_at) }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <span class="text-xs font-semibold text-slate-600 dark:text-slate-300">{{ formatDuracion(s.duracion_minutos) }}</span>
                    </td>
                    <td class="px-4 py-3 text-right">
                      <button
                        class="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-[10px] font-bold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
                        @click="cerrarSesion(s)"
                      >
                        <LogOut class="w-3 h-3" />
                        Cerrar
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Mobile -->
            <div class="lg:hidden divide-y divide-slate-100 dark:divide-slate-700/60">
              <div v-for="s in sesionesActivas" :key="s.id" class="p-4">
                <div class="flex items-start justify-between gap-3 mb-3">
                  <div class="flex items-center gap-2.5 min-w-0">
                    <span class="w-2 h-2 rounded-full bg-emerald-500 shrink-0 animate-pulse"></span>
                    <div class="min-w-0">
                      <p class="text-sm font-bold text-slate-700 dark:text-slate-200 truncate">{{ nombreMostrar(s) }}</p>
                      <p class="text-[11px] text-slate-400 font-semibold">{{ s.identificador ?? '—' }} · {{ rolLabel(s.rol_codigo) }}</p>
                    </div>
                  </div>
                  <button class="text-red-500 shrink-0 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20" @click="cerrarSesion(s)">
                    <LogOut class="w-4 h-4" />
                  </button>
                </div>
                <div class="grid grid-cols-2 gap-y-2 gap-x-4 text-[11px]">
                  <div class="flex items-center gap-1.5 text-slate-500 dark:text-slate-400"><Globe class="w-3 h-3" />{{ s.ip ?? '—' }}</div>
                  <div class="flex items-center gap-1.5 text-slate-500 dark:text-slate-400"><component :is="deviceIcon(s.dispositivo)" class="w-3 h-3" />{{ s.sistema_operativo ?? '—' }}</div>
                  <div class="flex items-center gap-1.5 text-slate-500 dark:text-slate-400"><Building2 class="w-3 h-3" /><span class="truncate">{{ s.institucion_nombre ?? '—' }}</span></div>
                  <div class="flex items-center gap-1.5 text-slate-500 dark:text-slate-400"><Clock class="w-3 h-3" />{{ tiempoRelativo(s.last_activity) }}</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ── TAB ESTADÍSTICAS ─────────────────────────────────────────────── -->
        <section v-else-if="tab === 'estadisticas'" class="flex-1 space-y-6">
          <!-- Accesos por hora -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-5 shadow-sm">
            <div class="flex items-center gap-2 mb-5">
              <BarChart3 class="w-4 h-4 text-rose-500" />
              <h3 class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Accesos por hora (últimas 24h)</h3>
            </div>
            <div v-if="!estadisticas?.accesos_por_hora.length" class="text-center text-xs font-semibold text-slate-400 py-6">Sin datos en las últimas 24 horas</div>
            <div v-else class="flex items-end gap-1 h-40 overflow-x-auto pb-1">
              <div v-for="p in estadisticas.accesos_por_hora" :key="p.periodo" class="flex flex-col items-center gap-1 flex-1 min-w-[26px]">
                <span class="text-[9px] font-bold text-slate-400">{{ p.total }}</span>
                <div class="w-full flex flex-col justify-end rounded-t-md overflow-hidden" :style="{ height: `${(p.total / maxHora) * 100}%`, minHeight: '4px' }">
                  <div class="w-full bg-gradient-to-t from-rose-500 to-red-400" :style="{ flex: p.exitos }"></div>
                  <div v-if="p.fallidos" class="w-full bg-amber-400" :style="{ flex: p.fallidos }"></div>
                </div>
                <span class="text-[9px] font-semibold text-slate-400 whitespace-nowrap">{{ p.periodo }}</span>
              </div>
            </div>
            <div class="flex items-center gap-4 mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
              <span class="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 dark:text-slate-400"><span class="w-2.5 h-2.5 rounded bg-gradient-to-t from-rose-500 to-red-400"></span>Exitosos</span>
              <span class="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 dark:text-slate-400"><span class="w-2.5 h-2.5 rounded bg-amber-400"></span>Fallidos</span>
            </div>
          </div>

          <div class="grid lg:grid-cols-2 gap-6">
            <!-- Accesos por día -->
            <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-5 shadow-sm">
              <div class="flex items-center gap-2 mb-5">
                <Clock class="w-4 h-4 text-indigo-500" />
                <h3 class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Accesos por día (14 días)</h3>
              </div>
              <div v-if="!estadisticas?.accesos_por_dia.length" class="text-center text-xs font-semibold text-slate-400 py-6">Sin datos</div>
              <div v-else class="flex items-end gap-2 h-32">
                <div v-for="p in estadisticas.accesos_por_dia" :key="p.periodo" class="flex flex-col items-center gap-1 flex-1" :title="`${p.periodo}: ${p.total}`">
                  <span class="text-[9px] font-bold text-slate-400">{{ p.total }}</span>
                  <div class="w-full rounded-t-md bg-gradient-to-t from-indigo-500 to-violet-400" :style="{ height: `${(p.total / maxDia) * 100}%`, minHeight: '4px' }"></div>
                  <span class="text-[9px] font-semibold text-slate-400">{{ p.periodo.slice(8) }}</span>
                </div>
              </div>
            </div>

            <!-- Distribuciones -->
            <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-5 shadow-sm space-y-5">
              <div>
                <h3 class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-3">Dispositivos</h3>
                <div v-if="!estadisticas?.dispositivos.length" class="text-[11px] text-slate-400 font-semibold">Sin datos</div>
                <div v-for="d in estadisticas?.dispositivos ?? []" :key="d.clave" class="mb-2">
                  <div class="flex items-center justify-between text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                    <span class="capitalize">{{ d.clave }}</span><span>{{ d.total }}</span>
                  </div>
                  <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                    <div class="h-full rounded-full bg-gradient-to-r from-rose-500 to-red-500" :style="{ width: `${(d.total / maxConteo(estadisticas?.dispositivos ?? [])) * 100}%` }"></div>
                  </div>
                </div>
              </div>
              <div>
                <h3 class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-3">Sistemas operativos</h3>
                <div v-for="d in estadisticas?.sistemas_operativos ?? []" :key="d.clave" class="mb-2">
                  <div class="flex items-center justify-between text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                    <span>{{ d.clave }}</span><span>{{ d.total }}</span>
                  </div>
                  <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                    <div class="h-full rounded-full bg-gradient-to-r from-teal-500 to-emerald-500" :style="{ width: `${(d.total / maxConteo(estadisticas?.sistemas_operativos ?? [])) * 100}%` }"></div>
                  </div>
                </div>
              </div>
              <div>
                <h3 class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-3">Navegadores</h3>
                <div v-for="d in estadisticas?.navegadores ?? []" :key="d.clave" class="mb-2">
                  <div class="flex items-center justify-between text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                    <span>{{ d.clave }}</span><span>{{ d.total }}</span>
                  </div>
                  <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                    <div class="h-full rounded-full bg-gradient-to-r from-indigo-500 to-violet-500" :style="{ width: `${(d.total / maxConteo(estadisticas?.navegadores ?? [])) * 100}%` }"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Top instituciones -->
          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-5 shadow-sm">
            <div class="flex items-center gap-2 mb-4">
              <Building2 class="w-4 h-4 text-violet-500" />
              <h3 class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest">Instituciones con más accesos (30 días)</h3>
            </div>
            <div v-if="!estadisticas?.top_instituciones.length" class="text-center text-xs font-semibold text-slate-400 py-4">Sin datos</div>
            <div class="grid sm:grid-cols-2 gap-3">
              <div v-for="(ie, i) in estadisticas?.top_instituciones ?? []" :key="ie.clave" class="flex items-center gap-3 bg-slate-50 dark:bg-slate-900/40 rounded-xl p-3 border border-slate-200 dark:border-slate-700">
                <span class="w-6 h-6 rounded-lg bg-gradient-to-br from-violet-400 to-purple-500 text-white text-[10px] font-black flex items-center justify-center shrink-0">{{ i + 1 }}</span>
                <p class="flex-1 text-xs font-bold text-slate-600 dark:text-slate-300 truncate">{{ ie.clave }}</p>
                <span class="text-xs font-black text-violet-600 dark:text-violet-400 shrink-0">{{ ie.total }}</span>
              </div>
            </div>
          </div>

          <!-- Activos por rol / UGEL -->
          <div class="grid lg:grid-cols-2 gap-6">
            <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-5 shadow-sm">
              <h3 class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-4">Sesiones activas por rol</h3>
              <div v-if="!resumen?.activos_por_rol.length" class="text-[11px] text-slate-400 font-semibold">Sin sesiones activas</div>
              <div v-for="r in resumen?.activos_por_rol ?? []" :key="r.clave" class="mb-2">
                <div class="flex items-center justify-between text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                  <span>{{ rolLabel(r.clave) }}</span><span>{{ r.total }}</span>
                </div>
                <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                  <div class="h-full rounded-full bg-gradient-to-r from-emerald-500 to-teal-500" :style="{ width: `${(r.total / maxConteo(resumen?.activos_por_rol ?? [])) * 100}%` }"></div>
                </div>
              </div>
            </div>
            <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-5 shadow-sm">
              <h3 class="text-xs font-black text-slate-500 dark:text-slate-400 uppercase tracking-widest mb-4">Sesiones activas por UGEL</h3>
              <div v-if="!resumen?.activos_por_ugel.length" class="text-[11px] text-slate-400 font-semibold">Sin sesiones activas</div>
              <div v-for="r in resumen?.activos_por_ugel ?? []" :key="r.clave" class="mb-2">
                <div class="flex items-center justify-between text-[11px] font-bold text-slate-600 dark:text-slate-300 mb-1">
                  <span class="truncate">{{ r.clave }}</span><span>{{ r.total }}</span>
                </div>
                <div class="h-2 rounded-full bg-slate-100 dark:bg-slate-700 overflow-hidden">
                  <div class="h-full rounded-full bg-gradient-to-r from-rose-500 to-red-500" :style="{ width: `${(r.total / maxConteo(resumen?.activos_por_ugel ?? [])) * 100}%` }"></div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <!-- ── TAB HISTÓRICO ────────────────────────────────────────────────── -->
        <section v-else class="flex-1">
          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 p-4 sm:p-5 shadow-sm mb-4">
            <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
              <div class="relative lg:col-span-2">
                <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input v-model="filtros.q" type="text" placeholder="Buscar por nombre, DNI o código..."
                  class="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-700 dark:text-slate-200 font-semibold focus:outline-none focus:border-rose-400"
                  @keyup.enter="aplicarFiltros" />
              </div>
              <select v-model="filtros.rol" class="px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm text-slate-700 dark:text-slate-200 font-semibold focus:outline-none focus:border-rose-400">
                <option value="">Todos los roles</option>
                <option v-for="(label, code) in ROL_LABELS" :key="code" :value="code">{{ label }}</option>
              </select>
              <label class="flex items-center gap-2 px-4 py-3 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 cursor-pointer">
                <input v-model="filtros.solo_fallidos" type="checkbox" class="w-4 h-4 accent-red-500 rounded" />
                <span class="text-xs font-bold text-slate-600 dark:text-slate-300">Solo fallidos</span>
              </label>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Desde</label>
                <input v-model="filtros.fecha_desde" type="date" class="w-full px-3 py-2.5 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm font-semibold text-slate-700 dark:text-slate-200 focus:outline-none focus:border-rose-400" />
              </div>
              <div>
                <label class="block text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">Hasta</label>
                <input v-model="filtros.fecha_hasta" type="date" class="w-full px-3 py-2.5 rounded-xl border-2 border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-sm font-semibold text-slate-700 dark:text-slate-200 focus:outline-none focus:border-rose-400" />
              </div>
              <div class="flex items-end">
                <BaseButton variant="primary" size="md" block @click="aplicarFiltros">
                  <template #icon><Search class="w-4 h-4" /></template>
                  Buscar
                </BaseButton>
              </div>
            </div>

            <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
              <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 flex items-center gap-1.5">
                <FileText class="w-3.5 h-3.5" />
                El reporte incluye todos los intentos (correctos y fallidos) que coincidan con los filtros, no solo esta página.
              </p>
              <div class="flex items-center gap-2 shrink-0">
                <BaseButton
                  variant="secondary"
                  size="sm"
                  :disabled="!!exportando"
                  :loading="exportando === 'xlsx'"
                  @click="exportarReporte('xlsx')"
                >
                  <template #icon><FileSpreadsheet class="w-3.5 h-3.5 text-emerald-500" /></template>
                  Excel
                </BaseButton>
                <BaseButton
                  variant="secondary"
                  size="sm"
                  :disabled="!!exportando"
                  :loading="exportando === 'pdf'"
                  @click="exportarReporte('pdf')"
                >
                  <template #icon><FileText class="w-3.5 h-3.5 text-rose-500" /></template>
                  PDF
                </BaseButton>
              </div>
            </div>
          </div>

          <div class="bg-white dark:bg-slate-800 rounded-2xl border-2 border-slate-200 dark:border-slate-700 overflow-hidden shadow-sm relative">
            <div v-if="cargandoHistorico" class="absolute inset-0 z-10 flex items-center justify-center bg-white/70 dark:bg-slate-800/70">
              <Loader2 class="w-8 h-8 animate-spin text-rose-500" />
            </div>

            <div v-if="!historico || historico.items.length === 0" class="flex flex-col items-center justify-center py-16">
              <Clock class="w-10 h-10 text-slate-300 dark:text-slate-600 mb-3" />
              <p class="text-sm font-bold text-slate-500 dark:text-slate-400">Sin registros</p>
            </div>

            <div v-else class="overflow-x-auto">
              <table class="w-full text-left">
                <thead>
                  <tr class="border-b-2 border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900/40">
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Estado</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Usuario</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Rol</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">IP</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Equipo</th>
                    <th class="px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">Fecha y hora</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="s in historico.items" :key="s.id" class="border-b border-slate-100 dark:border-slate-700/60 hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
                    <td class="px-4 py-3">
                      <span v-if="s.exito" class="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 class="w-3.5 h-3.5" /> Correcto
                      </span>
                      <span v-else class="inline-flex items-center gap-1 text-[10px] font-bold text-red-600 dark:text-red-400">
                        <XCircle class="w-3.5 h-3.5" /> Fallido
                      </span>
                    </td>
                    <td class="px-4 py-3">
                      <p class="text-xs font-bold text-slate-700 dark:text-slate-200">{{ nombreMostrar(s) }}</p>
                      <p class="text-[10px] text-slate-400 font-semibold">{{ s.identificador ?? '—' }}</p>
                    </td>
                    <td class="px-4 py-3">
                      <span class="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300">{{ rolLabel(s.rol_codigo) }}</span>
                    </td>
                    <td class="px-4 py-3"><span class="text-xs font-mono font-semibold text-slate-600 dark:text-slate-300">{{ s.ip ?? '—' }}</span></td>
                    <td class="px-4 py-3">
                      <p class="text-xs font-semibold text-slate-600 dark:text-slate-300">{{ s.sistema_operativo ?? '—' }}</p>
                      <p class="text-[10px] text-slate-400">{{ s.navegador ?? '—' }}</p>
                    </td>
                    <td class="px-4 py-3"><span class="text-xs font-semibold text-slate-600 dark:text-slate-300">{{ formatFecha(s.login_at) }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Paginación -->
            <div v-if="historico && historico.total > 0" class="flex items-center justify-between px-4 py-3 border-t-2 border-slate-100 dark:border-slate-700">
              <p class="text-[11px] font-bold text-slate-400">{{ historico.total }} registros · página {{ historico.page }} de {{ historico.pages }}</p>
              <div class="flex items-center gap-2">
                <button
                  class="p-2 rounded-xl border-2 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  :disabled="filtros.page <= 1"
                  @click="cambiarPagina(-1)"
                >
                  <ChevronLeft class="w-4 h-4" />
                </button>
                <button
                  class="p-2 rounded-xl border-2 border-slate-200 dark:border-slate-700 text-slate-500 dark:text-slate-400 disabled:opacity-40 hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
                  :disabled="!historico || filtros.page >= historico.pages"
                  @click="cambiarPagina(1)"
                >
                  <ChevronRight class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>
