<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

defineProps<{
    text?: string;
    variant?: 'blue' | 'teal' | 'indigo' | 'purple' | 'rainbow';
}>();

// Pattern types
type PatternType = 'checkerboard' | 'snake' | 'perimeter';

// Colors for each cell position (rainbow effect)
const cellColors = [
    'color-0', // cyan
    'color-1', // blue
    'color-2', // indigo
    'color-3', // purple
    'color-4', // pink
    'color-5', // red
    'color-6', // orange
    'color-7', // yellow
    'color-8', // green
];

// Grid cells for checkerboard pattern (101/010/101)
const checkerboardCells = [
    { row: 0, col: 0, group: 'A', colorIndex: 0 },
    { row: 0, col: 1, group: 'B', colorIndex: 1 },
    { row: 0, col: 2, group: 'A', colorIndex: 2 },
    { row: 1, col: 0, group: 'B', colorIndex: 3 },
    { row: 1, col: 1, group: 'A', colorIndex: 4 },
    { row: 1, col: 2, group: 'B', colorIndex: 5 },
    { row: 2, col: 0, group: 'A', colorIndex: 6 },
    { row: 2, col: 1, group: 'B', colorIndex: 7 },
    { row: 2, col: 2, group: 'A', colorIndex: 8 },
];

// Grid cells for snake pattern (S-shape traversal)
const snakeCells = [
    { row: 0, col: 0, delay: 0, colorIndex: 0 },
    { row: 0, col: 1, delay: 0.11, colorIndex: 1 },
    { row: 0, col: 2, delay: 0.22, colorIndex: 2 },
    { row: 1, col: 2, delay: 0.33, colorIndex: 3 },
    { row: 1, col: 1, delay: 0.44, colorIndex: 4 },
    { row: 1, col: 0, delay: 0.55, colorIndex: 5 },
    { row: 2, col: 0, delay: 0.66, colorIndex: 6 },
    { row: 2, col: 1, delay: 0.77, colorIndex: 7 },
    { row: 2, col: 2, delay: 0.88, colorIndex: 8 },
];

// Grid cells for perimeter pattern (travels around the border + center)
// Sequence: top-left → top-center → top-right → mid-right → bottom-right → 
//           bottom-center → bottom-left → mid-left → center
const perimeterCells = [
    { row: 0, col: 0, delay: 0, colorIndex: 0 },     // top-left
    { row: 0, col: 1, delay: 0.1, colorIndex: 1 },   // top-center
    { row: 0, col: 2, delay: 0.2, colorIndex: 2 },   // top-right
    { row: 1, col: 2, delay: 0.3, colorIndex: 3 },   // mid-right
    { row: 2, col: 2, delay: 0.4, colorIndex: 4 },   // bottom-right
    { row: 2, col: 1, delay: 0.5, colorIndex: 5 },   // bottom-center
    { row: 2, col: 0, delay: 0.6, colorIndex: 6 },   // bottom-left
    { row: 1, col: 0, delay: 0.7, colorIndex: 7 },   // mid-left
    { row: 1, col: 1, delay: 0.8, colorIndex: 8 },   // center (end)
];

const patterns: PatternType[] = ['checkerboard', 'snake', 'perimeter'];
const currentPatternIndex = ref(0);
const currentPattern = ref<PatternType>('checkerboard');
let patternInterval: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
    patternInterval = setInterval(() => {
        currentPatternIndex.value = (currentPatternIndex.value + 1) % patterns.length;
        const nextPattern = patterns[currentPatternIndex.value];
        if (nextPattern) {
            currentPattern.value = nextPattern;
        }
    }, 3000);
});

onUnmounted(() => {
    if (patternInterval) {
        clearInterval(patternInterval);
    }
});
</script>

<template>
    <div class="thinking-loader">
        <!-- SVG Filter for Bloom Effect -->
        <svg class="sr-only" aria-hidden="true">
            <defs>
                <filter id="glow" x="-100%" y="-100%" width="300%" height="300%">
                    <feGaussianBlur stdDeviation="2" result="blur1" />
                    <feGaussianBlur stdDeviation="4" result="blur2" />
                    <feMerge>
                        <feMergeNode in="blur2" />
                        <feMergeNode in="blur1" />
                        <feMergeNode in="SourceGraphic" />
                    </feMerge>
                </filter>
            </defs>
        </svg>

        <!-- Pill container -->
        <div class="pill">
            <!-- Synapse Grid - Checkerboard Pattern -->
            <div v-if="currentPattern === 'checkerboard'" class="grid-container" :class="variant || 'rainbow'">
                <div class="glow-layer">
                    <div v-for="(cell, index) in checkerboardCells" :key="'cb-glow-' + index" class="cell-glow"
                        :class="['group-' + cell.group, cellColors[cell.colorIndex]]"
                        :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1 }"></div>
                </div>
                <div class="cells-layer">
                    <div v-for="(cell, index) in checkerboardCells" :key="'cb-cell-' + index" class="cell"
                        :class="['group-' + cell.group, cellColors[cell.colorIndex]]"
                        :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1 }"></div>
                </div>
            </div>

            <!-- Synapse Grid - Snake Pattern -->
            <div v-else-if="currentPattern === 'snake'" class="grid-container" :class="variant || 'rainbow'">
                <div class="glow-layer">
                    <div v-for="(cell, index) in snakeCells" :key="'snake-glow-' + index" class="cell-glow seq-cell"
                        :class="cellColors[cell.colorIndex]" :style="{
                            gridRow: cell.row + 1,
                            gridColumn: cell.col + 1,
                            animationDelay: cell.delay + 's'
                        }"></div>
                </div>
                <div class="cells-layer">
                    <div v-for="(cell, index) in snakeCells" :key="'snake-cell-' + index" class="cell seq-cell"
                        :class="cellColors[cell.colorIndex]" :style="{
                            gridRow: cell.row + 1,
                            gridColumn: cell.col + 1,
                            animationDelay: cell.delay + 's'
                        }"></div>
                </div>
            </div>

            <!-- Synapse Grid - Perimeter Pattern -->
            <div v-else class="grid-container" :class="variant || 'rainbow'">
                <div class="glow-layer">
                    <div v-for="(cell, index) in perimeterCells" :key="'peri-glow-' + index" class="cell-glow seq-cell"
                        :class="cellColors[cell.colorIndex]" :style="{
                            gridRow: cell.row + 1,
                            gridColumn: cell.col + 1,
                            animationDelay: cell.delay + 's'
                        }"></div>
                </div>
                <div class="cells-layer">
                    <div v-for="(cell, index) in perimeterCells" :key="'peri-cell-' + index" class="cell seq-cell"
                        :class="cellColors[cell.colorIndex]" :style="{
                            gridRow: cell.row + 1,
                            gridColumn: cell.col + 1,
                            animationDelay: cell.delay + 's'
                        }"></div>
                </div>
            </div>

            <!-- Text -->
            <span class="text">{{ text || 'Thinking' }}</span>
        </div>
    </div>
