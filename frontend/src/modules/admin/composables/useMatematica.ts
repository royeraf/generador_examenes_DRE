import { ref, shallowRef, computed, onMounted, watch } from 'vue'
import { matematicaService } from '../../../shared/services/api'
import { showSuccess, showError, showDeleteConfirm } from '../../../shared/utils/swal'
import type {
  CompetenciaMatematica,
  CapacidadMatConCompetencia,
  DesempenoMatCompleto,
  GradoMatematica,
} from '../../../shared/types/matematica'

export type MatematicaTab = 'competencias' | 'capacidades' | 'desempenos'

export function useMatematica() {
  const activeTab = shallowRef<MatematicaTab>('desempenos')
  const loading = shallowRef(false)
  const saving = shallowRef(false)

  const grados = ref<GradoMatematica[]>([])
  const competencias = ref<CompetenciaMatematica[]>([])
  const capacidades = ref<CapacidadMatConCompetencia[]>([])
  const desempenos = ref<DesempenoMatCompleto[]>([])

  const selectedGradoId = shallowRef<number | null>(null)
  const selectedCompetenciaId = shallowRef<number | null>(null)
  const filterCapCompetenciaId = shallowRef<number | null>(null)

  const showModal = shallowRef(false)
  const isEditing = shallowRef(false)
  const editItem = ref<any>(null)

  const gradoOptions = computed(() =>
    grados.value.map(g => ({ id: g.id, label: g.nombre }))
  )
  const competenciaOptions = computed(() =>
    competencias.value.map(c => ({ id: c.id, label: c.nombre }))
  )
  const competenciaOptionsConTodas = computed(() => [
    { id: null as any, label: 'Todas' },
    ...competencias.value.map(c => ({ id: c.id as any, label: c.nombre })),
  ])
  const capacidadesFiltradas = computed(() =>
    filterCapCompetenciaId.value
      ? capacidades.value.filter(c => c.competencia_id === filterCapCompetenciaId.value)
      : capacidades.value
  )
  const capacidadesPorCompetencia = computed(() =>
    selectedCompetenciaId.value
      ? capacidades.value.filter(c => c.competencia_id === selectedCompetenciaId.value)
      : capacidades.value
  )
  const capacidadModalOptions = computed(() =>
    capacidadesPorCompetencia.value.map(c => ({ id: c.id, label: `Cap. ${c.orden}: ${c.nombre}` }))
  )

  async function loadBase() {
    loading.value = true
    try {
      const [g, c, cap] = await Promise.all([
        matematicaService.getGrados(),
        matematicaService.getCompetencias(),
        matematicaService.getCapacidades(),
      ])
      grados.value = g
      competencias.value = c
      capacidades.value = cap
      if (g.length > 0 && !selectedGradoId.value) selectedGradoId.value = g[0]!.id
      if (c.length > 0 && !selectedCompetenciaId.value) selectedCompetenciaId.value = c[0]!.id
      await loadDesempenos()
    } catch (e) {
      console.error('useMatematica: error loading base data', e)
    } finally {
      loading.value = false
    }
  }

  async function loadDesempenos() {
    if (!selectedGradoId.value || !selectedCompetenciaId.value) return
    try {
      desempenos.value = await matematicaService.getDesempenosPorGradoYCompetencia(
        selectedGradoId.value,
        selectedCompetenciaId.value,
      )
    } catch (e) {
      console.error('useMatematica: error loading desempeños', e)
    }
  }

  watch([selectedGradoId, selectedCompetenciaId], () => {
    if (activeTab.value === 'desempenos') loadDesempenos()
  })

  function openModal(item: any = null) {
    isEditing.value = !!item
    if (item) {
      editItem.value = { ...item }
    } else if (activeTab.value === 'competencias') {
      editItem.value = { codigo: competencias.value.length + 1, nombre: '', descripcion: '' }
    } else if (activeTab.value === 'capacidades') {
      editItem.value = { orden: 1, nombre: '', competencia_id: selectedCompetenciaId.value, descripcion: '' }
    } else {
      editItem.value = {
        codigo: '',
        descripcion: '',
        grado_id: selectedGradoId.value,
        capacidad_id: capacidadesPorCompetencia.value[0]?.id ?? null,
      }
    }
    showModal.value = true
  }

  async function saveItem() {
    if (activeTab.value !== 'desempenos') {
      showModal.value = false
      return
    }
    if (!editItem.value?.codigo || !editItem.value?.descripcion) {
      showError('Campos requeridos', 'Complete todos los campos obligatorios')
      return
    }
    saving.value = true
    try {
      if (isEditing.value) {
        await matematicaService.updateDesempeno(editItem.value.id, {
          codigo: editItem.value.codigo,
          descripcion: editItem.value.descripcion,
          grado_id: editItem.value.grado_id,
          capacidad_id: editItem.value.capacidad_id,
        })
      } else {
        await matematicaService.createDesempeno({
          codigo: editItem.value.codigo,
          descripcion: editItem.value.descripcion,
          grado_id: editItem.value.grado_id,
          capacidad_id: editItem.value.capacidad_id,
        })
      }
      await loadDesempenos()
      showModal.value = false
      showSuccess('Guardado', 'Desempeño guardado correctamente')
    } catch (e: any) {
      showError('Error al guardar', e.response?.data?.detail ?? String(e))
    } finally {
      saving.value = false
    }
  }

  async function deleteItem(id: number) {
    if (activeTab.value !== 'desempenos') return
    const ok = await showDeleteConfirm('¿Eliminar este desempeño?', 'Esta acción no se puede deshacer')
    if (!ok) return
    try {
      await matematicaService.deleteDesempeno(id)
      await loadDesempenos()
      showSuccess('Eliminado', 'Desempeño eliminado correctamente')
    } catch (e: any) {
      showError('Error al eliminar', e.response?.data?.detail ?? String(e))
    }
  }

  onMounted(loadBase)

  return {
    activeTab,
    loading,
    saving,
    grados,
    competencias,
    capacidades,
    desempenos,
    selectedGradoId,
    selectedCompetenciaId,
    filterCapCompetenciaId,
    gradoOptions,
    competenciaOptions,
    competenciaOptionsConTodas,
    capacidadesFiltradas,
    capacidadesPorCompetencia,
    capacidadModalOptions,
    showModal,
    isEditing,
    editItem,
    loadDesempenos,
    openModal,
    saveItem,
    deleteItem,
  }
}
