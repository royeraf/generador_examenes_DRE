from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base

class Docente(Base):
    """Modelo para docentes que usan el sistema."""
    __tablename__ = "docentes"
    
    id = Column(Integer, primary_key=True, index=True)
    dni = Column(String(8), unique=True, index=True, nullable=False)
    nombres = Column(String(100), nullable=True)
    password_hash = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Docente {self.dni}: {self.nombres}>"
