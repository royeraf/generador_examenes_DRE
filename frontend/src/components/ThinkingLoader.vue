<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';

defineProps<{
    text?: string;
    variant?: 'blue' | 'teal' | 'indigo' | 'purple' | 'rainbow';
}>();

type PatternType = 'stream' | 'pulse-out' | 'scan' | 'converge';

// All cells in a 3x3 grid
const allCells = [
    { row: 0, col: 0, colorIndex: 0 },
    { row: 0, col: 1, colorIndex: 1 },
    { row: 0, col: 2, colorIndex: 2 },
    { row: 1, col: 0, colorIndex: 3 },
    { row: 1, col: 1, colorIndex: 4 },
    { row: 1, col: 2, colorIndex: 5 },
    { row: 2, col: 0, colorIndex: 6 },
    { row: 2, col: 1, colorIndex: 7 },
    { row: 2, col: 2, colorIndex: 8 },
];

// Stream: flows left→right, top→bottom like text being generated
const streamCells = allCells.map(c => ({
    ...c,
    delay: (c.row * 3 + c.col) * 0.1,
}));

// Pulse-out: radiates from center outward (AI thinking)
const pulseOutCells = allCells.map(c => {
    const dist = Math.sqrt((c.row - 1) ** 2 + (c.col - 1) ** 2);
    return { ...c, delay: dist * 0.18 };
});

// Scan: horizontal scan line like processing
const scanCells = allCells.map(c => ({
    ...c,
    delay: c.row * 0.25,
}));

// Converge: corners→edges→center (assembling)
const convergeOrder: [number, number][] = [
    [0, 0], [0, 2], [2, 0], [2, 2],
    [0, 1], [1, 0], [1, 2], [2, 1],
    [1, 1],
];
const convergeCells = convergeOrder.map(([row, col], i) => {
    const cell = allCells.find(c => c.row === row && c.col === col)!;
    return { ...cell, delay: i * 0.09 };
});

const patterns: PatternType[] = ['stream', 'pulse-out', 'scan', 'converge'];
const currentPattern = ref<PatternType>('stream');
let idx = 0;
let timer: ReturnType<typeof setInterval> | null = null;

onMounted(() => {
    timer = setInterval(() => {
        idx = (idx + 1) % patterns.length;
        currentPattern.value = patterns[idx]!;
    }, 2800);
});

onUnmounted(() => {
    if (timer) clearInterval(timer);
});

const cellColors = [
    'color-0', 'color-1', 'color-2',
    'color-3', 'color-4', 'color-5',
    'color-6', 'color-7', 'color-8',
];
</script>

