---
version: alpha
name: LectoSistem DRE
description: Sistema Integrado de Evaluación de Aula para la Dirección Regional de Educación Huánuco. Aplicación SaaS educativa con soporte multi-rol, modo oscuro y módulos de generación de evaluaciones con IA.

colors:
  # Primarios
  primary: "#0d9488"
  primary-light: "#14b8a6"
  primary-dark: "#0f766e"
  on-primary: "#ffffff"
  primary-container: "#f0fdfa"
  on-primary-container: "#134e4a"

  # Secundario (Matemática / Indigo)
  secondary: "#4f46e5"
  secondary-light: "#6366f1"
  on-secondary: "#ffffff"
  secondary-container: "#eef2ff"
  on-secondary-container: "#312e81"

  # Acento (Logro / Amber)
  accent: "#f59e0b"
  accent-light: "#fbbf24"
  on-accent: "#ffffff"
  accent-container: "#fffbeb"

  # Módulos — colores semánticos por área
  module-comunicacion: "#14b8a6"
  module-matematica: "#6366f1"
  module-asignaciones: "#8b5cf6"
  module-admin: "#64748b"
  module-estudiante: "#0ea5e9"

  # Superficies — modo claro
  surface: "#ffffff"
  surface-dim: "#f8fafc"
  surface-container: "#f1f5f9"
  surface-container-high: "#e2e8f0"
  on-surface: "#1e293b"
  on-surface-variant: "#64748b"
  on-surface-muted: "#94a3b8"

  # Superficies — modo oscuro
  surface-dark: "#1e293b"
  surface-dim-dark: "#0f172a"
  surface-container-dark: "#334155"
  surface-container-high-dark: "#475569"
  on-surface-dark: "#f1f5f9"
  on-surface-variant-dark: "#94a3b8"
  on-surface-muted-dark: "#64748b"

  # Bordes
  outline: "#e2e8f0"
  outline-dark: "#334155"
  outline-strong: "#cbd5e1"
  outline-strong-dark: "#475569"

  # Semánticos
  success: "#10b981"
  success-container: "#d1fae5"
  on-success: "#ffffff"
  warning: "#f59e0b"
  warning-container: "#fef3c7"
  error: "#ef4444"
  error-container: "#fee2e2"
  on-error: "#ffffff"

  # Degradados principales (como referencia)
  gradient-header: "from-teal-600 via-teal-500 to-sky-500"
  gradient-comunicacion: "from-teal-400 to-emerald-500"
  gradient-matematica: "from-indigo-400 to-purple-500"
  gradient-asignaciones: "from-violet-500 to-indigo-600"
  gradient-background-light: "from-slate-50 to-gray-100"
  gradient-background-dark: "from-slate-900 to-slate-950"

typography:
  display:
    fontFamily: "Fredoka, Nunito, sans-serif"
    fontSize: 36px
    fontWeight: "700"
    lineHeight: 44px
    letterSpacing: -0.01em
  headline-lg:
    fontFamily: "Fredoka, Nunito, sans-serif"
    fontSize: 28px
    fontWeight: "700"
    lineHeight: 36px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: "Fredoka, Nunito, sans-serif"
    fontSize: 20px
    fontWeight: "700"
    lineHeight: 28px
  title:
    fontFamily: "Nunito, Inter, sans-serif"
    fontSize: 16px
    fontWeight: "700"
    lineHeight: 24px
  body-lg:
    fontFamily: "Nunito, Inter, sans-serif"
    fontSize: 16px
    fontWeight: "400"
    lineHeight: 24px
  body-md:
    fontFamily: "Nunito, Inter, sans-serif"
    fontSize: 14px
    fontWeight: "400"
    lineHeight: 20px
  body-sm:
    fontFamily: "Nunito, Inter, sans-serif"
    fontSize: 12px
    fontWeight: "400"
    lineHeight: 16px
  label-lg:
    fontFamily: "Nunito, Inter, sans-serif"
    fontSize: 14px
    fontWeight: "700"
    lineHeight: 20px
  label-md:
    fontFamily: "Nunito, Inter, sans-serif"
    fontSize: 12px
    fontWeight: "700"
    lineHeight: 16px
  label-sm:
    fontFamily: "Nunito, Inter, sans-serif"
    fontSize: 10px
    fontWeight: "700"
    lineHeight: 14px
    letterSpacing: 0.01em
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, monospace"
    fontSize: 12px
    fontWeight: "500"
    lineHeight: 16px

