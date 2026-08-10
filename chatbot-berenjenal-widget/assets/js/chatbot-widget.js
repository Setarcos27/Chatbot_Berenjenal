/**
 * Chatbot El Berenjenal — Widget de chat
 * -----------------------------------------------------------------------------
 * JavaScript vanilla (sin jQuery) que conecta con el backend Flask:
 *
 *   POST {endpoint}
 *   body:  {"pregunta": "..."}
 *   resp:  {"respuesta": "...", "categoria": "A|B|C", "fuente": "archivo.md"}
 *
 * La configuración (URL del endpoint y textos) llega desde PHP mediante
 * wp_localize_script en la variable global `chatbotBerenjenal`.
 *
 * Soporta dos modos (detectados por la clase CSS del contenedor):
 *   - chatbot-berenjenal--flotante : botón circular fijo + ventana desplegable.
 *   - chatbot-berenjenal--embebido : ventana siempre visible (shortcode).
 */
(function () {
	'use strict';

	// =========================================================================
	// Configuración
	// =========================================================================

	var config = window.chatbotBerenjenal || {};

	var AJUSTES = {
		// URL del endpoint /chat (configurable desde Ajustes → Chatbot El Berenjenal).
		endpoint: config.endpoint || 'http://localhost:5000/chat',
		// Tiempo máximo de espera de la respuesta del backend (milisegundos).
		tiempoEsperaMs: 25000,
		mensajeBienvenida: config.mensajeBienvenida || '¡Hola! Soy el chatbot de El Berenjenal 🌱 Pregúntame sobre el proyecto, la asociación, permacultura, compost, riego o el huerto.',
		mensajeError: config.mensajeError || 'Ups… no he podido conectar con el huerto. Inténtalo de nuevo en un momento. 🌱',
		textoEscribiendo: config.textoEscribiendo || 'escribiendo…'
	};

	// =========================================================================
	// Utilidades
	// =========================================================================

	/**
	 * Escapa el HTML de un texto para evitar inyección de código
	 * (los mensajes del bot se renderizan con innerHTML tras formatear).
	 *
	 * @param {string} texto Texto sin escapar.
	 * @return {string} Texto seguro.
	 */
	function escaparHTML(texto) {
		var div = document.createElement('div');
		div.textContent = texto;
		return div.innerHTML;
	}

	/**
	 * Mini-formateador Markdown seguro (sin dependencias externas):
	 * convierte enlaces, negritas, cursivas, encabezados y listas en HTML.
	 * Se aplica SIEMPRE después de escapar el HTML, por lo que es seguro.
	 *
	 * @param {string} texto Respuesta en bruto del backend.
	 * @return {string} HTML formateado.
	 */
	function formatearRespuesta(texto) {
		var html = escaparHTML(String(texto));

		// Enlaces: [texto](https://ejemplo.com)
		html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g, function (todo, textoEnlace, url) {
			return '<a href="' + url + '" target="_blank" rel="noopener noreferrer">' + textoEnlace + '</a>';
		});

		// Negrita **texto** y cursiva *texto*
		html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
		html = html.replace(/(^|[^*])\*([^*\n]+)\*/g, '$1<em>$2</em>');

		var lineas = html.split('\n');
		var salida = '';
		var enLista = null; // 'ul' | 'ol' | null

		/** Cierra la lista actual si hay una abierta. */
		function cerrarLista() {
			if (enLista) {
				salida += '</' + enLista + '>';
				enLista = null;
			}
		}

		for (var i = 0; i < lineas.length; i++) {
			var linea = lineas[i].trim();

			// Línea en blanco: separador de párrafos.
			if (!linea) {
				cerrarLista();
				continue;
			}

			// Encabezados: #, ##, ### …
			var encabezado = linea.match(/^(#{1,6})\s+(.+)$/);
			if (encabezado) {
				cerrarLista();
				var nivel = Math.min(encabezado[1].length, 4);
				salida += '<div class="chatbot-berenjenal__h chatbot-berenjenal__h--' + nivel + '">' + encabezado[2] + '</div>';
				continue;
			}

			// Lista con viñetas: "- elemento" o "* elemento"
			var vineta = linea.match(/^[-*]\s+(.+)$/);
			if (vineta) {
				if (enLista !== 'ul') {
					cerrarLista();
					salida += '<ul class="chatbot-berenjenal__lista">';
					enLista = 'ul';
				}
				salida += '<li>' + vineta[1] + '</li>';
				continue;
			}

			// Lista numerada: "1. elemento" o "1) elemento"
			var numerada = linea.match(/^\d+[.)]\s+(.+)$/);
			if (numerada) {
				if (enLista !== 'ol') {
					cerrarLista();
					salida += '<ol class="chatbot-berenjenal__lista">';
					enLista = 'ol';
				}
				salida += '<li>' + numerada[1] + '</li>';
				continue;
			}

			// Párrafo normal.
			cerrarLista();
			salida += '<p>' + linea + '</p>';
		}
		cerrarLista();

		return salida;
	}

	// =========================================================================
	// Inicialización del widget (una instancia por contenedor)
	// =========================================================================

	/**
	 * Activa un contenedor .chatbot-berenjenal ya presente en la página.
	 *
	 * @param {HTMLElement} contenedor Elemento raíz del widget.
	 */
	function inicializarWidget(contenedor) {
		var esFlotante = contenedor.classList.contains('chatbot-berenjenal--flotante');

		var boton = contenedor.querySelector('.chatbot-berenjenal__boton');
		var ventana = contenedor.querySelector('.chatbot-berenjenal__ventana');
		var cerrar = contenedor.querySelector('.chatbot-berenjenal__cerrar');
		var mensajes = contenedor.querySelector('.chatbot-berenjenal__mensajes');
		var formulario = contenedor.querySelector('.chatbot-berenjenal__formulario');
		var entrada = contenedor.querySelector('.chatbot-berenjenal__entrada');
		var enviar = contenedor.querySelector('.chatbot-berenjenal__enviar');

		// Estado interno de la instancia.
		var abierto = !esFlotante;              // En modo embebido la ventana siempre está abierta.
		var bienvenidaMostrada = false;
		var peticionEnCurso = false;

		// =====================================================================
		// Funciones internas
		// =====================================================================

		/** Lleva el scroll del área de mensajes hasta abajo. */
		function desplazarAbajo() {
			mensajes.scrollTop = mensajes.scrollHeight;
		}

		/** Muestra el mensaje de bienvenida una única vez. */
		function mostrarBienvenida() {
			if (bienvenidaMostrada) {
				return;
			}
			bienvenidaMostrada = true;
			anadirMensaje(AJUSTES.mensajeBienvenida, 'bot');
			desplazarAbajo();
		}

		/** Abre la ventana de chat (modo flotante). */
		function abrirVentana() {
			contenedor.classList.add('chatbot-berenjenal--abierto');
			if (boton) {
				boton.setAttribute('aria-expanded', 'true');
				boton.setAttribute('aria-label', 'Cerrar el chat de El Berenjenal');
			}
			abierto = true;
			mostrarBienvenida();
			desplazarAbajo();
			if (entrada) {
				entrada.focus();
			}
		}

		/** Cierra la ventana de chat (modo flotante). */
		function cerrarVentana() {
			contenedor.classList.remove('chatbot-berenjenal--abierto');
			if (boton) {
				boton.setAttribute('aria-expanded', 'false');
				boton.setAttribute('aria-label', 'Abrir el chat de El Berenjenal');
				boton.focus();
			}
			abierto = false;
		}

		/** Alterna entre abrir y cerrar (al pulsar el botón flotante). */
		function alternarVentana() {
			if (abierto) {
				cerrarVentana();
			} else {
				abrirVentana();
			}
		}

		/**
		 * Añade una burbuja de mensaje al área de mensajes.
		 *
		 * @param {string} texto Texto del mensaje.
		 * @param {string} tipo  'usuario' o 'bot'.
		 * @param {string} [fuente] Fuente de la respuesta (p. ej. "compost.md").
		 */
		function anadirMensaje(texto, tipo, fuente) {
			var burbuja = document.createElement('div');
			burbuja.className = 'chatbot-berenjenal__mensaje chatbot-berenjenal__mensaje--' + tipo;

			if ('bot' === tipo) {
				// El contenido del bot se formatea (markdown-lite) y se inserta como HTML.
				var contenido = document.createElement('div');
				contenido.className = 'chatbot-berenjenal__contenido';
				contenido.innerHTML = formatearRespuesta(texto);
				burbuja.appendChild(contenido);

				// Etiqueta pequeña con la fuente consultada por el backend.
				if (fuente) {
					var etiqueta = document.createElement('span');
					etiqueta.className = 'chatbot-berenjenal__fuente';
					etiqueta.textContent = '📄 ' + fuente;
					burbuja.appendChild(etiqueta);
				}
			} else {
				// El mensaje del usuario se inserta como texto plano (seguro).
				burbuja.textContent = texto;
			}

			mensajes.appendChild(burbuja);
			desplazarAbajo();
			return burbuja;
		}

		/** Muestra la burbuja "escribiendo…" con tres puntos animados. */
		function mostrarEscribiendo() {
			var burbuja = document.createElement('div');
			burbuja.className = 'chatbot-berenjenal__mensaje chatbot-berenjenal__mensaje--bot';

			var indicador = document.createElement('span');
			indicador.className = 'chatbot-berenjenal__escribiendo';
			indicador.setAttribute('aria-label', AJUSTES.textoEscribiendo);

			for (var i = 0; i < 3; i++) {
				var punto = document.createElement('span');
				punto.className = 'chatbot-berenjenal__punto';
				punto.setAttribute('aria-hidden', 'true');
				indicador.appendChild(punto);
			}

			burbuja.appendChild(indicador);
			mensajes.appendChild(burbuja);
			desplazarAbajo();
			return burbuja;
		}

		/** Elimina un elemento del DOM si todavía sigue colgado. */
		function eliminarSiExiste(elemento) {
			if (elemento && elemento.parentNode) {
				elemento.parentNode.removeChild(elemento);
			}
		}

		/**
		 * Envía la pregunta al backend y muestra la respuesta del bot.
		 * Flujo: mensaje del usuario → "escribiendo…" → respuesta JSON → burbuja del bot.
		 */
		function enviarPregunta() {
			var pregunta = entrada.value.trim();

			// No se envía nada si está vacío o si ya hay una petición en curso.
			if (!pregunta || peticionEnCurso) {
				return;
			}

			// 1. Mensaje del usuario y bloqueo temporal del formulario.
			anadirMensaje(pregunta, 'usuario');
			entrada.value = '';
			peticionEnCurso = true;
			entrada.disabled = true;
			enviar.disabled = true;

			// 2. Indicador "escribiendo…".
			var indicador = mostrarEscribiendo();

			// 3. Petición POST al backend con tiempo máximo de espera.
			var controlador = new AbortController();
			var temporizador = setTimeout(function () {
				controlador.abort();
			}, AJUSTES.tiempoEsperaMs);

			fetch(AJUSTES.endpoint, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ pregunta: pregunta }),
				signal: controlador.signal
			})
				.then(function (respuesta) {
					if (!respuesta.ok) {
						throw new Error('HTTP ' + respuesta.status);
					}
					return respuesta.json();
				})
				.then(function (datos) {
					eliminarSiExiste(indicador);
					if (datos && 'string' === typeof datos.respuesta) {
						// 4. Respuesta del bot (con su fuente si la trae).
						anadirMensaje(datos.respuesta, 'bot', datos.fuente || '');
					} else {
						throw new Error('Respuesta inesperada del backend');
					}
				})
				.catch(function () {
					// 5. Fallback: error de conexión o respuesta inválida.
					eliminarSiExiste(indicador);
					anadirMensaje(AJUSTES.mensajeError, 'bot');
				})
				.finally(function () {
					// Se reactiva el formulario pase lo que pase.
					clearTimeout(temporizador);
					peticionEnCurso = false;
					entrada.disabled = false;
					enviar.disabled = false;
					if (abierto) {
						entrada.focus();
					}
				});
		}

		// =====================================================================
		// Eventos
		// =====================================================================

		// Botón flotante: abre/cierra la ventana.
		if (boton) {
			boton.addEventListener('click', alternarVentana);
		}

		// Botón ✕ de la cabecera.
		if (cerrar) {
			cerrar.addEventListener('click', function () {
				if (esFlotante) {
					cerrarVentana();
				}
			});
		}

		// Formulario: Enter o clic en ➤.
		formulario.addEventListener('submit', function (evento) {
			evento.preventDefault();
			enviarPregunta();
		});

		// =====================================================================
		// Estado inicial
		// =====================================================================

		if (esFlotante) {
			// En modo flotante la ventana empieza cerrada (CSS: opacity 0 +
			// visibility hidden, que la saca del árbol de accesibilidad);
			// la bienvenida se muestra en la primera apertura.
		} else {
			// En modo embebido la ventana está visible desde el principio.
			contenedor.classList.add('chatbot-berenjenal--abierto');
			mostrarBienvenida();
		}
	}

	// =========================================================================
	// Arranque
	// =========================================================================

	/** Inicializa todos los widgets presentes en la página. */
	function iniciar() {
		var contenedores = document.querySelectorAll('.chatbot-berenjenal');
		for (var i = 0; i < contenedores.length; i++) {
			inicializarWidget(contenedores[i]);
		}
	}

	// Espera a que el DOM esté listo (o arranca ya si lo está).
	if ('loading' === document.readyState) {
		document.addEventListener('DOMContentLoaded', iniciar);
	} else {
		iniciar();
	}
})();
