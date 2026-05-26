<script setup lang="ts">
import { shallowRef, computed, type Component } from 'vue'
import {
  BookOpenText, Calculator, FlaskConical, Cpu, GraduationCap, ChevronRight,
  Menu, PanelLeftClose, X,
} from 'lucide-vue-next'
import Header from '../../shared/components/Header.vue'
import EduBackground from '../../shared/components/EduBackground.vue'
import { useAuthStore } from '../../stores/auth'
import GradosPanel from './components/curriculum/GradosPanel.vue'
import ComunicacionPanel from './components/curriculum/ComunicacionPanel.vue'
import MatematicaPanel from './components/curriculum/MatematicaPanel.vue'

const auth = useAuthStore()

// ── Registro de áreas ─────────────────────────────────────────────────────────
// Para agregar un área nueva: añadir entrada aquí + crear su Panel component.

interface AreaConfig {
  id: string
  label: string
  descripcion: string
  icon: Component
  panel: Component | null  // null = comingSoon
  accentBg: string
  accentText: string
  accentRing: string
  activeBg: string
}

const AREAS: AreaConfig[] = [
  {
    id: 'grados',
    label: 'Grados',
    descripcion: 'Estructura institucional',
    icon: GraduationCap,
    panel: GradosPanel,
    accentBg: 'bg-slate-500',
    accentText: 'text-slate-600 dark:text-slate-400',
    accentRing: 'ring-slate-500',
    activeBg: 'bg-slate-50 dark:bg-slate-800/60 border-slate-300 dark:border-slate-600',
  },
  {
    id: 'comunicacion',
    label: 'Comunicación',
    descripcion: 'Comprensión lectora',
    icon: BookOpenText,
    panel: ComunicacionPanel,
    accentBg: 'bg-teal-500',
    accentText: 'text-teal-600 dark:text-emerald-400',
    accentRing: 'ring-teal-500',
    activeBg: 'bg-teal-50 dark:bg-emerald-900/20 border-teal-200 dark:border-emerald-800',
  },
  {
    id: 'matematica',
    label: 'Matemática',
    descripcion: 'Resolución de problemas',
    icon: Calculator,
    panel: MatematicaPanel,
    accentBg: 'bg-violet-500',
    accentText: 'text-violet-600 dark:text-violet-400',
    accentRing: 'ring-violet-500',
    activeBg: 'bg-violet-50 dark:bg-violet-900/20 border-violet-200 dark:border-violet-800',
  },
  {
    id: 'ciencias',
    label: 'Ciencia y Tecnología',
    descripcion: 'Próximamente',
    icon: FlaskConical,
    panel: null,
    accentBg: 'bg-emerald-500',
    accentText: 'text-emerald-600 dark:text-emerald-400',
    accentRing: 'ring-emerald-500',
    activeBg: 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-200 dark:border-emerald-800',
  },
  {
    id: 'ept',
    label: 'EPT',
    descripcion: 'Próximamente',
    icon: Cpu,
    panel: null,
    accentBg: 'bg-orange-500',
    accentText: 'text-orange-600 dark:text-orange-400',
    accentRing: 'ring-orange-500',
    activeBg: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800',
  },
]

// Áreas visibles según permisos del usuario
const visibleAreas = computed(() => AREAS.map(area => ({
  ...area,
  panel: (() => {
    if (area.id === 'grados')       return area.panel  // siempre activo para cualquier acceso curricular
    if (area.id === 'comunicacion') return auth.canAccessAdminDesempenosComunicacion ? area.panel : null
    if (area.id === 'matematica')   return auth.canAccessAdminDesempenosMatematica   ? area.panel : null
    return area.panel
  })(),
  hidden: (() => {
    if (area.id === 'comunicacion') return !auth.canAccessAdminDesempenosComunicacion
    if (area.id === 'matematica')   return !auth.canAccessAdminDesempenosMatematica
    return false
  })(),
})).filter(a => !a.hidden))

const selectedAreaId = shallowRef(
  visibleAreas.value.find(a => a.panel)?.id ?? AREAS[0]!.id
)
const currentArea = computed(
  () => visibleAreas.value.find(a => a.id === selectedAreaId.value) ?? visibleAreas.value[0]!
)

function selectArea(area: AreaConfig) {
  if (!area.panel) return
  selectedAreaId.value = area.id
  // Opcional: Cerrar sidebar en móvil tras seleccionar
  if (window.innerWidth < 640) {
    sidebarOpen.value = false
  }
}

const sidebarCollapsed = shallowRef(false)
const sidebarOpen = shallowRef(false) // Para móvil (drawer)
</script>

