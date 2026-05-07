"""
Script para cargar las provincias y distritos de Huánuco en la base de datos.
Ejecutar desde el directorio backend:
    python -m scripts.load_ubigeo
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.ubigeo import Provincia, Distrito

# Motor síncrono para el script de carga
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./desempenos.db")
if DATABASE_URL.startswith("postgresql+asyncpg://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
elif DATABASE_URL.startswith("mysql+aiomysql://"):
    DATABASE_URL = DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL)
elif DATABASE_URL.startswith("mysql"):
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

# 11 provincias de Huánuco con todos sus distritos
UBIGEO_HUANUCO = {
    "Huánuco": [
        "Huánuco", "Amarilis", "Chinchao", "Churubamba", "Margos",
        "Quisqui (Kichki)", "San Francisco de Cayrán", "San Pedro de Chaulán",
        "Santa María del Valle", "Yarumayo", "Pillco Marca", "Yacus",
        "San Pablo de Pillao",
    ],
    "Ambo": [
        "Ambo", "Cayna", "Colpas", "Conchamarca", "Huácar",
        "San Francisco", "San Rafael", "Tomay Kichwa",
    ],
    "Dos de Mayo": [
        "La Unión", "Chuquis", "Marías", "Pachas", "Quivilla",
        "Ripán", "Shunqui", "Sillapata", "Yanas",
    ],
    "Huacaybamba": [
        "Huacaybamba", "Canchabamba", "Cochabamba", "Pinra",
    ],
    "Huamalíes": [
        "Llata", "Arancay", "Chavín de Pariarca", "Jacas Grande",
        "Jircán", "Miraflores", "Monzón", "Punchao", "Puños",
        "Singa", "Tantamayo",
    ],
    "Leoncio Prado": [
        "Rupa-Rupa", "Daniel Alomía Robles", "Hermilio Valdizán",
        "José Crespo y Castillo", "Luyando", "Mariano Dámaso Beraún",
        "Pucayacu", "Castillo Grande", "Pueblo Nuevo",
        "Santo Domingo de Anda",
    ],
    "Marañón": [
        "Huacrachuco", "Cholón", "San Buenaventura", "La Morada",
        "Santa Rosa de Alto Yanajanca",
    ],
    "Pachitea": [
        "Panao", "Chaglla", "Molino", "Umari",
    ],
    "Puerto Inca": [
        "Puerto Inca", "Codo del Pozuzo", "Honoria",
        "Tournavista", "Yuyapichis",
    ],
    "Lauricocha": [
        "Jesús", "Baños", "Jivia", "Queropalca",
        "Rondos", "San Francisco de Asís", "San Miguel de Cauri",
    ],
    "Yarowilca": [
        "Chavinillo", "Cahuac", "Chacabamba", "Aparicio Pomares",
        "Jacas Chico", "Obas", "Pampamarca", "Choras",
    ],
}


def load_ubigeo():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()

    try:
        created_prov = 0
        created_dist = 0

        for prov_nombre, distritos in UBIGEO_HUANUCO.items():
            provincia = session.query(Provincia).filter_by(nombre=prov_nombre).first()
            if not provincia:
                provincia = Provincia(nombre=prov_nombre)
                session.add(provincia)
                session.flush()
                created_prov += 1

            for dist_nombre in distritos:
                exists = (
                    session.query(Distrito)
                    .filter_by(nombre=dist_nombre, provincia_id=provincia.id)
                    .first()
                )
                if not exists:
                    session.add(Distrito(nombre=dist_nombre, provincia_id=provincia.id))
                    created_dist += 1

        session.commit()
        print(f"Ubigeo cargado: {created_prov} provincias nuevas, {created_dist} distritos nuevos.")
        print(f"Total: {len(UBIGEO_HUANUCO)} provincias, {sum(len(d) for d in UBIGEO_HUANUCO.values())} distritos.")

    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    load_ubigeo()
