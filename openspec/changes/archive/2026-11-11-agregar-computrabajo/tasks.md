# Tasks

## 1. Configuración y consultas

- [x] 1.1 Agregar `COMPUTRABAJO_USER_AGENT` con el valor inicial acordado y documentar su configuración; verificar con pruebas que el valor configurado se envía en listados y fichas.
- [x] 1.2 Construir rutas `/trabajo-de-{término}-en-{ciudad}` (o sin sufijo de ciudad cuando aplique) con `pubdate=1&p=1&by=relevance`, incluyendo ubicaciones cercanas y modalidad aplicable; verificar el ejemplo de analista de procesos en Medellín, normalización de acentos y espacios, parámetros y ausencia de solicitudes a otras páginas.

## 2. Extracción y normalización

- [x] 2.1 Implementar la lectura de tarjetas de Computrabajo y la normalización a `JobListing`; verificar con HTML representativo identificador, título, empresa, ubicación, salario, antigüedad, enlace canónico y campos incompletos.
- [x] 2.2 Implementar la consulta de fichas únicas y la conservación de descripción, condiciones y requisitos disponibles; verificar con muestras de fichas, valores contradictorios, fallos temporales y que una respuesta 401/403/429 detenga las siguientes solicitudes a Computrabajo conservando los datos del listado.
- [x] 2.3 Aplicar límites de tiempo, pausas y validación de destinos y redirecciones; verificar los rechazos de hosts inseguros y respuestas 401, 403 y 429 sin evasión.

## 3. Integración y verificación

- [x] 3.1 Registrar el conector en el flujo común y comprobar con pruebas que las consultas equivalentes se comparten y las vacantes se deduplican sin perder seguimientos ni análisis por perfil.
- [x] 3.2 Verificar mediante pruebas que un bloqueo de búsqueda o ficha de Computrabajo se registra en observabilidad, detiene las solicitudes restantes a esa fuente y no impide procesar El Empleo; revisar compatibilidad con el cambio `preseleccion-titulos-vacantes` si ya está integrado.
- [x] 3.3 Comprobar en un entorno autorizado la búsqueda pública y una ficha con el User-Agent configurado, y registrar el resultado y cualquier limitación de acceso.
- [x] 3.4 Validar el cambio en staging con datos sintéticos y revisar consultas, deduplicación y análisis antes de solicitar cualquier promoción a producción.

Resultado de staging: la actualización manual del 2026-11-11 consultó Computrabajo y obtuvo 11 vacantes sin fallas; la fuente quedó disponible y no reportó errores. Otras consultas individuales de Computrabajo también terminaron correctamente. La actualización completa cubrió 32 búsquedas, terminó en 18,3 minutos y el panel mostró análisis completados/reutilizados y cero pendientes. No se observó bloqueo de acceso.
