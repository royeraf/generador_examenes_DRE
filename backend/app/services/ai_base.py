from abc import ABC, abstractmethod
from typing import Any, Optional, Type
import json
import re

_VALID_JSON_TWO_CHAR_ESCAPES = set('"\\/')


def repair_latex_backslash_escapes(text: str) -> str:
    """Repara backslashes de comandos LaTeX mal escapados dentro de strings JSON.

    Se usa SOLO como reintento cuando json.loads ya falló. En JSON, "\\f",
    "\\n", "\\t", etc. son escapes válidos de un solo carácter (formfeed,
    newline, tab...), pero el texto pedagógico nunca contiene esos
    caracteres de control legítimamente. Si el modelo emite un comando LaTeX
    como "\\frac" o "\\ne" sin doblar el backslash ("\\\\frac"), el parser
    JSON lo consumiría en silencio como ese carácter de control seguido de
    texto suelto. Como esta función solo corre tras un fallo de parseo, es
    seguro asumir que cualquier backslash que no forme un escape JSON válido
    de dos caracteres (\\", \\\\, \\/) ni una secuencia \\uXXXX completa es en
    realidad el inicio de un comando LaTeX, y se duplica.
    """
    out = []
    in_string = False
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == '"':
            in_string = not in_string
            out.append(ch)
            i += 1
            continue
        if in_string and ch == '\\' and i + 1 < n:
            nxt = text[i + 1]
            if nxt in _VALID_JSON_TWO_CHAR_ESCAPES:
                out.append(text[i:i + 2])
                i += 2
                continue
            if nxt == 'u' and i + 5 < n and all(c in '0123456789abcdefABCDEF' for c in text[i + 2:i + 6]):
                out.append(text[i:i + 6])
                i += 6
                continue
            # \b \f \n \r \t u otro: se asume comando LaTeX mal escapado.
            out.append('\\\\')
            i += 1
            continue
        out.append(ch)
        i += 1
    return ''.join(out)


_CONTROL_CHAR_LATEX_MAP = {
    '\x0c': 'f',  # formfeed  -> \f  (ej: \frac mal escapado)
    '\x08': 'b',  # backspace -> \b  (ej: \begin, \beta mal escapado)
}


