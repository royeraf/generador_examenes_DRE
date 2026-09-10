"""
Servicio para extraer texto de archivos PDF y Word.
Incluye validaciones de seguridad multicapa para prevenir archivos maliciosos.
Los PDF escaneados (solo imágenes) se procesan con OCR (Tesseract, spa+eng).
Requiere en el servidor: binario `tesseract-ocr` + datos `spa`, y `pytesseract`.
"""
import fitz  # PyMuPDF
from docx import Document
from fastapi import UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
import io
import re
import unicodedata
from typing import Tuple
import zipfile
import logging


logger = logging.getLogger(__name__)


class FileExtractionService:

    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "docx", "doc"}

    # ── OCR (fallback para PDFs escaneados / sin texto embebido) ──────────────
    # Si una página aporta menos caracteres que este umbral, se asume que es
    # una imagen escaneada y se procesa con Tesseract vía pytesseract.
    OCR_MIN_CHARS_PER_PAGE = 20
    # Límite de páginas a procesar con OCR por archivo (protege CPU/tiempo).
    OCR_MAX_PAGES = 10
    # Zoom de renderizado (72 dpi base × 3 ≈ 216 dpi, suficiente para OCR).
    OCR_ZOOM = 3.0
    # Español primero (lecturas de aula), inglés como respaldo.
    OCR_LANG = "spa+eng"

    MAGIC_BYTES: dict[str, list[bytes]] = {
        "pdf":  [b"%PDF"],
        "docx": [b"PK\x03\x04"],
        "doc":  [b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"],
    }

    # ── Escáner PDF estructural ──────────────────────────────────────────────
    # El escáner anterior buscaba patrones con regex sobre los bytes crudos,
    # incluyendo streams comprimidos de imágenes: cualquier PDF con fotos
    # (p. ej. CamScanner) podía ser rechazado por una coincidencia aleatoria.
    # Ahora se inspeccionan los diccionarios reales del PDF con PyMuPDF
    # (los bytes de imágenes nunca se tocan): cero falsos positivos sin
    # perder la detección de amenazas estructurales.
    # Follow-up posible: análisis estructural ya implementado aquí.

    # Tipos de acción peligrosos (/S en diccionarios de acción).
    # /GoTo, /GoToR, /URI y transiciones (/Trans) se permiten: son benignos.
    PDF_THREAT_ACTIONS = {"JavaScript", "Launch", "SubmitForm", "ImportData"}

    # Claves que nunca aparecen en un PDF benigno.
    PDF_THREAT_KEYS = {"JS", "JavaScript", "XFA", "EF", "RichMedia"}

    DOCX_DANGEROUS_PATTERNS = [
        r"<\s*script",
        r"javascript\s*:",
        r"vbscript\s*:",
        r"\bon\w+\s*=",
        r"<\s*object\b",
        r"<\s*embed\b",
        r"<\s*iframe\b",
        r"macroEnabled",
        r"w:macros",
    ]

    DOCX_XML_MEMBERS = [
        "word/document.xml",
        "word/settings.xml",
        "word/webSettings.xml",
        "[Content_Types].xml",
        "_rels/.rels",
    ]

    # ── Seguridad ──────────────────────────────────────────────────────────────

    def _sanitize_filename(self, filename: str) -> str:
        filename = unicodedata.normalize("NFKD", filename)
        filename = filename.replace("..", "").replace("/", "").replace("\\", "")
        filename = re.sub(r"[^\w\s.\-]", "_", filename)
        filename = filename[:200]
        return filename.strip() or "archivo_sin_nombre"

    def _validate_magic_bytes(self, content: bytes, extension: str) -> None:
        expected = self.MAGIC_BYTES.get(extension, [])
        if not expected:
            raise HTTPException(400, f"Extensión '{extension}' no tiene firma conocida.")
        for sig in expected:
            if content.startswith(sig):
                return
        raise HTTPException(
            status_code=400,
            detail=(
                f"El archivo no es un {extension.upper()} válido. "
                "El contenido real no coincide con la extensión declarada. "
                "Posible archivo malicioso o renombrado."
            ),
        )

    def _reject_pdf(self, motivo: str) -> None:
        logger.warning("PDF rechazado: %s", motivo)
        raise HTTPException(
            status_code=400,
            detail=(
                "El archivo PDF contiene elementos potencialmente peligrosos "
                "(JavaScript, acciones automáticas u objetos embebidos). "
                "Por seguridad, el archivo fue rechazado."
            ),
        )

    def _resolve_pdf_value(self, doc, value: str, depth: int = 0) -> str:
        """Resuelve referencias indirectas ('12 0 R') a su diccionario real."""
        value = (value or "").strip()
        if depth > 3:
            return value
        m = re.fullmatch(r"(\d+)\s+\d+\s+R", value)
        if not m:
            return value
        try:
            return self._resolve_pdf_value(doc, doc.xref_object(int(m.group(1))), depth + 1)
        except Exception:
            return value

    def _dict_value(self, doc, xref: int, key: str) -> str:
        """Valor resuelto de una clave de diccionario ('' si no existe)."""
        try:
            raw = doc.xref_get_key(xref, key)
        except Exception:
            return ""
        if raw is None:
            return ""
        if not isinstance(raw, str):
            raw = str(raw)
        if raw.strip() in ("", "null"):
            return ""
        return self._resolve_pdf_value(doc, raw)

    def _has_threat_action(self, dict_text: str) -> bool:
        """¿El diccionario contiene una acción peligrosa (/S /JavaScript, ...)?"""
        m = re.search(r"/S\s*/(\w+)", dict_text)
        return bool(m and m.group(1) in self.PDF_THREAT_ACTIONS)

    def _scan_pdf_for_threats(self, content: bytes) -> None:
        """Inspección estructural del PDF (diccionarios, no bytes crudos).

        Rechaza: JavaScript, acciones de lanzamiento/envío, archivos
        embebidos, XFA y RichMedia. Permite: destinos de apertura benignos
        (/OpenAction con /GoTo), enlaces URI y el texto/imágenes normales
        aunque contengan palabras como 'XFA' o 'eval('.
        """
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            raise HTTPException(400, f"El archivo no es un PDF válido: {e}")
        try:
            # 1. Archivos embebidos (árbol /EmbeddedFiles).
            try:
                emb = doc.embfile_names()
            except Exception:
                emb = []
            if emb:
                self._reject_pdf(f"archivos embebidos: {emb[:3]}")

            catalog = doc.pdf_catalog()

            # 2. Árbol de nombres JavaScript (ningún PDF benigno lo trae).
            names = self._dict_value(doc, catalog, "Names")
            if names and "/JavaScript" in names:
                self._reject_pdf("árbol de nombres JavaScript")

            # 3. XFA en el formulario AcroForm.
            acroform = self._dict_value(doc, catalog, "AcroForm")
            if acroform and re.search(r"/XFA\b", acroform):
                self._reject_pdf("formulario XFA")

            # 4. Acciones automáticas del catálogo (/OpenAction, /AA):
            # solo rechaza si la acción es peligrosa (/GoTo es benigno).
            for key in ("OpenAction", "AA"):
                value = self._dict_value(doc, catalog, key)
                if value and self._has_threat_action(value):
                    self._reject_pdf(f"acción automática peligrosa ({key})")

            # 5. Barrido de objetos: claves y acciones a nivel de diccionario.
            # Los streams binarios (fotos) nunca se inspeccionan.
            for xref in range(doc.xref_length()):
                try:
                    keys = doc.xref_get_keys(xref)
                except Exception:
                    continue
                if not keys:
                    continue
                if any(k in self.PDF_THREAT_KEYS for k in keys):
                    self._reject_pdf(f"clave peligrosa en objeto {xref}")
                if "S" in keys:
                    try:
                        raw_s = doc.xref_get_key(xref, "S")
                        action = (raw_s if isinstance(raw_s, str) else str(raw_s)).strip().lstrip("/")
                    except Exception:
                        continue
                    if action in self.PDF_THREAT_ACTIONS:
                        self._reject_pdf(f"acción /{action} en objeto {xref}")
                if "AA" in keys:
                    aa = self._dict_value(doc, xref, "AA")
                    if aa and self._has_threat_action(aa):
                        self._reject_pdf(f"acción adicional peligrosa en objeto {xref}")
        finally:
            doc.close()

    def _scan_docx_for_threats(self, content: bytes) -> None:
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                member_names = zf.namelist()

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
                        ),
                    )

                for member in self.DOCX_XML_MEMBERS:
                    if member in member_names:
                        try:
                            xml_content = zf.read(member).decode("utf-8", errors="replace")
                            for pattern in self.DOCX_DANGEROUS_PATTERNS:
                                if re.search(pattern, xml_content, re.IGNORECASE):
                                    logger.warning(
                                        "DOCX rechazado: patrón peligroso '%s' en %s", pattern, member
                                    )
                                    raise HTTPException(
                                        status_code=400,
                                        detail=(
                                            "El archivo Word contiene scripts o macros potencialmente peligrosos. "
                                            "Por seguridad, el archivo fue rechazado."
                                        ),
                                    )
                        except HTTPException:
                            raise
                        except Exception:
                            pass

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
                        ),
                    )

        except HTTPException:
            raise
        except zipfile.BadZipFile:
            raise HTTPException(400, "El archivo .docx está corrupto o no es un documento Word válido.")
        except Exception as e:
            logger.error("Error al escanear DOCX: %s", e)
            raise HTTPException(400, "No se pudo verificar la seguridad del archivo Word.")

    # ── Extracción de texto ────────────────────────────────────────────────────

    def _ocr_pdf_pages(self, doc, page_numbers: list[int]) -> Tuple[list, int]:
        """Aplica OCR (Tesseract) a las páginas indicadas.

        Retorna (textos_por_pagina, n_paginas_ok) manteniendo el orden de
        `page_numbers`. Los imports son diferidos para que el servicio siga
        funcionando aunque las dependencias de OCR no estén instaladas.
        """
        try:
            from PIL import Image
            import pytesseract
            pytesseract.get_tesseract_version()
        except ImportError:
            raise HTTPException(
                status_code=400,
                detail=(
                    "El PDF parece ser una imagen escaneada y el servidor no tiene "
                    "habilitado el reconocimiento de texto (OCR). "
                    "Pruebe con un PDF con texto seleccionable o un Word."
                ),
            )
        except Exception:
            logger.error("Binario de Tesseract no disponible para OCR")
            raise HTTPException(
                status_code=400,
                detail=(
                    "El PDF parece ser una imagen escaneada y el OCR no está "
                    "disponible en este momento. Intente más tarde o use un "
                    "PDF con texto seleccionable."
                ),
            )

        matrix = fitz.Matrix(self.OCR_ZOOM, self.OCR_ZOOM)
        ocr_texts: list = []
        for page_num in page_numbers:
            try:
                pix = doc[page_num].get_pixmap(matrix=matrix)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                page_text = pytesseract.image_to_string(img, lang=self.OCR_LANG).strip()
            except Exception as e:
                logger.warning("OCR falló en página %s: %s", page_num + 1, e)
                page_text = ""
            ocr_texts.append(page_text)
        ok_pages = sum(1 for t in ocr_texts if t)
        return ocr_texts, ok_pages

    def _extract_text_from_pdf(self, content: bytes) -> Tuple[str, dict]:
        """Extrae texto embebido y aplica OCR por página cuando falta texto.

        Retorna (texto, info_ocr) donde info_ocr incluye `ocr_aplicado` y,
        de ser el caso, `ocr_paginas` y `ocr_paginas_omitidas`.
        """
        try:
            doc = fitz.open(stream=content, filetype="pdf")
        except Exception as e:
            raise HTTPException(400, f"Error al procesar PDF: {e}")
        try:
            page_texts: dict[int, str] = {}
            scanned_pages: list[int] = []
            for i, page in enumerate(doc):
                try:
                    t = page.get_text().strip()
                except Exception:
                    t = ""
                if len(t) >= self.OCR_MIN_CHARS_PER_PAGE:
                    page_texts[i] = t
                else:
                    scanned_pages.append(i)

            ocr_info: dict = {"ocr_aplicado": False, "total_paginas": len(doc)}
            if scanned_pages:
                to_ocr = scanned_pages[: self.OCR_MAX_PAGES]
                omitted = len(scanned_pages) - len(to_ocr)
                logger.info(
                    "PDF con %s página(s) escaneada(s), aplicando OCR a %s",
                    len(scanned_pages), len(to_ocr),
                )
                ocr_texts, ok_pages = self._ocr_pdf_pages(doc, to_ocr)
                for page_num, ocr_text in zip(to_ocr, ocr_texts):
                    if ocr_text:
                        page_texts[page_num] = ocr_text
                if ok_pages > 0:
                    ocr_info = {
                        "ocr_aplicado": True,
                        "ocr_paginas": ok_pages,
                        "ocr_idioma": self.OCR_LANG,
                    }
                    if omitted:
                        ocr_info["ocr_paginas_omitidas"] = omitted
                elif not page_texts:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "No se pudo extraer texto del PDF, ni siquiera con "
                            "reconocimiento óptico (OCR). Verifique que las imágenes "
                            "sean legibles (buena resolución, sin fotos borrosas)."
                        ),
                    )
                # Si el OCR no rescató nada pero hay algo de texto embebido,
                # se continúa con ese texto (el pipeline valida el mínimo).

            ordered = [page_texts[i] for i in sorted(page_texts)]
            return "\n".join(ordered), ocr_info
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Error al procesar PDF: {e}")
        finally:
            doc.close()

    def _extract_text_from_docx(self, content: bytes) -> str:
        try:
            doc = Document(io.BytesIO(content))
            text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            text_parts.append(cell.text)
            return "\n".join(text_parts)
        except Exception as e:
            raise HTTPException(400, f"Error al procesar Word: {e}")

    def _validate_scan_and_extract(self, content: bytes, extension: str) -> Tuple[str, dict]:
        """Trabajo CPU-bound (magic bytes, escaneo de amenazas, extracción de texto).

        Se ejecuta en threadpool porque bloquearía el event loop si corriera
        directamente dentro de la ruta async (archivos grandes/lentos frenan
        a todos los usuarios conectados al mismo worker).

        Retorna (texto, info_extra) donde info_extra trae datos de OCR
        cuando aplicó (solo PDF).
        """
        self._validate_magic_bytes(content, extension)

        if extension == "pdf":
            self._scan_pdf_for_threats(content)
        elif extension == "docx":
            self._scan_docx_for_threats(content)

        if extension == "pdf":
            return self._extract_text_from_pdf(content)
        return self._extract_text_from_docx(content), {}

    # ── Pipeline público ───────────────────────────────────────────────────────

    async def extract_text_from_file(self, file: UploadFile) -> Tuple[str, dict]:
        """
        Pipeline de seguridad multicapa:
        1. Validar extensión  2. Sanitizar nombre  3. Verificar tamaño
        4. Verificar magic bytes  5. Escanear amenazas  6. Extraer texto
        """
        filename = file.filename or "sin_nombre"
        extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

        if extension not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Tipo de archivo no permitido: '.{extension}'. "
                    f"Solo se aceptan: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
                ),
            )

        safe_filename = self._sanitize_filename(filename)
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(400, "El archivo está vacío.")
        if len(content) > self.MAX_FILE_SIZE_BYTES:
            size_mb = len(content) / (1024 * 1024)
            raise HTTPException(
                status_code=413,
                detail=(
                    f"El archivo '{safe_filename}' pesa {size_mb:.1f} MB. "
                    f"El tamaño máximo permitido es {self.MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB."
                ),
            )

        text, extra = await run_in_threadpool(self._validate_scan_and_extract, content, extension)

        text = text.strip()
        if not text:
            raise HTTPException(
                status_code=400,
                detail=(
                    "No se pudo extraer texto del archivo, ni siquiera con "
                    "reconocimiento óptico (OCR). Verifique que el contenido "
                    "sea legible."
                ),
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
            "ocr_aplicado": bool(extra.get("ocr_aplicado", False)),
        }
        if extra.get("ocr_aplicado"):
            metadata["ocr_paginas"] = extra.get("ocr_paginas", 0)
            if extra.get("ocr_paginas_omitidas"):
                metadata["ocr_paginas_omitidas"] = extra["ocr_paginas_omitidas"]
        if extra.get("total_paginas"):
            metadata["total_paginas"] = extra["total_paginas"]

        logger.info(
            "Archivo procesado correctamente: %s (%s KB, %s palabras, ocr=%s)",
            safe_filename, metadata["size_kb"], metadata["palabras"],
            metadata["ocr_aplicado"],
        )

        return text, metadata


file_extraction_service = FileExtractionService()
