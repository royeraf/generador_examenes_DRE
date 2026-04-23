<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../../services/api'
import { useTheme } from '../../composables/useTheme'
import { BookOpen, GraduationCap, ChevronLeft, Loader2, Clock, CheckCircle2, AlertCircle, Sun, Moon } from 'lucide-vue-next'

const router = useRouter()
const { isDark, toggleTheme } = useTheme()

interface AsignacionResumen {
  id: number
  tipo_examen: string
  titulo: string
  fecha_inicio: string | null
  fecha_fin: string | null
  duracion_minutos: number | null
  intentos_permitidos: number
  mis_intentos: number
  completado: boolean
  puntaje?: number | null
  nivel_logro?: string | null
}

const examenes = ref<AsignacionResumen[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const res = await apiClient.get('/estudiante/examenes')
    examenes.value = res.data
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar exámenes'
  } finally {
    loading.value = false
  }
})

const nivelColors: Record<string, string> = {
  pre_inicio: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
  inicio: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
  proceso: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
  satisfactorio: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
  destacado: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400',
}

const nivelLabels: Record<string, string> = {
  pre_inicio: 'Pre Inicio', inicio: 'Inicio', proceso: 'En Proceso',
  satisfactorio: 'Satisfactorio', destacado: 'Destacado',
}

function formatFecha(fecha: string | null) {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleDateString('es-PE', { day: '2-digit', month: 'short' })
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-teal-50 to-indigo-50 dark:from-slate-900 dark:to-slate-800">
    <header class="bg-white/80 dark:bg-slate-800/80 backdrop-blur-md border-b border-slate-100 dark:border-slate-700 sticky top-0 z-40">
      <div class="max-w-4xl mx-auto px-4 h-14 flex items-center gap-3">
        <button @click="router.push('/estudiante')" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors">
          <ChevronLeft class="w-5 h-5" />
        </button>
        <div class="flex items-center gap-2">
          <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-teal-500 to-indigo-600 flex items-center justify-center">
            <GraduationCap class="w-4 h-4 text-white" />
          </div>
          <span class="font-bold text-slate-800 dark:text-white text-sm">Mis Exámenes</span>
        </div>
      </div>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-8">
      <div v-if="loading" class="flex justify-center py-16">
        <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
      </div>

      <div v-else-if="error" class="text-center py-16 text-red-500 flex flex-col items-center gap-3">
        <AlertCircle class="w-8 h-8" />
        <p>{{ error }}</p>
      </div>

      <div v-else-if="examenes.length === 0"
        class="text-center py-16 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700">
        <BookOpen class="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p class="text-slate-500 dark:text-slate-400 font-medium">No tienes exámenes asignados</p>
        <p class="text-sm text-slate-400 dark:text-slate-500 mt-1">Tu docente aún no ha asignado exámenes</p>
      </div>

      <div v-else class="space-y-4">
        <div
          v-for="examen in examenes"
          :key="examen.id"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-5 shadow-sm hover:shadow-md transition-all"
        >
          <div class="flex items-start gap-4">
            <div :class="examen.tipo_examen === 'lectura'
              ? 'from-teal-500 to-indigo-600'
              : 'from-orange-500 to-amber-500'"
              class="w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center shrink-0">
              <BookOpen class="w-5 h-5 text-white" />
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2 flex-wrap">
                <div>
                  <h3 class="font-bold text-slate-800 dark:text-white">{{ examen.titulo }}</h3>
                  <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {{ examen.tipo_examen === 'lectura' ? 'Comunicación' : 'Matemática' }}
                    <span v-if="examen.duracion_minutos" class="ml-2 flex items-center gap-0.5 inline-flex">
                      <Clock class="w-3 h-3" /> {{ examen.duracion_minutos }} min
                    </span>
                  </p>
                </div>
                <div class="flex items-center gap-2 flex-wrap">
                  <span v-if="examen.completado && examen.nivel_logro"
                    :class="nivelColors[examen.nivel_logro] || 'bg-slate-100 text-slate-700'"
                    class="px-2.5 py-0.5 rounded-full text-xs font-bold">
                    {{ nivelLabels[examen.nivel_logro] ?? examen.nivel_logro }}
                  </span>
                  <span v-if="examen.completado"
                    class="inline-flex items-center gap-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2.5 py-0.5 rounded-full text-xs font-bold">
                    <CheckCircle2 class="w-3 h-3" /> Completado
                  </span>
                </div>
              </div>

              <div class="flex items-center gap-4 mt-3 text-xs text-slate-500 dark:text-slate-400">
                <span v-if="examen.fecha_inicio">Desde: {{ formatFecha(examen.fecha_inicio) }}</span>
                <span v-if="examen.fecha_fin">Hasta: {{ formatFecha(examen.fecha_fin) }}</span>
                <span>Intento {{ examen.mis_intentos }}/{{ examen.intentos_permitidos }}</span>
                <span v-if="examen.completado && examen.puntaje != null">
                  Puntaje: <span class="font-semibold text-teal-600 dark:text-teal-400">{{ examen.puntaje.toFixed(1) }}%</span>
                </span>
              </div>
            </div>
          </div>

          <div class="mt-4 flex justify-end">
            <button
              v-if="!examen.completado || examen.mis_intentos < examen.intentos_permitidos"
              @click="router.push(`/estudiante/examen/${examen.id}`)"
              class="px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all"
            >
              {{ examen.mis_intentos > 0 ? 'Reintentar' : 'Comenzar' }}
            </button>
            <button v-else @click="router.push(`/estudiante/examen/${examen.id}`)"
              class="px-4 py-2 bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold text-sm rounded-xl transition-all">
              Ver resultados
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
