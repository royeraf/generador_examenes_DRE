"""
Script para cargar las competencias, capacidades, estándares y desempeños de Matemática
desde los archivos Word en la base de datos SQLite.

Ejecutar desde el directorio backend:
    python -m scripts.load_matematica

Archivos fuente (en capacidades_mat/):
    - COMPETENCIA MATEMATICA 1.docx (Cantidad)
    - COMPETENCIA MATEMATICA 2.docx (Regularidad, equivalencia y cambio)
    - COMPETENCIA MATEMATICA 3.docx (Forma, movimiento y localización)
    - COMPETENCIA MATEMATICA 4.docx (Gestión de datos e incertidumbre)
"""

import sys
import os
import re
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, Base
from app.models.db_models import (
    Grado, 
    CompetenciaMatematica, 
    CapacidadMatematica, 
    EstandarMatematica, 
    DesempenoMatematica
)


# Ruta a la carpeta con los archivos Word
DOCX_FOLDER = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "capacidades_mat"
)

# Definición de las 4 competencias matemáticas
COMPETENCIAS = [
    {
        "codigo": 1,
        "nombre": "Resuelve problemas de cantidad",
        "descripcion": """Consiste en que el estudiante solucione problemas o plantee nuevos problemas que le demanden construir y comprender las nociones de cantidad, de número, de sistemas numéricos, sus operaciones y propiedades. Además, dotar de significado a estos conocimientos en la situación y usarlos para representar o reproducir las relaciones entre sus datos y condiciones. Implica también discernir si la solución buscada requiere darse como una estimación o cálculo exacto, y para ello selecciona estrategias, procedimientos, unidades de medida y diversos recursos.""",
        "capacidades": [
            "Traduce cantidades a expresiones numéricas",
            "Comunica su comprensión sobre los números y las operaciones",
            "Usa estrategias y procedimientos de estimación y cálculo",
            "Argumenta afirmaciones sobre las relaciones numéricas y las operaciones"
        ]
    },
    {
        "codigo": 2,
        "nombre": "Resuelve problemas de regularidad, equivalencia y cambio",
        "descripcion": """Consiste en que el estudiante logre caracterizar equivalencias y generalizar regularidades y el cambio de una magnitud con respecto de otra, a través de reglas generales que le permitan encontrar valores desconocidos, determinar restricciones y hacer predicciones sobre el comportamiento de un fenómeno.""",
        "capacidades": [
            "Traduce datos y condiciones a expresiones algebraicas y gráficas",
            "Comunica su comprensión sobre las relaciones algebraicas",
            "Usa estrategias y procedimientos para encontrar equivalencias y reglas generales",
            "Argumenta afirmaciones sobre relaciones de cambio y equivalencia"
        ]
    },
    {
        "codigo": 3,
        "nombre": "Resuelve problemas de forma, movimiento y localización",
        "descripcion": """Consiste en que el estudiante se oriente y describa la posición y el movimiento de objetos y de sí mismo en el espacio, visualizando, interpretando y relacionando las características de los objetos con formas geométricas bidimensionales y tridimensionales.""",
        "capacidades": [
            "Modela objetos con formas geométricas y sus transformaciones",
            "Comunica su comprensión sobre las formas y relaciones geométricas",
            "Usa estrategias y procedimientos para medir y orientarse en el espacio",
            "Argumenta afirmaciones sobre relaciones geométricas"
        ]
    },
    {
        "codigo": 4,
        "nombre": "Resuelve problemas de gestión de datos e incertidumbre",
        "descripcion": """Consiste en que el estudiante analice datos sobre un tema de interés o estudio o de situaciones aleatorias, que le permitan tomar decisiones, elaborar predicciones razonables y conclusiones respaldadas en la información producida.""",
        "capacidades": [
            "Representa datos con gráficos y medidas estadísticas o probabilísticas",
            "Comunica su comprensión de los conceptos estadísticos y probabilísticos",
            "Usa estrategias y procedimientos para recopilar y procesar datos",
            "Sustenta conclusiones o decisiones con base en la información obtenida"
        ]
    }
]

