# Alias de compatibilidad — todo el código nuevo debe importar desde usuario_service
from app.services.usuario_service import usuario_service, UsuarioService

docente_service = usuario_service
DocenteService = UsuarioService
