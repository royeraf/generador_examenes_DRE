<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { organizacionService } from '../../shared/services/api'
import type { Ugel, InstitucionEducativa } from '../../shared/types'
import Navbar from '../../shared/components/Navbar.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import { Building2, Loader2, MapPin } from 'lucide-vue-next'
const ugel = ref<Ugel | null>(null)
const instituciones = ref<InstitucionEducativa[]>([])
const loading = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const [u, ies] = await Promise.all([
      organizacionService.getMiUgel(),
      organizacionService.getInstituciones(),
    ])
    ugel.value = u
    instituciones.value = ies
  } catch (e: any) {
    error.value = e.response?.data?.detail ?? 'Error al cargar datos'
  } finally {
    loading.value = false
  }
})

const nivelLabel: Record<string, string> = { inicial: 'Inicial', primaria: 'Primaria', secundaria: 'Secundaria' }
</script>

<template>
  <EduBackground />
  <Navbar title="Mi UGEL" :show-home="true" />

  <main class="max-w-5xl mx-auto px-4 py-8 relative z-10">
    <div v-if="loading" class="flex justify-center py-16">
      <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
    </div>

    <div v-else-if="error" class="text-center py-16 text-red-500">{{ error }}</div>

    <div v-else-if="ugel" class="space-y-6">
      <!-- Info UGEL -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-6 shadow-sm">
        <div class="flex items-start gap-4">
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-600 flex items-center justify-center shrink-0">
            <Building2 class="w-6 h-6 text-white" />
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-bold text-slate-800 dark:text-white">{{ ugel.nombre }}</h2>
            <p class="text-sm text-slate-500 dark:text-slate-400 mt-0.5">Código: <span class="font-mono font-semibold">{{ ugel.codigo }}</span></p>
            <p v-if="ugel.provincia_nombre" class="text-sm text-slate-500 dark:text-slate-400 flex items-center gap-1 mt-1">
              <MapPin class="w-3.5 h-3.5" /> {{ ugel.provincia_nombre }}
            </p>
          </div>
          <span :class="ugel.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-slate-100 text-slate-500'"
            class="px-2.5 py-1 rounded-full text-xs font-bold">
            {{ ugel.is_active ? 'Activa' : 'Inactiva' }}
          </span>
        </div>
      </div>

      <!-- Estadísticas -->
      <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-4 shadow-sm text-center">
          <p class="text-2xl font-bold text-teal-600 dark:text-emerald-400">{{ instituciones.length }}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Total Instituciones</p>
        </div>
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-4 shadow-sm text-center">
          <p class="text-2xl font-bold text-green-600 dark:text-green-400">{{ instituciones.filter(i => i.is_active).length }}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Activas</p>
        </div>
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-4 shadow-sm text-center">
          <p class="text-2xl font-bold text-emerald-600 dark:text-emerald-400">{{ instituciones.filter(i => Array.isArray(i.nivel_educativo) ? i.nivel_educativo.includes('primaria') : i.nivel_educativo === 'primaria').length }}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Primaria</p>
        </div>
        <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 p-4 shadow-sm text-center">
          <p class="text-2xl font-bold text-orange-600 dark:text-orange-400">{{ instituciones.filter(i => Array.isArray(i.nivel_educativo) ? i.nivel_educativo.includes('secundaria') : i.nivel_educativo === 'secundaria').length }}</p>
          <p class="text-xs text-slate-500 dark:text-slate-400 mt-0.5">Secundaria</p>
        </div>
      </div>

      <!-- Lista de instituciones -->
      <div class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-300 dark:border-slate-700 overflow-hidden shadow-sm">
        <div class="px-5 py-4 border-b border-slate-300 dark:border-slate-700">
          <h3 class="font-bold text-slate-800 dark:text-white">Instituciones Educativas</h3>
        </div>
        <table class="w-full text-sm">
          <thead class="bg-slate-50 dark:bg-slate-700/50 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            <tr>
              <th class="px-4 py-3 text-left">Nombre</th>
              <th class="px-4 py-3 text-left">Nivel</th>
              <th class="px-4 py-3 text-center">Estado</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
            <tr v-for="ie in instituciones" :key="ie.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/30">
              <td class="px-4 py-3">
                <p class="font-medium text-slate-800 dark:text-white">{{ ie.nombre }}</p>
                <p class="text-xs text-slate-400 font-mono">{{ ie.codigo_modular }}</p>
              </td>
              <td class="px-4 py-3">
                <div class="flex flex-wrap gap-1">
                  <span v-for="niv in (Array.isArray(ie.nivel_educativo) ? ie.nivel_educativo : [ie.nivel_educativo])" :key="niv"
                    class="bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 px-2 py-0.5 rounded-full text-xs font-semibold">
                    {{ nivelLabel[niv] ?? niv }}
                  </span>
                </div>
              </td>
              <td class="px-4 py-3 text-center">
                <span :class="ie.is_active ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-slate-100 text-slate-500'"
                  class="px-2 py-0.5 rounded-full text-xs font-semibold">
                  {{ ie.is_active ? 'Activa' : 'Inactiva' }}
                </span>
              </td>
            </tr>
            <tr v-if="instituciones.length === 0">
              <td colspan="3" class="px-4 py-8 text-center text-slate-400">No hay instituciones en esta UGEL</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>
</template>
