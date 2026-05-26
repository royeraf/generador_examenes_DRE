<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import {
  BookOpen, Calculator, Sparkles, GraduationCap, Users, ArrowRight,
  BarChart3, Building2, MapPin, ClipboardList, Loader2, ChevronRight, School
} from 'lucide-vue-next';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../../stores/auth';
import UserBadge from '../../shared/components/UserBadge.vue';
import logoDre from '../../assets/logo.png';

const router = useRouter();
const auth = useAuthStore();
const isLoading = ref(true);

console.log('[HomeView] setup:', {
  hasUser: !!auth.user,
  userRole: auth.userRole,
  isLoading: isLoading.value,
  token: !!auth.token,
  canAccessLecto: auth.canAccessLectosistem,
  isAdmin: auth.isAdmin,
});

onMounted(async () => {
  console.log('[HomeView] onMounted START');
  if (!auth.token) {
    router.push('/login');
    return;
  }
  try {
    await auth.fetchMe();
    console.log('[HomeView] fetchMe OK:', { userRole: auth.userRole, canAccessLecto: auth.canAccessLectosistem, isAdmin: auth.isAdmin });
  } catch (err) {
    console.error('[HomeView] fetchMe FAILED:', err);
    if (!auth.isAuthenticated) { router.push('/login'); return; }
  } finally {
    isLoading.value = false;
  }
});

interface NavItem {
  label: string;
  sub: string;
  icon: any;
  color: string;
  route: string;
}

const managementItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [];
  if (auth.isDocente || auth.isAuxiliar) {
    items.push({ label: 'Mis Estudiantes', sub: 'Registrar y gestionar', icon: Users, color: 'from-teal-400 to-emerald-500', route: '/mis-estudiantes' });
    if (auth.canAccessCodigosClase) items.push({ label: 'Aulas', sub: 'Registro de estudiantes', icon: School, color: 'from-violet-400 to-purple-500', route: '/codigos-clase' });
    if (auth.canAccessAsignaciones) items.push({ label: 'Asignaciones', sub: 'Ver resultados', icon: ClipboardList, color: 'from-violet-400 to-purple-500', route: '/asignaciones' });
    if (auth.canAccessMetricas) items.push({ label: 'Métricas', sub: 'Uso del sistema', icon: BarChart3, color: 'from-violet-500 to-purple-600', route: '/admin/metricas' });
  }
  if (auth.isDirector) {
    items.push({ label: 'Mi Institución', sub: 'Detalle y estadísticas', icon: Building2, color: 'from-teal-400 to-emerald-500', route: '/mi-institucion' });
    items.push({ label: 'Aulas', sub: 'Registro de estudiantes', icon: School, color: 'from-violet-400 to-purple-500', route: '/codigos-clase' });
    items.push({ label: 'Asignaciones', sub: 'Ver resultados', icon: ClipboardList, color: 'from-rose-400 to-pink-500', route: '/asignaciones' });
    items.push({ label: 'Usuarios', sub: 'Docentes y estudiantes', icon: Users, color: 'from-violet-400 to-pink-500', route: '/admin/usuarios' });
    items.push({ label: 'Métricas', sub: 'Uso del sistema', icon: BarChart3, color: 'from-violet-500 to-purple-600', route: '/admin/metricas' });
  }
  if (auth.isResponsableUGEL) {
    items.push({ label: 'Mi UGEL', sub: 'Detalle y estadísticas', icon: MapPin, color: 'from-teal-400 to-emerald-500', route: '/mi-ugel' });
    items.push({ label: 'Instituciones', sub: 'IEs de mi UGEL', icon: Building2, color: 'from-violet-400 to-purple-500', route: '/admin/instituciones' });
    items.push({ label: 'Métricas', sub: 'Uso del sistema', icon: BarChart3, color: 'from-violet-400 to-pink-500', route: '/admin/metricas' });
  }
  if (auth.isEspecialista) {
    if (auth.canAccessGestionCurricular) {
      items.push({ label: 'Gestión Curricular', sub: 'Desempeños por área', icon: BookOpen, color: 'from-teal-400 to-emerald-500', route: '/admin' });
    }
    if (auth.canAccessAdminUgeles) items.push({ label: 'UGELes', sub: 'Gestión', icon: MapPin, color: 'from-teal-500 to-emerald-600', route: '/admin/ugeles' });
    if (auth.canAccessAdminInstituciones) items.push({ label: 'Instituciones', sub: 'IEs del sistema', icon: Building2, color: 'from-violet-400 to-purple-500', route: '/admin/instituciones' });
    if (auth.canAccessAdminUsuarios) items.push({ label: 'Usuarios', sub: 'Gestión de accesos', icon: Users, color: 'from-violet-400 to-pink-500', route: '/admin/usuarios' });
    if (auth.canAccessMetricas) items.push({ label: 'Métricas', sub: 'Uso del sistema', icon: BarChart3, color: 'from-violet-500 to-purple-600', route: '/admin/metricas' });
    if (auth.canAccessCodigosClase) items.push({ label: 'Aulas', sub: 'Registro estudiantil', icon: School, color: 'from-teal-400 to-emerald-500', route: '/codigos-clase' });
    if (auth.canAccessAsignaciones) items.push({ label: 'Asignaciones', sub: 'Ver resultados', icon: ClipboardList, color: 'from-violet-400 to-purple-500', route: '/asignaciones' });
  }
  return items;
});