<template>
    <div class="ai-loader">
        <!-- SVG Filter for Glow -->
        <svg class="sr-only" aria-hidden="true">
            <defs>
                <filter id="ai-glow" x="-100%" y="-100%" width="300%" height="300%">
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

        <div class="pill" :class="variant || 'teal'">
            <!-- Spark icon -->
            <div class="spark-icon">
                <svg viewBox="0 0 24 24" fill="none" class="w-[14px] h-[14px]">
                    <path
                        d="M12 2L13.09 8.26L18 6L14.74 10.91L21 12L14.74 13.09L18 18L13.09 15.74L12 22L10.91 15.74L6 18L9.26 13.09L3 12L9.26 10.91L6 6L10.91 8.26L12 2Z"
                        fill="currentColor" />
                </svg>
            </div>

            <!-- 3x3 Grid -->
            <div class="grid-container" :class="variant || 'rainbow'">
                <!-- Stream pattern -->
                <template v-if="currentPattern === 'stream'">
                    <div class="glow-layer">
                        <div v-for="(cell, i) in streamCells" :key="'sg-' + i" class="cell-glow anim-stream"
                            :class="cellColors[cell.colorIndex]"
                            :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1, animationDelay: cell.delay + 's' }" />
                    </div>
                    <div class="cells-layer">
                        <div v-for="(cell, i) in streamCells" :key="'sc-' + i" class="cell anim-stream"
                            :class="cellColors[cell.colorIndex]"
                            :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1, animationDelay: cell.delay + 's' }" />
                    </div>
                </template>

                <!-- Pulse-out pattern -->
                <template v-else-if="currentPattern === 'pulse-out'">
                    <div class="glow-layer">
                        <div v-for="(cell, i) in pulseOutCells" :key="'pg-' + i" class="cell-glow anim-pulse-out"
                            :class="cellColors[cell.colorIndex]"
                            :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1, animationDelay: cell.delay + 's' }" />
                    </div>
                    <div class="cells-layer">
                        <div v-for="(cell, i) in pulseOutCells" :key="'pc-' + i" class="cell anim-pulse-out"
                            :class="cellColors[cell.colorIndex]"
                            :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1, animationDelay: cell.delay + 's' }" />
                    </div>
                </template>

                <!-- Scan pattern -->
                <template v-else-if="currentPattern === 'scan'">
                    <div class="glow-layer">
                        <div v-for="(cell, i) in scanCells" :key="'scg-' + i" class="cell-glow anim-scan"
                            :class="cellColors[cell.colorIndex]"
                            :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1, animationDelay: cell.delay + 's' }" />
                    </div>
                    <div class="cells-layer">
                        <div v-for="(cell, i) in scanCells" :key="'scc-' + i" class="cell anim-scan"
                            :class="cellColors[cell.colorIndex]"
                            :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1, animationDelay: cell.delay + 's' }" />
                    </div>
                </template>

                <!-- Converge pattern -->
                <template v-else>
                    <div class="glow-layer">
                        <div v-for="(cell, i) in convergeCells" :key="'cg-' + i" class="cell-glow anim-converge"
                            :class="cellColors[cell.colorIndex]"
                            :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1, animationDelay: cell.delay + 's' }" />
                    </div>
                    <div class="cells-layer">
                        <div v-for="(cell, i) in convergeCells" :key="'cc-' + i" class="cell anim-converge"
                            :class="cellColors[cell.colorIndex]"
                            :style="{ gridRow: cell.row + 1, gridColumn: cell.col + 1, animationDelay: cell.delay + 's' }" />
                    </div>
                </template>
            </div>

            <!-- Text with cursor -->
            <span class="label">{{ text || 'Generando' }}<span class="cursor" /></span>
        </div>
    </div>
</template>

