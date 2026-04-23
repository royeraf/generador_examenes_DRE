# Alias de compatibilidad — todo el código nuevo debe importar desde schemas/usuario.py
from app.schemas.usuario import (
    Usuario as Docente,
    UsuarioAdminCreate as DocenteAdminCreate,
    UsuarioUpdate as DocenteUpdate,
    UsuarioBase as DocenteBase,
    UsuarioInDB as DocenteInDB,
    UsuarioAdminCreate as DocenteCreate,
)

__all__ = ["Docente", "DocenteAdminCreate", "DocenteUpdate", "DocenteBase", "DocenteInDB", "DocenteCreate"]
