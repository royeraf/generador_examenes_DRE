"""
Servicio para extraer texto de archivos PDF y Word.
Incluye validaciones de seguridad multicapa para prevenir archivos maliciosos.
"""
import fitz  # PyMuPDF
from docx import Document
from fastapi import UploadFile, HTTPException
import io
import re
import unicodedata
from typing import Tuple
import zipfile
import logging

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Constantes de seguridad
# ──────────────────────────────────────────────

# Tamaño máximo permitido: 10 MB
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Extensiones permitidas
ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}

# Magic bytes (firmas binarias) de cada tipo permitido
MAGIC_BYTES: dict[str, list[bytes]] = {
    "pdf":  [b"%PDF"],
    "docx": [b"PK\x03\x04"],   # ZIP (formato OOXML)
    "doc":  [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],  # OLE2 Compound Document
}

# Patrones de contenido peligroso en texto plano de PDFs
PDF_DANGEROUS_PATTERNS = [
    rb"/JavaScript",
    rb"/JS\b",
    rb"/AA\b",          # Additional Actions
    rb"/OpenAction",
    rb"/Launch",
    rb"/EmbeddedFile",
    rb"/RichMedia",
    rb"/XFA",           # XML Forms Architecture (puede ejecutar scripts)
    rb"eval\s*\(",
    rb"<script",
]

# Patrones peligrosos en XML interno de DOCX
DOCX_DANGEROUS_PATTERNS = [
    r"<\s*script",
    r"javascript\s*:",
    r"vbscript\s*:",
    r"on\w+\s*=",       # onload=, onclick=, etc.
    r"<\s*object\b",
    r"<\s*embed\b",
    r"<\s*iframe\b",
    r"macroEnabled",
    r"w:macros",
]

# Archivos XML internos del DOCX que se deben inspeccionar
DOCX_XML_MEMBERS = [
    "word/document.xml",
    "word/settings.xml",
    "word/webSettings.xml",
    "[Content_Types].xml",
    "_rels/.rels",
]


# ──────────────────────────────────────────────
# Utilidades de seguridad
# ──────────────────────────────────────────────

def sanitize_filename(filename: str) -> str:
    """
    Sanitiza el nombre del archivo:
    - Elimina caracteres de control y no ASCII peligrosos.
    - Elimina path traversal (../, ..\\ etc.).
    - Limita la longitud.
    """
    # Normalizar unicode
    filename = unicodedata.normalize("NFKD", filename)
    # Eliminar path traversal
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    # Conservar solo caracteres seguros
    filename = re.sub(r"[^\w\s.\-]", "_", filename)
    # Limitar longitud
    filename = filename[:200]
    return filename.strip() or "archivo_sin_nombre"


def validate_magic_bytes(content: bytes, extension: str) -> None:
    """
    Verifica que los primeros bytes del archivo coincidan con la firma
    real del tipo declarado por la extensión.
    Lanza HTTPException 400 si no coincide.
    """
    expected_signatures = MAGIC_BYTES.get(extension, [])
    if not expected_signatures:
        raise HTTPException(
            status_code=400,
            detail=f"Extensión '{extension}' no tiene firma conocida."
        )

    for sig in expected_signatures:
        if content.startswith(sig):
            return  # ✅ Firma válida

    raise HTTPException(
        status_code=400,
        detail=(
            f"El archivo no es un {extension.upper()} válido. "
            "El contenido real no coincide con la extensión declarada. "
            "Posible archivo malicioso o renombrado."
        )
    )


def scan_pdf_for_threats(content: bytes) -> None:
    """
    Escanea el contenido binario de un PDF en busca de patrones
    peligrosos (JavaScript embebido, acciones automáticas, etc.).
    """
    for pattern in PDF_DANGEROUS_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            logger.warning("PDF rechazado: patrón peligroso detectado: %s", pattern)
            raise HTTPException(
                status_code=400,
                detail=(
                    "El archivo PDF contiene elementos potencialmente peligrosos "
                    "(JavaScript, acciones automáticas u objetos embebidos). "
                    "Por seguridad, el archivo fue rechazado."
                )
            )


