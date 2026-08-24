"""
Fragmentos de prompt reutilizados por los servicios de generación con IA.
"""

# Nota de escapes: el JSON de salida se parsea con json.loads, donde \f, \b, \n,
# \r y \t son escapes válidos de un solo carácter. Comandos LaTeX que empiezan
# con esas letras (\frac, \begin...) se recuperan automáticamente si el modelo
# olvida doblar el backslash (ver app/services/ai_base.py: repair_stray_control_chars).
# Por eso preferimos \cdot sobre \times y evitamos \ne: "t" y "n" colisionan con
# \t (tab) y \n (salto de línea), que sí pueden aparecer legítimamente en textos
# largos (lecturas), así que no se pueden reparar de forma segura si el modelo
# los deja mal escapados.
NOTACION_MATEMATICA = r"""
**NOTACIÓN MATEMÁTICA (OBLIGATORIO):**
Escribe TODA expresión matemática en LaTeX delimitada por signos de dólar:
- En línea: $x^2 + 3x - 5 = 0$, $\frac{3}{4}$, $\sqrt{25}$, $12 \cdot 8$, $\pi r^2$, $A_1$, $30^\circ$.
- En bloque, solo si la expresión ocupa una línea propia: $$A = \frac{b \cdot h}{2}$$

Reglas estrictas:
- Multiplicación: usa \cdot. NUNCA uses "x", "*" ni "X" como signo de multiplicar.
- Fracciones: usa \frac{a}{b}. NUNCA escribas "3/4" ni "3 sobre 4".
- Otros comandos permitidos: \sqrt{x}, \pi, \le, \ge, \pm, \div, \infty,
  ^ para potencias, _ para subíndices, ^\circ para grados sexagesimales.
- NO envuelvas prosa en los delimitadores. Solo la expresión va dentro de $...$;
  las unidades y las palabras van fuera: "$v = 60$ km/h", "el perímetro mide $4a$ metros".
- NO envuelvas números sueltos sin operación: escribe "25 estudiantes", no "$25$ estudiantes".
- NUNCA uses el símbolo $ como moneda. La moneda peruana se escribe "S/ 25.50",
  siempre FUERA de cualquier delimitador matemático.
- NO uses entornos avanzados (align, array, matrix, cases) ni imágenes; solo
  expresiones simples de una línea.
- En el JSON de salida, escapa los backslash como corresponde: "\\frac", "\\sqrt".
"""

NOTACION_MATEMATICA_BREVE = r"""
**NOTACIÓN MATEMÁTICA:** si algún texto incluye expresiones matemáticas o numéricas
no triviales, escríbelas en LaTeX entre $...$ (por ejemplo $\frac{3}{4}$, $x^2$,
$12 \cdot 8$). Usa \cdot, \frac, \sqrt, \pi, \le, \ge. No envuelvas prosa ni números
sueltos en $...$. NUNCA uses $ como moneda: la moneda peruana se escribe "S/ 25.50"
fuera de los delimitadores.
"""
