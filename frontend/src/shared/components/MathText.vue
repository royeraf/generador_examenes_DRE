<script setup lang="ts">
/**
 * Renderiza texto que puede contener LaTeX delimitado con $...$ (en línea)
 * o $$...$$ / \[...\] / \(...\) (defensivo, por si el modelo los usa).
 *
 * El texto plano SIEMPRE se escapa antes de insertarse; solo la salida de
 * KaTeX (con trust:false) entra como HTML. Una fórmula inválida degrada a
 * texto plano en vez de romper la vista.
 */
import { computed } from 'vue'
import katex from 'katex'

const props = withDefaults(
  defineProps<{
    text?: string | null
    as?: string
  }>(),
  {
    text: '',
    as: 'span',
  }
)

// Orden de alternativas importa: bloque antes que en línea.
// El grupo $...$ excluye llaves vacías, espacios en los bordes y saltos de
// línea para no confundir signos de moneda (S/ ... o "$ 25 y $ 30") con matemática.
const MATH_RE = /\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\\\(([\s\S]+?)\\\)|\$(?!\s)([^$\n]+?)(?<!\s)\$/g

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderExpr(expr: string, displayMode: boolean, rawMatch: string): string {
  try {
    return katex.renderToString(expr.trim(), {
      throwOnError: false,
      displayMode,
      strict: 'ignore',
      trust: false,
      output: 'htmlAndMathml',
    })
  } catch {
    return escapeHtml(rawMatch)
  }
}

const html = computed(() => {
  const source = props.text ?? ''
  if (!source) return ''

  let result = ''
  let lastIndex = 0
  let match: RegExpExecArray | null

  MATH_RE.lastIndex = 0
  while ((match = MATH_RE.exec(source)) !== null) {
    const [full, display, bracketDisplay, paren, inline] = match
    result += escapeHtml(source.slice(lastIndex, match.index))

    if (display !== undefined) {
      result += renderExpr(display, true, full)
    } else if (bracketDisplay !== undefined) {
      result += renderExpr(bracketDisplay, true, full)
    } else if (paren !== undefined) {
      result += renderExpr(paren, false, full)
    } else if (inline !== undefined) {
      result += renderExpr(inline, false, full)
    }

    lastIndex = match.index + full.length
  }
  result += escapeHtml(source.slice(lastIndex))

  return result
})
</script>

<template>
  <component :is="as" v-html="html" />
</template>
