"""
Servicio para extraer texto de archivos PDF y Word.
"""
import fitz  # PyMuPDF
from docx import Document
from fastapi import UploadFile, HTTPException
import io
from typing import Tuple


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


async def extract_text_from_file(file: UploadFile) -> Tuple[str, dict]:
    """
    Extrae texto de un archivo subido (PDF o Word).
    
    Returns:
        Tuple con (texto_extraido, metadata)
    """
    # Validar extensión
    filename = file.filename or ""
    extension = filename.lower().split(".")[-1] if "." in filename else ""
    
    allowed_extensions = ["pdf", "docx", "doc"]
    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de archivo no soportado. Use: {', '.join(allowed_extensions)}"
        )
    
    # Leer contenido
    content = await file.read()
    
    # Extraer texto según tipo
    if extension == "pdf":
        text = extract_text_from_pdf(content)
    elif extension in ["docx", "doc"]:
        text = extract_text_from_docx(content)
    else:
        raise HTTPException(status_code=400, detail="Tipo de archivo no soportado")
    
    # Limpiar texto
    text = text.strip()
    
    if not text:
        raise HTTPException(
            status_code=400,
            detail="No se pudo extraer texto del archivo. Verifique que el archivo contenga texto legible."
        )
    
    metadata = {
        "filename": filename,
        "extension": extension,
        "caracteres": len(text),
        "palabras": len(text.split()),
        "lineas": text.count("\n") + 1
    }
    
    return text, metadata
