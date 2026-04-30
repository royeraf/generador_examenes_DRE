# Usuarios de Prueba — LectoSistem DRE

Contraseña para todos los usuarios: **`Test2024!`**

El login acepta DNI o código de estudiante como identificador.

---

## Infraestructura de prueba

| Entidad | ID | Detalle |
|---|---|---|
| UGEL | 2 | UGEL DOS DE MAYO |
| Institución Educativa | 2 | I.E. Pública Yarowilca (ugel_id=2) |
| Grado de referencia | 1 | Primer grado de Primaria |

---

## Usuarios por rol

### Especialistas DRE

| DNI | Contraseña | Nombre | Rol | Acceso |
|---|---|---|---|---|
| `00000000` | `admin123` | Administrador Sistema | `especialista_dre_comunicacion` | Todo el sistema |
| `11111111` | `Test2024!` | María López Díaz | `especialista_dre_matematica` | Todo el sistema |

**Vistas disponibles:** Home → módulos LectoSistem y MatSistem + panel DRE completo (Usuarios, UGELes, Instituciones, Desempeños Comunicación y Matemática, Métricas, Asignaciones, Códigos de Clase).

---

### Responsable UGEL

| DNI | Contraseña | Nombre | Rol | UGEL |
|---|---|---|---|---|
| `22222222` | `Test2024!` | Carlos Mendoza Ruiz | `responsable_ugel` | UGEL DOS DE MAYO (id=2) |

**Vistas disponibles:** Mi UGEL → lista IEs de la UGEL + métricas scoped a la UGEL + gestión de instituciones + gestión de usuarios de sus IEs.

> **Nota:** La ruta de inicio es `/mi-ugel`, no `/`.

---

### Director

| DNI | Contraseña | Nombre | Rol | IE |
|---|---|---|---|---|
| `99999999` | `Test2024!` | Manuel Rosas Test | `director` | I.E. Pública Yarowilca (id=2) |

**Vistas disponibles:** Home → LectoSistem, MatSistem + panel director: Mi Institución (con analytics), Asignaciones de la institución (ve todas las de su IE), Códigos de Clase, Usuarios, Métricas.

---

### Auxiliar

| DNI | Contraseña | Nombre | Rol | IE |
|---|---|---|---|---|
| `33333333` | `Test2024!` | Ana Torres Vásquez | `auxiliar` | I.E. Pública Yarowilca (id=2) |

**Vistas disponibles:** Home → LectoSistem, MatSistem + Mis Estudiantes, Códigos de Clase, Asignaciones, Métricas. Ve las asignaciones de toda la IE (igual que el director).

---

### Docentes

| DNI | Contraseña | Nombre | Rol | IE |
|---|---|---|---|---|
| `44444444` | `Test2024!` | Pedro Quispe Alvarado | `docente` | I.E. Pública Yarowilca (id=2) |
| `55555555` | `Test2024!` | Lucía Fernández Poma | `docente` | I.E. Pública Yarowilca (id=2) |
| `71499036` | `Test2024!` | Royer Ariza | `docente` | I.E. Pública Yarowilca (id=2) |
| `76543210` | `Test2024!` | Usuario Pruebas | `docente` | — |

**Vistas disponibles:** Home → LectoSistem, MatSistem + Mis Estudiantes, Asignaciones (solo las propias), Códigos de Clase, Métricas.

---

### Estudiantes

| DNI / Código | Contraseña | Nombre | IE | Grado | Sección |
|---|---|---|---|---|---|
| `66666666` | `Test2024!` | Sofía Campos Reyes | I.E. Pública Yarowilca | 1° Primaria | A |
| `77777777` | `Test2024!` | Diego Ramos Flores | I.E. Pública Yarowilca | 1° Primaria | A |
| `75432199` | `Test2024!` | Mario Perez | — | — | — |

> Los estudiantes inician sesión con su DNI. Si fueron registrados sin DNI y con código `ESTxxxx`, usan ese código.

**Vistas disponibles:** Portal estudiantil (`/estudiante`) → Mis Exámenes, Mi Progreso.

---

## Resumen de scoping por rol

| Rol | Genera exámenes | Ve asignaciones | Gestiona usuarios | Métricas |
|---|---|---|---|---|
| `especialista_dre_*` | Sí | Todo el sistema | Todo | Global |
| `responsable_ugel` | No | IEs de su UGEL | IEs de su UGEL | Scoped a UGEL |
| `director` | Sí | Toda su IE | Su IE | Scoped a IE |
| `auxiliar` | Sí | Toda su IE | — | Scoped a IE |
| `docente` | Sí | Solo las propias | — | Solo las propias |
| `estudiante` | No | — | — | Su progreso |

---

## Cómo re-ejecutar el seed

```bash
cd backend
./venv/bin/python -m scripts.seed_test_users
```

El script es idempotente: omite usuarios que ya existen por DNI.

---

## Flujo de prueba sugerido

### Probar asignaciones scoped por IE (Director)

1. Login como `44444444` (docente Pedro) → Generar un examen en LectoSistem → Guardarlo → ir a Asignaciones → crear una asignación para grado 1° sección A.
2. Login como `99999999` (director Manuel) → Asignaciones → debe ver la asignación de Pedro + las propias.
3. Login como `66666666` (estudiante Sofía, 1° A) → Mis Exámenes → debe ver la asignación.

### Probar analytics de institución (Director)

1. Login como `99999999` → Mi Institución → debe mostrar contadores de estudiantes, docentes, exámenes y asignaciones.

### Probar métricas scoped por UGEL

1. Login como `22222222` (responsable UGEL) → Métricas → debe mostrar solo datos de las IEs de su UGEL.

### Probar módulos DRE completos

1. Login como `00000000` o `11111111` → Home → ver todos los paneles del especialista DRE.
