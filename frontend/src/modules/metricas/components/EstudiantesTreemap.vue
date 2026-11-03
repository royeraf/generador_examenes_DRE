<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import * as d3 from 'd3'
import type { EstudianteItem } from '../types'

interface TileDatum {
  id: number
  nombre: string
  ugel?: string | null
  estudiantes: number
  children?: TileDatum[]
}

const props = defineProps<{ items: EstudianteItem[] }>()

const MAX_TILES = 12

const host = ref<HTMLDivElement | null>(null)
let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null
let raf = 0
let lastWidth = 0

function isDark(): boolean {
  return document.documentElement.classList.contains('dark')
}

function truncate(text: string, maxChars: number): string {
  if (maxChars <= 1) return ''
  return text.length <= maxChars ? text : `${text.slice(0, maxChars - 1).trimEnd()}…`
}

function readableText(fill: string): string {
  const color = d3.color(fill)
  if (!color) return '#0f172a'
  const { r, g, b } = color.rgb()
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.62 ? '#0f172a' : '#ffffff'
}

function render(animate = true) {
  const el = host.value
  if (!el) return

  const width = Math.max(el.clientWidth, 260)
  lastWidth = width
  const height = Math.round(Math.max(260, Math.min(360, width * 0.66)))
  const dark = isDark()

  d3.select(el).selectAll('*').remove()

  const ordenados = [...props.items]
    .filter((item) => item.estudiantes > 0)
    .sort((a, b) => b.estudiantes - a.estudiantes)

  const visibles = ordenados.slice(0, MAX_TILES)
  const resto = ordenados.slice(MAX_TILES)
  if (resto.length > 0) {
    visibles.push({
      id: -1,
      nombre: `Otras ${resto.length} instituciones`,
      ugel: null,
      estudiantes: resto.reduce((acc, item) => acc + item.estudiantes, 0),
    })
  }

  const total = ordenados.reduce((acc, item) => acc + item.estudiantes, 0)

  const svg = d3.select(el)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('role', 'img')
    .attr('aria-label', `Distribución de ${total} estudiantes entre instituciones educativas`)
    .style('display', 'block')
    .style('width', '100%')
    .style('height', 'auto')

  const rootDatum: TileDatum = {
    id: -1,
    nombre: 'Instituciones',
    estudiantes: 0,
    children: visibles,
  }

  const root = d3.hierarchy<TileDatum>(rootDatum)
    .sum((d) => d.estudiantes)
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0))

  d3.treemap<TileDatum>()
    .size([width, height])
    .paddingInner(4)
    .paddingOuter(0)
    .round(true)(root)

  const leaves = root.leaves() as d3.HierarchyRectangularNode<TileDatum>[]
  const valores = leaves.map((leaf) => leaf.value ?? 0)
  const min = d3.min(valores) ?? 0
  const max = d3.max(valores) ?? 0

  const color = d3.scaleSequential<string>()
    .domain(min === max ? [0, Math.max(1, max)] : [min, max])
    .interpolator(
      d3.interpolateRgb(
        dark ? '#134e4a' : '#99f6e4',
        dark ? '#2dd4bf' : '#0d9488',
      ),
    )

  const tiles = svg.append('g')
    .selectAll<SVGGElement, (typeof leaves)[number]>('g')
    .data(leaves)
    .join('g')
    .attr('transform', (leaf) => `translate(${leaf.x0},${leaf.y0})`)

  const rects = tiles.append('rect')
    .attr('width', (leaf) => Math.max(0, leaf.x1 - leaf.x0))
    .attr('height', (leaf) => Math.max(0, leaf.y1 - leaf.y0))
    .attr('rx', 9)
    .attr('fill', (leaf) => color(leaf.value ?? 0))
    .attr('stroke', dark ? '#0f172a' : '#ffffff')
    .attr('stroke-width', 1)
    .style('cursor', 'default')
    .attr('fill-opacity', animate ? 0 : 1)

  tiles.append('title')
    .text((leaf) => {
      const ugel = leaf.data.ugel ? `${leaf.data.ugel} · ` : ''
      const pct = total > 0 ? Math.round(((leaf.value ?? 0) / total) * 100) : 0
      return `${leaf.data.nombre}\n${ugel}${leaf.value ?? 0} estudiantes (${pct}%)`
    })

  tiles
    .on('mouseenter', function () {
      d3.select(this).select('rect').attr('fill-opacity', 0.82)
    })
    .on('mouseleave', function () {
      d3.select(this).select('rect').attr('fill-opacity', 1)
    })

  // Etiquetas: se omiten cuando el bloque es demasiado pequeño.
  const labels = tiles.append('g').attr('pointer-events', 'none')

  labels.each(function (leaf) {
    const tileWidth = Math.max(0, leaf.x1 - leaf.x0)
    const tileHeight = Math.max(0, leaf.y1 - leaf.y0)
    if (tileWidth < 44 || tileHeight < 22) return

    const fill = color(leaf.value ?? 0)
    const textColor = readableText(fill)
    const group = d3.select(this)
    const maxChars = Math.floor((tileWidth - 16) / 6.4)

    if (tileHeight >= 44 && tileWidth >= 70) {
      group.append('text')
        .attr('x', 9)
        .attr('y', 19)
        .attr('fill', textColor)
        .attr('font-size', 11)
        .attr('font-weight', 800)
        .text(truncate(leaf.data.nombre, maxChars))

      group.append('text')
        .attr('x', 9)
        .attr('y', 35)
        .attr('fill', textColor)
        .attr('font-size', 10)
        .attr('font-weight', 600)
        .attr('fill-opacity', 0.85)
        .text(`${leaf.value ?? 0} estudiantes`)
    } else if (tileHeight >= 30 && tileWidth >= 58) {
      group.append('text')
        .attr('x', 8)
        .attr('y', 18)
        .attr('fill', textColor)
        .attr('font-size', 10)
        .attr('font-weight', 800)
        .text(truncate(leaf.data.nombre, Math.floor((tileWidth - 14) / 5.9)))
    } else {
      group.append('text')
        .attr('x', tileWidth / 2)
        .attr('y', tileHeight / 2 + 3)
        .attr('text-anchor', 'middle')
        .attr('fill', textColor)
        .attr('font-size', 9)
        .attr('font-weight', 800)
        .text(leaf.value ?? 0)
    }
  })

  if (animate) {
    rects.transition()
      .duration(650)
      .delay((_, i) => i * 35)
      .ease(d3.easeCubicOut)
      .attr('fill-opacity', 1)
  }
}

function scheduleRender(animate = true) {
  if (raf) cancelAnimationFrame(raf)
  raf = requestAnimationFrame(() => {
    raf = 0
    render(animate)
  })
}

function observeTheme() {
  themeObserver?.disconnect()
  themeObserver = new MutationObserver(() => scheduleRender(false))
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
}

watch(host, (el) => {
  resizeObserver?.disconnect()
  resizeObserver = null
  if (!el) return
  resizeObserver = new ResizeObserver(() => {
    const current = host.value
    if (current && Math.abs(current.clientWidth - lastWidth) > 0.5) {
      scheduleRender(false)
    }
  })
  resizeObserver.observe(el)
  scheduleRender(true)
})

watch(() => props.items, () => {
  if (host.value) scheduleRender(true)
}, { deep: true })

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
