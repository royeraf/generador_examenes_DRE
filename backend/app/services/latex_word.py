r"""
Convierte fragmentos de texto con LaTeX simple ($...$ / $$...$$) a runs de
python-docx con superíndice/subíndice nativos y símbolos Unicode, para que
el examen exportado a Word muestre ecuaciones legibles sin depender de
ninguna librería nueva (sin OMML/MathML).

No es un motor LaTeX completo: cubre el subconjunto típico de matemática
escolar (potencias, subíndices, fracciones simples, raíces, operadores y
símbolos griegos/comparación más comunes). Un comando no reconocido se
emite sin el backslash, para nunca dejar un "\comando" crudo en el documento.

IMPORTANTE: el tokenizador de delimitadores ($$...$$, $...$, \[...\], \(...\))
debe mantenerse en sincronía con frontend/src/shared/components/MathText.vue.
"""
import re
from typing import Optional

# --- Segmentación texto plano / matemática -----------------------------------

_MATH_SEGMENT_RE = re.compile(
    r'\$\$([\s\S]+?)\$\$|\\\[([\s\S]+?)\\\]|\\\(([\s\S]+?)\\\)|\$(?!\s)([^$\n]+?)(?<!\s)\$'
)


def split_segments(text: str):
    """Devuelve [(contenido, es_math), ...] preservando el texto plano intacto."""
    segments = []
    last = 0
    for m in _MATH_SEGMENT_RE.finditer(text):
        display, bracket, paren, inline = m.groups()
        expr = display if display is not None else bracket if bracket is not None else paren if paren is not None else inline
        if m.start() > last:
            segments.append((text[last:m.start()], False))
        segments.append((expr, True))
        last = m.end()
    if last < len(text):
        segments.append((text[last:], False))
    if not segments:
        segments.append((text, False))
    return segments


# --- Tokenizador LaTeX ---------------------------------------------------------

_TOKEN_RE = re.compile(r'\\[a-zA-Z]+|\\.|[{}^_\[\]]|[^\\{}^_\[\]]+')

_SYMBOLS = {
    'times': '×', 'div': '÷', 'pm': '±', 'mp': '∓', 'cdot': '·',
    'cdots': '…', 'ldots': '…', 'dots': '…',
    'le': '≤', 'leq': '≤', 'ge': '≥', 'geq': '≥', 'ne': '≠', 'neq': '≠',
    'approx': '≈', 'equiv': '≡', 'infty': '∞', 'angle': '∠', 'sum': 'Σ', 'in': '∈',
    'to': '→', 'rightarrow': '→', 'Rightarrow': '⇒',
    'pi': 'π', 'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'theta': 'θ', 'delta': 'Δ',
    'circ': '°', 'degree': '°',
    'left': '', 'right': '', 'quad': ' ', 'qquad': '  ',
    ',': ' ', ';': ' ', '!': '', '%': '%', '$': '$', '&': '&',
}

_OPERATOR_CHARS = set('+-±×÷=<> ')


def _tokenize(expr: str) -> list:
    return list(_TOKEN_RE.findall(expr))


def _consume_group(tokens: list, i: int):
    """A partir de tokens[i] == '{', consume hasta el '}' que cierra
    (balanceando anidamiento). Devuelve (tokens_internos, siguiente_indice)."""
    depth = 1
    j = i + 1
    inner = []
    while j < len(tokens) and depth > 0:
        t = tokens[j]
        if t == '{':
            depth += 1
        elif t == '}':
            depth -= 1
            if depth == 0:
                j += 1
                break
        if not (t == '}' and depth == 0):
            inner.append(t)
        j += 1
    return inner, j


def _consume_atom(tokens: list, i: int):
    """Consume el 'átomo' que sigue a ^, _ o \\frac/\\sqrt: un grupo {...} o
    un solo carácter/comando. Si el token en tokens[i] es texto plano de más
    de un carácter, sólo se toma el primero y el resto queda para la
    siguiente lectura (mutamos tokens[i] in-place; misma semántica que
    "x^24" = (x²)4 en LaTeX real)."""
    if i < len(tokens) and tokens[i] == '{':
        return _consume_group(tokens, i)
    if i >= len(tokens):
        return [], i
    tok = tokens[i]
    if tok.startswith('\\') or tok in ('^', '_', '[', ']'):
        return [tok], i + 1
    if len(tok) > 1:
        tokens[i] = tok[1:]
        return [tok[0]], i
    return [tok], i + 1


def _symbol_text(cmd: str) -> str:
    name = cmd[1:]
    if name in _SYMBOLS:
        return _SYMBOLS[name]
    if len(name) == 1 and not name.isalpha():
        return name  # \%, \$, \_, \& ...
    return name  # comando desconocido: se deja el nombre sin el backslash


def _flatten_plain(tokens: list) -> str:
    """Aplana tokens a texto plano, sin conservar formato. Se usa sólo para
    decidir si un numerador/denominador/radicando necesita paréntesis."""
    out = []
    i = 0
    n = len(tokens)
    while i < n:
        t = tokens[i]
        if t in ('^', '_'):
            atom, i = _consume_atom(tokens, i + 1)
            out.append(_flatten_plain(atom))
            continue
        if t == '{':
            group, i = _consume_group(tokens, i)
            out.append(_flatten_plain(group))
            continue
        if t.startswith('\\'):
            out.append(_symbol_text(t))
        else:
            out.append(t)
        i += 1
    return ''.join(out)