rounded:
  sm: 0.25rem
  DEFAULT: 0.375rem
  md: 0.5rem
  lg: 0.75rem
  xl: 1rem
  full: 9999px

spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  2xl: 40px
  gutter: 16px
  section: 24px
  page-x: 16px
  page-x-sm: 24px
  max-content: 1024px

components:
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.xl}"
    padding: "{spacing.xl}"
    size: "border border-slate-100 dark:border-slate-700 shadow-sm"
  card-dark:
    backgroundColor: "{colors.surface-dark}"
  card-hover:
    size: "hover:shadow-md transition-all duration-150"

  card-module:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.xl}"
    padding: "20px 24px"
    size: "border border-slate-100 dark:border-slate-700 shadow-lg hover:shadow-xl"
  card-module-hover:
    size: "transform -translate-y-2 transition-transform duration-150"

  card-admin:
    backgroundColor: "rgba(255,255,255,0.8)"
    rounded: "{rounded.lg}"
    padding: "12px 16px"
    size: "border border-slate-200/80 dark:border-slate-700/80 backdrop-blur-sm"
  card-admin-hover:
    size: "transform -translate-y-1.5 transition-transform duration-150"

  button-primary:
    textColor: "{colors.on-primary}"
    typography: "{typography.label-lg}"
    rounded: "{rounded.lg}"
    padding: "8px 16px"
    size: "shadow font-bold text-sm"
  button-primary-comunicacion:
    backgroundColor: "linear-gradient(to right, #14b8a6, #10b981)"
  button-primary-matematica:
    backgroundColor: "linear-gradient(to right, #6366f1, #8b5cf6)"
  button-primary-asignaciones:
    backgroundColor: "linear-gradient(to right, #8b5cf6, #4f46e5)"

  button-ghost:
    backgroundColor: transparent
    textColor: "{colors.on-surface-variant}"
    rounded: "{rounded.lg}"
    padding: "8px 12px"
  button-ghost-hover:
    backgroundColor: "{colors.surface-container}"

  button-icon:
    backgroundColor: "rgba(255,255,255,0.2)"
    rounded: "{rounded.lg}"
    padding: "10px"
    size: "border border-white/30 text-white"
  button-icon-hover:
    backgroundColor: "rgba(255,255,255,0.3)"

  input:
    backgroundColor: "{colors.surface-dim}"
    textColor: "{colors.on-surface}"
    typography: "{typography.body-md}"
    rounded: "{rounded.lg}"
    padding: "10px 14px"
    size: "border border-slate-200 dark:border-slate-600 outline-none focus:ring-2 focus:ring-teal-500/40 focus:border-teal-500"
  input-dark:
    backgroundColor: "{colors.surface-container-dark}"

  badge:
    typography: "{typography.label-sm}"
    rounded: "{rounded.full}"
    padding: "2px 8px"
    size: "font-bold uppercase tracking-wide"
  badge-comunicacion:
    backgroundColor: "{colors.primary-container}"
    textColor: "{colors.on-primary-container}"
  badge-matematica:
    backgroundColor: "{colors.secondary-container}"
    textColor: "{colors.on-secondary-container}"
  badge-success:
    backgroundColor: "{colors.success-container}"
    textColor: "#065f46"
  badge-error:
    backgroundColor: "{colors.error-container}"
    textColor: "#991b1b"

  header:
    backgroundColor: "linear-gradient(to right, {colors.primary-dark}, {colors.primary-light}, #0ea5e9)"
    textColor: "{colors.on-primary}"
    size: "sticky top-0 z-50 shadow-lg backdrop-blur-md"
  header-dark:
    backgroundColor: "{colors.surface-dark}"

  icon-container:
    rounded: "{rounded.lg}"
    size: "w-8 h-8 flex items-center justify-center shadow-sm"
  icon-container-lg:
    rounded: "{rounded.lg}"
    size: "w-11 h-11 flex items-center justify-center"

  nivel-logro-pre-inicio:
    backgroundColor: "#fee2e2"
    textColor: "#991b1b"
    rounded: "{rounded.full}"
    padding: "2px 8px"
  nivel-logro-inicio:
    backgroundColor: "#ffedd5"
    textColor: "#9a3412"
  nivel-logro-proceso:
    backgroundColor: "#fef9c3"
    textColor: "#713f12"
  nivel-logro-satisfactorio:
    backgroundColor: "#dcfce7"
    textColor: "#14532d"
  nivel-logro-destacado:
    backgroundColor: "#f0fdfa"
    textColor: "#134e4a"
