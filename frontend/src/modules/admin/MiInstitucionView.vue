<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, onMounted } from 'vue'
import { organizacionService } from '../../shared/services/api'
import type { InstitucionEducativa } from '../../shared/types'
import Navbar from '../../shared/components/Navbar.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import { Building2, Loader2, MapPin, GraduationCap, BookOpen, Calculator, ClipboardList, CheckCircle2, Users } from 'lucide-vue-next'
const institucion = ref<InstitucionEducativa | null>(null)
const analytics = ref<{
  total_estudiantes: number
  total_docentes: number
  total_examenes_lectura: number
  total_examenes_matematica: number
  total_examenes: number
  total_asignaciones: number
  total_completados: number
  recientes: Array<{ id: number; titulo: string; grado: string; area: string; fecha: string | null; docente: string }>
} | null>(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    institucion.value = await organizacionService.getMiInstitucion()
    if (institucion.value?.id) {
      analytics.value = await organizacionService.getIEAnalytics(institucion.value.id)
    }
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar datos'
  } finally {
    loading.value = false
  }
})

const nivelLabel: Record<string, string> = { inicial: 'Inicial', primaria: 'Primaria', secundaria: 'Secundaria' }
const nivelColor: Record<string, string> = {
  inicial: 'from-amber-500 to-orange-500',
  primaria: 'from-teal-500 to-emerald-600',
  secundaria: 'from-violet-500 to-purple-600',
}

// formatFecha importado de shared/utils/dateUtils

const completadosPct = () => {
  if (!analytics.value || !analytics.value.total_asignaciones) return 0
  return Math.round((analytics.value.total_completados / analytics.value.total_asignaciones) * 100)
}
</script>

