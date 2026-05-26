<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../../../stores/auth'
import { useTheme } from '../../../shared/composables/useTheme'
import { isSidebarCollapsed as rawSidebarCollapsed, toggleSidebar } from '../composables/useStudentLayout'
import { 
  Home, BookOpen, BarChart3, Sun, Moon, LogOut, Rocket,
  Menu, X, User, ChevronDown, ChevronUp, HelpCircle, 
  Building2, Sparkles, Compass, Info, GraduationCap,
  PanelLeft
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const { isDark, toggleTheme } = useTheme()

const isSidebarOpen = ref(false)
const isProfileExpanded = ref(true)
const isHelpExpanded = ref(false)

const windowWidth = ref(typeof window !== 'undefined' ? window.innerWidth : 1024)

function updateWidth() {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', updateWidth)
})

onUnmounted(() => {
  window.removeEventListener('resize', updateWidth)
})

const isDesktop = computed(() => windowWidth.value >= 1024)
const isSidebarCollapsed = computed(() => rawSidebarCollapsed.value && isDesktop.value)

const activeTab = computed(() => {
  const path = route.path
  if (path === '/estudiante' || path === '/estudiante/') return 'inicio'
  if (path.startsWith('/estudiante/examenes')) return 'examenes'
  if (path.startsWith('/estudiante/progreso')) return 'progreso'
  return ''
})

const navItems = [
  { id: 'inicio', label: 'Inicio', path: '/estudiante', icon: Home },
  { id: 'examenes', label: 'Exámenes', path: '/estudiante/examenes', icon: BookOpen },
  { id: 'progreso', label: 'Progreso', path: '/estudiante/progreso', icon: BarChart3 },
]

function navigate(path: string) {
  isSidebarOpen.value = false
  router.push(path)
}

function handleLogout() {
  isSidebarOpen.value = false
  auth.logout()
  router.push('/login')
}



const userInitials = computed(() => {
  const nombres = auth.user?.nombres || ''
  const apellidos = auth.user?.apellidos || ''
  const first = nombres.trim()[0] || ''
  const last = apellidos.trim()[0] || ''
  return (first + last).toUpperCase() || 'E'
})
</script>

