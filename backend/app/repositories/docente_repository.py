# Alias de compatibilidad — todo el código nuevo debe importar desde usuario_repository
from app.repositories.usuario_repository import usuario_repository, UsuarioRepository

docente_repository = usuario_repository
DocenteRepository = UsuarioRepository
