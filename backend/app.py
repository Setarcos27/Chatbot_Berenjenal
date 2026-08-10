# -*- coding: utf-8 -*-
"""
Backend del Chatbot El Berenjenal (Flask)
------------------------------------------
Clasifica las preguntas en tres categorías (A, B, C) y responde según la lógica
definida en las especificaciones:

- Paso 0: coincidencia con FAQ (faqs.json)
- Paso 1: clasificación A (proyecto/asociación) | B (permacultura/técnicas) | C (fuera de contexto)

Desplegable en Render, Railway, etc. con CORS abierto.
"""

import json
import os
import re
import unicodedata

from flask import Flask, jsonify, request
from flask_cors import CORS

# =============================================================================
# Configuración y carga inicial de datos
# =============================================================================

# Directorios de trabajo (independientes de dónde se ejecute el script)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPOS_DIR = os.path.join(BASE_DIR, "..", "repositories")

# Archivos técnicos (categoría B). manual.md también se guarda aparte en la
# variable `manual`, tal y como piden las especificaciones.
TECHNICAL_FILES = ["suelo.md", "riego.md", "compost.md", "plantas.md", "manual.md"]

# Mensajes de respuesta por defecto
CONTACTO_FALLBACK_A = (
    "No tengo esa información específica en mi base de datos. "
    "Puedes escribir a info@vagamundis.org y te ayudaremos."
)
CONTACTO_FALLBACK_B = (
    "No tengo información sobre eso en mi base de datos. Te sugiero que consultes "
    "la bibliografía recomendada en nuestro manual o escribas a info@vagamundis.org."
)
FALLBACK_C = (
    "Soy un chatbot sobre permacultura y el proyecto El Berenjenal. "
    "Esta consulta se sale de mis conocimientos."
)

# Palabras clave por categoría (según especificaciones)
KEYWORDS_A = [
    "berenjenal", "vagamundis", "reunión", "cuándo", "quién", "dónde",
    "asociación", "equipo", "contacto", "horario", "próximo", "evento",
    "taller", "inscripción", "cómo participar", "qué es", "objetivos",
    "misión", "participar",
]
KEYWORDS_B = [
    "permacultura", "compost", "riego", "suelo", "planta", "siembra",
    "cosecha", "abono", "biodiversidad", "polinizador", "clima", "variedad",
    "semilla", "ecológico", "orgánico", "hortaliza", "frutal", "árbol",
    "seto", "acolchado", "goteo", "nutriente", "fertilidad",
]

# Palabras vacías: se ignoran a la hora de buscar coincidencias por palabras clave
STOPWORDS = {
    "que", "es", "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "en", "a", "al", "y", "o", "u", "como", "cuando", "donde",
    "cual", "cuales", "quien", "quienes", "se", "me", "te", "le", "nos",
    "les", "lo", "su", "sus", "mi", "mis", "tu", "tus", "nuestro",
    "nuestros", "nuestra", "nuestras", "para", "por", "con", "sin", "sobre",
    "entre", "hacia", "hasta", "desde", "este", "esta", "estos", "estas",
    "ese", "esa", "esos", "esas", "aqui", "hay", "muy", "mas", "menos",
    "bien", "mal", "hace", "hacer", "hacen", "tiene", "tienen", "tener",
    "tengo", "ser", "soy", "eres", "estoy", "esta", "estan", "no", "si",
    "ya", "tambien", "tan", "todo", "toda", "todos", "todas", "algo",
    "nada", "porque", "pues", "cuanta", "cuanto", "cuantas", "cuantos",
}


