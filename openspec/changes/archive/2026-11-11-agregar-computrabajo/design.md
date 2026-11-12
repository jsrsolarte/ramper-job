# Design

## Context

El registro `jobs/registry.py` instancia actualmente el conector de El Empleo, que entrega `JobListing` a las tareas compartidas. Computrabajo devolvió HTTP 200 al usuario con el User-Agent indicado y HTML que incluye tarjetas `article.box_offer`, su `data-id` y enlaces a fichas; la extracción de fichas mediante Python queda por verificar en implementación.

## Goals / Non-Goals

**Goals:** incorporar una fuente a los procesos y la observabilidad existentes y limitar su volumen por consulta.

**Non-Goals:** agregar una interfaz administrativa para introducir URL de Computrabajo, recorrer páginas posteriores o publicar/promover a producción.

## Decisions

- Crear `ComputrabajoConnector` bajo `jobs/connectors` e incorporarlo a `jobs/registry.py`, entregando `JobListing` con fuente `computrabajo_co`. Se conserva el contrato común y el aislamiento de fallos por fuente.
- Construir búsquedas públicas con la ruta `/trabajo-de-{término-normalizado}-en-{ciudad-normalizada}` cuando hay ubicación y `/trabajo-de-{término-normalizado}` sin ella, en el host colombiano observado `co.computrabajo.com`, y los parámetros `pubdate=1&p=1&by=relevance`. Por ejemplo: `https://co.computrabajo.com/trabajo-de-analista-de-procesos-en-medellin?pubdate=1&p=1&by=relevance`. Utilizar las ubicaciones expandidas por el flujo existente; cuando se acepten remotas, conservar la estrategia de consulta aplicable y validar modalidad y ubicación en el flujo común. No asumir que «Hoy» garantiza exactamente 24 horas ni descartar etiquetas «Ayer».
- Procesar tarjetas `article.box_offer`, obtener `data-id` y el enlace `a.js-o-link`, retirar fragmentos de seguimiento y conservar la URL pública canónica. Reutilizar identidad y deduplicación comunes; cuando el identificador falte, usar la huella existente.
- Consultar las fichas únicas con `requests` y analizar HTML con BeautifulSoup, dependencias ya utilizadas por El Empleo. Conservar datos del listado ante errores de detalle y guardar por separado valores contradictorios. La estructura exacta del HTML de detalle y el comportamiento de solicitudes directas desde el worker deben verificarse durante la implementación.
- Configurar `COMPUTRABAJO_USER_AGENT` mediante entorno, con el valor inicial de la prueba: `Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36`. Aplicarlo a listados y fichas; documentar cómo actualizarlo sin alterar El Empleo. Un 401, 403 o 429 en una búsqueda o ficha detiene las siguientes solicitudes a Computrabajo en esa ejecución. Conservar los datos de listado obtenidos y permitir que las demás fuentes continúen, sin reintentos para eludir controles.
- Aplicar tiempos de espera y pausas entre consultas, limitar redirecciones y validar hosts públicos y destinos para las fichas. Mantener la búsqueda en curso de `preseleccion-titulos-vacantes` como cambio independiente y revisar su compatibilidad al integrar ambos cambios.

## Risks / Trade-offs

- [La primera página omite otras publicaciones] → es el límite de volumen acordado; deduplicar entre términos y ciclos.
- [El HTML y los filtros pueden cambiar] → conservar ejemplos de listado y detalle y cubrir campos incompletos con pruebas.
- [Una respuesta 200 de listado no garantiza que el worker pueda consultar fichas] → verificar el acceso desde el entorno autorizado antes de dar por completada la integración, conservar resultados parciales y detener la fuente ante una respuesta de bloqueo.
- [El orden por relevancia puede incluir cargos poco relacionados] → usar el análisis por perfil existente.

## Migration Plan

Registrar la fuente y su configuración en la aplicación; validar primero en staging con datos sintéticos y observar fallos por fuente. Si hay problemas, retirar o deshabilitar el registro de Computrabajo y conservar El Empleo. La promoción a producción requiere autorización explícita.
