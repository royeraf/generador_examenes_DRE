<script setup lang="ts">
import { formatFecha } from '../../shared/utils/dateUtils'
import { ref, onMounted } from 'vue'
import { codigosClaseService, organizacionService, type CodigoClase, type CodigoClaseCreatePayload } from '../../shared/services/api'
import type { Grado } from '../../shared/types'
import Header from '../../shared/components/Header.vue'
import { Plus, Trash2, ToggleLeft, ToggleRight, Copy, AlertCircle, Loader2, QrCode, Home, X, Download } from 'lucide-vue-next'
import { useRouter } from 'vue-router'
import Swal from 'sweetalert2'
import QRCode from 'qrcode'

const router = useRouter()
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
  <Header title="Aulas" subtitle="">
    <template #actions-before>
      <button @click="router.push('/')"
        class="p-2.5 rounded-xl bg-white/20 text-white border border-white/30 hover:bg-white/30 dark:bg-slate-700 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-600 transition-all duration-300"
        title="Inicio">
        <Home class="w-4 h-4" />
      </button>
    </template>
  </Header>

  <main class="max-w-4xl mx-auto px-4 py-8">

    <div class="flex items-center justify-between mb-6">
      <div>
        <h2 class="text-lg font-bold text-slate-800 dark:text-white">Mis Aulas</h2>
        <p class="text-sm text-slate-500 dark:text-slate-400">Gestiona tus aulas y códigos de acceso para estudiantes</p>
      </div>
      <button @click="openCreate"
        class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all">
        <Plus class="w-4 h-4" /> Nuevo código
      </button>
    </div>

    <!-- Cargando -->
    <div v-if="loading" class="flex items-center justify-center py-16">
      <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
    </div>

    <!-- Lista vacía -->
    <div v-else-if="codigos.length === 0"
      class="text-center py-16 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700">
      <QrCode class="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
      <p class="text-slate-500 dark:text-slate-400 font-medium">No tienes aulas creadas</p>
      <p class="text-sm text-slate-400 dark:text-slate-500 mt-1">Crea una aula para que tus estudiantes puedan registrarse</p>
    </div>

    <!-- Tabla -->
    <div v-else class="bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 overflow-hidden shadow-sm">
      <table class="w-full text-sm">
        <thead class="bg-slate-50 dark:bg-slate-700/50 text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          <tr>
            <th class="px-4 py-3 text-left">Código</th>
            <th class="px-4 py-3 text-left">Grado / Sección</th>
            <th class="px-4 py-3 text-center">Estudiantes</th>
            <th class="px-4 py-3 text-center">Estado</th>
            <th class="px-4 py-3 text-left">Creado</th>
            <th class="px-4 py-3"></th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
          <tr v-for="c in codigos" :key="c.id" class="hover:bg-slate-50 dark:hover:bg-slate-700/30 transition-colors">
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <span class="font-mono font-bold text-teal-600 dark:text-teal-400 tracking-widest text-base">{{ c.codigo }}</span>
                <button @click="copiar(c.codigo)" class="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200">
                  <Copy class="w-3.5 h-3.5" />
                </button>
              </div>
            </td>
            <td class="px-4 py-3">
              <span class="font-medium text-slate-700 dark:text-slate-200">{{ c.grado_nombre || `Grado ${c.grado_id}` }}</span>
              <span class="text-slate-400 ml-1">Sec. {{ c.seccion }}</span>
            </td>
            <td class="px-4 py-3 text-center">
              <span class="text-slate-600 dark:text-slate-300">{{ c.total_estudiantes }}/{{ c.max_estudiantes }}</span>
            </td>
            <td class="px-4 py-3 text-center">
              <button @click="toggle(c)" class="transition-colors">
                <ToggleRight v-if="c.is_active" class="w-6 h-6 text-teal-500" />
                <ToggleLeft v-else class="w-6 h-6 text-slate-400" />
              </button>
            </td>
            <td class="px-4 py-3 text-slate-500 dark:text-slate-400 text-xs">{{ formatFecha(c.fecha_creacion) }}</td>
            <td class="px-4 py-3">
              <div class="flex items-center gap-2">
                <button @click="abrirQR(c)" class="text-teal-500 hover:text-teal-600 dark:hover:text-teal-400 transition-colors" title="Mostrar QR de registro">
                  <QrCode class="w-4 h-4" />
                </button>
                <button @click="eliminar(c)" class="text-red-400 hover:text-red-600 transition-colors">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

  </main>

  <!-- Modal QR -->
  <Teleport to="body">
    <Transition enter-active-class="transition ease-out duration-200" enter-from-class="opacity-0" enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150" leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-if="qrModal" class="fixed inset-0 z-50 flex flex-col bg-white dark:bg-slate-900">

        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-slate-100 dark:border-slate-800 shrink-0">
          <div>
            <h2 class="text-lg font-bold text-slate-800 dark:text-white">Código QR de Registro</h2>
            <p class="text-sm text-slate-500 dark:text-slate-400">
              {{ qrModal.grado_nombre }} — Sección {{ qrModal.seccion }}
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button @click="descargarQR" :disabled="!qrDataUrl"
              class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-50">
              <Download class="w-4 h-4" /> Descargar
            </button>
            <button @click="qrModal = null" class="p-2 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
              <X class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Layout dos columnas, scrollable si el viewport es pequeño -->
        <div class="flex-1 min-h-0 overflow-y-auto">
          <div class="flex flex-col md:flex-row items-center md:items-start justify-center gap-8 p-6 md:p-10 min-h-full md:min-h-0">

            <!-- Columna izquierda: QR -->
            <div class="flex flex-col items-center gap-3 shrink-0">
              <div v-if="qrLoading" class="w-64 h-64 flex items-center justify-center bg-slate-50 dark:bg-slate-800 rounded-2xl">
                <Loader2 class="w-8 h-8 animate-spin text-teal-500" />
              </div>
              <img v-else-if="qrDataUrl" :src="qrDataUrl" alt="QR de registro"
                class="w-64 h-64 lg:w-72 lg:h-72 rounded-2xl shadow-xl border-4 border-slate-100 dark:border-slate-700" />
              <p class="text-[10px] text-slate-400 dark:text-slate-500 text-center break-all max-w-[16rem]">
                {{ registroUrl(qrModal.codigo) }}
              </p>
            </div>

            <!-- Divisor -->
            <div class="hidden md:block w-px self-stretch bg-slate-200 dark:bg-slate-700 shrink-0 mx-2"></div>
            <div class="block md:hidden w-full max-w-xs h-px bg-slate-200 dark:bg-slate-700 shrink-0"></div>

            <!-- Columna derecha: datos -->
            <div class="flex flex-col justify-center gap-6 w-full max-w-xs md:max-w-sm">

              <!-- Info de la sección como lista tipográfica -->
              <div class="space-y-4">
                <div>
                  <p class="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-0.5">Grado</p>
                  <p class="text-base font-bold text-slate-800 dark:text-white leading-tight">{{ qrModal.grado_nombre }}</p>
                </div>
                <div class="h-px bg-slate-100 dark:bg-slate-800"></div>
                <div class="flex items-center justify-between">
                  <div>
                    <p class="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-0.5">Sección</p>
                    <p class="text-base font-bold text-slate-800 dark:text-white">{{ qrModal.seccion }}</p>
                  </div>
                  <div class="text-right">
                    <p class="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-0.5">Estudiantes</p>
                    <p class="text-base font-bold text-slate-800 dark:text-white">
                      {{ qrModal.total_estudiantes }}<span class="text-sm font-normal text-slate-400"> / {{ qrModal.max_estudiantes }}</span>
                    </p>
                  </div>
                </div>
                <div class="h-px bg-slate-100 dark:bg-slate-800"></div>
                <div>
                  <p class="text-[10px] font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest mb-1">Código de acceso</p>
                  <div class="flex items-center gap-2">
                    <span class="font-mono font-black text-3xl text-teal-600 dark:text-teal-400 tracking-[0.2em]">{{ qrModal.codigo }}</span>
                    <button @click="copiar(qrModal.codigo)" class="text-slate-400 hover:text-teal-500 transition-colors" title="Copiar código">
                      <Copy class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              <!-- Instrucción -->
              <div class="flex items-start gap-2.5 bg-teal-50 dark:bg-teal-900/20 rounded-xl px-3 py-3 border border-teal-100 dark:border-teal-800/30">
                <QrCode class="w-3.5 h-3.5 text-teal-500 shrink-0 mt-0.5" />
                <p class="text-xs text-slate-600 dark:text-slate-300">
                  Proyecta este QR en clase. Los estudiantes lo escanean y se registran directamente en tu sección.
                </p>
              </div>

            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Modal crear código -->
  <Teleport to="body">
    <Transition enter-active-class="transition ease-out duration-200" enter-from-class="opacity-0" enter-to-class="opacity-100"
      leave-active-class="transition ease-in duration-150" leave-from-class="opacity-100" leave-to-class="opacity-0">
      <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" @click.self="showModal = false">
        <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl w-full max-w-sm">
          <div class="p-5 border-b border-slate-100 dark:border-slate-700">
            <h2 class="text-base font-bold text-slate-800 dark:text-white">Nueva Aula</h2>
          </div>
          <div class="p-5 space-y-4">
            <div v-if="serverError" class="flex items-start gap-2 bg-red-50 dark:bg-red-900/20 text-red-600 text-xs p-3 rounded-xl border border-red-100">
              <AlertCircle class="w-3.5 h-3.5 shrink-0 mt-0.5" /> {{ serverError }}
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Grado</label>
              <select v-model="form.grado_id"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50">
                <option v-for="g in grados" :key="g.id" :value="g.id">{{ g.nombre }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Sección</label>
              <select v-model="form.seccion"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all">
                <option value="" disabled>Seleccione sección...</option>
                <option value="A">A</option>
                <option value="B">B</option>
                <option value="C">C</option>
                <option value="D">D</option>
                <option value="E">E</option>
                <option value="F">F</option>
                <option value="G">G</option>
                <option value="H">H</option>
                <option value="I">I</option>
                <option value="J">J</option>
                <option value="Única">Única</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-bold text-slate-600 dark:text-slate-300 mb-1">Máx. estudiantes</label>
              <input v-model.number="form.max_estudiantes" type="number" min="1" max="200"
                class="w-full bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm text-slate-900 dark:text-white outline-none focus:ring-2 focus:ring-teal-500/50 focus:border-teal-500 transition-all" />
            </div>
          </div>
          <div class="flex justify-end gap-2 px-5 py-4 border-t border-slate-100 dark:border-slate-700">
            <button @click="showModal = false" class="px-4 py-2 text-sm font-medium text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-xl transition-colors">
              Cancelar
            </button>
            <button @click="crear" :disabled="saving"
              class="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-500 to-indigo-600 hover:from-teal-600 hover:to-indigo-700 text-white font-bold text-sm rounded-xl shadow transition-all disabled:opacity-70">
              <Loader2 v-if="saving" class="w-3.5 h-3.5 animate-spin" /> Crear
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