---

## Overview

LectoSistem DRE es una aplicación web SaaS para la Dirección Regional de Educación de Huánuco (Perú). Permite a docentes, directores y especialistas DRE generar evaluaciones de Comunicación (comprensión lectora) y Matemática con IA, asignarlas a estudiantes y visualizar métricas de uso.

El lenguaje visual es **Educativo Premium**: moderno y confiable, con gradientes suaves, superficies limpias y una paleta basada en teal (conocimiento) e índigo (matemática). El modo oscuro es ciudadano de primera clase — cada componente lo soporta nativamente.

**Stack:** Vue 3 + Tailwind CSS 4 + Lucide Icons. Sin librerías de componentes externas.

---

## Colors

La paleta tiene tres ejes cromáticos fijos y dos semánticos:

### Eje principal — Teal (Comunicación / Conocimiento)
`#14b8a6` (teal-500) es el color primario del sistema. Representa la lectura, el saber y la navegación global. Usado en: header principal, LectoSistem, íconos de acción, focus rings, scrollbar.

### Eje secundario — Indigo/Violet (Matemática / Tecnología)
`#6366f1` (indigo-500) representa la precisión matemática y la IA. Aparece en MatSistem y en los badges de módulos tecnológicos.

### Eje terciario — Amber (Logro / Alerta positiva)
`#f59e0b` (amber-500) se reserva para logros, niveles destacados, advertencias y el acento del logo DRE. No se usa en elementos interactivos primarios.

### Superficies y neutrales
- **Claro:** fondo principal `slate-50` → tarjetas en `white` → hover en `slate-50` → bordes en `slate-100/200`
- **Oscuro:** fondo principal `slate-950` → tarjetas en `slate-800` → hover en `slate-700` → bordes en `slate-700`
- El texto principal es `slate-800` (claro) / `white` (oscuro); el texto secundario es `slate-500` (claro) / `slate-400` (oscuro)

### Color semántico por módulo
Cada módulo tiene su color de acento que se aplica de forma consistente al gradiente del header, los íconos y los hover states:

| Módulo | Gradiente | Uso |
|---|---|---|
| LectoSistem | `from-teal-400 to-emerald-500` | Comunicación / Lectura |
| MatSistem | `from-indigo-400 to-purple-500` | Matemática |
| Asignaciones | `from-violet-500 to-indigo-600` | Gestión de exámenes |
| Admin DRE | `from-slate-700 to-slate-900` | Configuración sistema |
| Estudiante | `from-teal-500 to-indigo-600` | Portal estudiantil |

### Niveles de logro
Los niveles de logro tienen colores semánticos fijos que no cambian entre módulos:
- **Pre-inicio:** rojo — `bg-red-50 text-red-600`
- **Inicio:** naranja — `bg-orange-50 text-orange-600`
- **En Proceso:** amarillo — `bg-yellow-50 text-yellow-700`
- **Satisfactorio:** verde — `bg-green-50 text-green-600`
- **Destacado:** teal — `bg-teal-50 text-teal-600`

---

## Typography

El sistema usa **dos familias tipográficas** complementarias:

### Fredoka — Titulares
Geométrica, redondeada y amigable. Refuerza el carácter educativo. Se aplica a `h1–h6` globalmente vía CSS. No usar para texto corrido, etiquetas de datos o monoespaciado.

### Nunito — Cuerpo y UI
Alta legibilidad a tamaños pequeños, con terminaciones redondeadas que armonizan con Fredoka. Cubre cuerpo, etiquetas, botones y metadatos.

### Escala de tamaños en uso
- `text-[10px]` / `text-[11px]` — etiquetas ultra-compactas (badges, metadata de tarjeta)
- `text-xs` (12px) — descripción secundaria, timestamps
- `text-sm` (14px) — texto de botón, cuerpo de formulario, lista
- `text-base` (16px) — texto de párrafo
- `text-lg` / `text-xl` — títulos de sección dentro de tarjeta
- `text-2xl` / `text-3xl` — título de página
- `font-black` solo para números/stats en tarjetas de métricas

### Pesos
- `font-medium` — texto secundario y descriptivo
- `font-semibold` — labels, subtítulos
- `font-bold` — el peso estándar para cualquier elemento interactivo
- `font-black` — números grandes en tarjetas de estadísticas

