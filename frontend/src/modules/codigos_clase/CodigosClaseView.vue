<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, onMounted } from 'vue'
import { codigosClaseService, organizacionService, type CodigoClase, type CodigoClaseCreatePayload } from '../../shared/services/api'
import type { Grado } from '../../shared/types'
import Navbar from '../../shared/components/Navbar.vue'
import { Plus, Trash2, ToggleLeft, ToggleRight, Copy, AlertCircle, Loader2, QrCode, X, Download, School } from 'lucide-vue-next'
import Swal from 'sweetalert2'
import QRCode from 'qrcode'
const codigos = ref<CodigoClase[]>([])
const grados = ref<Grado[]>([])
const loading = ref(true)
const showModal = ref(false)
const saving = ref(false)
const serverError = ref('')

const form = ref<CodigoClaseCreatePayload>({
  grado_id: 0,
  seccion: '',
  max_estudiantes: 40,
})

async function load() {
  loading.value = true
  try {
    const [c, g] = await Promise.all([
      codigosClaseService.getAll(),
      organizacionService.getGrados(),
    ])
    codigos.value = c
    grados.value = g
  } catch {
    Swal.fire('Error', 'No se pudo cargar los datos', 'error')
  } finally {
    loading.value = false
  }
}

onMounted(load)

function openCreate() {
  form.value = { grado_id: grados.value[0]?.id ?? 0, seccion: '', max_estudiantes: 40 }
  serverError.value = ''
  showModal.value = true
}

async function crear() {
  if (!form.value.grado_id || !form.value.seccion.trim()) {
    serverError.value = 'Grado y sección son requeridos'
    return
  }
  serverError.value = ''
  saving.value = true
  try {
    const nuevo = await codigosClaseService.create(form.value)
    codigos.value.unshift(nuevo)
    showModal.value = false
  } catch (e: any) {
    serverError.value = e.response?.data?.detail ?? 'Error al crear el código'
  } finally {
    saving.value = false
  }
}

async function toggle(codigo: CodigoClase) {
  try {
    const r = await codigosClaseService.toggle(codigo.id)
    codigo.is_active = r.is_active
  } catch {
    Swal.fire('Error', 'No se pudo cambiar el estado', 'error')
  }
}

async function eliminar(codigo: CodigoClase) {
  const confirm = await Swal.fire({
    title: '¿Eliminar código?',
    text: `El código ${codigo.codigo} será eliminado permanentemente.`,
    icon: 'warning',
    showCancelButton: true,
    confirmButtonColor: '#ef4444',
    cancelButtonColor: '#94a3b8',
    confirmButtonText: 'Eliminar',
    cancelButtonText: 'Cancelar',
  })
  if (!confirm.isConfirmed) return
  try {
    await codigosClaseService.delete(codigo.id)
    codigos.value = codigos.value.filter(c => c.id !== codigo.id)
  } catch {
    Swal.fire('Error', 'No se pudo eliminar', 'error')
  }
}

function copiar(codigo: string) {
  navigator.clipboard.writeText(codigo)
  Swal.fire({ toast: true, position: 'top-end', icon: 'success', title: 'Código copiado', timer: 1500, showConfirmButton: false })
}

// formatFecha importado de shared/utils/dateUtils

// ── Modal QR ──────────────────────────────────────────────────────────────────
const qrModal = ref<CodigoClase | null>(null)
const qrDataUrl = ref('')
const qrLoading = ref(false)

function registroUrl(codigo: string): string {
  return `${window.location.origin}/registro?code=${codigo}`
}

async function abrirQR(c: CodigoClase) {
  qrModal.value = c
  qrDataUrl.value = ''
  qrLoading.value = true
  try {
    qrDataUrl.value = await QRCode.toDataURL(registroUrl(c.codigo), {
      width: 512,
      margin: 2,
      color: { dark: '#0f172a', light: '#ffffff' },
      errorCorrectionLevel: 'M',
    })
  } finally {
    qrLoading.value = false
  }
}

function descargarQR() {
  if (!qrDataUrl.value || !qrModal.value) return
  const a = document.createElement('a')
  a.href = qrDataUrl.value
  a.download = `QR-${qrModal.value.codigo}.png`
  a.click()
}
</script>

