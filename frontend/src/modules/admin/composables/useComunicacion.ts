import { ref, shallowRef, computed, onMounted, watch } from 'vue'
import { adminService } from '../../../shared/services/api'
import { showSuccess, showError, showDeleteConfirm } from '../../../shared/utils/swal'
import type { Grado, Capacidad, DesempenoItem } from '../../../shared/types'

export type ComunicacionTab = 'capacidades' | 'desempenos'

export function useComunicacion() {
  const activeTab = shallowRef<ComunicacionTab>('capacidades')
  const loading = shallowRef(false)
  const saving = shallowRef(false)

  const grados = ref<Grado[]>([])
  const capacidades = ref<Capacidad[]>([])
  const desempenos = ref<DesempenoItem[]>([])
  const selectedGradoId = shallowRef<number | null>(null)

  const showModal = shallowRef(false)
  const isEditing = shallowRef(false)
  const editItem = ref<any>(null)

  const currentList = computed(() =>
    activeTab.value === 'capacidades' ? capacidades.value : desempenos.value
  )

  const gradoOptions = computed(() =>
    grados.value.map(g => ({ id: g.id, label: g.nombre }))
  )

  async function loadBase() {
    loading.value = true
    try {
      const [g, c] = await Promise.all([
        adminService.getGrados(),
        adminService.getCapacidades(),
      ])
      grados.value = g
      capacidades.value = c
      if (g.length > 0 && !selectedGradoId.value) {
        selectedGradoId.value = g[0]!.id
      }
      await loadDesempenos()
    } catch (e) {
      console.error('useComunicacion: error loading base data', e)
    } finally {
      loading.value = false
    }
  }

  async function loadDesempenos() {
    if (!selectedGradoId.value) return
    try {
      desempenos.value = await adminService.getDesempenos(selectedGradoId.value)
    } catch (e) {
      console.error('useComunicacion: error loading desempeños', e)
    }
  }

  watch(selectedGradoId, () => {
    if (activeTab.value === 'desempenos') loadDesempenos()
  })

  function openModal(item: any = null) {
    isEditing.value = !!item
    if (item) {
      editItem.value = { ...item }
    } else if (activeTab.value === 'capacidades') {
      editItem.value = { nombre: '', tipo: 'literal', descripcion: '' }
    } else {
      editItem.value = {
        codigo: '',
        descripcion: '',
        grado_id: selectedGradoId.value,
        capacidad_id: capacidades.value[0]?.id ?? null,
      }
    }
    showModal.value = true
  }

  async function saveItem() {
    saving.value = true
    try {
      if (activeTab.value === 'capacidades') {
        if (isEditing.value) await adminService.updateCapacidad(editItem.value.id, editItem.value)
        else await adminService.createCapacidad(editItem.value)
        capacidades.value = await adminService.getCapacidades()
      } else {
        if (isEditing.value) await adminService.updateDesempeno(editItem.value.id, editItem.value)
        else await adminService.createDesempeno(editItem.value)
        await loadDesempenos()
      }
      showModal.value = false
      showSuccess('Guardado', 'El registro se guardó correctamente')
    } catch (e) {
      showError('Error al guardar', String(e))
    } finally {
      saving.value = false
    }
  }

  async function deleteItem(id: number) {
    const ok = await showDeleteConfirm('¿Eliminar este elemento?', 'Esta acción no se puede deshacer')
    if (!ok) return
    try {
      if (activeTab.value === 'capacidades') {
        await adminService.deleteCapacidad(id)
        capacidades.value = await adminService.getCapacidades()
      } else {
        await adminService.deleteDesempeno(id)
        await loadDesempenos()
      }
      showSuccess('Eliminado', 'Registro eliminado correctamente')
    } catch (e) {
      showError('Error al eliminar', String(e))
    }
  }

  onMounted(loadBase)

  return {
    activeTab,
    loading,
    saving,
    grados,
    capacidades,
    desempenos,
    selectedGradoId,
    currentList,
    gradoOptions,
    showModal,
    isEditing,
    editItem,
    loadDesempenos,
    openModal,
    saveItem,
    deleteItem,
  }
}