<style scoped>
.ai-loader {
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
    gap: 10px;
    padding: 10px 18px 10px 12px;
    background: linear-gradient(135deg, #0f172a, #1e293b);
    border-radius: 9999px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 0 20px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

/* ========== SPARK ICON ========== */
.spark-icon {
    flex-shrink: 0;
    animation: spark-pulse 2s ease-in-out infinite;
}

@keyframes spark-pulse {
    0%, 100% { opacity: 0.6; transform: scale(0.9); }
    50% { opacity: 1; transform: scale(1.15); }
}

/* ========== GRID ========== */
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
    filter: url(#ai-glow);
    z-index: 1;
}

.cells-layer {
    z-index: 2;
}

/* ========== STREAM: text-like generation flow ========== */
.anim-stream {
    animation: stream 1.2s ease-in-out infinite;
}

@keyframes stream {
    0% { opacity: 0.05; transform: scale(0.5); filter: brightness(0.2); }
    25%, 35% { opacity: 1; transform: scale(1.15); filter: brightness(2.5); }
    60% { opacity: 0.3; transform: scale(0.85); filter: brightness(0.6); }
    100% { opacity: 0.05; transform: scale(0.5); filter: brightness(0.2); }
}

/* ========== PULSE-OUT: radiates from center ========== */
.anim-pulse-out {
    animation: pulse-out 1.4s ease-out infinite;
}

@keyframes pulse-out {
    0% { opacity: 0.05; transform: scale(0.4); filter: brightness(0.2); }
    30%, 40% { opacity: 1; transform: scale(1.2); filter: brightness(2.4); }
    70% { opacity: 0.2; transform: scale(0.9); filter: brightness(0.5); }
    100% { opacity: 0.05; transform: scale(0.4); filter: brightness(0.2); }
}

/* ========== SCAN: horizontal processing line ========== */
.anim-scan {
    animation: scan 1s ease-in-out infinite;
}

@keyframes scan {
    0% { opacity: 0.05; transform: scaleX(0.3); filter: brightness(0.2); }
    20%, 40% { opacity: 1; transform: scaleX(1.1); filter: brightness(2.2); }
    60% { opacity: 0.4; transform: scaleX(0.9); filter: brightness(0.8); }
    100% { opacity: 0.05; transform: scaleX(0.3); filter: brightness(0.2); }
}

/* ========== CONVERGE: assembling from corners ========== */
.anim-converge {
    animation: converge 1.3s ease-in-out infinite;
}

@keyframes converge {
    0% { opacity: 0; transform: scale(0.3); filter: brightness(0.1); }
    30%, 45% { opacity: 1; transform: scale(1.15); filter: brightness(2.6); }
    70% { opacity: 0.3; transform: scale(0.85); filter: brightness(0.5); }
    100% { opacity: 0; transform: scale(0.3); filter: brightness(0.1); }
}

/* ========== CURSOR ========== */
.cursor::after {
    content: '|';
    animation: blink 0.7s steps(2, start) infinite;
    margin-left: 1px;
    font-weight: 300;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

/* ========== TEXT ========== */
.label {
    font-size: 0.9rem;
    font-weight: 500;
    color: #e2e8f0;
    letter-spacing: 0.01em;
    white-space: nowrap;
}

/* ========== RAINBOW COLORS ========== */
.grid-container.rainbow .color-0 { background: #22d3ee; }
.grid-container.rainbow .color-1 { background: #3b82f6; }
.grid-container.rainbow .color-2 { background: #6366f1; }
.grid-container.rainbow .color-3 { background: #8b5cf6; }
.grid-container.rainbow .color-4 { background: #ec4899; }
.grid-container.rainbow .color-5 { background: #f43f5e; }
.grid-container.rainbow .color-6 { background: #f97316; }
.grid-container.rainbow .color-7 { background: #eab308; }
.grid-container.rainbow .color-8 { background: #22c55e; }

/* ========== SINGLE COLOR VARIANTS ========== */
.grid-container.blue .cell,
.grid-container.blue .cell-glow { background: linear-gradient(135deg, #60a5fa, #38bdf8) !important; }
.grid-container.teal .cell,
.grid-container.teal .cell-glow { background: linear-gradient(135deg, #2dd4bf, #14b8a6) !important; }
.grid-container.indigo .cell,
.grid-container.indigo .cell-glow { background: linear-gradient(135deg, #818cf8, #6366f1) !important; }
.grid-container.purple .cell,
.grid-container.purple .cell-glow { background: linear-gradient(135deg, #c084fc, #a855f7) !important; }

/* Variant-specific accent colors */
.pill.teal .spark-icon { color: #2dd4bf; }
.pill.teal .cursor::after { color: #2dd4bf; }
.pill.teal { border-color: rgba(45, 212, 191, 0.15); }

.pill.blue .spark-icon { color: #60a5fa; }
.pill.blue .cursor::after { color: #60a5fa; }
.pill.blue { border-color: rgba(96, 165, 250, 0.15); }

.pill.indigo .spark-icon { color: #818cf8; }
.pill.indigo .cursor::after { color: #818cf8; }
.pill.indigo { border-color: rgba(129, 140, 248, 0.15); }

.pill.purple .spark-icon { color: #c084fc; }
.pill.purple .cursor::after { color: #c084fc; }
.pill.purple { border-color: rgba(192, 132, 252, 0.15); }

.pill.rainbow .spark-icon { animation: rainbow-color 4s linear infinite; }
.pill.rainbow .cursor::after { color: #a78bfa; }
.pill.rainbow { border-color: rgba(139, 92, 246, 0.12); }

@keyframes rainbow-color {
    0%, 100% { color: #22d3ee; }
    25% { color: #8b5cf6; }
    50% { color: #ec4899; }
    75% { color: #f97316; }
}
</style>
