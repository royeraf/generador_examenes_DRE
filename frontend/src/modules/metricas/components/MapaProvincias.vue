<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import * as d3 from 'd3'
import type { FeatureCollection, Geometry } from 'geojson'
import type { AvanceItem, EstudianteItem, MetricaMapa, ProvinciaStats } from '../types'
import geojsonRaw from '../data/huanuco_provincias.json'

interface ProvinciaProps {
  id: string
  nombre: string
}

const props = defineProps<{
  avance: AvanceItem[]
  estudiantes: EstudianteItem[]
  metrica: MetricaMapa
  seleccionada: string | null
}>()

const emit = defineEmits<{ select: [nombre: string] }>()

const geojson = geojsonRaw as unknown as FeatureCollection<Geometry, ProvinciaProps>

const host = ref<HTMLDivElement | null>(null)
let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null
let raf = 0
let lastWidth = 0

const gradientId = `mapa-grad-${Math.random().toString(36).slice(2, 9)}`

function isDark(): boolean {
  return document.documentElement.classList.contains('dark')
}

function normalize(text: string): string {
  return text
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
}

function readableText(fill: string): string {
  const color = d3.color(fill)
  if (!color) return '#0f172a'
  const { r, g, b } = color.rgb()
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.6 ? '#0f172a' : '#ffffff'
}

const stats = computed(() => {
  const mapa = new Map<string, ProvinciaStats>()

  const asegurar = (nombre: string): ProvinciaStats => {
    const key = normalize(nombre)
    let item = mapa.get(key)
    if (!item) {
      item = {
        nombre,
        asignaciones: 0,
        completados: 0,
        estudiantes: 0,
        avancePct: 0,
        enAlcance: true,
      }
      mapa.set(key, item)
    }
    return item
  }

  for (const item of props.avance) {
    if (!item.provincia) continue
    const provincia = asegurar(item.provincia)
    provincia.asignaciones += item.asignaciones
    provincia.completados += item.completados
  }

  for (const item of props.estudiantes) {
    if (!item.provincia) continue
    asegurar(item.provincia).estudiantes += item.estudiantes
  }

  for (const provincia of mapa.values()) {
    provincia.avancePct = provincia.asignaciones > 0
      ? Math.min(100, Math.round((provincia.completados / provincia.asignaciones) * 100))
      : 0
  }

  return mapa
})

const maxEstudiantes = computed(() => {
  let max = 0
  for (const provincia of stats.value.values()) {
    if (provincia.estudiantes > max) max = provincia.estudiantes
  }
  return max
})

function colorFor(provincia: ProvinciaStats | undefined, dark: boolean): string {
  if (!provincia?.enAlcance) return dark ? '#1e293b' : '#e2e8f0'

  if (props.metrica === 'avance') {
    return d3.scaleSequential<string>()
      .domain([0, 100])
      .interpolator(
        d3.interpolateRgb(
          dark ? '#134e4a' : '#ccfbf1',
          dark ? '#2dd4bf' : '#0f766e',
        ),
      )(provincia.avancePct)
  }

  const max = Math.max(1, maxEstudiantes.value)
  return d3.scaleSequential<string>()
    .domain([0, max])
    .interpolator(
      d3.interpolateRgb(
        dark ? '#1e1b4b' : '#e0e7ff',
        dark ? '#818cf8' : '#4338ca',
      ),
    )(provincia.estudiantes)
}