---

## Layout

### Estructura general de página
Cada vista de módulo sigue este patrón:

```
┌─────────────────────────────────────────┐
│  Header (sticky, gradiente módulo)       │  ← z-50
├─────────────────────────────────────────┤
│  <main> max-w-{md|lg|xl|4xl} mx-auto    │
│    px-4 sm:px-6  py-6 sm:py-8          │
│                                         │
│    Grid de tarjetas / contenido         │
├─────────────────────────────────────────┤
│  Footer (gradiente teal)                │
└─────────────────────────────────────────┘
```

### Anchos máximos por tipo de vista
- `max-w-sm` — modales, formularios simples
- `max-w-lg` / `max-w-xl` — formularios de configuración
- `max-w-3xl` / `max-w-4xl` — vistas de módulo estándar
- `max-w-5xl` — vistas con tablas o listas largas
- `max-w-7xl` — panel admin con múltiples columnas

### Grid de módulos en HomeView
Las tarjetas de módulo principales (LectoSistem / MatSistem) usan `grid sm:grid-cols-2 gap-3 sm:gap-4`. Las tarjetas de acceso rápido (admin) usan `grid grid-cols-3 sm:grid-cols-4` o `grid-cols-2 sm:grid-cols-4`.

### Mobile-first
El breakpoint `sm` (640px) es el principal. Los componentes se apilan en `flex-col` en móvil y pasan a `flex-row` o multi-columna en `sm:`. El padding de página es `px-4` en móvil y `sm:px-6` en escritorio.

---

## Elevation & Depth

La jerarquía de capas se construye con sombras y fondos tonales, sin glassmorphism pesado:

| Nivel | Uso | Clases |
|---|---|---|
| Base | Fondo de página | `bg-slate-50 dark:bg-slate-950` |
| Elevado | Tarjetas principales | `bg-white dark:bg-slate-800` + `shadow-sm` |
| Flotante | Dropdowns, tooltips | `bg-white dark:bg-slate-800` + `shadow-lg` |
| Modal | Modales / drawers | `bg-white dark:bg-slate-800` + `shadow-2xl` + `backdrop-blur-sm` |
| Header | Barra superior | `shadow-lg` + `backdrop-blur-md` |

### Hover state en tarjetas
Las tarjetas interactivas elevan su sombra en hover y se desplazan -4px a -8px en Y usando `will-change: transform` y `transition: transform 160ms cubic-bezier(0.34,1.4,0.64,1)`. Las tarjetas admin pequeñas se desplazan -5px.

### Sombras de color
Los hover de tarjetas de módulo usan sombras de color teñidas (`shadow-teal-500/15`, `shadow-indigo-500/15`) para reforzar la identidad del módulo, nunca sombras grises neutras.

---

## Shapes

El lenguaje de formas es **Rounded Progresivo**: el radio crece con el tamaño del componente.

| Componente | Radio | Clases |
|---|---|---|
| Inputs, selects | `0.75rem` / 12px | `rounded-xl` |
| Botones | `0.75rem` / 12px | `rounded-xl` |
| Tarjetas admin (pequeñas) | `0.75rem` / 12px | `rounded-xl` |
| Tarjetas estándar | `1rem` / 16px | `rounded-2xl` |
| Tarjetas de módulo (Home) | `1rem` / 16px | `rounded-2xl` |
| Modales | `1rem` / 16px (arriba) | `rounded-t-2xl sm:rounded-2xl` |
| Badges / pills | `9999px` | `rounded-full` |
| Íconos-contenedor pequeños | `0.5rem` / 8px | `rounded-lg` |
| Íconos-contenedor medianos | `0.75rem` / 12px | `rounded-xl` |
| Avatares / indicadores | `9999px` | `rounded-full` |

---

## Components

### Header de página
Cada vista de módulo tiene un header con gradiente propio. La estructura interna es:

```
[Botón Home icon-only] [Icono módulo + Título + Subtítulo] [UserBadge]
```

El header usa el slot `#actions-before` para el botón de inicio y expone el `UserBadge` en el lado derecho. En la HomeView, el header es un `<div>` fixed (no el componente `<Header>`).

### Tarjetas de módulo (HomeView)
Tarjetas grandes con watermark de ícono (opacity 0.04 → 0.09 en hover), overlay de gradiente radial al hover, línea de acento en el borde inferior que crece desde el centro, e ícono con glow ring en hover.

