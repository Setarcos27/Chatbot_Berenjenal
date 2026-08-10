=== Chatbot El Berenjenal ===
Contributors: vagamundis
Tags: chat, chatbot, widget, flotante, huerto, permacultura
Requires at least: 5.0
Tested up to: 6.7
Requires PHP: 7.2
Stable tag: 1.0.0
License: GPLv2 or later
License URI: https://www.gnu.org/licenses/gpl-2.0.html

Widget de chat flotante para el huerto comunitario El Berenjenal. Conecta con el backend Flask (POST /chat) y es configurable desde Ajustes → Chatbot El Berenjenal.

== Description ==

Este plugin añade un widget de chat flotante (botón circular 💬 en la esquina inferior derecha) que permite a los visitantes hacer preguntas al chatbot de El Berenjenal, un backend Flask ya desarrollado que clasifica las preguntas en tres categorías:

* **A — Proyecto/asociación**: busca en `info-berenjenal.md`.
* **B — Permacultura/técnicas**: busca en los archivos técnicos (`suelo.md`, `riego.md`, `compost.md`, `plantas.md`, `manual.md`).
* **C — Fuera de contexto**: respuesta de cortesía.

Características:

* Botón flotante con animación de apertura (slide-up + fade) y pulso sutil.
* Ventana de chat con cabecera "🌱 El Berenjenal", área de mensajes con scroll automático, indicador "escribiendo…" (tres puntos animados) y manejo de errores.
* **Shortcode `[chatbot_berenjenal]`** para colocar el chat en una página o entrada concreta (modo embebido, siempre visible).
* Si no se usa el shortcode, el widget aparece automáticamente en todas las páginas.
* **Configurable desde Ajustes → Chatbot El Berenjenal**: un único campo con la URL del endpoint `/chat`.
* Sin dependencias externas: CSS vanilla y JavaScript vanilla (sin jQuery, sin Bootstrap, sin Tailwind).
* Diseño responsive: en móviles el chat ocupa casi toda la pantalla.
* Paleta de colores naturales (verdes, blanco roto y tonos tierra) y animaciones respetuosas con `prefers-reduced-motion`.

== Installation ==

1. En el panel de WordPress ve a **Plugins → Añadir nuevo → Subir plugin**.
2. Sube el archivo `chatbot-berenjenal-widget.zip` y pulsa **Instalar ahora**.
3. Activa el plugin (**Activar**).
4. Ve a **Ajustes → Chatbot El Berenjenal**.
5. Comprueba la **URL del endpoint /chat**. El valor por defecto es `http://localhost:5000/chat` (desarrollo local). Cuando el backend esté desplegado (por ejemplo en Render o Railway), pega aquí su URL pública terminada en `/chat` y pulsa **Guardar cambios**.

El widget flotante aparecerá automáticamente en todas las páginas del sitio.

== Frequently Asked Questions ==

= ¿Cómo coloco el chat solo en una página concreta? =

Añade el shortcode `[chatbot_berenjenal]` en esa página o entrada. Cuando el shortcode está presente, el widget flotante no se duplica en el resto de la página.

= ¿Qué URL tengo que poner en los ajustes? =

La URL del endpoint `/chat` del backend Flask, por ejemplo:

* Desarrollo local: `http://localhost:5000/chat`
* Producción (Render/Railway): `https://tu-backend-en-render.onrender.com/chat`

= ¿Necesita el backend estar en el mismo dominio? =

No. El backend tiene CORS abierto, por lo que el widget puede llamarlo desde cualquier dominio.

= ¿Qué pasa si el backend no responde? =

El widget muestra un mensaje de error de cortesía y el formulario se reactiva automáticamente. También hay un tiempo máximo de espera de 25 segundos.

== Changelog ==

= 1.0.0 =
* Versión inicial: widget flotante, shortcode, página de ajustes y conexión con el endpoint POST /chat.