def _needs_parens(tokens: list) -> bool:
    text = _flatten_plain(tokens).strip()
    return len(text) != 1 and any(ch in _OPERATOR_CHARS for ch in text)


def _emit(paragraph, tokens: list, *, bold: bool, italic: bool, superscript: bool, subscript: bool):
    i = 0
    n = len(tokens)
    while i < n:
        t = tokens[i]

        if t == '^' or t == '_':
            is_super = (t == '^')
            atom, i = _consume_atom(tokens, i + 1)
            # ^\circ (grados) no es un superíndice real, es un símbolo
            if is_super and len(atom) == 1 and atom[0] in ('\\circ', '\\degree'):
                run = paragraph.add_run('°')
                run.bold = bold
                run.italic = italic
                continue
            _emit(paragraph, atom, bold=bold, italic=italic,
                  superscript=is_super, subscript=not is_super)
            continue

        if t == '{':
            group, i = _consume_group(tokens, i)
            _emit(paragraph, group, bold=bold, italic=italic,
                  superscript=superscript, subscript=subscript)
            continue

        if t in ('\\frac', '\\dfrac', '\\tfrac'):
            i += 1
            num, i = _consume_atom(tokens, i)
            den, i = _consume_atom(tokens, i)
            _emit_side(paragraph, num, bold, italic, superscript, subscript)
            plain = paragraph.add_run('/')
            plain.bold = bold
            plain.italic = italic
            _emit_side(paragraph, den, bold, italic, superscript, subscript)
            continue

        if t in ('\\sqrt',):
            i += 1
            index_tokens = None
            if i < len(tokens) and tokens[i] == '[':
                j = i + 1
                idx_inner = []
                while j < len(tokens) and tokens[j] != ']':
                    idx_inner.append(tokens[j])
                    j += 1
                index_tokens = idx_inner
                i = j + 1
            radicand, i = _consume_atom(tokens, i)
            if index_tokens:
                _emit(paragraph, index_tokens, bold=bold, italic=italic,
                      superscript=True, subscript=False)
            run = paragraph.add_run('√')
            run.bold = bold
            run.italic = italic
            _emit_side(paragraph, radicand, bold, italic, superscript, subscript, force_parens=_needs_parens(radicand) or len(radicand) != 1)
            continue

        if t.startswith('\\'):
            text = _symbol_text(t)
            if text:
                run = paragraph.add_run(text)
                run.bold = bold
                run.italic = italic
                run.font.superscript = superscript
                run.font.subscript = subscript
            i += 1
            continue

        run = paragraph.add_run(t)
        run.bold = bold
        run.italic = italic
        run.font.superscript = superscript
        run.font.subscript = subscript
        i += 1


def _emit_side(paragraph, tokens, bold, italic, superscript, subscript, force_parens: Optional[bool] = None):
    paren = _needs_parens(tokens) if force_parens is None else force_parens
    if paren:
        run = paragraph.add_run('(')
        run.bold = bold
        run.italic = italic
    _emit(paragraph, tokens, bold=bold, italic=italic, superscript=superscript, subscript=subscript)
    if paren:
        run = paragraph.add_run(')')
        run.bold = bold
        run.italic = italic


# --- API pública ---------------------------------------------------------------

def add_latex_runs(paragraph, text: Optional[str], *, bold: bool = False, italic: bool = False) -> None:
    """Escribe `text` en `paragraph`, convirtiendo los tramos LaTeX ($...$,
    $$...$$) a runs con superíndice/subíndice nativos y símbolos Unicode.
    El texto plano (o cualquier texto sin delimitadores) se agrega tal cual,
    idéntico al comportamiento previo — no rompe exámenes ya generados."""
    if not text:
        return
    for content, is_math in split_segments(text):
        if not content:
            continue
        if is_math:
            try:
                tokens = _tokenize(content)
                _emit(paragraph, tokens, bold=bold, italic=italic, superscript=False, subscript=False)
            except Exception:
                # Nunca romper la generación del Word por una fórmula rara:
                # se deja el texto original tal cual, delimitadores incluidos.
                run = paragraph.add_run(f"${content}$")
                run.bold = bold
                run.italic = italic
        else:
            run = paragraph.add_run(content)
            run.bold = bold
            run.italic = italic


def set_cell_text(cell, text: Optional[str], *, align=None, bold: bool = False) -> None:
    """Equivalente a `cell.text = text` pero soportando LaTeX. Asignar
    `cell.text` directamente destruye la estructura de párrafo/runs de la
    celda, así que en su lugar limpiamos los runs existentes y delegamos en
    add_latex_runs."""
    para = cell.paragraphs[0]
    for run in list(para.runs):
        run._element.getparent().remove(run._element)
    add_latex_runs(para, text or "", bold=bold)
    if align is not None:
        para.alignment = align


def truncate_math_safe(text: str, limit: int) -> str:
    """Trunca `text` a `limit` caracteres sin cortar a la mitad de una
    fórmula $...$: si el corte deja un número impar de '$' sin escapar,
    recorta hasta antes del último '$'."""
    if not text or len(text) <= limit:
        return text or ""
    cut = text[:limit]
    if cut.count('$') % 2 == 1:
        last_dollar = cut.rfind('$')
        if last_dollar != -1:
            cut = cut[:last_dollar]
    return cut + "..."