<template>
  <div>
    <!-- Desktop/Tablet Header (Sticky Top) -->
    <header class="sticky top-0 z-40 w-full bg-white/80 dark:bg-[#121212]/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800 shadow-sm transition-all duration-300"
            :class="isSidebarCollapsed ? 'lg:pl-[84px]' : 'lg:pl-[280px]'">
      <div class="max-w-4xl mx-auto px-6 h-16 flex items-center justify-between">
        
        <!-- Left: Hamburger Button (for Left Sidebar) + Branding -->
        <div class="flex items-center gap-3 shrink-0">
          <!-- Hamburger Button (Mobile only) -->
          <button @click="isSidebarOpen = true"
            class="lg:hidden w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all border border-transparent hover:border-slate-300 dark:hover:border-slate-700 cursor-pointer"
            title="Opciones y Perfil">
            <Menu class="w-4.5 h-4.5" />
          </button>


          <div class="flex items-center gap-3 cursor-pointer hover:opacity-90 transition-opacity" @click="navigate('/estudiante')">
            <div class="w-9 h-9 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-600 flex items-center justify-center shadow-lg shadow-teal-500/20">
              <Rocket class="w-4.5 h-4.5 text-white" />
            </div>
            <div class="flex flex-col">
              <span class="font-bold text-slate-800 dark:text-white text-sm tracking-tight leading-none">SIEVA</span>
              <span class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest mt-0.5">Estudiante</span>
            </div>
          </div>
        </div>


        <!-- Right: Actions -->
        <div class="flex items-center gap-1.5">
          <button @click="toggleTheme()"
            class="w-9 h-9 rounded-xl flex items-center justify-center text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all border border-transparent hover:border-slate-300 dark:hover:border-slate-700 cursor-pointer"
            title="Cambiar tema">
            <Sun v-if="isDark" class="w-4.5 h-4.5 text-amber-500" />
            <Moon v-else class="w-4.5 h-4.5" />
          </button>
        </div>

      </div>
    </header>

    <!-- ── Sliding Lateral Drawer Menu ── -->
    
    <!-- Semi-transparent Overlay Backdrop -->
    <div v-if="isSidebarOpen" 
         @click="isSidebarOpen = false" 
         class="lg:hidden fixed inset-0 z-50 bg-slate-950/50 dark:bg-[#0d0d0d]/70 backdrop-blur-xs transition-opacity duration-300 ease-out"
    ></div>

    <!-- Drawer Panel Container -->
    <aside 
      class="fixed top-0 left-0 h-full z-50 bg-white dark:bg-[#121212] shadow-2xl lg:shadow-none border-r border-slate-200 dark:border-slate-800 transition-all duration-300 ease-out transform flex flex-col justify-between"
      :class="[
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        isSidebarCollapsed ? 'lg:w-[84px]' : 'lg:w-[280px]',
        'w-[290px] sm:w-[340px]',
        'overflow-hidden lg:overflow-visible'
      ]"
    >
      <!-- Floating Sidebar Toggle Button (Desktop only) -->
      <button 
        @click="toggleSidebar()"
        class="hidden lg:flex absolute top-6 -right-3 w-6 h-6 rounded-full bg-white dark:bg-[#121212] border border-slate-200 dark:border-slate-800 items-center justify-center text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 shadow-md hover:shadow-lg hover:scale-105 active:scale-95 transition-all cursor-pointer z-50"
        :title="isSidebarCollapsed ? 'Expandir panel' : 'Colapsar panel'"
      >
        <PanelLeft class="w-3.5 h-3.5" />
      </button>

      <!-- Top Section -->
      <div class="flex-1 overflow-y-auto px-6 py-6 scrollbar-thin">
        
        <!-- Header Row -->
        <div class="flex items-center mb-6" :class="isSidebarCollapsed ? 'justify-center' : 'justify-between'">
          <div class="flex items-center gap-2">
            <Compass class="w-5 h-5 text-teal-500 shrink-0" />
            <h2 v-show="!isSidebarCollapsed" class="text-md font-bold text-slate-800 dark:text-white font-fredoka uppercase tracking-widest">Opciones</h2>
          </div>
          <button @click="isSidebarOpen = false" 
                  class="lg:hidden w-8 h-8 rounded-xl border border-slate-200/60 dark:border-slate-800 flex items-center justify-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all cursor-pointer">
            <X class="w-4 h-4" />
          </button>
        </div>

        <!-- Student Profile Box -->
        <div class="mb-6 bg-slate-50 dark:bg-[#0d0d0d]/50 border border-slate-200 dark:border-slate-800 rounded-2xl shadow-xs transition-all duration-300"
             :class="isSidebarCollapsed ? 'p-2 flex justify-center' : 'p-4'">
          <!-- Avatar + General Info -->
          <div class="flex items-center gap-3" :class="isSidebarCollapsed ? 'justify-center' : ''">
            <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center shadow-md shadow-teal-500/10 shrink-0">
              <span class="text-md font-black text-white">{{ userInitials }}</span>
            </div>
            <div v-show="!isSidebarCollapsed" class="flex-1 min-w-0">
              <h3 class="text-sm font-bold text-slate-800 dark:text-white truncate leading-tight">{{ auth.displayName }}</h3>
              <span class="inline-block bg-teal-50 dark:bg-emerald-950/40 text-teal-600 dark:text-emerald-400 text-[9px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider mt-1 border border-teal-100 dark:border-emerald-900/30">
                Estudiante
              </span>
            </div>
          </div>

          <!-- Divider -->
          <div v-show="!isSidebarCollapsed" class="my-4 border-t border-slate-200 dark:border-slate-800/80"></div>

          <!-- Collapsible Academic Details -->
          <div v-show="!isSidebarCollapsed">
            <button @click="isProfileExpanded = !isProfileExpanded" 
                    class="w-full flex items-center justify-between text-xs font-bold text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors cursor-pointer select-none">
              <span>Datos Académicos</span>
              <ChevronUp v-if="isProfileExpanded" class="w-3.5 h-3.5" />
              <ChevronDown v-else class="w-3.5 h-3.5" />
            </button>

            <!-- Collapsible panel -->
            <div v-show="isProfileExpanded" class="mt-3 space-y-2.5">
              <div v-if="auth.user?.matricula_activa?.grado_nombre" class="flex items-start gap-2.5">
                <GraduationCap class="w-4 h-4 text-slate-400 dark:text-slate-500 mt-0.5 shrink-0" />
                <div class="text-[11px] leading-tight">
                  <p class="font-extrabold text-slate-400 uppercase tracking-wider text-[8px]">Grado y Sección</p>
                  <p class="font-bold text-slate-700 dark:text-slate-300 mt-0.5">{{ auth.user.matricula_activa.grado_nombre }} - "{{ auth.user.matricula_activa.seccion || 'A' }}"</p>
                </div>
              </div>

              <div v-if="auth.user?.institucion_nombre" class="flex items-start gap-2.5">
                <Building2 class="w-4 h-4 text-slate-400 dark:text-slate-500 mt-0.5 shrink-0" />
                <div class="text-[11px] leading-tight">
                  <p class="font-extrabold text-slate-400 uppercase tracking-wider text-[8px]">Institución Educativa</p>
                  <p class="font-bold text-slate-700 dark:text-slate-300 mt-0.5">{{ auth.user.institucion_nombre }}</p>
                </div>
              </div>

              <div class="flex items-start gap-2.5">
                <User class="w-4 h-4 text-slate-400 dark:text-slate-500 mt-0.5 shrink-0" />
                <div class="text-[11px] leading-tight">
                  <p class="font-extrabold text-slate-400 uppercase tracking-wider text-[8px]">Código de Estudiante</p>
                  <p class="font-mono font-bold text-slate-700 dark:text-slate-300 mt-0.5">{{ auth.user?.codigo_estudiante || auth.user?.dni || '—' }}</p>
                </div>
              </div>

              <div v-if="auth.user?.ugel_nombre" class="flex items-start gap-2.5">
                <Sparkles class="w-4 h-4 text-slate-400 dark:text-slate-500 mt-0.5 shrink-0" />
                <div class="text-[11px] leading-tight">
                  <p class="font-extrabold text-slate-400 uppercase tracking-wider text-[8px]">Jurisdicción UGEL</p>
                  <p class="font-bold text-slate-700 dark:text-slate-300 mt-0.5">{{ auth.user.ugel_nombre }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Sidebar Navigation Menu Items -->
        <div class="space-y-2 mb-6">
          <p v-show="!isSidebarCollapsed" class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest pl-1 mb-2">Secciones Rápidas</p>
          
          <button v-for="item in navItems" :key="item.id"
            @click="navigate(item.path)"
            class="w-full flex items-center p-3 rounded-xl border transition-all text-xs font-bold cursor-pointer"
            :class="[
              activeTab === item.id
                ? 'bg-slate-100 dark:bg-[#252525]/80 border-slate-300 dark:border-slate-700 text-teal-600 dark:text-emerald-400 font-bold'
                : 'bg-transparent border-transparent text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/40 hover:text-slate-800 dark:hover:text-slate-200',
              isSidebarCollapsed ? 'justify-center px-0' : 'justify-between'
            ]"
            :title="isSidebarCollapsed ? item.label : ''"
          >
            <div class="flex items-center gap-2.5">
              <component :is="item.icon" class="w-4 h-4 shrink-0" />
              <span v-show="!isSidebarCollapsed">{{ item.label }}</span>
            </div>
            <div v-show="!isSidebarCollapsed && activeTab === item.id" class="w-1.5 h-1.5 bg-teal-500 dark:bg-emerald-400 rounded-full"></div>
          </button>
        </div>

        <!-- Dark/Light Mode explicit control in sidebar -->
        <div class="mb-6">
          <p v-show="!isSidebarCollapsed" class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest pl-1 mb-2">Apariencia</p>
          <button @click="toggleTheme()" 
                  class="w-full flex items-center p-3 rounded-xl bg-slate-50 dark:bg-[#0d0d0d]/20 border border-slate-200 dark:border-slate-800/60 hover:bg-slate-100 dark:hover:bg-slate-800/40 transition-colors text-xs font-bold cursor-pointer text-slate-600 dark:text-slate-400"
                  :class="isSidebarCollapsed ? 'justify-center px-0' : 'justify-between'"
                  :title="isSidebarCollapsed ? 'Cambiar Modo' : ''">
            <div class="flex items-center gap-2.5">
              <Sun v-if="isDark" class="w-4 h-4 text-amber-500 shrink-0" />
              <Moon v-else class="w-4 h-4 text-slate-400 shrink-0" />
              <span v-show="!isSidebarCollapsed">Cambiar a Modo {{ isDark ? 'Claro' : 'Oscuro' }}</span>
            </div>
            <span v-show="!isSidebarCollapsed" class="text-[10px] font-bold text-slate-400 px-2 py-0.5 bg-white dark:bg-[#121212] border border-slate-200 dark:border-slate-850 rounded-lg shadow-2xs uppercase">
              {{ isDark ? 'Oscuro' : 'Claro' }}
            </span>
          </button>
        </div>

        <!-- Collapsible Info / Ayuda & Guía -->
        <div v-show="!isSidebarCollapsed" class="space-y-3">
          <p class="text-[9px] font-black text-slate-400 dark:text-slate-500 uppercase tracking-widest pl-1">Información</p>
          
          <!-- Ayuda & Guía -->
          <div class="bg-slate-50 dark:bg-[#0d0d0d]/20 border border-slate-200/80 dark:border-slate-850 rounded-xl overflow-hidden">
            <button @click="isHelpExpanded = !isHelpExpanded" 
                    class="w-full flex items-center justify-between p-3 text-xs font-bold text-slate-600 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors cursor-pointer select-none">
              <div class="flex items-center gap-2">
                <HelpCircle class="w-4 h-4 text-teal-500/80" />
                <span>¿Cómo usar SIEVA?</span>
              </div>
              <ChevronUp v-if="isHelpExpanded" class="w-3.5 h-3.5" />
              <ChevronDown v-else class="w-3.5 h-3.5" />
            </button>
            
            <div v-show="isHelpExpanded" class="px-3 pb-3 text-[11px] leading-relaxed text-slate-500 dark:text-slate-400 space-y-2 border-t border-slate-200/50 dark:border-slate-800/50 pt-2.5">
              <p>📖 <strong class="text-slate-700 dark:text-slate-300">Rinde Exámenes:</strong> Ingresa a la sección "Exámenes" para ver tus tareas pendientes generadas por tus docentes.</p>
              <p>🎯 <strong class="text-slate-700 dark:text-slate-300">Verifica Resultados:</strong> Al culminar un examen, podrás ver tu calificación y la retroalimentación inteligente detallada pregunta por pregunta.</p>
              <p>📈 <strong class="text-slate-700 dark:text-slate-300">Monitorea tu Progreso:</strong> En la sección "Progreso" observa tus puntajes promedio y tu Nivel de Logro actual en Comunicación y Matemática.</p>
            </div>
          </div>

          <!-- Acerca de -->
          <div class="p-3 bg-slate-50/50 dark:bg-[#0d0d0d]/10 border border-slate-200/60 dark:border-slate-800/40 rounded-xl flex gap-2.5">
            <Info class="w-4 h-4 text-slate-400 dark:text-slate-500 mt-0.5 shrink-0" />
            <div class="text-[10px] leading-relaxed text-slate-400 dark:text-slate-550">
              <p class="font-extrabold uppercase text-[8px] tracking-wider text-slate-400">SIEVA DRE Huánuco</p>
              <p class="mt-0.5">Sistema Integrado de Evaluación de Aula de la Dirección Regional de Educación de Huánuco, Perú.</p>
            </div>
          </div>
        </div>

      </div>

      <!-- Bottom / Logout Section -->
      <div class="px-6 py-6 border-t border-slate-200 dark:border-slate-800/80 bg-slate-50/50 dark:bg-[#0d0d0d]/20"
           :class="isSidebarCollapsed ? 'px-2 py-4 flex justify-center' : 'px-6 py-6'">
        <button 
          @click="handleLogout"
          class="w-full flex items-center justify-center gap-2 rounded-xl border border-red-200 dark:border-red-950/40 text-xs font-bold text-red-600 dark:text-red-400 bg-white dark:bg-[#121212]/60 hover:bg-red-50 dark:hover:bg-red-950/20 hover:text-red-700 dark:hover:text-red-300 shadow-sm hover:shadow transition-all cursor-pointer"
          :class="isSidebarCollapsed ? 'p-0 w-10 h-10' : 'py-3 px-4'"
          :title="isSidebarCollapsed ? 'Cerrar Sesión' : ''"
        >
          <LogOut class="w-4 h-4 shrink-0" />
          <span v-show="!isSidebarCollapsed">Cerrar Sesión</span>
        </button>
      </div>

    </aside>
  </div>
</template>

<style scoped>
/* Scrollbar support */
.scrollbar-thin::-webkit-scrollbar {
  width: 4px;
}
.scrollbar-thin::-webkit-scrollbar-track {
  background: transparent;
}
.scrollbar-thin::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 9999px;
}
.scrollbar-thin::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}
</style>