const hasModules = computed(() => auth.canAccessLectosistem || auth.canAccessMatsistem);
const hasManagement = computed(() => managementItems.value.length > 0);

const saludo = computed(() => {
  const h = new Date().getHours();
  if (h >= 6 && h < 12) return 'Buenos días';
  if (h >= 12 && h < 19) return 'Buenas tardes';
  return 'Buenas noches';
});

const nombreCompleto = computed(() => {
  const u = auth.user;
  if (!u) return '';
  const partes = [u.nombres, u.apellidos].filter(Boolean).join(' ');
  return partes || (u as any).dni || '';
});
</script>

<template>
  <div class="min-h-screen flex flex-col bg-surface transition-colors duration-300">

    <!-- Loading overlay -->
    <div v-if="isLoading"
      class="fixed inset-0 z-[200] flex flex-col items-center justify-center bg-slate-50/95 dark:bg-surface/95">
      <Loader2 class="w-7 h-7 animate-spin text-teal-500 mb-2" />
      <p class="text-sm text-slate-500 dark:text-text-muted">Cargando...</p>
    </div>

    <!-- Subtle background -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
      <div class="absolute top-0 left-1/4 w-96 h-96 bg-teal-400/6 dark:bg-emerald-500/4 rounded-full blur-3xl"></div>
      <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-emerald-400/6 dark:bg-emerald-500/4 rounded-full blur-3xl">
      </div>
    </div>

    <!-- Header -->
    <header
      class="relative z-30 border-b border-slate-300/80 dark:border-slate-800 bg-white/90 dark:bg-surface/90 backdrop-blur-sm shrink-0">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between gap-4">
        <div class="flex items-center gap-3">
          <div class="relative w-8 h-8 shrink-0">
            <div class="absolute -inset-0.5 bg-gradient-to-r from-teal-500 to-emerald-600 rounded-lg blur opacity-25">
            </div>
            <div
              class="absolute inset-0 flex items-center justify-center p-1.5 bg-surface-card rounded-lg border border-slate-300 dark:border-slate-700 overflow-hidden">
              <GraduationCap class="absolute w-4 h-4 text-primary animate-logo-cycle-1" />
              <div class="absolute logo-gradient-display-static w-4 h-4 animate-logo-cycle-2"
                :style="{ 'mask-image': `url(${logoDre})`, '-webkit-mask-image': `url(${logoDre})` }"></div>
            </div>
          </div>
          <div class="hidden sm:flex items-baseline gap-2">
            <span class="shimmer-text text-sm font-black tracking-tight">SIEVA</span>
          </div>
        </div>
        <UserBadge />
      </div>
    </header>

    <!-- Main content -->
    <main v-if="!isLoading" class="relative z-10 flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">

      <!-- Greeting row -->
      <div class="flex items-center justify-between mb-6 sm:mb-8 animate-fade-in">
        <div>
          <p class="text-xs text-slate-400 dark:text-text-subtle mb-0.5">{{ saludo }},</p>
          <h1 class="text-base sm:text-lg font-bold text-text tracking-tight leading-tight">
            {{ nombreCompleto }}
          </h1>
        </div>
        <div class="hidden sm:block text-right">
          <p class="shimmer-text text-xl font-black tracking-tight leading-none">SIEVA</p>
          <p class="text-[11px] text-slate-400 dark:text-text-subtle font-medium mt-0.5 leading-tight">Sistema Integrado
            de Evaluación de Aula</p>
        </div>
      </div>

      <!-- Workspace grid -->
      <div class="grid gap-6" :class="hasManagement ? 'lg:grid-cols-[1fr_300px]' : ''">

        <!-- LEFT: Módulos IA -->
        <div v-if="hasModules" class="space-y-3">
          <div class="flex items-center gap-2 mb-4">
            <Sparkles class="w-4 h-4 text-slate-400" />
            <span class="text-xs font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest">Módulos con
              IA</span>
          </div>

          <div class="grid sm:grid-cols-2 gap-3">

            <!-- LectoSistem -->
            <button v-if="auth.canAccessLectosistem" @click="router.push('/lectosistem')"
              class="module-card-teal cursor-pointer group relative bg-surface rounded-2xl p-5 text-left overflow-hidden flex flex-col gap-4 border border-slate-300 dark:border-slate-800 hover:border-teal-200 dark:hover:border-emerald-700/60 shadow-sm hover:shadow-lg hover:shadow-teal-500/10 transition-all duration-200 animate-slide-up"
              style="animation-delay:0ms">
              <div class="card-overlay absolute inset-0 rounded-2xl pointer-events-none"></div>
              <div class="card-line absolute bottom-0 left-6 right-6 h-[2px] rounded-full pointer-events-none"></div>
              <div
                class="absolute -right-3 -bottom-3 pointer-events-none opacity-[0.05] group-hover:opacity-[0.10] transition-opacity">
                <BookOpen class="w-24 h-24 text-teal-500" />
              </div>
              <div class="flex items-center justify-between relative z-10">
                <div
                  class="card-icon-teal w-10 h-10 rounded-xl bg-gradient-to-br from-teal-400 to-emerald-500 flex items-center justify-center">
                  <BookOpen class="w-5 h-5 text-white" />
                </div>
                <span
                  class="text-[10px] font-bold text-primary bg-teal-50 dark:bg-emerald-900/30 px-2 py-0.5 rounded-full uppercase tracking-wide border border-teal-100 dark:border-emerald-800/50">
                  Comunicación
                </span>
              </div>
              <div class="relative z-10 flex-1">
                <h2
                  class="text-base font-bold text-text mb-1 group-hover:text-teal-600 dark:group-hover:text-emerald-400 transition-colors">
                  LectoSistem</h2>
                <p class="text-xs text-slate-500 dark:text-text-muted leading-relaxed">Genera exámenes de comprensión
                  lectora con niveles literal, inferencial y crítico.</p>
              </div>
              <div class="relative z-10 flex items-center gap-1.5 text-xs font-bold text-primary">
                Ir al módulo
                <ArrowRight class="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>

            <!-- MatSistem -->
            <button v-if="auth.canAccessMatsistem" @click="router.push('/matsistem')"
              class="module-card-indigo cursor-pointer group relative bg-surface rounded-2xl p-5 text-left overflow-hidden flex flex-col gap-4 border border-slate-300 dark:border-slate-800 hover:border-emerald-200 dark:hover:border-emerald-700/60 shadow-sm hover:shadow-lg hover:shadow-emerald-500/10 transition-all duration-200 animate-slide-up"
              style="animation-delay:80ms">
              <div class="card-overlay absolute inset-0 rounded-2xl pointer-events-none"></div>
              <div class="card-line absolute bottom-0 left-6 right-6 h-[2px] rounded-full pointer-events-none"></div>
              <div
                class="absolute -right-3 -bottom-3 pointer-events-none opacity-[0.05] group-hover:opacity-[0.10] transition-opacity">
                <Calculator class="w-24 h-24 text-emerald-500" />
              </div>
              <div class="flex items-center justify-between relative z-10">
                <div
                  class="card-icon-indigo w-10 h-10 rounded-xl bg-gradient-to-br from-violet-400 to-purple-500 flex items-center justify-center">
                  <Calculator class="w-5 h-5 text-white" />
                </div>
                <span
                  class="text-[10px] font-bold text-emerald-600 dark:text-primary bg-emerald-50 dark:bg-emerald-900/30 px-2 py-0.5 rounded-full uppercase tracking-wide border border-emerald-100 dark:border-emerald-800/50">
                  Matemática
                </span>
              </div>
              <div class="relative z-10 flex-1">
                <h2
                  class="text-base font-bold text-text mb-1 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 transition-colors">
                  MatSistem</h2>
                <p class="text-xs text-slate-500 dark:text-text-muted leading-relaxed">Genera prácticas matemáticas por
                  competencia, capacidad y grado escolar.</p>
              </div>
              <div
                class="relative z-10 flex items-center gap-1.5 text-xs font-bold text-emerald-600 dark:text-primary">
                Ir al módulo
                <ArrowRight class="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
              </div>
            </button>

          </div>
        </div>

        <!-- RIGHT: Gestión -->
        <div v-if="hasManagement" class="space-y-2">
          <div class="flex items-center gap-2 mb-4">
            <span class="text-xs font-bold text-slate-400 dark:text-text-subtle uppercase tracking-widest">Gestión</span>
          </div>

          <div
            class="bg-surface rounded-2xl border border-slate-300 dark:border-slate-800 overflow-hidden shadow-sm">
            <button v-for="(item, i) in managementItems" :key="item.route" @click="router.push(item.route)"
              class="mgmt-item cursor-pointer w-full flex items-center gap-3 px-4 py-3 text-left transition-all duration-150 hover:bg-slate-50 dark:hover:bg-slate-800/60 group animate-slide-up"
              :style="`animation-delay:${i * 40 + 160}ms`"
              :class="i < managementItems.length - 1 ? 'border-b border-slate-300 dark:border-slate-800' : ''">
              <div
                class="w-8 h-8 rounded-lg bg-gradient-to-br shrink-0 flex items-center justify-center shadow-sm mgmt-icon"
                :class="item.color">
                <component :is="item.icon" class="w-4 h-4 text-white" />
              </div>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-semibold text-slate-700 dark:text-text leading-tight truncate">{{ item.label
                  }}</p>
                <p class="text-[11px] text-slate-400 dark:text-text-subtle leading-tight">{{ item.sub }}</p>
              </div>
              <ChevronRight
                class="w-4 h-4 text-slate-300 dark:text-text-subtle shrink-0 group-hover:text-slate-400 group-hover:translate-x-0.5 transition-all" />
            </button>
          </div>
        </div>

      </div>

      <!-- Footer -->
      <p
        class="mt-8 text-center text-[11px] text-slate-400 dark:text-text-subtle flex items-center justify-center gap-1.5">
        <Sparkles class="w-3 h-3 animate-sparkle" /> Desarrollado para la Dirección Regional de Educación Huánuco
      </p>

    </main>
  </div>
