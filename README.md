# Chatbot El Berenjenal — Backend (Flask)

Backend del chatbot del huerto comunitario **El Berenjenal** (asociación Vagamundis, La Luisiana, Sevilla).

Clasifica las preguntas en tres categorías:

- **Categoría A** — Proyecto, asociación, fechas, burocracia y filosofía → busca en `repositories/info-berenjenal.md`.
- **Categoría B** — Permacultura, técnicas, plantas, suelo, riego, compost, etc. → busca en los `.md` técnicos (`suelo.md`, `riego.md`, `compost.md`, `plantas.md`, `manual.md`).
- **Categoría C** — Preguntas fuera de contexto, ofensivas o sin sentido → respuesta de cortesía.

Antes de clasificar, comprueba si la pregunta coincide con una FAQ de `repositories/faqs.json`.

## Estructura

```
backend/app.py          # Aplicación Flask con el endpoint POST /chat
repositories/           # Base de conocimiento (faqs.json y archivos .md)
requirements.txt        # Dependencias: Flask y flask-cors
README.md
```

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución (local, puerto 5000)

```bash
python backend/app.py
```

El servidor escucha en `0.0.0.0:5000` (la variable de entorno `PORT` permite cambiarlo para despliegues como Render o Railway).

## Uso

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Cómo se hace el compost?"}'
```

Respuesta:

```json
{
  "respuesta": "...",
  "categoria": "B",
  "fuente": "compost.md"
}
```

Comprobación de estado:

```bash
curl http://localhost:5000/
```

## Despliegue

El CORS está abierto, por lo que funciona con cualquier frontend. En **Render**/**Railway**:

- Comando de inicio: `python backend/app.py` (o `gunicorn backend.app:app`).
- El puerto se toma automáticamente de la variable `PORT`.