def load_faqs():
    """Carga el contenido de faqs.json y devuelve la lista de preguntas."""
    path = os.path.join(REPOS_DIR, "faqs.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("preguntas", [])


def load_md(filename):
    """Lee un archivo Markdown de la carpeta repositories."""
    path = os.path.join(REPOS_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


# Variables globales con el contenido de cada archivo (tal como piden las
# especificaciones: faqs, info_proyecto, manual, conocimiento_tecnico).
faqs = load_faqs()
info_proyecto = load_md("info-berenjenal.md")
manual = load_md("manual.md")
conocimiento_tecnico = {fname: load_md(fname) for fname in TECHNICAL_FILES}


# =============================================================================
# Utilidades de normalización y búsqueda
# =============================================================================

def normalize_text(text):
    """Minúsculas, sin acentos y con la puntuación convertida en espacios."""
    text = text.lower()
    text = "".join(
        c for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9\s]", " ", text)


def significant_tokens(text):
    """Palabras clave de la pregunta: sin acentos y sin stopwords."""
    norm = normalize_text(text)
    return [t for t in norm.split() if t not in STOPWORDS and len(t) > 2]


def match_token(token, word):
    """
    ¿Coincide un token de la pregunta con una palabra del texto?
    Coincidencia exacta o por prefijo (p. ej. "taller" ~ "talleres",
    "compost" ~ "compostaje", "próximo" ~ "próxima").
    """
    if token == word:
        return True
    if len(token) >= 4 and len(word) >= 4:
        return word.startswith(token) or token.startswith(word)
    return False


def count_matches(tokens, text):
    """
    Devuelve (nº de tokens distintos que aparecen, nº de ocurrencias).
    Se usa para puntuar secciones y archivos completos.
    """
    norm = normalize_text(text)
    words = set(norm.split())
    matched = set()
    for t in tokens:
        if any(match_token(t, w) for w in words):
            matched.add(t)
    occurrences = sum(len(re.findall(re.escape(t), norm)) for t in matched)
    return len(matched), occurrences


def parse_sections(md_text):
    """
    Divide un Markdown en secciones (encabezado + cuerpo).
    Devuelve una lista de tuplas (heading, body).
    """
    sections = []
    current = None
    body = []
    for line in md_text.splitlines():
        if re.match(r"^#{1,6}\s+", line):
            if current is not None:
                sections.append((current, "\n".join(body).strip()))
            current = line.strip()
            body = []
        else:
            if current is not None:
                body.append(line)
            elif line.strip():
                # Texto previo al primer encabezado
                sections.append(("", line.strip()))
    if current is not None:
        sections.append((current, "\n".join(body).strip()))
    return sections


def extraer_bibliografia():
    """Extrae la sección 'Bibliografía recomendada' de manual.md si existe."""
    for heading, body in parse_sections(manual):
        if "bibliografia" in normalize_text(heading):
            return body.strip()
    return ""


# =============================================================================
# Lógica de búsqueda y clasificación
# =============================================================================

def match_faq(pregunta):
    """
    Paso 0: coincidencia con FAQ.
    - Coincidencia exacta: la pregunta normalizada coincide con la de la FAQ.
    - Coincidencia por palabras clave: al menos 2 coincidencias (según especificación).
    """
    user_norm = normalize_text(pregunta).strip()
    user_tokens = set(significant_tokens(pregunta))
    if not user_tokens:
        return None
    best = None
    for faq in faqs:
        # Coincidencia exacta (misma pregunta, reescrita de otra forma)
        if user_norm == normalize_text(faq["pregunta"]).strip():
            return faq
        # Coincidencia por palabras clave (al menos 2)
        faq_tokens = set(significant_tokens(faq["pregunta"]))
        overlap = user_tokens & faq_tokens
        if len(overlap) >= 2 and best is None:
            best = faq
    return best


def classify(pregunta):
    """
    Paso 1: clasifica la pregunta en A, B o C según las palabras clave.
    Si hay empate entre A y B, se prefiere B (los temas técnicos son más
    específicos que las palabras genéricas tipo "qué es").
    """
    norm = normalize_text(pregunta)
    count_a = sum(1 for kw in KEYWORDS_A if normalize_text(kw).strip() in norm)
    count_b = sum(1 for kw in KEYWORDS_B if normalize_text(kw).strip() in norm)
    if count_b >= count_a and count_b > 0:
        return "B"
    if count_a > 0:
        return "A"
    return "C"


def buscar_en_info_proyecto(tokens):
    """
    Categoría A: busca la respuesta en info-berenjenal.md.
    Devuelve el texto de la(s) sección(es) mejor puntuada(s) o None.
    Las coincidencias en el encabezado de la sección pesan más que las del cuerpo.
    """
    scored = []
    for heading, body in parse_sections(info_proyecto):
        dh, oh = count_matches(tokens, heading)
        db, ob = count_matches(tokens, body)
        if dh + db > 0:
            scored.append((dh, db, oh + ob, heading, body))
    if not scored:
        return None
    scored.sort(key=lambda s: (-s[0], -s[1], -s[2]))
    # Devolver hasta 2 secciones con la mejor puntuación
    top = scored[:2]
    parts = []
    for _, _, _, heading, body in top:
        parts.append(f"{heading}\n{body}" if heading else body)
    return "\n\n".join(parts)


def buscar_en_conocimiento_tecnico(tokens):
    """
    Categoría B: busca en todos los .md técnicos (suelo, riego, compost,
    plantas, manual). Devuelve (contenido, fuentes) o None.
    """
    all_sections = []
    for fname in TECHNICAL_FILES:
        for heading, body in parse_sections(conocimiento_tecnico[fname]):
            dh, oh = count_matches(tokens, heading)
            db, ob = count_matches(tokens, body)
            if dh + db > 0:
                all_sections.append((dh, db, oh + ob, fname, heading, body))

    if not all_sections:
        return None

    # Ordenar: coincidencias en el encabezado primero, luego en el cuerpo
    all_sections.sort(key=lambda s: (-s[0], -s[1], -s[2]))
    best_total = max(s[0] + s[1] for s in all_sections)

    if best_total >= 2:
        # Coincidencia fuerte: devolver las mejores secciones (máx. 2)
        top = all_sections[:2]
        content = "\n\n".join(
            f"{h}\n{b}" if h else b for _, _, _, _, h, b in top
        )
        sources = ", ".join(sorted({s[3] for s in top}))
        return content, sources

    # Coincidencia débil: devolver el/los archivo(s) completo(s) mejor puntuado(s)
    file_scores = {}
    for fname in TECHNICAL_FILES:
        distinct, occ = count_matches(tokens, conocimiento_tecnico[fname])
        if distinct > 0:
            file_scores[fname] = (distinct, occ)
    if not file_scores:
        return None
    ranked = sorted(file_scores.items(), key=lambda kv: (-kv[1][0], -kv[1][1]))
    best_score = ranked[0][1]
    top_files = [f for f, s in ranked if s == best_score][:2]
    content = "\n\n".join(conocimiento_tecnico[f] for f in top_files)
    return content, ", ".join(top_files)


# =============================================================================
# Aplicación Flask y endpoint
# =============================================================================

app = Flask(__name__)
CORS(app)  # CORS abierto para permitir peticiones desde cualquier origen


@app.route("/", methods=["GET"])
def index():
    """Comprobación de que el servidor está vivo."""
    return jsonify({
        "status": "ok",
        "mensaje": "Chatbot El Berenjenal funcionando. Usa POST /chat con {\"pregunta\": \"...\"}",
    })


@app.route("/chat", methods=["POST"])
def chat():
    """Endpoint principal: recibe JSON con {'pregunta': '...'} y responde."""
    data = request.get_json(silent=True)
    if not data or "pregunta" not in data:
        return jsonify({"error": "Falta el campo 'pregunta' en el JSON."}), 400

    pregunta = (data.get("pregunta") or "").strip()
    if not pregunta:
        return jsonify({"error": "La pregunta no puede estar vacía."}), 400

    # ---------- Paso 0: coincidencia con FAQ ----------
    faq = match_faq(pregunta)
    if faq:
        return jsonify({
            "respuesta": faq["respuesta"],
            "categoria": "FAQ",
            "fuente": "faqs.json",
        })

    # ---------- Paso 1: clasificación de la pregunta ----------
    categoria = classify(pregunta)
    tokens = significant_tokens(pregunta)

    if categoria == "A":
        # Categoría A: proyecto, asociación, fechas, burocracia, filosofía
        respuesta = buscar_en_info_proyecto(tokens)
        if respuesta:
            return jsonify({
                "respuesta": respuesta,
                "categoria": "A",
                "fuente": "info-berenjenal.md",
            })
        # Si no hay respuesta, adjuntar siempre el correo de contacto
        return jsonify({
            "respuesta": CONTACTO_FALLBACK_A,
            "categoria": "A",
            "fuente": None,
        })

    if categoria == "B":
        # Categoría B: permacultura, técnicas, plantas, suelo, riego, compost...
        resultado = buscar_en_conocimiento_tecnico(tokens)
        if resultado:
            contenido, fuentes = resultado
            bibliografia = extraer_bibliografia()
            if bibliografia:
                respuesta = (
                    f"{contenido}\n\n"
                    f"Puedes ampliar información en la bibliografía recomendada:\n"
                    f"{bibliografia}"
                )
            else:
                respuesta = (
                    f"{contenido}\n\n"
                    "Puedes ampliar información en la bibliografía recomendada de nuestro manual."
                )
            return jsonify({
                "respuesta": respuesta,
                "categoria": "B",
                "fuente": fuentes,
            })
        return jsonify({
            "respuesta": CONTACTO_FALLBACK_B,
            "categoria": "B",
            "fuente": None,
        })

    # Categoría C: preguntas no relacionadas, ofensivas o sin sentido
    return jsonify({
        "respuesta": FALLBACK_C,
        "categoria": "C",
        "fuente": None,
    })


if __name__ == "__main__":
    # Puerto configurable para despliegue (Render, Railway, ...) con 5000 por defecto
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