# Definición de grados (incluyendo Inicial)
GRADOS_MATEMATICA = [
    {"nombre": "INICIAL DE 5 AÑOS", "numero": 0, "nivel": "inicial", "orden": 1, "ciclo": "II"},
    {"nombre": "PRIMER GRADO DE PRIMARIA", "numero": 1, "nivel": "primaria", "orden": 2, "ciclo": "III"},
    {"nombre": "SEGUNDO GRADO DE PRIMARIA", "numero": 2, "nivel": "primaria", "orden": 3, "ciclo": "III"},
    {"nombre": "TERCER GRADO DE PRIMARIA", "numero": 3, "nivel": "primaria", "orden": 4, "ciclo": "IV"},
    {"nombre": "CUARTO GRADO DE PRIMARIA", "numero": 4, "nivel": "primaria", "orden": 5, "ciclo": "IV"},
    {"nombre": "QUINTO GRADO DE PRIMARIA", "numero": 5, "nivel": "primaria", "orden": 6, "ciclo": "V"},
    {"nombre": "SEXTO GRADO DE PRIMARIA", "numero": 6, "nivel": "primaria", "orden": 7, "ciclo": "V"},
    {"nombre": "PRIMER GRADO DE SECUNDARIA", "numero": 1, "nivel": "secundaria", "orden": 8, "ciclo": "VI"},
    {"nombre": "SEGUNDO GRADO DE SECUNDARIA", "numero": 2, "nivel": "secundaria", "orden": 9, "ciclo": "VI"},
    {"nombre": "TERCER GRADO DE SECUNDARIA", "numero": 3, "nivel": "secundaria", "orden": 10, "ciclo": "VII"},
    {"nombre": "CUARTO GRADO DE SECUNDARIA", "numero": 4, "nivel": "secundaria", "orden": 11, "ciclo": "VII"},
    {"nombre": "QUINTO GRADO DE SECUNDARIA", "numero": 5, "nivel": "secundaria", "orden": 12, "ciclo": "VII"},
]


def extract_text_from_docx(docx_path: str) -> str:
    """Extrae texto plano de un archivo .docx."""
    try:
        with zipfile.ZipFile(docx_path, 'r') as zip_ref:
            xml_content = zip_ref.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Namespace de Word
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            text_parts = []
            for paragraph in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                para_text = ''
                for text_elem in paragraph.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
                    if text_elem.text:
                        para_text += text_elem.text
                if para_text.strip():
                    text_parts.append(para_text.strip())
            
            return '\n'.join(text_parts)
    except Exception as e:
        print(f"   ⚠️ Error extrayendo texto de {docx_path}: {e}")
        return ""


def identify_grado(text: str) -> dict | None:
    """Identifica el grado a partir de un texto."""
    text_upper = text.upper()
    
    for grado in GRADOS_MATEMATICA:
        # Buscar coincidencia flexible
        grado_check = grado["nombre"].upper()
        
        # Patrones de búsqueda
        if grado["nivel"] == "inicial":
            if "INICIAL" in text_upper and ("5 AÑOS" in text_upper or "5AÑOS" in text_upper):
                return grado
        elif "GRADO DE PRIMARIA" in text_upper or "GRADO DE SECUNDARIA" in text_upper:
            # Extraer número ordinal
            ordinals = {
                "PRIMER": 1, "SEGUNDO": 2, "TERCER": 3, "CUARTO": 4,
                "QUINTO": 5, "SEXTO": 6
            }
            for ordinal, num in ordinals.items():
                if ordinal in text_upper:
                    if "PRIMARIA" in text_upper and grado["nivel"] == "primaria" and grado["numero"] == num:
                        return grado
                    if "SECUNDARIA" in text_upper and grado["nivel"] == "secundaria" and grado["numero"] == num:
                        return grado
    
    return None


