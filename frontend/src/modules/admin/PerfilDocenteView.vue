<script setup lang="ts">
import { formatFechaLarga } from '../../shared/utils/dateUtils'
import { useAuthStore } from '../../stores/auth'
import { User, MapPin, Building2, BadgeCheck, Shield, CalendarDays, Info } from 'lucide-vue-next'
import Header from '../../shared/components/Header.vue'
import EduBackground from '../../shared/components/EduBackground.vue'

const auth = useAuthStore()

// formatFechaLarga importado de shared/utils/dateUtils

const ROL_LABELS: Record<string, string> = {
  especialista_dre_comunicacion: 'Esp. DRE Comunicación',
  especialista_dre_matematica: 'Esp. DRE Matemática',
  responsable_ugel: 'Responsable UGEL',
  director: 'Director',
  auxiliar: 'Auxiliar',
  docente: 'Docente',
  estudiante: 'Estudiante',
}
function rolLabel(codigo?: string | null) {
  return ROL_LABELS[codigo ?? ''] ?? codigo ?? '—'
}
</script>

<template>
  <div class="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 to-gray-100 dark:from-slate-900 dark:to-slate-950">
    <EduBackground />
    <Header title="Mis Datos" subtitle="Información del Docente" :show-home="true" />

    <div class="flex-1 p-4 md:p-8 relative z-10">
    <div class="max-w-2xl mx-auto">

      <!-- Aviso solo lectura -->
      <div class="flex items-start gap-2.5 bg-blue-50 dark:bg-emerald-900/20 border border-blue-200 dark:border-emerald-700/50 text-blue-700 dark:text-emerald-400 p-3.5 rounded-xl text-sm mb-6">
        <Info class="w-4 h-4 shrink-0 mt-0.5" />
        <span>Esta vista es de solo lectura. Para modificar tus datos, comunícate con un administrador del sistema.</span>
      </div>

      <!-- Tarjeta perfil -->
      <div class="bg-white dark:bg-[#252525] rounded-2xl shadow-xl border border-slate-300 dark:border-slate-700 overflow-hidden">

        <!-- Banner con nombre -->
        <div class="bg-gradient-to-r from-teal-500 to-emerald-600 px-6 py-6 flex items-center gap-4 text-white">
          <div class="w-16 h-16 rounded-2xl bg-white/20 backdrop-blur-sm flex items-center justify-center font-black text-2xl border border-white/20 shadow-inner shrink-0">
            {{ auth.user?.nombres ? auth.user.nombres.charAt(0).toUpperCase() : (auth.user?.dni?.charAt(0) ?? 'U') }}
          </div>
          <div class="min-w-0">
            <h2 class="text-xl font-bold leading-tight truncate">
              {{ [auth.user?.nombres, auth.user?.apellidos].filter(Boolean).join(' ') || 'Sin nombre registrado' }}
            </h2>
            <p class="text-emerald-100 text-sm font-mono mt-0.5">DNI: {{ auth.user?.dni }}</p>
            <span class="inline-flex items-center gap-1 text-[11px] font-bold bg-white/20 px-2 py-0.5 rounded-full mt-1">
              <Shield class="w-3 h-3" /> {{ rolLabel(auth.user?.rol_codigo) }}
            </span>
          </div>
        </div>

        <!-- Datos -->
        <div class="p-6 space-y-5">

          <!-- Información personal -->
          <div>
            <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-3 flex items-center gap-1.5">
              <User class="w-3.5 h-3.5" /> Información personal
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Nombres</p>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ auth.user?.nombres || '—' }}</p>
              </div>
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Apellidos</p>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ auth.user?.apellidos || '—' }}</p>
              </div>
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">DNI</p>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200 font-mono">{{ auth.user?.dni }}</p>
              </div>
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Profesión</p>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ auth.user?.profesion || '—' }}</p>
              </div>
            </div>
          </div>

          <div class="border-t border-slate-300 dark:border-slate-700 pt-5">
            <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-3 flex items-center gap-1.5">
              <Building2 class="w-3.5 h-3.5" /> Institución educativa
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div class="sm:col-span-2">
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Institución Educativa</p>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ auth.user?.institucion_nombre || '—' }}</p>
              </div>
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">UGEL</p>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">{{ auth.user?.ugel_nombre || '—' }}</p>
              </div>
            </div>
          </div>

          <div class="border-t border-slate-300 dark:border-slate-700 pt-5">
            <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-3 flex items-center gap-1.5">
              <MapPin class="w-3.5 h-3.5" /> Ubicación
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Provincia</p>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">
                  <span v-if="auth.user?.provincia_nombre" class="inline-flex items-center gap-1">
                    <MapPin class="w-3 h-3 text-teal-500" /> {{ auth.user.provincia_nombre }}
                  </span>
                  <span v-else>—</span>
                </p>
              </div>
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Distrito</p>
                <p class="text-sm font-medium text-slate-700 dark:text-slate-200">
                  <span v-if="auth.user?.distrito_nombre" class="inline-flex items-center gap-1">
                    <MapPin class="w-3 h-3 text-emerald-500" /> {{ auth.user.distrito_nombre }}
                  </span>
                  <span v-else>—</span>
                </p>
              </div>
            </div>
          </div>

          <div class="border-t border-slate-300 dark:border-slate-700 pt-5">
            <p class="text-[10px] uppercase font-bold text-slate-400 dark:text-slate-500 tracking-wider mb-3 flex items-center gap-1.5">
              <BadgeCheck class="w-3.5 h-3.5" /> Cuenta
            </p>
            <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Estado</p>
                <div class="flex items-center gap-1.5">
                  <div class="w-2 h-2 rounded-full" :class="auth.user?.is_active ? 'bg-green-500' : 'bg-red-500'"></div>
                  <span class="text-sm font-medium text-slate-700 dark:text-slate-200">
                    {{ auth.user?.is_active ? 'Activo' : 'Inactivo' }}
                  </span>
                </div>
              </div>
              <div>
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Rol</p>
                <div class="flex items-center gap-1.5">
                  <Shield class="w-3.5 h-3.5 text-slate-400" />
                  <span class="text-sm font-medium text-slate-700 dark:text-slate-200">
                    {{ rolLabel(auth.user?.rol_codigo) }}
                  </span>
                </div>
              </div>
              <div v-if="auth.user?.fecha_creacion">
                <p class="text-[11px] font-semibold text-slate-400 dark:text-slate-500 mb-0.5">Registrado el</p>
                <div class="flex items-center gap-1.5">
                  <CalendarDays class="w-3.5 h-3.5 text-slate-400" />
                  <span class="text-sm font-medium text-slate-700 dark:text-slate-200">
                    {{ formatFechaLarga(auth.user.fecha_creacion) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

    </div>
    </div>
  </div>
</template>
