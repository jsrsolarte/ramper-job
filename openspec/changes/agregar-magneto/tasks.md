# Tasks

## 1. Muestras y consultas

- [x] 1.1 Preparar fixtures sanitizados de las dos muestras de listado y de la ficha independiente compartida; verificar tarjetas, secciones, campos y rutas de término y ubicación, y documentar incertidumbres sin conservar datos personales.
- [x] 1.2 Confirmar las condiciones aplicables a las rutas antes de activar consultas y documentar el resultado; detenerse si prohíben el acceso previsto.
- [x] 1.3 Construir consultas por término y ubicación, una página por combinación, y comprobar con pruebas el ejemplo Medellín/procesos/últimos tres días, acentos, espacios, ubicaciones expandidas y búsqueda sin ciudad para remotos; verificar el mapeo de otras ubicaciones sin asumirlo a partir de Medellín.

## 2. Extracción y seguridad

- [x] 2.1 Implementar extracción HTML de tarjetas a `JobListing` y comprobar con fixtures títulos, enlaces, campos disponibles y ausentes, repetidos y HTML sin resultados.
- [x] 2.2 Implementar extracción de ficha y comprobar con fixtures secciones, ubicaciones múltiples, salarios contradictorios con procedencia, metadatos incompatibles, identidad ambigua, campos incompletos, reutilización de detalle y conservación del listado ante errores individuales.
- [x] 2.3 Implementar validación de URL, DNS y redirecciones, pausas y tiempos de espera; verificar con pruebas destinos inseguros, 401, 403, 429 y autenticación sin evasión.

## 3. Integración y validación

- [x] 3.1 Registrar la fuente y configurar su agente de usuario; comprobar mediante pruebas que se aplica a listados y fichas y documentar configuración y límites.
- [x] 3.2 Verificar búsquedas compartidas, preselección, deduplicación por fuente y URL, elegibilidad y conservación de seguimientos con pruebas sintéticas.
- [x] 3.3 Verificar que bloqueos producen resultados parciales y estado observable sin detener las demás fuentes mediante pruebas de integración.
- [x] 3.4 Incrementar VERSION en MINOR y ejecutar las validaciones de versión y pruebas pertinentes; registrar los resultados.
- [x] 3.5 Desplegar y validar en staging mediante el flujo autorizado, con pruebas sintéticas; registrar resultados y limitaciones antes de solicitar promoción.
