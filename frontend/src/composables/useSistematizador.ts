import { ref, shallowRef, reactive, computed, watch } from 'vue';
import type { Grado, DesempenoItem, NivelConfig, Estudiante, Stats } from '../types';
import desempenosService from '../services/api';
import * as d3 from 'd3';
import * as XLSX from 'xlsx';
import { Toast, showError, showWarning } from '../utils/swal';

export function useSistematizador() {
    const grados = ref<Grado[]>([]);
    const selectedGradoId = shallowRef<number | null>(null);
    const loadingGrados = shallowRef(false);

    // Desempeños fetched from DB for the selected grade
    const availableDesempenos = ref<DesempenoItem[]>([]);
    const loadingDesempenos = shallowRef(false);

    const activeTab = shallowRef<'config' | 'registro' | 'resultados'>('config');

    // Configuración de Desempeños
    const niveles = reactive<Record<string, NivelConfig>>({
        'pre-inicio': {
            nombre: 'PRE INICIO',
            descripcion: '(Literal, Inferencial o Crítico)',
            color: '#ef4444',
            bg: 'rgba(239, 68, 68, 0.15)',
            key: 'pre-inicio',
            preguntas: []
        },
        'inicio': {
            nombre: 'INICIO',
            descripcion: '(Literal)',
            color: '#f97316',
            bg: 'rgba(249, 115, 22, 0.15)',
            key: 'inicio',
            preguntas: []
        },
        'proceso': {
            nombre: 'EN PROCESO',
            descripcion: '(Inferencial)',
            color: '#eab308',
            bg: 'rgba(234, 179, 8, 0.15)',
            key: 'proceso',
            preguntas: []
        },
        'satisfactorio': {
            nombre: 'SATISFACTORIO',
            descripcion: '(Crítico)',
            color: '#22c55e',
            bg: 'rgba(34, 197, 94, 0.15)',
            key: 'satisfactorio',
            preguntas: []
        },
        'destacado': {
            nombre: 'LOGRO DESTACADO',
            descripcion: '(Literal, Inferencial o Crítico)',
            color: '#6366f1',
            bg: 'rgba(99, 102, 241, 0.15)',
            key: 'destacado',
            preguntas: []
        }
    });

    const competencia = shallowRef('Lee diversos tipos de textos escritos en su lengua materna');

    // Students Data
    const estudiantes = ref<Estudiante[]>([]);
    const chartContainer = ref<HTMLDivElement | null>(null);

    const gradosPorNivel = computed(() => {
        return {
            primaria: grados.value.filter(g => g.nivel === 'primaria'),
            secundaria: grados.value.filter(g => g.nivel === 'secundaria')
        };
    });

    const gradoOptions = computed(() => {
        const options: { id: number; label: string; group: string }[] = [];
        gradosPorNivel.value.primaria.forEach(g => {
            options.push({ id: g.id, label: `${g.numero}° Primaria`, group: 'Primaria' });
        });
        gradosPorNivel.value.secundaria.forEach(g => {
            options.push({ id: g.id, label: `${g.numero}° Secundaria`, group: 'Secundaria' });
        });
        return options;
    });

    const desempenoOptions = computed(() => {
        return availableDesempenos.value.map(d => ({
            id: d.id,
            label: `${d.codigo} - ${d.descripcion.substring(0, 100)}${d.descripcion.length > 100 ? '...' : ''}`,
            group: d.capacidad_tipo ? d.capacidad_tipo.toUpperCase() : 'General'
        }));
    });

    const stats = computed<Stats>(() => {
        const s = {
            total: estudiantes.value.length,
            'pre-inicio': 0,
            'inicio': 0,
            'proceso': 0,
            'satisfactorio': 0,
            'destacado': 0
        };

        estudiantes.value.forEach(est => {
            if (est.nivelFinal) {
                const nivel = est.nivelFinal.toLowerCase().replace(/ /g, '-').replace('en-', '');
                if (nivel === 'pre-inicio') s['pre-inicio']++;
                else if (nivel === 'inicio') s['inicio']++;
                else if (nivel === 'proceso') s['proceso']++;
                else if (nivel === 'satisfactorio') s['satisfactorio']++;
                else if (nivel === 'destacado' || nivel === 'logro-destacado') s['destacado']++;
            }
        });
        return s;
    });

    const loadGrados = async () => {
        loadingGrados.value = true;
        try {
            grados.value = await desempenosService.getGrados();
            if (grados.value.length > 0 && !selectedGradoId.value) {
                selectedGradoId.value = grados.value[0]?.id ?? null;
            }
        } catch (e) {
            console.error("Error loading degrees", e);
        } finally {
            loadingGrados.value = false;
        }
    };

    const loadDesempenos = async () => {
        if (!selectedGradoId.value) return;
        loadingDesempenos.value = true;
        try {
            availableDesempenos.value = await desempenosService.getDesempenosPorGrado(selectedGradoId.value);
        } catch (e) {
            console.error("Error loading performances", e);
        } finally {
            loadingDesempenos.value = false;
        }
    };

    watch(selectedGradoId, () => {
        Object.keys(niveles).forEach(key => {
            if (niveles[key]) {
                niveles[key].preguntas = [];
            }
        });
        loadDesempenos();
    });

    const addPregunta = (nivelKey: string) => {
        if (niveles[nivelKey]) {
            niveles[nivelKey].preguntas.push({
                descripcion: '',
                desempenoId: null,
                clave: ''
            });
        }
    };

    const removePregunta = (nivelKey: string, index: number) => {
        if (niveles[nivelKey]) {
            niveles[nivelKey].preguntas.splice(index, 1);
        }
    };

    const onDesempenoSelect = (nivelKey: string, index: number, id: number | null) => {
        if (niveles[nivelKey]) {
            const preg = niveles[nivelKey].preguntas[index];
            if (preg) {
                preg.desempenoId = id;
                if (id) {
                    const found = availableDesempenos.value.find(d => d.id === id);
                    if (found) {
                        preg.descripcion = found.descripcion;
                    }
                }
            }
        }
    };

    const addEstudiante = () => {
        estudiantes.value.push({
            nombre: '',
            respuestas: {},
            puntajes: {},
            nivelFinal: null
        });
    };

    const removeEstudiante = (index: number) => {
        estudiantes.value.splice(index, 1);
    };

    const determinarNivelFinal = (est: Estudiante) => {
        const nivelesOrden = ['destacado', 'satisfactorio', 'proceso', 'inicio', 'pre-inicio'];
        const nombres = {
            'destacado': 'LOGRO DESTACADO',
            'satisfactorio': 'SATISFACTORIO',
            'proceso': 'EN PROCESO',
            'inicio': 'INICIO',
            'pre-inicio': 'PRE INICIO'
        };

        for (const nivelKey of nivelesOrden) {
            if (est.puntajes && est.puntajes[nivelKey]) {
                const puntaje = est.puntajes[nivelKey];
                const nivelConfig = niveles[nivelKey];

                if (nivelConfig && nivelConfig.preguntas.length > 0 && puntaje.correctas > 0) {
                    if (puntaje.porcentaje >= 60) {
                        return nombres[nivelKey as keyof typeof nombres];
                    }
                }
            }
        }
        return nombres['pre-inicio'];
    };

    const updateChart = () => {
        if (!chartContainer.value) return;

        d3.select(chartContainer.value).selectAll('*').remove();

        const total = stats.value.total;

        const data = [
            { label: 'Pre Inicio', value: stats.value['pre-inicio'], color: '#ef4444' },
            { label: 'Inicio', value: stats.value['inicio'], color: '#f97316' },
            { label: 'Proceso', value: stats.value['proceso'], color: '#eab308' },
            { label: 'Satisfactorio', value: stats.value['satisfactorio'], color: '#22c55e' },
            { label: 'Destacado', value: stats.value['destacado'], color: '#6366f1' }
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

    const calcularResultados = () => {
        if (estudiantes.value.length === 0) {
            showWarning('Sin estudiantes', 'Agrega estudiantes antes de calcular');
            return;
        }
        const nivelesKeys = ['pre-inicio', 'inicio', 'proceso', 'satisfactorio', 'destacado'];

        estudiantes.value.forEach(est => {
            if (!est.respuestas) est.respuestas = {};
            est.puntajes = est.puntajes || {};

            nivelesKeys.forEach(nivelKey => {
                const nivelConfig = niveles[nivelKey];
                if (nivelConfig) {
                    const preguntas = nivelConfig.preguntas;
                    const respuestas = est.respuestas[nivelKey] || [];

                    let correctas = 0;
                    preguntas.forEach((pregunta, idx) => {
                        if (respuestas[idx] && respuestas[idx] === pregunta.clave) {
                            correctas++;
                        }
                    });

                    if (est.puntajes) {
                        est.puntajes[nivelKey] = {
                            correctas,
                            total: preguntas.length,
                            porcentaje: preguntas.length > 0 ? (correctas / preguntas.length * 100) : 0
                        };
                    }
                }
            });

            est.nivelFinal = determinarNivelFinal(est);
        });
        updateChart();
        Toast.fire({ icon: 'success', title: 'Resultados calculados' });
    };

    const exportarExcel = () => {
        if (estudiantes.value.length === 0) return;

        let csv = 'N°,Nombre,';
        const nivelesKeys = ['pre-inicio', 'inicio', 'proceso', 'satisfactorio', 'destacado'];

        nivelesKeys.forEach(nivelKey => {
            const nivel = niveles[nivelKey];
            if (nivel) {
                const preguntas = nivel.preguntas;
                for (let i = 0; i < preguntas.length; i++) {
                    csv += `${nivel.nombre} P${i + 1},`;
                }
            }
        });

        csv += 'Pre Inicio,Inicio,En Proceso,Satisfactorio,Destacado,Nivel Final\n';

        estudiantes.value.forEach((est, index) => {
            csv += `${index + 1},"${est.nombre || ''}",`;

            nivelesKeys.forEach(nivelKey => {
                const respuestas = est.respuestas[nivelKey] || [];
                const nivel = niveles[nivelKey];
                if (nivel) {
                    const preguntas = nivel.preguntas;
                    for (let i = 0; i < preguntas.length; i++) {
                        csv += `${respuestas[i] || ''},`;
                    }
                }
            });

            const puntajes = est.puntajes || {};
            nivelesKeys.forEach(nivelKey => {
                csv += `${puntajes[nivelKey]?.correctas || 0}/${puntajes[nivelKey]?.total || 0},`;
            });

            csv += `"${est.nivelFinal || 'Sin calcular'}"\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = `sistematizador_resultados_${new Date().toISOString().split('T')[0]}.csv`;
        link.click();
        URL.revokeObjectURL(link.href);
    };

    const nivelesKeys = ['pre-inicio', 'inicio', 'proceso', 'satisfactorio', 'destacado'];

    const descargarPlantillaExcel = () => {
        // Build column headers based on current niveles configuration
        const headerRow1: string[] = ['N°', 'Apellidos y Nombres'];
        const headerRow2: string[] = ['', ''];
        const claveRow: string[] = ['', 'CLAVE'];

        nivelesKeys.forEach(key => {
            const nivel = niveles[key];
            if (nivel && nivel.preguntas.length > 0) {
                nivel.preguntas.forEach((preg, idx) => {
                    headerRow1.push(idx === 0 ? nivel.nombre : '');
                    headerRow2.push(`P${idx + 1}`);
                    claveRow.push(preg.clave || '');
                });
            }
        });

        // Create worksheet data
        const wsData: string[][] = [headerRow1, headerRow2, claveRow];

        // Add 30 empty student rows
        for (let i = 1; i <= 30; i++) {
            const row: string[] = [String(i), ''];
            nivelesKeys.forEach(key => {
                const nivel = niveles[key];
                if (nivel) {
                    for (let j = 0; j < nivel.preguntas.length; j++) {
                        row.push('');
                    }
                }
            });
            wsData.push(row);
        }

        const ws = XLSX.utils.aoa_to_sheet(wsData);

        // Set column widths
        ws['!cols'] = [
            { wch: 5 },  // N°
            { wch: 35 }, // Nombre
            ...headerRow2.slice(2).map(() => ({ wch: 6 })),
        ];

        // Merge nivel header cells
        const merges: XLSX.Range[] = [];
        let col = 2;
        nivelesKeys.forEach(key => {
            const nivel = niveles[key];
            if (nivel && nivel.preguntas.length > 0) {
                if (nivel.preguntas.length > 1) {
                    merges.push({ s: { r: 0, c: col }, e: { r: 0, c: col + nivel.preguntas.length - 1 } });
                }
                col += nivel.preguntas.length;
            }
        });
        ws['!merges'] = merges;

        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Registro');
        XLSX.writeFile(wb, `plantilla_sistematizador_${new Date().toISOString().split('T')[0]}.xlsx`);
    };

    const importarExcel = (file: File) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const data = new Uint8Array(e.target?.result as ArrayBuffer);
                const wb = XLSX.read(data, { type: 'array' });
                const sheetName = wb.SheetNames[0];
                if (!sheetName) return;
                const ws = wb.Sheets[sheetName];
                if (!ws) return;

                const rows: string[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: '' });

                // Row 0: nivel names, Row 1: P1/P2..., Row 2: CLAVE, Row 3+: students
                const dataStartRow = 3;
                if (rows.length < 4) return;

                // Build column mapping: which columns correspond to which nivel
                const columnMap: { nivelKey: string; pregIndex: number }[] = [];
                nivelesKeys.forEach(key => {
                    const nivel = niveles[key];
                    if (nivel) {
                        for (let j = 0; j < nivel.preguntas.length; j++) {
                            columnMap.push({ nivelKey: key, pregIndex: j });
                        }
                    }
                });

                // Parse student rows
                const newEstudiantes: Estudiante[] = [];
                for (let r = dataStartRow; r < rows.length; r++) {
                    const row = rows[r] as string[] | undefined;
                    if (!row) continue;
                    const nombre = String(row[1] ?? '').trim();
                    if (!nombre) continue;

                    const respuestas: Record<string, string[]> = {};

                    columnMap.forEach((mapping, colIdx) => {
                        const cellValue = String(row[colIdx + 2] ?? '').trim().toUpperCase();
                        if (!respuestas[mapping.nivelKey]) {
                            respuestas[mapping.nivelKey] = [];
                        }
                        const arr = respuestas[mapping.nivelKey];
                        if (arr) {
                            arr[mapping.pregIndex] = ['A', 'B', 'C', 'D'].includes(cellValue) ? cellValue : '';
                        }
                    });

                    newEstudiantes.push({
                        nombre,
                        respuestas,
                        puntajes: {},
                        nivelFinal: null,
                    });
                }

                if (newEstudiantes.length > 0) {
                    estudiantes.value = newEstudiantes;
                    Toast.fire({ icon: 'success', title: `${newEstudiantes.length} estudiantes importados` });
                } else {
                    showWarning('Sin datos', 'No se encontraron estudiantes en el archivo');
                }
            } catch (err) {
                console.error('Error al importar Excel:', err);
                showError('Error al importar', 'El archivo no tiene el formato esperado');
            }
        };
        reader.readAsArrayBuffer(file);
    };

    return {
        grados,
        selectedGradoId,
        loadingGrados,
        availableDesempenos,
        loadingDesempenos,
        activeTab,
        niveles,
        competencia,
        estudiantes,
        chartContainer,
        gradoOptions,
        desempenoOptions,
        stats,
        loadGrados,
        loadDesempenos,
        addPregunta,
        removePregunta,
        onDesempenoSelect,
        addEstudiante,
        removeEstudiante,
        calcularResultados,
        exportarExcel,
        descargarPlantillaExcel,
        importarExcel,
        updateChart
    };
}
