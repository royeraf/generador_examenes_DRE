<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import * as d3 from 'd3'
import type { AvanceItem } from '../types'

const props = defineProps<{ items: AvanceItem[] }>()

const host = ref<HTMLDivElement | null>(null)
let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null
let raf = 0
let lastWidth = 0

const gradientId = `avance-grad-${Math.random().toString(36).slice(2, 9)}`

function isDark(): boolean {
  return document.documentElement.classList.contains('dark')
}

function truncate(text: string, maxChars: number): string {
  if (maxChars <= 1) return ''
  return text.length <= maxChars ? text : `${text.slice(0, maxChars - 1).trimEnd()}…`
}

function render(animate = true) {
  const el = host.value
  if (!el) return

  const width = Math.max(el.clientWidth, 260)
  lastWidth = width
  const dark = isDark()
  const rowHeight = 58
  const height = props.items.length * rowHeight + 4

  d3.select(el).selectAll('*').remove()

  const svg = d3.select(el)
    .append('svg')
    .attr('width', width)
    .attr('height', height)
    .attr('viewBox', `0 0 ${width} ${height}`)
    .attr('role', 'img')
    .attr('aria-label', 'Avance de evaluaciones por unidad de gestión educativa')
    .style('display', 'block')
    .style('width', '100%')
    .style('height', 'auto')
    .style('overflow', 'visible')

  const defs = svg.append('defs')
  const gradient = defs.append('linearGradient')
    .attr('id', gradientId)
    .attr('x1', '0%')
    .attr('x2', '100%')
  gradient.append('stop').attr('offset', '0%').attr('stop-color', '#2dd4bf')
  gradient.append('stop').attr('offset', '100%').attr('stop-color', '#10b981')

  const trackColor = dark ? '#1e293b' : '#f1f5f9'
  const nameColor = dark ? '#f1f5f9' : '#1e293b'
  const metaColor = dark ? '#94a3b8' : '#94a3b8'
  const pctColor = dark ? '#5eead4' : '#0f766e'

  const rows = svg.append('g')
    .selectAll<SVGGElement, AvanceItem>('g')
    .data(props.items)
    .join('g')
    .attr('transform', (_, i) => `translate(0, ${i * rowHeight})`)

  rows.append('title')
    .text((d) => `${d.nombre}: ${d.completados} de ${d.asignaciones} asignaciones completadas (${d.avance_pct}%)`)

  // Nombre
  rows.append('text')
    .attr('x', 0)
    .attr('y', 14)
    .attr('fill', nameColor)
    .attr('font-size', 12)
    .attr('font-weight', 700)
    .text((d) => truncate(d.nombre, Math.floor((width - 52) / 6.4)))

  // Porcentaje
  rows.append('text')
    .attr('x', width)
    .attr('y', 14)
    .attr('text-anchor', 'end')
    .attr('fill', pctColor)
    .attr('font-size', 12)
    .attr('font-weight', 800)
    .text((d) => `${d.avance_pct}%`)

  // Pista
  rows.append('rect')
    .attr('x', 0)
    .attr('y', 23)
    .attr('width', width)
    .attr('height', 8)
    .attr('rx', 4)
    .attr('fill', trackColor)

  // Barra
  const bars = rows.append('rect')
    .attr('x', 0)
    .attr('y', 23)
    .attr('height', 8)
    .attr('rx', 4)
    .attr('fill', `url(#${gradientId})`)
    .attr('width', animate ? 0 : (d) => (width * d.avance_pct) / 100)

  bars.append('title')
    .text((d) => `${d.completados} / ${d.asignaciones} asignaciones`)

  // Detalle
  rows.append('text')
    .attr('x', 0)
    .attr('y', 45)
    .attr('fill', metaColor)
    .attr('font-size', 10)
    .attr('font-weight', 600)
    .text((d) => {
      const ugel = d.ugel ? `${d.ugel} · ` : ''
      return `${ugel}${d.completados} de ${d.asignaciones} asignaciones completadas`
    })

  if (animate) {
    bars.transition()
      .duration(750)
      .delay((_, i) => i * 70)
      .ease(d3.easeCubicOut)
      .attr('width', (d) => (width * d.avance_pct) / 100)
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