<template>
  <div class="min-h-screen bg-slate-50 dark:bg-slate-950 font-sans relative flex flex-col">
    <EduBackground variant="emerald" />

    <div class="relative z-10 flex flex-col h-screen">

      <!-- Header -->
      <Header
        title="Gestión Curricular"
        subtitle="Desempeños por área"
        :show-home="true"
      >
        <template #actions-before>
          <button
            @click="sidebarOpen = !sidebarOpen"
            class="sm:hidden p-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-white border border-slate-300 dark:border-slate-700 cursor-pointer"
          >
            <Menu class="w-5 h-5" />
          </button>
        </template>
      </Header>

      <!-- Main layout: sidebar + content -->
      <div class="flex flex-1 min-h-0 overflow-hidden relative">

        <!-- Mobile Backdrop -->
        <Transition name="fade">
          <div v-if="sidebarOpen"
            class="sm:hidden fixed inset-0 z-[60] bg-black/50 backdrop-blur-sm cursor-pointer"
            @click="sidebarOpen = false"
          />
        </Transition>

        <!-- Sidebar / Navigation -->
        <aside
          class="fixed sm:relative z-[70] h-full sm:h-auto bg-white dark:bg-slate-900 border-r border-slate-300 dark:border-slate-800 transition-all duration-300 flex flex-col"
          :class="[
            sidebarOpen ? 'translate-x-0 w-64' : '-translate-x-full sm:translate-x-0',
            !sidebarCollapsed ? 'sm:w-64' : 'sm:w-20'
          ]"
        >
          <!-- Desktop toggle button -->
          <button
            @click="sidebarCollapsed = !sidebarCollapsed"
            class="hidden sm:flex absolute -right-3 top-4 w-6 h-6 rounded-full bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 shadow-sm z-10 transition-transform cursor-pointer"
            :class="sidebarCollapsed ? 'rotate-180' : ''"
          >
            <PanelLeftClose class="w-3.5 h-3.5" />
          </button>

          <!-- Mobile close button -->
          <div class="sm:hidden flex items-center justify-between p-4 border-b border-slate-300 dark:border-slate-800">
            <span class="font-bold text-slate-800 dark:text-white">Menú</span>
            <button @click="sidebarOpen = false" class="text-slate-400 cursor-pointer">
              <X class="w-5 h-5" />
            </button>
          </div>

          <div class="flex flex-col py-4 overflow-y-auto custom-scrollbar flex-1">
            <p v-if="!sidebarCollapsed || sidebarOpen" class="px-4 mb-3 text-[10px] font-bold text-slate-400 uppercase tracking-widest whitespace-nowrap">Áreas curriculares</p>

            <nav class="flex flex-col gap-1 px-2">
              <button
                v-for="area in visibleAreas"
                :key="area.id"
                @click="selectArea(area)"
                :disabled="!area.panel"
                class="flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all group relative shrink-0"
                :class="[
                  area.panel ? 'cursor-pointer' : 'cursor-not-allowed opacity-50',
                  selectedAreaId === area.id && area.panel
                    ? `${area.activeBg} border`
                    : 'hover:bg-slate-50 dark:hover:bg-slate-800 border border-transparent',
                ]"
                :title="sidebarCollapsed ? area.label : ''"
              >
                <!-- Color dot -->
                <span
                  class="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 transition-colors"
                  :class="selectedAreaId === area.id && area.panel
                    ? `${area.accentBg} text-white shadow-md`
                    : 'bg-slate-100 dark:bg-slate-800 text-slate-500'"
                >
                  <component :is="area.icon" class="w-4.5 h-4.5" />
                </span>

                <div v-if="!sidebarCollapsed || sidebarOpen" class="flex-1 min-w-0 transition-opacity duration-300">
                  <p class="text-sm font-semibold truncate"
                     :class="selectedAreaId === area.id && area.panel ? area.accentText : 'text-slate-700 dark:text-slate-300'">
                    {{ area.label }}
                  </p>
                  <p class="text-[10px] text-slate-400 truncate">{{ area.descripcion }}</p>
                </div>

                <ChevronRight
                  v-if="area.panel && selectedAreaId === area.id && (!sidebarCollapsed || sidebarOpen)"
                  class="w-3.5 h-3.5 shrink-0"
                  :class="area.accentText"
                />
              </button>
            </nav>
          </div>

          <!-- Bottom Footer Info -->
          <div v-if="!sidebarCollapsed || sidebarOpen" class="p-4 border-t border-slate-300 dark:border-slate-800">
            <div class="flex items-center gap-3 p-2 bg-slate-50 dark:bg-slate-800/50 rounded-xl">
              <div class="w-8 h-8 rounded-full bg-teal-500 flex items-center justify-center text-white font-bold text-xs">
                {{ auth.user?.nombres?.charAt(0) || 'A' }}
              </div>
              <div class="min-w-0">
                <p class="text-xs font-bold text-slate-700 dark:text-slate-200 truncate">{{ auth.user?.nombres || 'Admin' }}</p>
                <p class="text-[10px] text-slate-500 truncate capitalize">{{ auth.userRole?.replace(/_/g, ' ') }}</p>
              </div>
            </div>
          </div>
        </aside>

        <!-- Content area -->
        <main class="flex-1 min-w-0 flex flex-col overflow-hidden">

          <!-- Area header strip -->
          <div class="shrink-0 px-6 py-3 border-b border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900 flex items-center gap-3">
            <span class="w-7 h-7 rounded-lg flex items-center justify-center text-white shadow-sm" :class="currentArea.accentBg">
              <component :is="currentArea.icon" class="w-3.5 h-3.5" />
            </span>
            <div>
              <h2 class="text-sm font-bold text-slate-800 dark:text-white">{{ currentArea.label }}</h2>
              <p class="text-xs text-slate-400">{{ currentArea.descripcion }}</p>
            </div>
          </div>

          <!-- Panel -->
          <div class="flex-1 min-h-0 overflow-hidden p-5">
            <component :is="currentArea.panel" v-if="currentArea.panel" class="h-full" />

            <!-- Coming soon placeholder -->
            <div v-else class="h-full flex flex-col items-center justify-center text-center gap-4">
              <span class="w-16 h-16 rounded-2xl flex items-center justify-center bg-slate-100 dark:bg-slate-800">
                <component :is="currentArea.icon" class="w-8 h-8 text-slate-400" />
              </span>
              <div>
                <p class="font-bold text-slate-700 dark:text-slate-200">{{ currentArea.label }}</p>
                <p class="text-sm text-slate-400 mt-1">Este módulo estará disponible próximamente</p>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