def parse_docx_competencia(docx_path: str, competencia_codigo: int) -> dict:
    """
    Parsea un archivo .docx de competencia matemática.
    Retorna un diccionario con estándares y desempeños por grado.
    """
    print(f"\n📄 Procesando: {os.path.basename(docx_path)}")
    
    text = extract_text_from_docx(docx_path)
    if not text:
        return {"estandares": [], "desempenos": []}
    
    lines = text.split('\n')
    
    result = {
        "estandares": [],   # [{grado_info, descripcion, ciclo}]
        "desempenos": []    # [{grado_info, capacidad_orden, descripcion}]
    }
    
    current_grado = None
    current_capacidad_orden = None
    current_section = None  # "estandar", "desempenos"
    
    # Buffer para acumular texto de estándar
    estandar_buffer = []
    
    # Mapeo de capacidades por competencia
    capacidades_competencia = COMPETENCIAS[competencia_codigo - 1]["capacidades"]
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        line_upper = line.upper()
        
        # Detectar cambio de grado
        grado_detected = identify_grado(line)
        if grado_detected:
            # Guardar estándar anterior si existe
            if current_grado and estandar_buffer:
                result["estandares"].append({
                    "grado_info": current_grado,
                    "descripcion": ' '.join(estandar_buffer),
                    "ciclo": current_grado.get("ciclo", "")
                })
                estandar_buffer = []
            
            current_grado = grado_detected
            current_section = None
            current_capacidad_orden = None
            print(f"   📍 Grado: {current_grado['nombre']}")
            i += 1
            continue
        
        # Detectar sección de estándar
        if "ESTÁNDAR" in line_upper or "ESTANDAR" in line_upper:
            current_section = "estandar"
            estandar_buffer = []
            i += 1
            continue
        
        # Detectar sección de desempeños
        if "DESEMPEÑO" in line_upper and "CAPACIDAD" in line_upper:
            # Guardar estándar si había uno en buffer
            if current_grado and estandar_buffer:
                result["estandares"].append({
                    "grado_info": current_grado,
                    "descripcion": ' '.join(estandar_buffer),
                    "ciclo": current_grado.get("ciclo", "")
                })
                estandar_buffer = []
            
            current_section = "desempenos"
            i += 1
            continue
        
        # Detectar capacidad específica
        if current_section == "desempenos" and current_grado:
            for idx, cap_nombre in enumerate(capacidades_competencia):
                # Buscar match de capacidad (comparación flexible)
                cap_words = cap_nombre.upper().split()[:3]  # Primeras 3 palabras
                if all(word in line_upper for word in cap_words):
                    current_capacidad_orden = idx + 1
                    print(f"      ✓ Capacidad {current_capacidad_orden}: {cap_nombre[:50]}...")
                    break
        
        # Acumular contenido de estándar
        if current_section == "estandar" and current_grado and line:
            # Evitar agregar líneas que son títulos de sección
            if "COMPETENCIA" not in line_upper and "CAPACIDAD" not in line_upper:
                estandar_buffer.append(line)
        
        # Detectar y guardar desempeños
        if current_section == "desempenos" and current_grado and current_capacidad_orden:
            # Los desempeños suelen empezar con verbos de acción
            verbos_inicio = [
                "Establece", "Expresa", "Selecciona", "Emplea", "Plantea", 
                "Compara", "Usa", "Representa", "Comunica", "Modela",
                "Describe", "Realiza", "Identifica", "Argumenta", "Justifica",
                "Evalúa", "Resuelve", "Traduce", "Interpreta", "Lee",
                "Recolecta", "Organiza", "Sustenta", "Predice", "Explica"
            ]
            
            starts_with_verb = any(line.startswith(v) for v in verbos_inicio)
            
            if starts_with_verb and len(line) > 20:
                result["desempenos"].append({
                    "grado_info": current_grado,
                    "capacidad_orden": current_capacidad_orden,
                    "descripcion": line
                })
        
        i += 1
    
    # Guardar último estándar si existe
    if current_grado and estandar_buffer:
        result["estandares"].append({
            "grado_info": current_grado,
            "descripcion": ' '.join(estandar_buffer),
            "ciclo": current_grado.get("ciclo", "")
        })
    
    print(f"   📊 Encontrados: {len(result['estandares'])} estándares, {len(result['desempenos'])} desempeños")
    
    return result


