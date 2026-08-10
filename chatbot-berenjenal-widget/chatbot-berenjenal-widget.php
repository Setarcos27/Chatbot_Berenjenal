<?php
/**
 * Plugin Name:       Chatbot El Berenjenal
 * Plugin URI:        https://vagamundis.org
 * Description:       Widget de chat flotante para el huerto comunitario El Berenjenal. Se conecta al backend Flask (endpoint POST /chat) y es configurable desde Ajustes → Chatbot El Berenjenal. Incluye el shortcode [chatbot_berenjenal].
 * Version:           1.0.0
 * Author:            Vagamundis
 * License:           GPL-2.0-or-later
 * Text Domain:       chatbot-berenjenal
 *
 * Estructura del plugin:
 *   chatbot-berenjenal-widget.php   → Lógica principal (ajustes, shortcode, inyección en el pie).
 *   assets/css/chatbot-style.css    → Estilos del widget (CSS vanilla, sin dependencias).
 *   assets/js/chatbot-widget.js     → Comportamiento del chat (JavaScript vanilla, sin jQuery).
 */

// Evita el acceso directo al archivo fuera de WordPress.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

// =============================================================================
// Constantes del plugin
// =============================================================================

define( 'CHATBOT_BERENJENAL_VERSION', '1.0.0' );
define( 'CHATBOT_BERENJENAL_PLUGIN_URL', plugin_dir_url( __FILE__ ) );
define( 'CHATBOT_BERENJENAL_OPCION_ENDPOINT', 'chatbot_berenjenal_endpoint' );

// URL por defecto: backend en desarrollo local. Se puede cambiar desde
// Ajustes → Chatbot El Berenjenal cuando el backend esté desplegado.
define( 'CHATBOT_BERENJENAL_ENDPOINT_DEFECTO', 'http://localhost:5000/chat' );

// =============================================================================
// Activación del plugin
// =============================================================================

/**
 * Al activar el plugin guardamos el valor por defecto del endpoint
 * (si todavía no existe ninguna opción guardada).
 */
function chatbot_berenjenal_activar() {
	if ( false === get_option( CHATBOT_BERENJENAL_OPCION_ENDPOINT ) ) {
		add_option( CHATBOT_BERENJENAL_OPCION_ENDPOINT, CHATBOT_BERENJENAL_ENDPOINT_DEFECTO );
	}
}
register_activation_hook( __FILE__, 'chatbot_berenjenal_activar' );

// =============================================================================
// Funciones auxiliares
// =============================================================================

/**
 * Devuelve la URL del endpoint configurada.
 * Si el campo está vacío (o nunca se configuró), se usa el valor por defecto
 * de desarrollo local: http://localhost:5000/chat
 *
 * @return string URL completa del endpoint /chat.
 */
function chatbot_berenjenal_obtener_endpoint() {
	$endpoint = get_option( CHATBOT_BERENJENAL_OPCION_ENDPOINT, '' );
	if ( empty( $endpoint ) ) {
		$endpoint = CHATBOT_BERENJENAL_ENDPOINT_DEFECTO;
	}
	return $endpoint;
}

/**
 * Marca en una variable global que el shortcode se ha usado en esta página.
 * Así el pie de página sabe que no debe inyectar el widget flotante (evita duplicados).
 */
function chatbot_berenjenal_marcar_shortcode() {
	$GLOBALS['chatbot_berenjenal_shortcode_usado'] = true;
}

/**
 * ¿Se ha usado el shortcode [chatbot_berenjenal] en la página actual?
 *
 * @return bool
 */
function chatbot_berenjenal_shortcode_usado() {
	return ! empty( $GLOBALS['chatbot_berenjenal_shortcode_usado'] );
}

/**
 * Genera el HTML del widget.
 *
 * @param string $modo 'flotante' (botón circular fijo abajo a la derecha)
 *                     o 'embebido' (ventana siempre visible, para el shortcode).
 * @return string
 */