</template>

<style scoped>
/* ── Entrance animations ──────────────────────────── */
.animate-fade-in {
  animation: fadeIn 0.4s ease-out both;
}

.animate-slide-up {
  animation: slideUp 0.45s cubic-bezier(0.34, 1.4, 0.64, 1) both;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ── Shimmer title ────────────────────────────────── */
.shimmer-text {
  background: linear-gradient(90deg, #14b8a6, #6366f1, #0ea5e9, #8b5cf6, #14b8a6);
  background-size: 250% auto;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: shimmerText 4s linear infinite;
}

.dark .shimmer-text {
  background: linear-gradient(90deg, #6ee7b7, #fbbf24, #34d399, #a7f3d0, #6ee7b7);
  background-size: 250% auto;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  animation: shimmerText 4s linear infinite;
}

@keyframes shimmerText {
  0% {
    background-position: 0% center;
  }

  100% {
    background-position: 250% center;
  }
}

/* ── Module cards ─────────────────────────────────── */
.module-card-teal,
.module-card-indigo {
  will-change: transform;
}

.module-card-teal:hover {
  transform: translateY(-4px);
}

.module-card-indigo:hover {
  transform: translateY(-4px);
}

.module-card-teal .card-overlay {
  background: radial-gradient(ellipse at 15% 20%, rgba(20, 184, 166, 0.08) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.15s;
}

.module-card-teal:hover .card-overlay {
  opacity: 1;
}

.module-card-indigo .card-overlay {
  background: radial-gradient(ellipse at 15% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 60%);
  opacity: 0;
  transition: opacity 0.15s;
}

.module-card-indigo:hover .card-overlay {
  opacity: 1;
}

.module-card-teal .card-line {
  background: linear-gradient(90deg, transparent, rgba(20, 184, 166, 0.8), transparent);
  transform: scaleX(0);
  transition: transform 0.15s ease;
  transform-origin: center;
}

.module-card-teal:hover .card-line {
  transform: scaleX(1);
}

.module-card-indigo .card-line {
  background: linear-gradient(90deg, transparent, rgba(99, 102, 241, 0.8), rgba(168, 85, 247, 0.8), transparent);
  transform: scaleX(0);
  transition: transform 0.15s ease;
  transform-origin: center;
}

.module-card-indigo:hover .card-line {
  transform: scaleX(1);
}

.card-icon-teal {
  box-shadow: 0 4px 8px -2px rgba(20, 184, 166, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.module-card-teal:hover .card-icon-teal {
  transform: scale(1.1) rotate(-5deg);
  box-shadow: 0 0 0 3px rgba(20, 184, 166, 0.2), 0 0 14px rgba(20, 184, 166, 0.35);
}

.card-icon-indigo {
  box-shadow: 0 4px 8px -2px rgba(99, 102, 241, 0.3);
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.module-card-indigo:hover .card-icon-indigo {
  transform: scale(1.1) rotate(-5deg);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2), 0 0 14px rgba(99, 102, 241, 0.35);
}

/* ── Management list ─────────────────────────────── */
.mgmt-icon {
  transition: transform 0.15s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.mgmt-item:hover .mgmt-icon {
  transform: scale(1.12) rotate(-5deg);
}

/* ── Logo cycle ───────────────────────────────────── */
.logo-gradient-display-static {
  background: linear-gradient(135deg, #14b8a6, #4f46e5);
  mask-size: contain;
  -webkit-mask-size: contain;
  mask-repeat: no-repeat;
  -webkit-mask-repeat: no-repeat;
  mask-position: center;
  -webkit-mask-position: center;
}

.dark .logo-gradient-display-static {
  background: linear-gradient(135deg, #34d399, #059669);
}

@keyframes logoCycle1 {

  0%,
  42% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }

  48%,
  92% {
    opacity: 0;
    transform: scale(0.5) rotate(-15deg);
  }

  98%,
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }
}

@keyframes logoCycle2 {

  0%,
  42% {
    opacity: 0;
    transform: scale(0.5) rotate(15deg);
  }

  48%,
  92% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }

  98%,
  100% {
    opacity: 0;
    transform: scale(0.5) rotate(-15deg);
  }
}

.animate-logo-cycle-1 {
  animation: logoCycle1 10s infinite;
}

.animate-logo-cycle-2 {
  animation: logoCycle2 10s infinite;
}

/* ── Sparkle ──────────────────────────────────────── */
.animate-sparkle {
  animation: sparklePulse 2.5s ease-in-out infinite;
}

@keyframes sparklePulse {

  0%,
  100% {
    opacity: 1;
    transform: scale(1) rotate(0deg);
  }

  50% {
    opacity: 0.6;
    transform: scale(1.3) rotate(20deg);
  }
}
</style>