<template>
  <Navbar title="Aulas" :show-home="true" />

  <main class="max-w-4xl mx-auto px-4 py-8">

    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h2 class="text-2xl font-black text-slate-800 dark:text-white">Mis Aulas</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">Gestiona tus aulas y códigos de acceso para estudiantes</p>
      </div>
      <button @click="openCreate"
        class="flex items-center justify-center gap-2 px-5 py-3 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-2xl shadow-lg shadow-indigo-500/20 hover:-translate-y-0.5 transition-all active:scale-95 cursor-pointer">
        <Plus class="w-5 h-5" /> 
        <span>Nuevo Código</span>
      </button>
    </div>

    <!-- Cargando -->
    <div v-if="loading" class="flex flex-col items-center justify-center py-24">
      <div class="relative w-12 h-12">
        <div class="absolute inset-0 rounded-full border-4 border-slate-300 dark:border-slate-800"></div>
        <div class="absolute inset-0 rounded-full border-4 border-teal-500 border-t-transparent animate-spin"></div>
      </div>
      <p class="mt-4 text-sm font-bold text-slate-400 dark:text-slate-500 tracking-widest uppercase">Cargando Aulas</p>
    </div>

    <!-- Lista vacía -->
    <div v-else-if="codigos.length === 0"
      class="text-center py-20 bg-white dark:bg-slate-900/40 backdrop-blur-xl rounded-2xl border border-slate-300 dark:border-slate-800 shadow-sm group">
      <div class="w-20 h-20 bg-slate-50 dark:bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6 group-hover:scale-110 transition-transform duration-500">
        <School class="w-10 h-10 text-slate-300 dark:text-slate-600" />
      </div>
      <p class="text-slate-800 dark:text-white font-black text-xl">No tienes aulas creadas</p>
      <p class="text-sm text-slate-500 dark:text-slate-400 mt-2 max-w-xs mx-auto">
        Crea una aula para que tus estudiantes puedan registrarse y rendir sus evaluaciones.
      </p>
      <button @click="openCreate" class="mt-8 text-teal-600 dark:text-teal-400 font-bold hover:underline cursor-pointer">
        Comenzar ahora →
      </button>
    </div>

    <!-- Lista de Aulas -->
    <div v-else class="space-y-4">
      
      <!-- Mobile View: Cards -->
      <div class="grid grid-cols-1 gap-4 md:hidden">
        <div v-for="c in codigos" :key="c.id" 
          class="bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl p-5 shadow-sm relative overflow-hidden"
          :class="{ 'opacity-60': !c.is_active }">
          
          <div class="flex justify-between items-start mb-4">
            <div>
              <p class="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-1">{{ c.grado_nombre || `Grado ${c.grado_id}` }}</p>
              <h3 class="text-xl font-black text-slate-800 dark:text-white">Sección {{ c.seccion }}</h3>
            </div>
            <button @click="toggle(c)" class="p-2 bg-slate-50 dark:bg-slate-800 rounded-xl transition-colors cursor-pointer">
              <ToggleRight v-if="c.is_active" class="w-7 h-7 text-teal-500" />
              <ToggleLeft v-else class="w-7 h-7 text-slate-400" />
            </button>
          </div>

          <div class="flex items-center gap-3 bg-slate-50 dark:bg-slate-800/50 p-4 rounded-2xl mb-4 border border-slate-300 dark:border-slate-700/50">
            <div class="flex-1">
              <p class="text-[10px] font-bold text-slate-400 uppercase mb-1">Código de Acceso</p>
              <div class="flex items-center gap-2">
                <span class="font-mono font-black text-2xl text-teal-600 dark:text-teal-400 tracking-widest">{{ c.codigo }}</span>
                <button @click="copiar(c.codigo)" class="p-1.5 text-slate-400 hover:text-teal-500 transition-colors cursor-pointer">
                  <Copy class="w-4 h-4" />
                </button>
              </div>
            </div>
            <div class="text-right">
              <p class="text-[10px] font-bold text-slate-400 uppercase mb-1">Alumnos</p>
              <p class="text-lg font-black text-slate-800 dark:text-white">
                {{ c.total_estudiantes }}<span class="text-sm font-normal text-slate-400">/{{ c.max_estudiantes }}</span>
              </p>
            </div>
          </div>

          <div class="flex items-center justify-between pt-2">
            <span class="text-[10px] font-bold text-slate-400">{{ formatFecha(c.fecha_creacion) }}</span>
            <div class="flex items-center gap-2">
              <button @click="abrirQR(c)" class="flex items-center gap-2 px-4 py-2 bg-teal-500/10 text-teal-600 dark:text-teal-400 font-bold text-xs rounded-xl hover:bg-teal-500 hover:text-white transition-all cursor-pointer">
                <QrCode class="w-4 h-4" />
                <span>Ver QR</span>
              </button>
              <button @click="eliminar(c)" class="p-2 text-red-500 bg-red-50 dark:bg-red-500/10 rounded-xl hover:bg-red-500 hover:text-white transition-all cursor-pointer">
                <Trash2 class="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Desktop View: Table -->
      <div class="hidden md:block bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-slate-50 dark:bg-slate-800/50 text-[11px] font-black text-slate-400 uppercase tracking-[0.1em]">
              <th class="px-6 py-4 text-left">Código Acceso</th>
              <th class="px-6 py-4 text-left">Grado / Sección</th>
              <th class="px-6 py-4 text-center">Estudiantes</th>
              <th class="px-6 py-4 text-center">Estado</th>
              <th class="px-6 py-4 text-left">Fecha Creación</th>
              <th class="px-6 py-4 text-right">Acciones</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100 dark:divide-slate-800">
            <tr v-for="c in codigos" :key="c.id" class="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all duration-200" :class="{ 'opacity-60': !c.is_active }">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <span class="font-mono font-black text-lg text-teal-600 dark:text-teal-400 tracking-widest">{{ c.codigo }}</span>
                  <button @click="copiar(c.codigo)" class="p-1.5 bg-slate-100 dark:bg-slate-800 rounded-lg text-slate-400 hover:text-teal-500 transition-all group cursor-pointer">
                    <Copy class="w-4 h-4 group-hover:scale-110" />
                  </button>
                </div>
              </td>
              <td class="px-6 py-4">
                <div class="flex flex-col">
                  <span class="font-black text-slate-800 dark:text-white">{{ c.grado_nombre || `Grado ${c.grado_id}` }}</span>
                  <span class="text-xs font-bold text-slate-400 uppercase">Sección {{ c.seccion }}</span>
                </div>
              </td>
              <td class="px-6 py-4 text-center">
                <div class="inline-flex items-center px-3 py-1 bg-slate-100 dark:bg-slate-800 rounded-full">
                  <span class="text-sm font-black text-slate-700 dark:text-slate-200">{{ c.total_estudiantes }}</span>
                  <span class="text-[10px] text-slate-400 mx-1">/</span>
                  <span class="text-xs font-bold text-slate-400">{{ c.max_estudiantes }}</span>
                </div>
              </td>
              <td class="px-6 py-4 text-center">
                <button @click="toggle(c)" class="hover:scale-110 transition-transform cursor-pointer">
                  <ToggleRight v-if="c.is_active" class="w-8 h-8 text-teal-500" />
                  <ToggleLeft v-else class="w-8 h-8 text-slate-300 dark:text-slate-700" />
                </button>
              </td>
              <td class="px-6 py-4 text-slate-500 dark:text-slate-400 font-medium">{{ formatFecha(c.fecha_creacion) }}</td>
              <td class="px-6 py-4">
                <div class="flex items-center justify-end gap-2">
                  <button @click="abrirQR(c)" class="p-2.5 bg-teal-50 dark:bg-teal-500/10 text-teal-600 dark:text-teal-400 rounded-xl hover:bg-teal-500 hover:text-white transition-all shadow-sm cursor-pointer" title="Ver QR">
                    <QrCode class="w-5 h-5" />
                  </button>
                  <button @click="eliminar(c)" class="p-2.5 bg-red-50 dark:bg-red-500/10 text-red-500 rounded-xl hover:bg-red-500 hover:text-white transition-all shadow-sm cursor-pointer">
                    <Trash2 class="w-5 h-5" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </main>

  <!-- Modal QR — estilo WhatsApp -->
  <Teleport to="body">
    <Transition name="qr-modal">
      <div v-if="qrModal"
        class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm cursor-pointer"
        @click.self="qrModal = null">

        <!-- Card -->
        <div class="w-full max-w-2xl bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-2xl overflow-hidden">

          <!-- Close bar -->
          <div class="flex justify-end px-5 pt-4 pb-0">
            <button @click="qrModal = null"
              class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all cursor-pointer">
              <X class="w-5 h-5" />
            </button>
          </div>

          <!-- Body: dos columnas -->
          <div class="flex flex-col sm:flex-row items-center sm:items-stretch gap-8 px-8 pb-10 pt-2">

            <!-- Izquierda: instrucciones -->
            <div class="flex-1 flex flex-col justify-center min-w-0">

              <h2 class="text-2xl font-black text-slate-800 dark:text-white mb-7 leading-tight">
                Escanea para unirte
              </h2>

              <!-- Pasos numerados -->
              <div class="space-y-4 mb-7">
                <div class="flex items-start gap-3">
                  <span class="w-6 h-6 rounded-full border-2 border-slate-400 dark:border-slate-500 flex items-center justify-center shrink-0 mt-0.5 text-[11px] font-bold text-slate-500 dark:text-slate-400">1</span>
                  <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">Abre la cámara de tu dispositivo</p>
                </div>
                <div class="flex items-start gap-3">
                  <span class="w-6 h-6 rounded-full border-2 border-slate-400 dark:border-slate-500 flex items-center justify-center shrink-0 mt-0.5 text-[11px] font-bold text-slate-500 dark:text-slate-400">2</span>
                  <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">Apunta al código QR de la pantalla</p>
                </div>
                <div class="flex items-start gap-3">
                  <span class="w-6 h-6 rounded-full border-2 border-slate-400 dark:border-slate-500 flex items-center justify-center shrink-0 mt-0.5 text-[11px] font-bold text-slate-500 dark:text-slate-400">3</span>
                  <p class="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">Completa el registro con tus datos en el formulario</p>
                </div>
              </div>

              <div class="h-px bg-slate-200 dark:bg-slate-700 mb-6" />

              <!-- Info del aula -->
              <p class="text-xs font-bold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">
                {{ qrModal.grado_nombre }} — Sección {{ qrModal.seccion }}
              </p>
              <div class="flex items-center gap-3 mb-3">
                <span class="font-mono font-black text-3xl text-teal-600 dark:text-teal-400 tracking-[0.2em]">{{ qrModal.codigo }}</span>
                <button @click="copiar(qrModal.codigo)"
                  class="p-2 bg-slate-100 dark:bg-slate-800 rounded-xl text-slate-400 hover:text-teal-500 transition-all cursor-pointer">
                  <Copy class="w-4 h-4" />
                </button>
              </div>
              <p class="text-[11px] text-teal-600 dark:text-teal-400 font-mono break-all mb-7 leading-relaxed select-all">
                {{ registroUrl(qrModal.codigo) }}
              </p>

              <!-- Botón descargar -->
              <button @click="descargarQR" :disabled="!qrDataUrl"
                class="self-start flex items-center gap-2 px-5 py-2.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-bold text-sm rounded-xl shadow transition-all hover:-translate-y-0.5 active:scale-95 disabled:opacity-40 cursor-pointer">
                <Download class="w-4 h-4" />
                Descargar imagen
              </button>
            </div>

            <!-- Separador vertical -->
            <div class="hidden sm:block w-px bg-slate-200 dark:bg-slate-700 shrink-0" />

            <!-- Derecha: QR -->
            <div class="flex items-center justify-center shrink-0">
              <div v-if="qrLoading"
                class="w-52 h-52 flex items-center justify-center bg-slate-50 dark:bg-slate-800 rounded-2xl animate-pulse">
                <Loader2 class="w-10 h-10 animate-spin text-teal-500" />
              </div>
              <img v-else-if="qrDataUrl"
                :src="qrDataUrl" alt="QR"
                class="w-52 h-52 rounded-2xl border-8 border-white dark:border-slate-800 shadow-lg bg-white" />
            </div>

          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Modal crear código: Bottom Sheet pattern -->
  <Teleport to="body">
    <Transition name="details-modal">
      <div v-if="showModal" class="fixed inset-0 z-[110] flex items-end sm:items-center justify-center sm:p-4">
        
        <!-- Backdrop -->
        <div class="absolute inset-0 bg-black/50 backdrop-blur-sm cursor-pointer" @click="showModal = false"></div>

        <div class="relative bg-white dark:bg-slate-900 w-full sm:max-w-md max-h-[92dvh] sm:max-h-fit flex flex-col sm:rounded-2xl rounded-t-2xl shadow-2xl overflow-hidden z-10 animate-slide-up">
          
          <!-- Drag handle (mobile) -->
          <div class="sm:hidden flex justify-center pt-3 pb-1 shrink-0 cursor-pointer" @click="showModal = false">
              <div class="w-10 h-1.5 rounded-full bg-slate-200 dark:bg-slate-800"></div>
          </div>

          <div class="px-8 py-6 border-b border-slate-300 dark:border-slate-800 flex items-center justify-between">
            <h2 class="text-xl font-black text-slate-800 dark:text-white tracking-tight">Nueva Aula</h2>
            <button @click="showModal = false" class="p-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 cursor-pointer">
              <X class="w-6 h-6" />
            </button>
          </div>

          <div class="p-8 space-y-6 overflow-y-auto">
            <div v-if="serverError" class="flex items-start gap-3 bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400 text-sm p-4 rounded-2xl border border-red-100 dark:border-red-500/20">
              <AlertCircle class="w-5 h-5 shrink-0" /> 
              <span class="font-bold">{{ serverError }}</span>
            </div>

            <div>
              <label class="block text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2">Grado Académico</label>
              <select v-model="form.grado_id"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-900 dark:text-white outline-none transition-all appearance-none cursor-pointer">
                <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
              </select>
            </div>

            <div>
              <label class="block text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2">Sección</label>
              <select v-model="form.seccion"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-900 dark:text-white outline-none transition-all appearance-none cursor-pointer">
                <option value="" disabled>Seleccione sección...</option>
                <option v-for="s in ['A','B','C','D','E','F','G','H','I','J','Única']" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>

            <div>
              <label class="block text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2">Límite de Estudiantes</label>
              <div class="relative">
                 <input v-model.number="form.max_estudiantes" type="number" min="1" max="200"
                  class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-300 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm font-bold text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
                 <span class="absolute right-5 top-1/2 -translate-y-1/2 text-xs font-black text-slate-400 uppercase">Capacidad</span>
              </div>
            </div>
          </div>

          <div class="px-8 py-6 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-300 dark:border-slate-800 flex flex-col sm:flex-row gap-3">
            <button @click="showModal = false" class="flex-1 px-6 py-4 text-sm font-bold text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-2xl transition-colors cursor-pointer">
              Cancelar
            </button>
            <button @click="crear" :disabled="saving"
              class="flex-1 flex items-center justify-center gap-2 px-6 py-4 bg-gradient-to-r from-teal-500 to-indigo-600 text-white font-black text-sm rounded-2xl shadow-lg shadow-teal-500/20 active:scale-95 transition-all disabled:opacity-50 cursor-pointer">
              <Loader2 v-if="saving" class="w-5 h-5 animate-spin" /> 
              <span>Crear Aula</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.2);
  border-radius: 10px;
}

/* QR Modal animation */
.qr-modal-enter-active, .qr-modal-leave-active {
  transition: opacity 0.2s ease;
}
.qr-modal-enter-active .w-full, .qr-modal-leave-active .w-full {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
.qr-modal-enter-from, .qr-modal-leave-to {
  opacity: 0;
}
.qr-modal-enter-from .w-full {
  transform: scale(0.96) translateY(8px);
  opacity: 0;
}

/* Details Modal / Bottom Sheet Animation */
.details-modal-enter-active, .details-modal-leave-active {
  transition: opacity 0.3s ease;
}
.details-modal-enter-active .relative, .details-modal-leave-active .relative {
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.details-modal-enter-from, .details-modal-leave-to {
  opacity: 0;
}
.details-modal-enter-from .relative, .details-modal-leave-to .relative {
  transform: translateY(100%);
}
@media (min-width: 640px) {
  .details-modal-enter-from .relative, .details-modal-leave-to .relative {
    transform: translateY(0) scale(0.95);
  }
}
</style>