def load_matematica_data():
    """Carga todos los datos de Matemática en la base de datos."""
    print("=" * 60)
    print("🔢 CARGADOR DE COMPETENCIAS MATEMÁTICAS")
    print("=" * 60)
    
    # Verificar carpeta de archivos Word
    if not os.path.exists(DOCX_FOLDER):
        print(f"❌ Error: No se encontró la carpeta: {DOCX_FOLDER}")
        return
    
    print(f"📂 Carpeta fuente: {DOCX_FOLDER}")
    
    # Crear tablas si no existen
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 1. Limpiar datos existentes de Matemática
        print("\n🗑️ Limpiando datos existentes de Matemática...")
        db.query(DesempenoMatematica).delete()
        db.query(EstandarMatematica).delete()
        db.query(CapacidadMatematica).delete()
        db.query(CompetenciaMatematica).delete()
        db.commit()
        
        # 2. Crear/Actualizar Grados (solo los de matemática si no existen)
        print("\n📚 Verificando grados...")
        grados_db = {}
        
        for grado_info in GRADOS_MATEMATICA:
            # Buscar si ya existe el grado
            existing = db.query(Grado).filter(
                Grado.nombre == grado_info["nombre"]
            ).first()
            
            if existing:
                grados_db[grado_info["nombre"]] = existing
            else:
                nuevo_grado = Grado(
                    nombre=grado_info["nombre"],
                    numero=grado_info["numero"],
                    nivel=grado_info["nivel"],
                    orden=grado_info["orden"]
                )
                db.add(nuevo_grado)
                db.flush()
                grados_db[grado_info["nombre"]] = nuevo_grado
                print(f"   ➕ Nuevo grado: {grado_info['nombre']}")
        
        db.commit()
        
        # 3. Crear Competencias y Capacidades
        print("\n🎯 Creando competencias y capacidades...")
        competencias_db = {}
        capacidades_db = {}
        
        for comp_data in COMPETENCIAS:
            # Crear competencia
            competencia = CompetenciaMatematica(
                codigo=comp_data["codigo"],
                nombre=comp_data["nombre"],
                descripcion=comp_data["descripcion"]
            )
            db.add(competencia)
            db.flush()
            competencias_db[comp_data["codigo"]] = competencia
            print(f"   ✓ Competencia {comp_data['codigo']}: {comp_data['nombre']}")
            
            # Crear capacidades de esta competencia
            for idx, cap_nombre in enumerate(comp_data["capacidades"], 1):
                capacidad = CapacidadMatematica(
                    orden=idx,
                    nombre=cap_nombre,
                    competencia_id=competencia.id
                )
                db.add(capacidad)
                db.flush()
                # Key: (competencia_codigo, orden_capacidad)
                capacidades_db[(comp_data["codigo"], idx)] = capacidad
        
        db.commit()
        
        # 4. Procesar cada archivo de competencia
        print("\n📖 Procesando archivos de competencias...")
        
        for comp_codigo in range(1, 5):
            docx_filename = f"COMPETENCIA MATEMATICA {comp_codigo}.docx"
            docx_path = os.path.join(DOCX_FOLDER, docx_filename)
            
            if not os.path.exists(docx_path):
                print(f"   ⚠️ No encontrado: {docx_filename}")
                continue
            
            # Parsear archivo
            parsed_data = parse_docx_competencia(docx_path, comp_codigo)
            competencia = competencias_db[comp_codigo]
            
            # Guardar estándares
            for estandar_data in parsed_data["estandares"]:
                grado_nombre = estandar_data["grado_info"]["nombre"]
                if grado_nombre in grados_db:
                    estandar = EstandarMatematica(
                        descripcion=estandar_data["descripcion"],
                        ciclo=estandar_data["ciclo"],
                        grado_id=grados_db[grado_nombre].id,
                        competencia_id=competencia.id
                    )
                    db.add(estandar)
            
            # Guardar desempeños
            desempeno_contador = {}  # Para códigos secuenciales por capacidad
            
            for desemp_data in parsed_data["desempenos"]:
                grado_nombre = desemp_data["grado_info"]["nombre"]
                cap_orden = desemp_data["capacidad_orden"]
                cap_key = (comp_codigo, cap_orden)
                
                if grado_nombre in grados_db and cap_key in capacidades_db:
                    # Generar código secuencial
                    contador_key = (grado_nombre, cap_key)
                    if contador_key not in desempeno_contador:
                        desempeno_contador[contador_key] = 0
                    desempeno_contador[contador_key] += 1
                    codigo = str(desempeno_contador[contador_key]).zfill(2)
                    
                    desempeno = DesempenoMatematica(
                        codigo=codigo,
                        descripcion=desemp_data["descripcion"],
                        grado_id=grados_db[grado_nombre].id,
                        capacidad_id=capacidades_db[cap_key].id
                    )
                    db.add(desempeno)
        
        db.commit()
        
        # 5. Estadísticas finales
        print("\n" + "=" * 60)
        print("✅ CARGA COMPLETADA")
        print("=" * 60)
        
        total_grados = db.query(Grado).count()
        total_competencias = db.query(CompetenciaMatematica).count()
        total_capacidades = db.query(CapacidadMatematica).count()
        total_estandares = db.query(EstandarMatematica).count()
        total_desempenos = db.query(DesempenoMatematica).count()
        
        print(f"\n📊 Resumen de datos cargados:")
        print(f"   - Grados totales (con Comunicación): {total_grados}")
        print(f"   - Competencias Matemáticas: {total_competencias}")
        print(f"   - Capacidades Matemáticas: {total_capacidades}")
        print(f"   - Estándares Matemáticos: {total_estandares}")
        print(f"   - Desempeños Matemáticos: {total_desempenos}")
        
        # Detalle por competencia
        print(f"\n📈 Desempeños por competencia:")
        for comp in db.query(CompetenciaMatematica).order_by(CompetenciaMatematica.codigo).all():
            count = db.query(DesempenoMatematica).join(CapacidadMatematica).filter(
                CapacidadMatematica.competencia_id == comp.id
            ).count()
            print(f"   {comp.codigo}. {comp.nombre[:45]}...: {count}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error durante la carga: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_matematica_data()
