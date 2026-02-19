"""
Script para cargar los desempeños precisados desde Excel en la base de datos SQLite.
Ejecutar desde el directorio backend:
    python -m scripts.load_desempenos
"""

import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.db_models import Grado, Capacidad, Desempeno

# Motor síncrono para el script de carga
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./desempenos.db")
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


# Ruta al archivo Excel
EXCEL_PATH = os.path.join(os.path.dirname(__file__), "Copia de Desempeños Precisados_Ver.xlsx")


def parse_capacidad_tipo(nombre_capacidad: str) -> str:
    """Extrae el tipo de capacidad (LITERAL, INFERENCIAL, CRÍTICO)."""
    nombre_lower = nombre_capacidad.lower()
    if "literal" in nombre_lower:
        return "literal"
    elif "inferencial" in nombre_lower:
        return "inferencial"
    elif "crítico" in nombre_lower or "critico" in nombre_lower:
        return "critico"
    return "literal"


def parse_grado(nombre_grado: str) -> tuple:
    """Extrae número y nivel del grado."""
    nombre_lower = nombre_grado.lower()
    
    # Mapeo de texto a número
    numeros = {
        "primer": 1, "segundo": 2, "tercer": 3, "cuarto": 4,
        "quinto": 5, "sexto": 6
    }
    
    numero = 1
    for texto, num in numeros.items():
        if texto in nombre_lower:
            numero = num
            break
    
    nivel = "secundaria" if "secundaria" in nombre_lower else "primaria"
    
    # Orden global (primaria 1-6, secundaria 7-11)
    orden = numero if nivel == "primaria" else numero + 6
    
    return numero, nivel, orden


def is_grado_row(value: str) -> bool:
    """Detecta si una fila contiene un nombre de grado."""
    if not value:
        return False
    value_upper = str(value).upper()
    return "GRADO DE PRIMARIA" in value_upper or "GRADO DE SECUNDARIA" in value_upper


def is_capacidad_row(value: str) -> bool:
    """Detecta si una fila contiene una capacidad."""
    if not value:
        return False
    value_str = str(value)
    return (
        "Obtiene información" in value_str or
        "Infiere e interpreta" in value_str or
        "Reflexiona y evalúa" in value_str
    )


def is_desempeno_row(value: str) -> bool:
    """Detecta si una fila contiene un desempeño (empieza con número)."""
    if not value or pd.isna(value):
        return False
    value_str = str(value).strip()
    # Verifica si el formato es "XX. Descripción" donde XX es un número
    match = re.match(r'^(\d{1,2})\.\s*.+', value_str)
    return match is not None


def load_desempenos():
    """Carga los desempeños desde el Excel en la base de datos."""
    # Verificar que existe el archivo Excel
    if not os.path.exists(EXCEL_PATH):
        print(f"❌ Error: No se encontró el archivo Excel: {EXCEL_PATH}")
        return
    
    print(f"📂 Leyendo archivo: {EXCEL_PATH}")
    
    # Leer Excel
    df = pd.read_excel(EXCEL_PATH, sheet_name="Hoja 1", header=None)
    print(f"   Dimensiones: {df.shape[0]} filas x {df.shape[1]} columnas")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Limpiar datos existentes
        db.query(Desempeno).delete()
        db.query(Capacidad).delete()
        db.query(Grado).delete()
        db.commit()
        
        # Diccionarios para tracking
        grados_db = {}
        capacidades_db = {}
        
        # Variables de contexto
        current_grado = None
        current_capacidad = None
        
        # Procesar filas del Excel
        for i in range(len(df)):
            col1 = df.iloc[i, 1] if pd.notna(df.iloc[i, 1]) else ""
            col2 = df.iloc[i, 2] if pd.notna(df.iloc[i, 2]) else ""
            
            col1_str = str(col1).strip()
            col2_str = str(col2).strip()
            
            # Detectar grado
            if is_grado_row(col1_str):
                grado_nombre = col1_str.upper()
                numero, nivel, orden = parse_grado(grado_nombre)
                
                if grado_nombre not in grados_db:
                    grado = Grado(
                        nombre=grado_nombre,
                        numero=numero,
                        nivel=nivel,
                        orden=orden
                    )
                    db.add(grado)
                    db.flush()
                    grados_db[grado_nombre] = grado
                    print(f"   ✓ Grado: {grado_nombre}")
                
                current_grado = grados_db[grado_nombre]
                continue
            
            # Detectar capacidad
            if is_capacidad_row(col1_str):
                tipo = parse_capacidad_tipo(col1_str)
                capacidad_key = tipo
                
                if capacidad_key not in capacidades_db:
                    # Extraer nombre sin el paréntesis
                    nombre_capacidad = col1_str.split('(')[0].strip()
                    capacidad = Capacidad(
                        nombre=nombre_capacidad,
                        tipo=tipo,
                        descripcion=col1_str
                    )
                    db.add(capacidad)
                    db.flush()
                    capacidades_db[capacidad_key] = capacidad
                
                current_capacidad = capacidades_db[capacidad_key]
            
            # Detectar desempeño en columna 2
            if is_desempeno_row(col2_str) and current_grado and current_capacidad:
                match = re.match(r'^(\d{1,2})\.\s*(.+)$', col2_str)
                if match:
                    codigo = match.group(1).zfill(2)
                    descripcion = match.group(2).strip()
                    
                    desempeno = Desempeno(
                        codigo=codigo,
                        descripcion=descripcion,
                        grado_id=current_grado.id,
                        capacidad_id=current_capacidad.id
                    )
                    db.add(desempeno)
        
        db.commit()
        
        # Estadísticas
        total_grados = db.query(Grado).count()
        total_capacidades = db.query(Capacidad).count()
        total_desempenos = db.query(Desempeno).count()
        
        print(f"\n✅ Datos cargados exitosamente:")
        print(f"   - {total_grados} grados")
        print(f"   - {total_capacidades} capacidades")
        print(f"   - {total_desempenos} desempeños")
        
        # Detalle por grado
        print(f"\n📊 Desempeños por grado:")
        grados = db.query(Grado).order_by(Grado.orden).all()
        for grado in grados:
            count = db.query(Desempeno).filter(Desempeno.grado_id == grado.id).count()
            print(f"   {grado.nombre}: {count}")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_desempenos()
