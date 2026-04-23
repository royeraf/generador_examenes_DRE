<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '../../services/api'
import { GraduationCap, ChevronLeft, Loader2, AlertCircle, BarChart3, BookOpen, Calculator } from 'lucide-vue-next'

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

const nivelColors: Record<string, { bar: string; badge: string }> = {
  pre_inicio: { bar: 'bg-red-400', badge: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' },
  inicio: { bar: 'bg-orange-400', badge: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' },
  proceso: { bar: 'bg-yellow-400', badge: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' },
  satisfactorio: { bar: 'bg-green-500', badge: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' },
  destacado: { bar: 'bg-teal-500', badge: 'bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400' },
}

const nivelLabels: Record<string, string> = {
  pre_inicio: 'Pre Inicio', inicio: 'Inicio', proceso: 'En Proceso',
  satisfactorio: 'Satisfactorio', destacado: 'Destacado',
}

function formatFecha(fecha: string | null) {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleDateString('es-PE', { day: '2-digit', month: 'short', year: 'numeric' })
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
          <div class="w-7 h-7 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <GraduationCap class="w-4 h-4 text-white" />
          </div>
          <span class="font-bold text-slate-800 dark:text-white text-sm">Mi Progreso</span>
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

      <div v-else-if="progreso.length === 0"
        class="text-center py-16 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700">
        <BarChart3 class="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
        <p class="text-slate-500 dark:text-slate-400 font-medium">Sin progreso aún</p>
        <p class="text-sm text-slate-400 dark:text-slate-500 mt-1">Completa al menos un examen para ver tu progreso</p>
      </div>

      <div v-else class="space-y-5">
        <div
          v-for="p in progreso"
          :key="p.area"
          class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm"
        >
          <div class="flex items-center gap-3 mb-5">
            <div :class="p.area === 'comunicacion' ? 'from-teal-500 to-indigo-600' : 'from-orange-500 to-amber-500'"
              class="w-10 h-10 rounded-xl bg-gradient-to-br flex items-center justify-center">
              <BookOpen v-if="p.area === 'comunicacion'" class="w-5 h-5 text-white" />
              <Calculator v-else class="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 class="font-bold text-slate-800 dark:text-white">
                {{ p.area === 'comunicacion' ? 'Comunicación' : 'Matemática' }}
              </h3>
              <p class="text-xs text-slate-500 dark:text-slate-400">Última actividad: {{ formatFecha(p.ultima_actividad) }}</p>
            </div>
            <div class="ml-auto">
              <span v-if="p.nivel_logro_actual"
                :class="(nivelColors[p.nivel_logro_actual] || { badge: 'bg-slate-100 text-slate-600' }).badge"
                class="px-2.5 py-1 rounded-full text-xs font-bold">
                {{ nivelLabels[p.nivel_logro_actual] ?? p.nivel_logro_actual }}
              </span>
            </div>
          </div>

          <!-- Puntaje promedio -->
          <div class="mb-4">
            <div class="flex justify-between items-center mb-1.5">
              <span class="text-xs font-semibold text-slate-500 dark:text-slate-400">Puntaje promedio</span>
              <span class="text-sm font-bold text-slate-700 dark:text-slate-200">{{ p.puntaje_promedio.toFixed(1) }}%</span>
            </div>
            <div class="h-2.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
              <div
                :class="(nivelColors[p.nivel_logro_actual || ''] || { bar: 'bg-slate-400' }).bar"
                class="h-full rounded-full transition-all duration-500"
                :style="{ width: p.puntaje_promedio + '%' }"
              ></div>
            </div>
          </div>

          <!-- Stats -->
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-slate-50 dark:bg-slate-700 rounded-xl p-3 text-center">
              <p class="text-xl font-bold text-slate-700 dark:text-slate-200">{{ p.total_examenes_completados }}</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">Exámenes completados</p>
            </div>
            <div class="bg-slate-50 dark:bg-slate-700 rounded-xl p-3 text-center">
              <p class="text-xl font-bold text-slate-700 dark:text-slate-200">{{ p.puntaje_promedio.toFixed(0) }}%</p>
              <p class="text-xs text-slate-500 dark:text-slate-400">Promedio general</p>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
