<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { BarChart3, Download, Users, FileText } from 'lucide-vue-next';
import * as d3 from 'd3';
import type { Stats, Estudiante } from '../../types';

// Define Props
interface Props {
    stats: Stats;
    estudiantes: Estudiante[];
}

const props = defineProps<Props>();

// Define Emits
const emit = defineEmits<{
    (e: 'exportarExcel'): void;
}>();

const chartContainer = ref<HTMLDivElement | null>(null);

const updateChart = () => {
    if (!chartContainer.value) return;

    d3.select(chartContainer.value).selectAll('*').remove();

    const total = props.stats.total;

    const data = [
        { label: 'Pre Inicio', value: props.stats['pre-inicio'], color: '#ef4444' },
        { label: 'Inicio', value: props.stats['inicio'], color: '#f97316' },
        { label: 'Proceso', value: props.stats['proceso'], color: '#eab308' },
        { label: 'Satisfactorio', value: props.stats['satisfactorio'], color: '#22c55e' },
        { label: 'Destacado', value: props.stats['destacado'], color: '#6366f1' }
    ].map(d => ({
        ...d,
        percentage: total > 0 ? Math.round((d.value / total) * 100) : 0
    }));

    const margin = { top: 20, right: 20, bottom: 40, left: 50 };
    const width = 350 - margin.left - margin.right;
    const height = 250 - margin.top - margin.bottom;

    const svg = d3.select(chartContainer.value)
        .append('svg')
        .attr('width', '100%')
        .attr('height', '100%')
        .attr('viewBox', `0 0 ${width + margin.left + margin.right} ${height + margin.top + margin.bottom}`)
        .append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

    const x = d3.scaleBand()
        .range([0, width])
        .domain(data.map(d => d.label))
        .padding(0.3);

    const y = d3.scaleLinear()
        .domain([0, 100])
        .range([height, 0]);

    svg.append('g')
        .attr('transform', `translate(0,${height})`)
        .call(d3.axisBottom(x))
        .selectAll('text')
        .attr('transform', 'rotate(-25)')
        .style('text-anchor', 'end')
        .style('font-size', '10px')
        .style('fill', '#64748b');

    svg.append('g')
        .call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d}%`))
        .selectAll('text')
        .style('font-size', '10px')
        .style('fill', '#64748b');

    svg.selectAll('rect')
        .data(data)
        .enter()
        .append('rect')
        .attr('x', d => x(d.label) || 0)
        .attr('y', height)
        .attr('width', x.bandwidth())
        .attr('height', 0)
        .attr('fill', d => d.color)
        .attr('rx', 4)
        .style('opacity', 0.85)
        .style('cursor', 'pointer')
        .transition()
        .duration(800)
        .delay((_, i) => i * 100)
        .attr('y', d => y(d.percentage))
        .attr('height', d => height - y(d.percentage));

    svg.selectAll('.bar-label')
        .data(data)
        .enter()
        .append('text')
        .attr('class', 'bar-label')
        .attr('x', d => (x(d.label) || 0) + x.bandwidth() / 2)
        .attr('y', d => y(d.percentage) - 5)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#334155')
        .style('opacity', 0)
        .text(d => `${d.percentage}%`)
        .transition()
        .duration(800)
        .delay((_, i) => i * 100 + 400)
        .style('opacity', 1);
};

onMounted(() => {
    // Update chart initially
    setTimeout(() => updateChart(), 100);
});

// Watch for changes in stats to update chart
watch(() => props.stats, () => {
    updateChart();
}, { deep: true });

</script>

<template>
    <div class="animate-fadeIn">
        <div class="flex justify-between items-center mb-8">
            <div>
                <h2 class="text-2xl font-bold text-violet-600 dark:text-violet-400 flex items-center gap-3">
                    <BarChart3 class="w-8 h-8" /> Resultados del Análisis
                </h2>
                <p class="text-slate-500 mt-1">Resumen estadístico y gráficos de evaluación</p>
            </div>
            <button @click="emit('exportarExcel')"
                class="px-5 py-3 bg-gradient-to-r from-teal-500 to-emerald-500 text-white rounded-xl hover:from-teal-600 hover:to-emerald-600 font-bold shadow-lg shadow-teal-500/30 flex items-center gap-2 transition-all duration-300 hover:-translate-y-0.5">
                <Download class="w-5 h-5" />
                Exportar Excel
            </button>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <!-- Stat Cards - Educativo -->
            <div
                class="bg-white dark:bg-slate-800 p-5 rounded-2xl border-2 border-teal-100 dark:border-slate-700 shadow-lg relative overflow-hidden group hover:-translate-y-1 transition-all duration-300">
                <div class="absolute top-0 left-0 w-full h-1.5 bg-gradient-to-r from-teal-500 to-sky-500"></div>
                <p class="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2 flex items-center gap-1">
                    <Users class="w-4 h-4" /> Total
                </p>
                <p class="text-3xl font-bold text-teal-600 dark:text-teal-400">{{ stats.total }}</p>
            </div>

            <div v-for="(count, key) in { 'Pre Inicio': stats['pre-inicio'], 'Inicio': stats['inicio'], 'Proceso': stats['proceso'], 'Satisfactorio': stats['satisfactorio'], 'Destacado': stats['destacado'] }"
                :key="key"
                class="bg-white dark:bg-slate-800 p-5 rounded-2xl border-2 dark:border-slate-700 shadow-lg relative overflow-hidden hover:-translate-y-1 transition-all duration-300"
                :class="{
                    'border-red-100 dark:border-red-900/40': key === 'Pre Inicio',
                    'border-orange-100 dark:border-orange-900/40': key === 'Inicio',
                    'border-yellow-100 dark:border-yellow-900/40': key === 'Proceso',
                    'border-green-100 dark:border-green-900/40': key === 'Satisfactorio',
                    'border-violet-100 dark:border-violet-900/40': key === 'Destacado'
                }">
                <div class="absolute top-0 left-0 w-full h-1.5" :class="{
                    'bg-gradient-to-r from-red-500 to-red-400': key === 'Pre Inicio',
                    'bg-gradient-to-r from-orange-500 to-amber-400': key === 'Inicio',
                    'bg-gradient-to-r from-yellow-500 to-amber-400': key === 'Proceso',
                    'bg-gradient-to-r from-green-500 to-emerald-400': key === 'Satisfactorio',
                    'bg-gradient-to-r from-violet-500 to-purple-400': key === 'Destacado'
                }"></div>
                <p class="text-xs text-slate-500 font-bold uppercase tracking-wider mb-2">{{ key }}</p>
                <div class="flex items-end justify-between">
                    <p class="text-3xl font-bold" :class="{
                        'text-red-500': key === 'Pre Inicio',
                        'text-orange-500': key === 'Inicio',
                        'text-yellow-500': key === 'Proceso',
                        'text-green-500': key === 'Satisfactorio',
                        'text-violet-500': key === 'Destacado'
                    }">{{ count }}</p>
                    <span class="text-xs font-bold px-2 py-1 rounded-full" :class="{
                        'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400': key === 'Pre Inicio',
                        'bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400': key === 'Inicio',
                        'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/40 dark:text-yellow-400': key === 'Proceso',
                        'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400': key === 'Satisfactorio',
                        'bg-violet-100 text-violet-600 dark:bg-violet-900/40 dark:text-violet-400': key === 'Destacado'
                    }">
                        {{ stats.total > 0 ? Math.round(count / stats.total * 100) : 0 }}%
                    </span>
                </div>
            </div>
        </div>

        <div class="grid lg:grid-cols-2 gap-6">
            <!-- Chart - Educativo -->
            <div
                class="bg-white dark:bg-slate-800 p-6 rounded-2xl border-2 border-violet-100 dark:border-slate-700 shadow-lg">
                <h3 class="font-bold text-violet-700 dark:text-violet-400 mb-6 flex items-center gap-2 text-lg">
                    <BarChart3 class="w-5 h-5" /> Distribución por Niveles
                </h3>
                <div class="relative h-64 w-full flex items-center justify-center">
                    <div ref="chartContainer" class="w-full h-full flex items-center justify-center"></div>
                </div>

                <!-- Summary Table - Educativo -->
                <div class="mt-6 border-t-2 border-violet-100 dark:border-slate-700 pt-4">
                    <h4 class="text-sm font-bold text-slate-600 dark:text-slate-400 mb-4 flex items-center gap-2">
                        <FileText class="w-4 h-4" /> Resumen de Niveles
                    </h4>
                    <div class="overflow-x-auto rounded-xl border-2 border-slate-100 dark:border-slate-700">
                        <table class="w-full text-sm">
                            <thead>
                                <tr
                                    class="bg-gradient-to-r from-slate-50 to-gray-50 dark:from-slate-900 dark:to-slate-950 border-b-2 border-slate-200 dark:border-slate-700">
                                    <th class="py-3 px-4 text-left font-bold text-slate-700 dark:text-slate-400">
                                        Nivel
                                    </th>
                                    <th class="py-3 px-4 text-center font-bold text-slate-700 dark:text-slate-400">
                                        Cantidad</th>
                                    <th class="py-3 px-4 text-center font-bold text-slate-700 dark:text-slate-400">
                                        Porcentaje</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                                <tr class="hover:bg-red-50/50 dark:hover:bg-red-900/10 transition-colors">
                                    <td class="py-3 px-4 flex items-center gap-3">
                                        <span
                                            class="w-4 h-4 rounded-full bg-gradient-to-r from-red-500 to-red-400 shadow-sm"></span>
                                        <span class="text-slate-700 dark:text-slate-300 font-medium">Pre
                                            Inicio</span>
                                    </td>
                                    <td class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                        {{
                                            stats['pre-inicio'] }}</td>
                                    <td class="py-3 px-4 text-center">
                                        <span
                                            class="px-3 py-1 rounded-full bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400 text-xs font-bold">
                                            {{ stats.total > 0 ? Math.round(stats['pre-inicio'] / stats.total *
                                                100) : 0 }}%
                                        </span>
                                    </td>
                                </tr>
                                <tr class="hover:bg-orange-50/50 dark:hover:bg-orange-900/10 transition-colors">
                                    <td class="py-3 px-4 flex items-center gap-3">
                                        <span
                                            class="w-4 h-4 rounded-full bg-gradient-to-r from-orange-500 to-amber-400 shadow-sm"></span>
                                        <span class="text-slate-700 dark:text-slate-300 font-medium">Inicio</span>
                                    </td>
                                    <td class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                        {{
                                            stats['inicio'] }}</td>
                                    <td class="py-3 px-4 text-center">
                                        <span
                                            class="px-3 py-1 rounded-full bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400 text-xs font-bold">
                                            {{ stats.total > 0 ? Math.round(stats['inicio'] / stats.total * 100)
                                                : 0 }}%
                                        </span>
                                    </td>
                                </tr>
                                <tr class="hover:bg-yellow-50/50 dark:hover:bg-yellow-900/10 transition-colors">
                                    <td class="py-3 px-4 flex items-center gap-3">
                                        <span
                                            class="w-4 h-4 rounded-full bg-gradient-to-r from-yellow-500 to-amber-400 shadow-sm"></span>
                                        <span class="text-slate-700 dark:text-slate-300 font-medium">En
                                            Proceso</span>
                                    </td>
                                    <td class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                        {{
                                            stats['proceso'] }}</td>
                                    <td class="py-3 px-4 text-center">
                                        <span
                                            class="px-3 py-1 rounded-full bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400 text-xs font-bold">
                                            {{ stats.total > 0 ? Math.round(stats['proceso'] / stats.total *
                                                100) : 0 }}%
                                        </span>
                                    </td>
                                </tr>
                                <tr class="hover:bg-green-50/50 dark:hover:bg-green-900/10 transition-colors">
                                    <td class="py-3 px-4 flex items-center gap-3">
                                        <span
                                            class="w-4 h-4 rounded-full bg-gradient-to-r from-green-500 to-emerald-400 shadow-sm"></span>
                                        <span
                                            class="text-slate-700 dark:text-slate-300 font-medium">Satisfactorio</span>
                                    </td>
                                    <td class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                        {{
                                            stats['satisfactorio'] }}</td>
                                    <td class="py-3 px-4 text-center">
                                        <span
                                            class="px-3 py-1 rounded-full bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 text-xs font-bold">
                                            {{ stats.total > 0 ? Math.round(stats['satisfactorio'] / stats.total
                                                * 100) : 0
                                            }}%
                                        </span>
                                    </td>
                                </tr>
                                <tr class="hover:bg-violet-50/50 dark:hover:bg-violet-900/10 transition-colors">
                                    <td class="py-3 px-4 flex items-center gap-3">
                                        <span
                                            class="w-4 h-4 rounded-full bg-gradient-to-r from-violet-500 to-purple-400 shadow-sm"></span>
                                        <span class="text-slate-700 dark:text-slate-300 font-medium">Logro
                                            Destacado</span>
                                    </td>
                                    <td class="py-3 px-4 text-center font-bold text-slate-800 dark:text-white text-lg">
                                        {{
                                            stats['destacado'] }}</td>
                                    <td class="py-3 px-4 text-center">
                                        <span
                                            class="px-3 py-1 rounded-full bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400 text-xs font-bold">
                                            {{ stats.total > 0 ? Math.round(stats['destacado'] / stats.total *
                                                100) : 0 }}%
                                        </span>
                                    </td>
                                </tr>
                            </tbody>
                            <tfoot class="border-t-2 border-slate-300 dark:border-slate-600">
                                <tr class="bg-slate-50 dark:bg-slate-900">
                                    <td class="py-2 px-3 font-bold text-slate-800 dark:text-white">Total</td>
                                    <td class="py-2 px-3 text-center font-bold text-slate-800 dark:text-white">
                                        {{
                                            stats.total }}</td>
                                    <td class="py-2 px-3 text-center font-bold text-slate-800 dark:text-white">
                                        100%</td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Resumen Table -->
            <div
                class="bg-white dark:bg-slate-800 p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm flex flex-col">
                <h3 class="font-bold text-slate-700 dark:text-slate-200 mb-6">Resumen por Estudiante</h3>
                <div
                    class="overflow-y-auto flex-1 max-h-[300px] border rounded-lg border-slate-100 dark:border-slate-700">
                    <table class="w-full text-sm">
                        <thead class="bg-slate-50 dark:bg-slate-900 sticky top-0">
                            <tr>
                                <th class="p-2 text-left font-semibold text-slate-600 dark:text-slate-400">
                                    Estudiante</th>
                                <th class="p-2 text-center font-semibold text-slate-600 dark:text-slate-400">
                                    Nivel</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-slate-100 dark:divide-slate-700">
                            <tr v-for="(est, i) in estudiantes" :key="i">
                                <td class="p-2 text-slate-700 dark:text-slate-300">{{ est.nombre || 'Sin Nombre'
                                }}</td>
                                <td class="p-2 text-center">
                                    <span v-if="est.nivelFinal"
                                        class="px-2 py-0.5 rounded text-[10px] font-bold uppercase" :class="{
                                            'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400': est.nivelFinal === 'PRE INICIO',
                                            'bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400': est.nivelFinal === 'INICIO',
                                            'bg-yellow-100 text-yellow-600 dark:bg-yellow-900/40 dark:text-yellow-400': est.nivelFinal === 'EN PROCESO',
                                            'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400': est.nivelFinal === 'SATISFACTORIO',
                                            'bg-indigo-100 text-indigo-600 dark:bg-indigo-900/40 dark:text-indigo-400': est.nivelFinal === 'LOGRO DESTACADO',
                                        }">
                                        {{ est.nivelFinal }}
                                    </span>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
canvas {
    max-width: 100%;
}
</style>