<template>
  <EduBackground />
  <Navbar title="Mi Institución" :show-home="true" />

  <main class="max-w-3xl mx-auto px-4 py-8 relative z-10">
    <div v-if="loading" class="flex justify-center py-16">
      <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
    </div>

    <div v-else-if="error" class="text-center py-16 text-red-500">{{ error }}</div>

    <div v-else-if="institucion" class="space-y-5">
      <!-- Cabecera -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-6 shadow-sm">
        <div class="flex items-start gap-4">
          <div :class="`bg-gradient-to-br ${nivelColor[(Array.isArray(institucion.nivel_educativo) ? (institucion.nivel_educativo[0] ?? '') : institucion.nivel_educativo)] || 'from-teal-500 to-emerald-600'}`"
            class="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0">
            <Building2 class="w-7 h-7 text-white" />
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-bold text-slate-800 dark:text-white leading-tight">{{ institucion.nombre }}</h2>
            <div class="flex items-center gap-3 mt-1.5 flex-wrap">
              <span class="font-mono text-xs text-slate-500 dark:text-slate-400">{{ institucion.codigo_modular }}</span>
              <span v-for="niv in (Array.isArray(institucion.nivel_educativo) ? institucion.nivel_educativo : [institucion.nivel_educativo])"
                :key="niv"
                :class="`bg-gradient-to-r ${nivelColor[niv] || 'from-teal-500 to-emerald-600'} text-white`"
                class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold">
                <GraduationCap class="w-3 h-3" />
                {{ nivelLabel[niv] ?? niv }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Detalles -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-6 shadow-sm space-y-4">
        <h3 class="text-xs uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider">Información</h3>
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <p class="text-[10px] font-semibold text-slate-400 mb-0.5">UGEL</p>
            <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ institucion.ugel_nombre || '—' }}</p>
          </div>
          <div v-if="institucion.distrito_nombre">
            <p class="text-[10px] font-semibold text-slate-400 mb-0.5">Distrito</p>
            <p class="text-sm font-medium text-slate-700 dark:text-slate-200 flex items-center gap-1">
              <MapPin class="w-3.5 h-3.5 text-teal-500" /> {{ institucion.distrito_nombre }}
            </p>
          </div>
          <div v-if="institucion.direccion" class="sm:col-span-2">
            <p class="text-[10px] font-semibold text-slate-400 mb-0.5">Dirección</p>
            <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ institucion.direccion }}</p>
          </div>
          <div>
            <p class="text-[10px] font-semibold text-slate-400 mb-0.5">Estado</p>
            <span :class="institucion.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-slate-100 text-slate-500 dark:bg-slate-700 dark:text-slate-400'"
              class="inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold">
              {{ institucion.is_active ? 'Activa' : 'Inactiva' }}
            </span>
          </div>
        </div>
      </div>

      <!-- Analytics -->
      <div v-if="analytics" class="space-y-4">
        <h3 class="text-xs uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider px-1">Actividad</h3>

        <!-- Stats cards -->
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-4 shadow-sm">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center mb-2">
              <Users class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ analytics.total_estudiantes }}</p>
            <p class="text-[11px] text-slate-400 mt-0.5">Estudiantes</p>
          </div>
          <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-4 shadow-sm">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-400 to-purple-500 flex items-center justify-center mb-2">
              <GraduationCap class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ analytics.total_docentes }}</p>
            <p class="text-[11px] text-slate-400 mt-0.5">Docentes</p>
          </div>
          <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-4 shadow-sm">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-violet-400 to-emerald-500 flex items-center justify-center mb-2">
              <ClipboardList class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ analytics.total_asignaciones }}</p>
            <p class="text-[11px] text-slate-400 mt-0.5">Asignaciones</p>
          </div>
          <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-4 shadow-sm">
            <div class="w-8 h-8 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center mb-2">
              <CheckCircle2 class="w-4 h-4 text-white" />
            </div>
            <p class="text-2xl font-black text-slate-800 dark:text-white">{{ completadosPct() }}%</p>
            <p class="text-[11px] text-slate-400 mt-0.5">Completados</p>
          </div>
        </div>

        <!-- Exámenes generados -->
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-5 shadow-sm">
          <h4 class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-3">Exámenes generados</h4>
          <div class="flex items-center gap-4">
            <div class="flex items-center gap-2 flex-1">
              <div class="w-7 h-7 rounded-lg bg-teal-100 dark:bg-emerald-900/30 flex items-center justify-center shrink-0">
                <BookOpen class="w-3.5 h-3.5 text-teal-600 dark:text-emerald-400" />
              </div>
              <div>
                <p class="text-lg font-black text-slate-800 dark:text-white">{{ analytics.total_examenes_lectura }}</p>
                <p class="text-[10px] text-slate-400">Comunicación</p>
              </div>
            </div>
            <div class="w-px h-8 bg-slate-100 dark:bg-slate-700"></div>
            <div class="flex items-center gap-2 flex-1">
              <div class="w-7 h-7 rounded-lg bg-emerald-100 dark:bg-emerald-900/30 flex items-center justify-center shrink-0">
                <Calculator class="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <p class="text-lg font-black text-slate-800 dark:text-white">{{ analytics.total_examenes_matematica }}</p>
                <p class="text-[10px] text-slate-400">Matemática</p>
              </div>
            </div>
            <div class="w-px h-8 bg-slate-100 dark:bg-slate-700"></div>
            <div class="flex-1 text-right">
              <p class="text-lg font-black text-slate-800 dark:text-white">{{ analytics.total_examenes }}</p>
              <p class="text-[10px] text-slate-400">Total</p>
            </div>
          </div>
        </div>

        <!-- Actividad reciente -->
        <div v-if="analytics.recientes.length > 0" class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 shadow-sm overflow-hidden">
          <div class="px-5 py-4 border-b border-slate-300 dark:border-slate-700">
            <h4 class="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Exámenes recientes</h4>
          </div>
          <div class="divide-y divide-slate-100 dark:divide-slate-700">
            <div v-for="ex in analytics.recientes" :key="`${ex.area}-${ex.id}`"
              class="flex items-center gap-3 px-5 py-3">
              <div :class="ex.area === 'lectura'
                ? 'bg-teal-100 dark:bg-emerald-900/30 text-teal-600 dark:text-emerald-400'
                : 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400'"
                class="w-8 h-8 rounded-lg flex items-center justify-center shrink-0">
                <BookOpen v-if="ex.area === 'lectura'" class="w-4 h-4" />
                <Calculator v-else class="w-4 h-4" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-slate-700 dark:text-slate-200 truncate">{{ ex.titulo }}</p>
                <p class="text-[10px] text-slate-400">{{ ex.grado }} · {{ ex.docente }}</p>
              </div>
              <p class="text-[10px] text-slate-400 shrink-0">{{ formatFecha(ex.fecha) }}</p>
            </div>
          </div>
        </div>
      </div>

    </div>
  </main>
</template>
