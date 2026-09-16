from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index

from app.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SesionAcceso(Base):
    """Registro de sesiones (y intentos fallidos) para el módulo de monitoreo."""

    __tablename__ = "sesiones_acceso"

    id = Column(Integer, primary_key=True, index=True)

    # Identificador del token JWT (null en intentos fallidos)
    jti = Column(String(36), unique=True, index=True, nullable=True)

    # True = credenciales válidas; False = intento fallido
    exito = Column(Boolean, default=True, nullable=False, index=True)
    motivo = Column(String(50), nullable=True)

    # Identidad del usuario (usuario staff o estudiante)
    tipo_usuario = Column(String(20), nullable=True)  # "usuario" | "estudiante"
    usuario_id = Column(Integer, nullable=True, index=True)
    identificador = Column(String(20), nullable=True, index=True)
    nombres = Column(String(100), nullable=True)
    apellidos = Column(String(100), nullable=True)
    rol_codigo = Column(String(30), nullable=True, index=True)

    # Ubicación organizacional (para estadísticas)
    institucion_educativa_id = Column(Integer, nullable=True, index=True)
    ugel_id = Column(Integer, nullable=True, index=True)

    # Metadata de la conexión
    ip = Column(String(64), nullable=True)
    user_agent = Column(Text, nullable=True)
    dispositivo = Column(String(20), nullable=True)  # desktop | mobile | tablet
    sistema_operativo = Column(String(40), nullable=True)
    navegador = Column(String(40), nullable=True)
    es_movil = Column(Boolean, default=False, nullable=False)

    # Ciclo de vida de la sesión
    login_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False, index=True)
    last_activity = Column(DateTime(timezone=True), default=_utcnow, nullable=True, index=True)
    logout_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False, index=True)

    __table_args__ = (
        Index("ix_sesiones_activas", "exito", "logout_at", "last_activity"),
    )

    def __repr__(self):
        return f"<SesionAcceso {self.identificador} {self.ip} exito={self.exito}>"