function chatbot_berenjenal_renderizar_widget( $modo = 'flotante' ) {
	$modo = ( 'embebido' === $modo ) ? 'embebido' : 'flotante';

	$html  = '<div class="chatbot-berenjenal chatbot-berenjenal--' . esc_attr( $modo ) . '">';

	// Botón flotante (solo en modo flotante).
	if ( 'flotante' === $modo ) {
		$html .= '<button type="button" class="chatbot-berenjenal__boton" aria-label="Abrir el chat de El Berenjenal" aria-expanded="false">'
			. '<span class="chatbot-berenjenal__boton-abrir" aria-hidden="true">💬</span>'
			. '<span class="chatbot-berenjenal__boton-cerrar" aria-hidden="true">✕</span>'
			. '</button>';
	}

	// Ventana de chat: cabecera + mensajes + formulario.
	$html .= '<div class="chatbot-berenjenal__ventana" role="dialog" aria-label="Chat de El Berenjenal">'
		. '<header class="chatbot-berenjenal__cabecera">'
		. '<span class="chatbot-berenjenal__titulo">🌱 El Berenjenal</span>'
		. '<button type="button" class="chatbot-berenjenal__cerrar" aria-label="Cerrar el chat">✕</button>'
		. '</header>'
		. '<div class="chatbot-berenjenal__mensajes" role="log" aria-live="polite"></div>'
		. '<form class="chatbot-berenjenal__formulario" novalidate>'
		. '<input type="text" class="chatbot-berenjenal__entrada" placeholder="Escribe tu pregunta…" autocomplete="off" maxlength="500" aria-label="Escribe tu pregunta" />'
		. '<button type="submit" class="chatbot-berenjenal__enviar" aria-label="Enviar mensaje">➤</button>'
		. '</form>'
		. '</div>';

	$html .= '</div>';

	return $html;
}

// =============================================================================
// Recursos (CSS y JS) en el frontend
// =============================================================================

/**
 * Registra y carga los estilos y el script del widget en todas las páginas
 * (el widget flotante aparece en todo el sitio salvo que se use el shortcode).
 * La URL del endpoint se pasa al JavaScript mediante wp_localize_script.
 */
function chatbot_berenjenal_cargar_assets() {
	// CSS del widget.
	wp_enqueue_style(
		'chatbot-berenjenal-estilos',
		CHATBOT_BERENJENAL_PLUGIN_URL . 'assets/css/chatbot-style.css',
		array(),
		CHATBOT_BERENJENAL_VERSION
	);

	// JavaScript del widget (vanilla, sin dependencias; se carga en el pie).
	wp_enqueue_script(
		'chatbot-berenjenal-script',
		CHATBOT_BERENJENAL_PLUGIN_URL . 'assets/js/chatbot-widget.js',
		array(),
		CHATBOT_BERENJENAL_VERSION,
		true
	);

	// Datos disponibles en JavaScript bajo la variable global `chatbotBerenjenal`.
	wp_localize_script(
		'chatbot-berenjenal-script',
		'chatbotBerenjenal',
		array(
			'endpoint'          => esc_url_raw( chatbot_berenjenal_obtener_endpoint() ),
			'mensajeBienvenida' => __( '¡Hola! Soy el chatbot de El Berenjenal 🌱 Pregúntame sobre el proyecto, la asociación, permacultura, compost, riego o el huerto.', 'chatbot-berenjenal' ),
			'mensajeError'      => __( 'Ups… no he podido conectar con el huerto. Inténtalo de nuevo en un momento. 🌱', 'chatbot-berenjenal' ),
			'textoEscribiendo'  => __( 'escribiendo…', 'chatbot-berenjenal' ),
		)
	);
}
add_action( 'wp_enqueue_scripts', 'chatbot_berenjenal_cargar_assets' );

// =============================================================================
// Shortcode [chatbot_berenjenal]
// =============================================================================

/**
 * Shortcode para colocar el chat manualmente en cualquier página o entrada.
 * En este modo la ventana está siempre visible (sin botón flotante).
 *
 * @return string
 */
function chatbot_berenjenal_shortcode( $atts ) {
	// Evitamos que el pie de página inyecte además el widget flotante.
	chatbot_berenjenal_marcar_shortcode();
	return chatbot_berenjenal_renderizar_widget( 'embebido' );
}
add_shortcode( 'chatbot_berenjenal', 'chatbot_berenjenal_shortcode' );

// =============================================================================
// Inyección automática en el pie de página
// =============================================================================

/**
 * Si no se ha usado el shortcode en la página, inyecta el widget flotante
 * al final del body para que aparezca en todas las páginas.
 */
function chatbot_berenjenal_inyectar_footer() {
	if ( chatbot_berenjenal_shortcode_usado() ) {
		return;
	}
	echo chatbot_berenjenal_renderizar_widget( 'flotante' ); // phpcs:ignore WordPress.Security.EscapeOutput.OutputNotEscaped -- HTML generado internamente.
}
add_action( 'wp_footer', 'chatbot_berenjenal_inyectar_footer' );

// =============================================================================
// Ajustes: Ajustes → Chatbot El Berenjenal
// =============================================================================

/**
 * Registra el ajuste del endpoint y su campo en la página de opciones.
 */
