<script setup lang="ts">
import type { Component } from 'vue'
import {
  BookOpen, Pencil, Star, GraduationCap, Calculator,
  Globe, Trophy, Atom, Layers, FileQuestion,
  Medal, Compass, Microscope, Ruler, PenTool, Shapes,
  Puzzle, Wand2, Infinity, Sigma,
  FlaskConical, Lightbulb, BookMarked, Library, Brain,
  Scroll, NotebookPen, Dna, Music, Palette,
  Map, Clock, Target, Award, Flame,
  Code, Variable, Pi, Triangle, Hexagon,
  Zap, Percent, Hash, Binary, ChartBar,
  BookText, Pen, Beaker, TestTube, AlarmClock,
} from 'lucide-vue-next'

// variant prop kept for API compatibility — not used in the new design
defineProps<{ variant?: string }>()

const COLS = 40
const ROWS = 24
const CELL = 64

const ICONS: Component[] = [
  BookOpen, Pencil, GraduationCap, Calculator, Star,
  Globe, Trophy, Atom, Layers, FileQuestion,
  Medal, Compass, Microscope, Ruler, PenTool, Shapes,
  Puzzle, Wand2, Infinity, Sigma,
  FlaskConical, Lightbulb, BookMarked, Library, Brain,
  Scroll, NotebookPen, Dna, Music, Palette,
  Map, Clock, Target, Award, Flame,
  Code, Variable, Pi, Triangle, Hexagon,
  Zap, Percent, Hash, Binary, ChartBar,
  BookText, Pen, Beaker, TestTube, AlarmClock,
]

const cells = Array.from({ length: COLS * ROWS }, (_, i) => {
  const col = i % COLS
  const row = Math.floor(i / COLS)
  return {
    dark: (col + row) % 2 === 0,
    icon: ICONS[Math.floor(i / 2) % ICONS.length] as Component,
  }
})
</script>

<template>
  <div class="fixed inset-0 overflow-hidden pointer-events-none z-0">
    <div :style="`display:grid;grid-template-columns:repeat(${COLS},${CELL}px);grid-auto-rows:${CELL}px`">
      <div
        v-for="(cell, i) in cells"
        :key="i"
        class="flex items-center justify-center"
        :class="cell.dark ? 'bg-slate-300/55 dark:bg-slate-500/25' : ''"
      >
        <component
          v-if="cell.dark"
          :is="cell.icon"
          class="w-5 h-5 text-slate-500/60 dark:text-text-muted/40"
        />
      </div>
    </div>
  </div>
</template>