</template>

<style scoped>
.thinking-loader {
    display: inline-flex;
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

.pill {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    padding: 10px 20px 10px 12px;
    background: #000000;
    border-radius: 9999px;
    border: 1px solid rgba(255, 255, 255, 0.1);
}

.grid-container {
    position: relative;
    width: 26px;
    height: 26px;
}

.glow-layer,
.cells-layer {
    position: absolute;
    inset: 0;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    grid-template-rows: repeat(3, 1fr);
    gap: 0;
}

.glow-layer {
    filter: url(#glow);
    z-index: 1;
}

.cells-layer {
    z-index: 2;
}

.cell {
    border-radius: 0;
}

.cell-glow {
    border-radius: 0;
}

/* ========== CHECKERBOARD ANIMATIONS ========== */
.group-A {
    animation: pulse-A 1s ease-in-out infinite;
}

.group-B {
    animation: pulse-B 1s ease-in-out infinite;
}

@keyframes pulse-A {

    0%,
    5% {
        opacity: 1;
        transform: scale(1);
        filter: brightness(1.8);
    }

    45%,
    50% {
        opacity: 1;
        transform: scale(1.1);
        filter: brightness(2);
    }

    55%,
    95% {
        opacity: 0.1;
        transform: scale(0.8);
        filter: brightness(0.3);
    }

    100% {
        opacity: 1;
        transform: scale(1);
        filter: brightness(1.8);
    }
}

@keyframes pulse-B {

    0%,
    5% {
        opacity: 0.1;
        transform: scale(0.8);
        filter: brightness(0.3);
    }

    45%,
    50% {
        opacity: 0.1;
        transform: scale(0.8);
        filter: brightness(0.3);
    }

    55%,
    95% {
        opacity: 1;
        transform: scale(1.1);
        filter: brightness(2);
    }

    100% {
        opacity: 0.1;
        transform: scale(0.8);
        filter: brightness(0.3);
    }
}

/* ========== SEQUENTIAL ANIMATION (Snake & Perimeter) ========== */
.seq-cell {
    animation: seq-pulse 1s ease-in-out infinite;
}

@keyframes seq-pulse {
    0% {
        opacity: 0.1;
        filter: brightness(0.3);
    }

    15%,
    25% {
        opacity: 1;
        filter: brightness(2.2);
    }

    40% {
        opacity: 0.5;
        filter: brightness(1);
    }

    100% {
        opacity: 0.1;
        filter: brightness(0.3);
    }
}

/* ========== RAINBOW COLORS (default) ========== */
.grid-container.rainbow .color-0 {
    background: #22d3ee;
}

/* cyan */
.grid-container.rainbow .color-1 {
    background: #3b82f6;
}

/* blue */
.grid-container.rainbow .color-2 {
    background: #6366f1;
}

/* indigo */
.grid-container.rainbow .color-3 {
    background: #8b5cf6;
}

/* purple */
.grid-container.rainbow .color-4 {
    background: #ec4899;
}

/* pink */
.grid-container.rainbow .color-5 {
    background: #f43f5e;
}

/* rose */
.grid-container.rainbow .color-6 {
    background: #f97316;
}

/* orange */
.grid-container.rainbow .color-7 {
    background: #eab308;
}

/* yellow */
.grid-container.rainbow .color-8 {
    background: #22c55e;
}

/* green */

/* ========== SINGLE COLOR VARIANTS ========== */
.grid-container.blue .cell,
.grid-container.blue .cell-glow {
    background: linear-gradient(135deg, #60a5fa, #38bdf8) !important;
}

.grid-container.teal .cell,
.grid-container.teal .cell-glow {
    background: linear-gradient(135deg, #2dd4bf, #14b8a6) !important;
}

.grid-container.indigo .cell,
.grid-container.indigo .cell-glow {
    background: linear-gradient(135deg, #818cf8, #6366f1) !important;
}

.grid-container.purple .cell,
.grid-container.purple .cell-glow {
    background: linear-gradient(135deg, #c084fc, #a855f7) !important;
}

/* Text styling */
.text {
    font-size: 1rem;
    font-weight: 500;
    color: #ffffff;
    letter-spacing: 0.01em;
}
</style>
