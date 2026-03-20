from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Provincia(Base):
    __tablename__ = "provincias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)

    distritos = relationship("Distrito", back_populates="provincia", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Provincia {self.nombre}>"


class Distrito(Base):
    __tablename__ = "distritos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    provincia_id = Column(Integer, ForeignKey("provincias.id", ondelete="CASCADE"), nullable=False)

    provincia = relationship("Provincia", back_populates="distritos")

    def __repr__(self):
        return f"<Distrito {self.nombre}>"
