<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { organizacionService } from '../services/api'
import type { InstitucionEducativa } from '../types'
import Header from '../components/Header.vue'
import { Home, Building2, Loader2, MapPin, GraduationCap } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()
const institucion = ref<InstitucionEducativa | null>(null)
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    institucion.value = await organizacionService.getMiInstitucion()
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar datos'
  } finally {
    loading.value = false
  }
})

const nivelLabel: Record<string, string> = { inicial: 'Inicial', primaria: 'Primaria', secundaria: 'Secundaria' }
const nivelColor: Record<string, string> = {
  inicial: 'from-amber-500 to-orange-500',
  primaria: 'from-teal-500 to-indigo-600',
  secundaria: 'from-indigo-500 to-purple-600',
}
</script>

<template>
  <Header title="Mi Institución" subtitle="">
    <template #actions-before>
      <button @click="router.push('/')"
        class="p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300"
        title="Inicio">
        <Home class="w-4 h-4" />
      </button>
    </template>
  </Header>

  <main class="max-w-3xl mx-auto px-4 py-8">
    <div v-if="loading" class="flex justify-center py-16">
      <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
    </div>

    <div v-else-if="error" class="text-center py-16 text-red-500">{{ error }}</div>

    <div v-else-if="institucion" class="space-y-5">
      <!-- Cabecera -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm">
        <div class="flex items-start gap-4">
          <div :class="`bg-gradient-to-br ${nivelColor[(Array.isArray(institucion.nivel_educativo) ? (institucion.nivel_educativo[0] ?? '') : institucion.nivel_educativo)] || 'from-teal-500 to-indigo-600'}`"
            class="w-14 h-14 rounded-2xl flex items-center justify-center shrink-0">
            <Building2 class="w-7 h-7 text-white" />
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-bold text-slate-800 dark:text-white leading-tight">{{ institucion.nombre }}</h2>
            <div class="flex items-center gap-3 mt-1.5 flex-wrap">
              <span class="font-mono text-xs text-slate-500 dark:text-slate-400">{{ institucion.codigo_modular }}</span>
              <span v-for="niv in (Array.isArray(institucion.nivel_educativo) ? institucion.nivel_educativo : [institucion.nivel_educativo])"
                :key="niv"
                :class="`bg-gradient-to-r ${nivelColor[niv] || 'from-teal-500 to-indigo-600'} text-white`"
                class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-bold">
                <GraduationCap class="w-3 h-3" />
                {{ nivelLabel[niv] ?? niv }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Detalles -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 p-6 shadow-sm space-y-4">
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
    </div>
  </main>
</template>