function chatbot_berenjenal_registrar_ajustes() {
	register_setting(
		'chatbot_berenjenal_grupo',
		CHATBOT_BERENJENAL_OPCION_ENDPOINT,
		array(
			'type'              => 'string',
			'sanitize_callback' => 'chatbot_berenjenal_sanitizar_endpoint',
			'default'           => CHATBOT_BERENJENAL_ENDPOINT_DEFECTO,
		)
	);

	add_settings_section(
		'chatbot_berenjenal_seccion',
		__( 'Conexión con el backend', 'chatbot-berenjenal' ),
		'chatbot_berenjenal_seccion_descripcion',
		'chatbot-berenjenal'
	);

	add_settings_field(
		'chatbot_berenjenal_campo_endpoint',
		__( 'URL del endpoint /chat', 'chatbot-berenjenal' ),
		'chatbot_berenjenal_campo_endpoint_html',
		'chatbot-berenjenal',
		'chatbot_berenjenal_seccion'
	);
}
add_action( 'admin_init', 'chatbot_berenjenal_registrar_ajustes' );

/**
 * Descripción de la sección de ajustes.
 */
function chatbot_berenjenal_seccion_descripcion() {
	echo '<p>' . esc_html__( 'Aquí se indica dónde está el backend del chatbot. En desarrollo local se usa http://localhost:5000/chat; cuando el backend esté desplegado (Render, Railway…), pega aquí su URL pública terminada en /chat.', 'chatbot-berenjenal' ) . '</p>';
}

/**
 * HTML del campo de texto del endpoint.
 */
function chatbot_berenjenal_campo_endpoint_html() {
	$endpoint = chatbot_berenjenal_obtener_endpoint();
	printf(
		'<input type="url" class="regular-text" name="%1$s" id="%1$s" value="%2$s" placeholder="%3$s" />',
		esc_attr( CHATBOT_BERENJENAL_OPCION_ENDPOINT ),
		esc_attr( $endpoint ),
		esc_attr( CHATBOT_BERENJENAL_ENDPOINT_DEFECTO )
	);
	echo '<p class="description">' . esc_html__( 'Ejemplo en producción: https://tu-backend-en-render.onrender.com/chat', 'chatbot-berenjenal' ) . '</p>';
}

/**
 * Sanitiza el endpoint antes de guardarlo.
 * Si se deja vacío, se restaura el valor por defecto (desarrollo local).
 *
 * @param string $valor Valor enviado desde el formulario.
 * @return string
 */
function chatbot_berenjenal_sanitizar_endpoint( $valor ) {
	$valor = trim( (string) $valor );
	if ( '' === $valor ) {
		return CHATBOT_BERENJENAL_ENDPOINT_DEFECTO;
	}
	return esc_url_raw( $valor );
}

/**
 * Añade la página de ajustes bajo el menú Ajustes.
 */
function chatbot_berenjenal_menu() {
	add_options_page(
		__( 'Chatbot El Berenjenal', 'chatbot-berenjenal' ),
		__( 'Chatbot El Berenjenal', 'chatbot-berenjenal' ),
		'manage_options',
		'chatbot-berenjenal',
		'chatbot_berenjenal_pagina_ajustes'
	);
}
add_action( 'admin_menu', 'chatbot_berenjenal_menu' );

/**
 * Contenido de la página de ajustes.
 */
function chatbot_berenjenal_pagina_ajustes() {
	if ( ! current_user_can( 'manage_options' ) ) {
		return;
	}
	?>
	<div class="wrap">
		<h1><?php esc_html_e( 'Chatbot El Berenjenal', 'chatbot-berenjenal' ); ?></h1>
		<p><?php esc_html_e( 'Configura la URL del endpoint /chat del backend Flask.', 'chatbot-berenjenal' ); ?></p>

		<form action="options.php" method="post">
			<?php settings_fields( 'chatbot_berenjenal_grupo' ); ?>
			<?php do_settings_sections( 'chatbot-berenjenal' ); ?>
			<?php submit_button( __( 'Guardar cambios', 'chatbot-berenjenal' ) ); ?>
		</form>

		<hr />

		<h2><?php esc_html_e( 'Colocar el chat en una página concreta', 'chatbot-berenjenal' ); ?></h2>
		<p><?php esc_html_e( 'Añade el shortcode en cualquier página o entrada:', 'chatbot-berenjenal' ); ?></p>
		<p><code>[chatbot_berenjenal]</code></p>
		<p><?php esc_html_e( 'Si no se usa el shortcode, el widget flotante aparece automáticamente en todas las páginas del sitio.', 'chatbot-berenjenal' ); ?></p>
	</div>
	<?php
}