### Tarjetas de acceso rápido (admin-card)
Tarjetas pequeñas cuadradas con ícono centrado arriba + etiqueta + descripción. El ícono rota `-6deg` y escala `1.18×` en hover. Tienen un sweep de brillo (shine) en `::after` al hacer hover.

### Modales
Los modales son Teleport a `body`. En móvil aparecen como bottom sheet (`items-end`, sin redondeo inferior); en `sm:` aparecen centrados con `rounded-2xl`. Incluyen drag handle visible solo en móvil. Usan `Transition` de entrada/salida con `scale-95 → scale-100`.

### Inputs y formularios
- Label: `text-xs font-bold text-slate-600 dark:text-slate-300 mb-1.5`
- Input: `bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl py-2.5 px-3.5 text-sm focus:ring-2 focus:ring-{module-color}-500/50 focus:border-{module-color}-500`
- Error inline: `bg-red-50 dark:bg-red-900/20 border border-red-100 text-red-600 rounded-xl p-3 text-sm`

### Tablas de resultados / listas
- Filas con `divide-y divide-slate-100 dark:divide-slate-700`
- Hover: `hover:bg-slate-50 dark:hover:bg-slate-700/30`
- Columnas de datos numéricos: `font-black text-emerald-600`
- Badges de nivel de logro: colores semánticos del eje de niveles

### Loading states
- Pantalla completa: `flex justify-center py-16` + `<Loader2 class="w-8 h-8 animate-spin text-teal-500" />`
- Inline en botón: `<Loader2 class="w-3.5 h-3.5 animate-spin" />`
- Overlay de carga (HomeView): `absolute inset-0 z-[200] backdrop-blur-sm`

### Íconos
Solo Lucide Icons (`lucide-vue-next`). Tamaños estándar:
- `w-3 h-3` — íconos en badges y texto inline
- `w-4 h-4` — íconos en botones y listas
- `w-5 h-5` — íconos en header y tarjetas estándar
- `w-6 h-6` — íconos en tarjetas de módulo grandes
- `w-8 h-8` — íconos de estado / loading
- `w-12 h-12` o más — íconos decorativos en estados vacíos

---

## Do's and Don'ts

### Hazlo

- **Usa Lucide Icons** para todos los íconos. Elige el más semántico para la acción (no el más parecido visualmente).
- **Aplica el color del módulo** de forma consistente: si una vista pertenece a LectoSistem, todos sus acentos interactivos son teal; si es MatSistem, indigo.
- **Soporta dark mode en cada componente** desde el primer momento con clases `dark:` explícitas.
- **Usa `font-bold` como peso base** para cualquier texto interactivo (botones, links, labels).
- **Pon `transition-colors duration-150`** en cualquier elemento que cambie de color en hover.
- **Usa `will-change: transform`** en tarjetas que hacen translate en hover para forzar GPU.
- **Mantén el patrón de label `text-xs font-bold uppercase tracking-widest text-slate-400`** para separadores de sección dentro de tarjetas.
- **Para estados vacíos**, muestra un ícono grande (`w-12 h-12`) en `text-slate-300 dark:text-slate-600` seguido de un título y descripción centrados.

### No lo hagas

- **No uses emojis en la UI.** Siempre usa un ícono Lucide equivalente.
- **No uses `text-black` ni `text-white` directamente** en elementos de texto; usa siempre tokens de la escala `slate-*` para que el dark mode funcione.
- **No apliques sombras neutras grises** en tarjetas de módulo. Las sombras de hover deben estar teñidas con el color del módulo.
- **No mezcles radios de borde.** Una tarjeta es `rounded-2xl`; sus elementos internos son `rounded-xl` o `rounded-lg`. Nunca el mismo radio para niveles diferentes.
- **No uses más de dos familias tipográficas.** `Fredoka` para headings, `Nunito` para todo lo demás.
- **No crees gradientes nuevos** sin usar la codificación de color por módulo establecida.
- **No uses `text-sm font-normal`** para etiquetas de botón; los botones son siempre `text-sm font-bold`.
- **No muestres datos sin estado de carga.** Toda carga asíncrona debe tener su spinner visible antes de renderizar contenido.
- **No uses `overflow: hidden` en contenedores** que tengan tooltips o dropdowns hijos — el overflow corta el contenido flotante.