def scan_docx_for_threats(content: bytes) -> None:
    """
    Abre el DOCX como ZIP e inspecciona los archivos XML internos
    en busca de scripts, macros o contenido malicioso.
    """
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as zf:
            member_names = zf.namelist()

            # Verificar que no haya archivos ejecutables embebidos
            dangerous_embedded = [
                name for name in member_names
                if name.lower().endswith(
                    (".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jar", ".sh")
                )
            ]
            if dangerous_embedded:
                logger.warning("DOCX rechazado: archivos ejecutables embebidos: %s", dangerous_embedded)
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El archivo Word contiene archivos ejecutables embebidos. "
                        "Por seguridad, el archivo fue rechazado."
                    )
                )

            # Inspeccionar XMLs internos
            for member in DOCX_XML_MEMBERS:
                if member in member_names:
                    try:
                        xml_content = zf.read(member).decode("utf-8", errors="replace")
                        for pattern in DOCX_DANGEROUS_PATTERNS:
                            if re.search(pattern, xml_content, re.IGNORECASE):
                                logger.warning(
                                    "DOCX rechazado: patrón peligroso '%s' en %s", pattern, member
                                )
                                raise HTTPException(
                                    status_code=400,
                                    detail=(
                                        "El archivo Word contiene scripts o macros potencialmente peligrosos. "
                                        "Por seguridad, el archivo fue rechazado."
                                    )
                                )
                    except HTTPException:
                        raise
                    except Exception:
                        pass  # Si no se puede leer el XML, continuar

            # Detectar macros habilitadas (archivos .xlsm / .docm)
            macro_files = [
                name for name in member_names
                if name.lower().startswith("word/vba") or name.lower().endswith(".bin")
            ]
            if macro_files:
                logger.warning("DOCX rechazado: macros VBA detectadas: %s", macro_files)
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "El archivo Word contiene macros VBA. "
                        "Por seguridad, solo se aceptan documentos sin macros (.docx estándar)."
                    )
                )

    except HTTPException:
        raise
    except zipfile.BadZipFile:
        raise HTTPException(
            status_code=400,
            detail="El archivo .docx está corrupto o no es un documento Word válido."
        )
    except Exception as e:
        logger.error("Error al escanear DOCX: %s", e)
        raise HTTPException(
            status_code=400,
            detail="No se pudo verificar la seguridad del archivo Word."
        )


# ──────────────────────────────────────────────
# Extractores de texto
# ──────────────────────────────────────────────

def extract_text_from_pdf(file_content: bytes) -> str:
    """Extrae texto de un archivo PDF usando PyMuPDF."""
    try:
        doc = fitz.open(stream=file_content, filetype="pdf")
        text_parts = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            if text.strip():
                text_parts.append(text)

        doc.close()
        return "\n".join(text_parts)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al procesar PDF: {str(e)}"
        )


def extract_text_from_docx(file_content: bytes) -> str:
    """Extrae texto de un archivo Word (.docx)."""
    try:
        doc = Document(io.BytesIO(file_content))
        text_parts = []

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        # También extraer de tablas
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        text_parts.append(cell.text)

        return "\n".join(text_parts)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error al procesar Word: {str(e)}"
        )


# ──────────────────────────────────────────────
# Función principal (pipeline de seguridad)
# ──────────────────────────────────────────────

async def extract_text_from_file(file: UploadFile) -> Tuple[str, dict]:
    """
    Extrae texto de un archivo subido (PDF o Word) aplicando un
    pipeline de seguridad multicapa:

    1. Validar extensión permitida
    2. Sanitizar nombre de archivo
    3. Verificar tamaño máximo (10 MB)
    4. Verificar magic bytes (firma real del archivo)
    5. Escanear contenido en busca de amenazas
    6. Extraer texto

    Returns:
        Tuple con (texto_extraido, metadata)
    """
    # ── 1. Validar extensión ──────────────────
    filename = file.filename or "sin_nombre"
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Tipo de archivo no permitido: '.{extension}'. "
                f"Solo se aceptan: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )
        )

    # ── 2. Sanitizar nombre ───────────────────
    safe_filename = sanitize_filename(filename)

    # ── 3. Leer contenido y verificar tamaño ─
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="El archivo está vacío.")

    if len(content) > MAX_FILE_SIZE_BYTES:
        size_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=(
                f"El archivo '{safe_filename}' pesa {size_mb:.1f} MB. "
                f"El tamaño máximo permitido es {MAX_FILE_SIZE_BYTES // (1024*1024)} MB."
            )
        )

    # ── 4. Verificar magic bytes ──────────────
    validate_magic_bytes(content, extension)

    # ── 5. Escanear amenazas ──────────────────
    if extension == "pdf":
        scan_pdf_for_threats(content)
    elif extension in ("docx", "doc"):
        # .doc (OLE2) no es ZIP, solo escaneamos DOCX
        if extension == "docx":
            scan_docx_for_threats(content)

    # ── 6. Extraer texto ──────────────────────
    if extension == "pdf":
        text = extract_text_from_pdf(content)
    elif extension in ("docx", "doc"):
        text = extract_text_from_docx(content)
    else:
        raise HTTPException(status_code=400, detail="Tipo de archivo no soportado.")

    text = text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail=(
                "No se pudo extraer texto del archivo. "
                "Verifique que el archivo contenga texto legible (no sea una imagen escaneada)."
            )
        )

    metadata = {
        "filename": safe_filename,
        "filename_original": filename,
        "extension": extension,
        "size_bytes": len(content),
        "size_kb": round(len(content) / 1024, 1),
        "caracteres": len(text),
        "palabras": len(text.split()),
        "lineas": text.count("\n") + 1,
    }

    logger.info(
        "Archivo procesado correctamente: %s (%s KB, %s palabras)",
        safe_filename, metadata["size_kb"], metadata["palabras"]
    )

    return text, metadata