function render() {
  const el = host.value
  if (!el) return

  const width = Math.max(el.clientWidth, 280)
  lastWidth = width
  const dark = isDark()
  const compact = width < 460
  const legendHeight = 30
  const height = Math.round(Math.max(300, Math.min(500, width * 0.72)))
  const mapHeight = height - legendHeight

  d3.select(el).selectAll('*').remove()

  const svg = d3.select(el)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('role', 'img')
    .attr('aria-label', 'Mapa de provincias de Huánuco con métricas de SIEVA')
    .style('display', 'block')
    .style('width', '100%')
    .style('height', 'auto')

  const defs = svg.append('defs')
  const gradient = defs.append('linearGradient')
    .attr('id', gradientId)
    .attr('x1', '0%')
    .attr('x2', '100%')
  gradient.append('stop').attr('offset', '0%').attr('stop-color', colorFor({ ...emptyStats(), nombre: '' }, dark))
  gradient.append('stop').attr('offset', '100%').attr('stop-color', colorFor({ ...fullStats(), nombre: '' }, dark))

  const projection = d3.geoMercator()
    .fitExtent([[10, 10], [width - 10, mapHeight - 6]], geojson)

  const path = d3.geoPath(projection)

  const seleccionKey = props.seleccionada ? normalize(props.seleccionada) : null
  const strokeColor = dark ? '#0f172a' : '#ffffff'
  const selectedStroke = dark ? '#a5b4fc' : '#4338ca'

  const provincias = svg.append('g')
    .selectAll<SVGPathElement, (typeof geojson.features)[number]>('path')
    .data(geojson.features)
    .join('path')
    .attr('d', path)
    .attr('fill', (feature) => colorFor(stats.value.get(normalize(feature.properties.nombre)), dark))
    .attr('stroke', (feature) => {
      const key = normalize(feature.properties.nombre)
      return key === seleccionKey ? selectedStroke : strokeColor
    })
    .attr('stroke-width', (feature) => {
      const key = normalize(feature.properties.nombre)
      return key === seleccionKey ? 2.6 : 1
    })
    .attr('stroke-linejoin', 'round')
    .style('cursor', (feature) => (
      stats.value.get(normalize(feature.properties.nombre))?.enAlcance ? 'pointer' : 'default'
    ))

  provincias.append('title')
    .text((feature) => {
      const provincia = stats.value.get(normalize(feature.properties.nombre))
      if (!provincia?.enAlcance) return `${feature.properties.nombre}\nFuera de tu ámbito`
      return [
        feature.properties.nombre,
        `Avance: ${provincia.avancePct}% (${provincia.completados} de ${provincia.asignaciones})`,
        `Estudiantes: ${provincia.estudiantes}`,
      ].join('\n')
    })

  provincias
    .on('mouseenter', function (_, feature) {
      const provincia = stats.value.get(normalize(feature.properties.nombre))
      if (!provincia?.enAlcance) return
      d3.select(this).attr('fill-opacity', 0.82)
    })
    .on('mouseleave', function () {
      d3.select(this).attr('fill-opacity', 1)
    })
    .on('click', (_, feature) => {
      const provincia = stats.value.get(normalize(feature.properties.nombre))
      if (!provincia?.enAlcance) return
      emit('select', feature.properties.nombre)
    })

  // Etiquetas de provincia
  const labels = svg.append('g').attr('pointer-events', 'none')

  geojson.features.forEach((feature) => {
    const [cx, cy] = path.centroid(feature)
    if (!Number.isFinite(cx) || !Number.isFinite(cy)) return

    const provincia = stats.value.get(normalize(feature.properties.nombre))
    const fill = colorFor(provincia, dark)
    const labelFill = readableText(fill)
    // El halo debe contrastar con el texto, no con el fondo del tema: si el
    // texto es blanco, el contorno debe ser oscuro (y viceversa).
    const labelStroke = labelFill === '#ffffff'
      ? (dark ? '#0f172a' : '#134e4a')
      : (dark ? '#f1f5f9' : '#ffffff')

    labels.append('text')
      .attr('x', cx)
      .attr('y', cy)
      .attr('text-anchor', 'middle')
      .attr('dominant-baseline', 'middle')
      .attr('font-size', compact ? 8 : 10)
      .attr('font-weight', 800)
      .attr('fill', labelFill)
      .attr('stroke', labelStroke)
      .attr('stroke-width', 2.4)
      .attr('paint-order', 'stroke')
      .text(feature.properties.nombre)
  })

  // Leyenda
  const legendWidth = Math.min(150, width * 0.42)
  const legendY = height - 16
  const legendMax = props.metrica === 'avance' ? '100%' : String(maxEstudiantes.value)
  const legendMin = props.metrica === 'avance' ? '0%' : '0'

  svg.append('rect')
    .attr('x', 0)
    .attr('y', legendY)
    .attr('width', legendWidth)
    .attr('height', 6)
    .attr('rx', 3)
    .attr('fill', `url(#${gradientId})`)

  svg.append('text')
    .attr('x', 0)
    .attr('y', legendY + 20)
    .attr('fill', dark ? '#94a3b8' : '#64748b')
    .attr('font-size', 9)
    .attr('font-weight', 700)
    .text(legendMin)

  svg.append('text')
    .attr('x', legendWidth)
    .attr('y', legendY + 20)
    .attr('text-anchor', 'end')
    .attr('fill', dark ? '#94a3b8' : '#64748b')
    .attr('font-size', 9)
    .attr('font-weight', 700)
    .text(legendMax)

  svg.append('rect')
    .attr('x', legendWidth + 18)
    .attr('y', legendY - 2)
    .attr('width', 10)
    .attr('height', 10)
    .attr('rx', 3)
    .attr('fill', dark ? '#1e293b' : '#e2e8f0')
    .attr('stroke', dark ? '#334155' : '#cbd5e1')

  svg.append('text')
    .attr('x', legendWidth + 33)
    .attr('y', legendY + 7)
    .attr('fill', dark ? '#94a3b8' : '#64748b')
    .attr('font-size', 9)
    .attr('font-weight', 700)
    .text('Sin datos')
}

function emptyStats(): ProvinciaStats {
  return { nombre: '', asignaciones: 0, completados: 0, estudiantes: 0, avancePct: 0, enAlcance: true }
}

function fullStats(): ProvinciaStats {
  return {
    nombre: '',
    asignaciones: 1,
    completados: 1,
    estudiantes: Math.max(1, maxEstudiantes.value),
    avancePct: 100,
    enAlcance: true,
  }
}

function scheduleRender() {
  if (raf) cancelAnimationFrame(raf)
  raf = requestAnimationFrame(() => {
    raf = 0
    render()
  })
}

function observeTheme() {
  themeObserver?.disconnect()
  themeObserver = new MutationObserver(() => scheduleRender())
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
}

watch(host, (el) => {
  resizeObserver?.disconnect()
  resizeObserver = null
  if (!el) return
  resizeObserver = new ResizeObserver(() => {
    const current = host.value
    if (current && Math.abs(current.clientWidth - lastWidth) > 0.5) {
      scheduleRender()
    }
  })
  resizeObserver.observe(el)
  scheduleRender()
})

watch(
  () => [props.metrica, props.seleccionada, props.avance, props.estudiantes],
  () => {
    if (host.value) scheduleRender()
  },
  { deep: true },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  if (raf) cancelAnimationFrame(raf)
})

observeTheme()
</script>

<template>
  <div ref="host" class="w-full" />
</template>