def repair_stray_control_chars(value):
    """Repara backspace/formfeed reales dentro de valores YA parseados.

    A diferencia de repair_latex_backslash_escapes (que actúa sobre el texto
    JSON crudo y solo se usa si json.loads falla), este caso NO lanza
    JSONDecodeError: "\\f" y "\\b" son escapes JSON válidos de un solo
    carácter (formfeed/backspace), así que un comando LaTeX mal escapado
    como "\\frac" se parsea "con éxito" pero corrompido en silencio a
    "<formfeed>rac". Esos caracteres de control nunca aparecen legítimamente
    en texto de examen, así que reconstruimos el backslash literal. Opera
    sobre el resultado ya parseado (dict/list/str) de forma recursiva, nunca
    sobre el texto JSON crudo, por lo que no puede introducir JSON inválido.
    """
    if isinstance(value, str):
        for control_char, letter in _CONTROL_CHAR_LATEX_MAP.items():
            if control_char in value:
                value = value.replace(control_char, '\\' + letter)
        return value
    if isinstance(value, dict):
        return {k: repair_stray_control_chars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [repair_stray_control_chars(v) for v in value]
    return value


class AIService(ABC):
    """Abstract base class for AI services."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if the service is properly configured (e.g. API key)."""
        pass

    @abstractmethod
    async def generate_content(self, prompt: str) -> str:
        """Generate text content from a prompt."""
        pass

    @abstractmethod
    async def generar_preguntas(
        self,
        competencias: list[dict],
        cantidad: int = 5,
        tipo: str = "multiple",
        dificultad: str = "intermedio"
    ) -> list[Any]:
        """Generate questions (legacy method mainly used by preguntas.py)."""
        pass

    async def generate_structured_content(self, prompt: str, schema: Type) -> dict:
        """Generate structured JSON output conforming to a Pydantic schema.

        Default implementation: generates text and parses as JSON.
        Override in subclasses (e.g. GeminiService) for native structured output.
        """
        text = await self.generate_content(prompt)
        text = self.clean_json_response(text)
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Reintento: puede haber comandos LaTeX (\frac, \times, \ne...)
            # con el backslash sin doblar. Ver repair_latex_backslash_escapes.
            data = json.loads(repair_latex_backslash_escapes(text))
        return repair_stray_control_chars(data)

    def clean_json_response(self, response_text: str) -> str:
        """Helper to clean JSON code blocks and recover JSON from text.
        
        Handles common AI output issues:
        - Markdown code blocks (```json ... ```)
        - Text before/after the JSON object
        - Single-line comments (// ...)
        - Trailing commas
        - Truncated JSON (unclosed brackets/braces)
        - Unescaped control characters inside strings
        - NaN / Infinity literals
        """
        # 1. Basic markdown cleaning
        response_text = response_text.strip()
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()

        # 2. Extract JSON if it's embedded in other text
        try:
            first_brace = response_text.find('{')
            last_brace = response_text.rfind('}')
            if first_brace != -1 and last_brace != -1:
                response_text = response_text[first_brace:last_brace + 1]
        except:
            pass
            
        # 3. Remove comments and trailing commas
        try:
            # Remove single-line comments // ... (but NOT inside strings)
            # Use a careful regex: only match // at the start of a line or after whitespace
            response_text = re.sub(r'^\s*//.*$', '', response_text, flags=re.MULTILINE)
            # Remove inline comments after values (e.g. "value" // comment)
            response_text = re.sub(r'([\"\d\}\]truefalsenull])\s*//[^\n]*', r'\1', response_text)
            # Remove trailing commas: ,} -> } and ,] -> ]
            response_text = re.sub(r',\s*\}', '}', response_text)
            response_text = re.sub(r',\s*\]', ']', response_text)
        except:
            pass
        
        # 4. Fix NaN / Infinity values (replace with null)
        try:
            response_text = re.sub(r'\bNaN\b', 'null', response_text)
            response_text = re.sub(r'\bInfinity\b', 'null', response_text)
            response_text = re.sub(r'\b-Infinity\b', 'null', response_text)
        except:
            pass

        # 5. Fix unescaped control characters inside JSON strings
        try:
            response_text = self._fix_control_chars_in_json(response_text)
        except:
            pass

        # 6. Repair truncated JSON (close unclosed brackets/braces)
        try:
            response_text = self._repair_truncated_json(response_text)
        except:
            pass

        return response_text.strip()

    def _fix_control_chars_in_json(self, text: str) -> str:
        """Fix unescaped control characters (tabs, literal newlines) inside JSON string values."""
        # Replace literal tab characters with \\t (escaped tab)
        # Replace other control chars that break JSON parsing
        result = []
        in_string = False
        escape_next = False
        
        for char in text:
            if escape_next:
                result.append(char)
                escape_next = False
                continue
            
            if char == '\\' and in_string:
                escape_next = True
                result.append(char)
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                result.append(char)
                continue
            
            if in_string:
                # Replace problematic control chars inside strings
                if char == '\t':
                    result.append('\\t')
                elif char == '\n':
                    result.append('\\n')
                elif char == '\r':
                    result.append('\\r')
                elif ord(char) < 32:
                    # Replace other control chars with their unicode escape
                    result.append(f'\\u{ord(char):04x}')
                else:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)

    def _repair_truncated_json(self, text: str) -> str:
        """Attempt to repair truncated JSON by closing unclosed structures.
        
        When Gemini hits max_output_tokens, the JSON gets cut off mid-way.
        This tries to close any unclosed strings, arrays, and objects.
        """
        # First, try to parse as-is. If it works, no repair needed.
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        
        # Count unclosed structures
        in_string = False
        escape_next = False
        stack = []  # track open { and [
        last_was_key = False
        
        for i, char in enumerate(text):
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\' and in_string:
                escape_next = True
                continue
            
            if char == '"':
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            if char == '{':
                stack.append('{')
            elif char == '[':
                stack.append('[')
            elif char == '}':
                if stack and stack[-1] == '{':
                    stack.pop()
            elif char == ']':
                if stack and stack[-1] == '[':
                    stack.pop()
        
        # If we were inside a string when it ended, close the string
        if in_string:
            text += '"'
        
        # Close any unclosed structures in reverse order
        # But first, handle partial values: if the JSON ends mid-value after a colon
        # we need to add a placeholder value
        stripped = text.rstrip()
        if stripped and stripped[-1] == ':':
            text += ' ""'
        elif stripped and stripped[-1] == ',':
            text = text.rstrip()[:-1]  # remove trailing comma
        
        # Close unclosed brackets/braces
        for bracket in reversed(stack):
            if bracket == '{':
                text += '}'
            elif bracket == '[':
                text += ']'
        
        return text
