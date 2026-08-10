# AGENTS.md — Frontend Widget WordPress para Chatbot El Berenjenal

## 🔍 Contexto del proyecto
Este proyecto tiene un **backend Flask** ya desarrollado, ubicado en la carpeta `backend/`.  
El backend expone un único endpoint:

- `POST /chat`  
  Recibe: `{"pregunta": "texto de la pregunta"}`  
  Responde: `{"respuesta": "texto de la respuesta", "categoria": "A|B|C", "fuente": "archivo.md"}`

Clasifica automáticamente las preguntas en:
- **A:** Proyecto, asociación, fechas, burocracia (busca en `info-berenjenal.md`)
- **B:** Permacultura, suelo, riego, compost, etc. (busca en los `.md` técnicos)
- **C:** Fuera de contexto → respuesta de cortesía.

Antes de clasificar, consulta `faqs.json` por si hay una coincidencia exacta.  
El backend corre en `localhost:5000` en desarrollo y tiene CORS abierto. Se desplegará posteriormente en Render/Railway.

## 🎯 Objetivo del nuevo desarrollo
Crear un **plugin de WordPress** que añada un **widget de chat flotante** en la web del huerto comunitario.  
El widget se conectará al endpoint `/chat` del backend y permitirá a los visitantes hacer preguntas.

Debe ser **autocontenido, fácil de instalar y configurable** desde el panel de WordPress.

## 📦 Requisitos del plugin

### 1. Estructura de archivos del plugin

chatbot-berenjenal-widget/
├── chatbot-berenjenal-widget.php
├── assets/
│ ├── css/
│ │ └── chatbot-style.css
│ └── js/
│ └── chatbot-widget.js
└── readme.txt (opcional)
text


### 2. Funcionalidad
- **Widget flotante:** botón circular con icono de chat (💬) fijo en la esquina inferior derecha.
- Al hacer clic, se despliega una ventana de chat (animación suave slide-up/fade).
- La ventana contiene:
  - Cabecera con el nombre “🌱 El Berenjenal” y botón de cerrar.
  - Área de mensajes (con scroll automático hacia abajo).
  - Campo de texto y botón de enviar (➤).
- El usuario escribe y pulsa enviar (o Enter). El JS:
  1. Muestra el mensaje del usuario.
  2. Hace `fetch` a la URL configurada con la pregunta.
  3. Mientras espera, muestra un indicador “escribiendo…” (tres puntos animados).
  4. Recibe la respuesta JSON y la muestra como mensaje del bot.
  5. En caso de error, muestra un mensaje de fallback.
- Debe haber un **shortcode `[chatbot_berenjenal]`** para colocar manualmente el chat en cualquier página/entrada.
- Si no se usa el shortcode, el plugin inyecta automáticamente el contenedor en el pie de página y el widget aparece en todas las páginas.

### 3. Configuración (Página de opciones)
- El plugin añadirá una página de ajustes en **Ajustes → Chatbot El Berenjenal**.
- Un único campo: **URL del endpoint `/chat`**.
- Valor por defecto: `http://localhost:5000/chat` (para desarrollo local).
- El valor se guarda en la base de datos (usando `register_setting` y `add_settings_field`) y se pasa al JavaScript mediante `wp_localize_script`.

### 4. Diseño y experiencia de usuario (sé creativo, pero mantén estas pautas)
- **Paleta de colores naturales:** verdes (#4CAF50 o #2E7D32), blancos rotos, tonos tierra.
- **Estética moderna:** bordes redondeados, sombras suaves, transiciones CSS.
- **Responsive:** en móviles, el chat puede ocupar toda la pantalla o adaptarse bien.
- **Animaciones:** apertura/cierre del chat, aparición de mensajes, indicador de escritura.
- **Sin dependencias externas** (no uses Bootstrap ni Tailwind, solo CSS vanilla).
- Código limpio y comentado en español.

### 5. Tecnologías
- PHP (para el plugin WordPress)
- CSS3 (con variables CSS recomendadas)
- JavaScript vanilla (sin jQuery)

## 🧪 Instrucciones para el agente
1. **Lee bien el contexto del backend** (lo tienes arriba). Ya sabes cómo responde.
2. **Genera el código completo** de los cuatro archivos del plugin, con todos los comentarios necesarios.
3. **Crea un ZIP** listo para instalar (opcional pero recomendable, explícalo).
4. **Explica claramente cómo instalarlo y configurarlo** (subir ZIP, activar, ir a Ajustes para cambiar la URL).
5. Asegúrate de que el plugin **funcione tanto en local** (con `http://localhost:5000/chat`) como en producción cambiando la URL.

## 📌 Notas adicionales
- Si tienes activada alguna “skill” de diseño frontend (por ejemplo, `frontend-designer` de awesome-llm-skills), puedes aplicarla para mejorar el aspecto visual, pero siempre manteniendo CSS vanilla.
- Respeta el idioma español en comentarios y textos del chat.

    Si el agente te pregunta por la URL del backend: dile que por ahora use la de local (http://localhost:5000/chat), porque no has desplegado todavía. El campo de configuración permitirá cambiarla después.

## 🚀 Entrega final
- Código fuente del plugin listo para copiar o empaquetado.
- Instrucciones de instalación y uso para el administrador de WordPress.


