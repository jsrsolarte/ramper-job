# Tasks

## 1. Configuración versionada de palabras clave

- [x] 1.1 Agregar el prompt de búsqueda a la configuración versionada de IA y exponerlo en Django Admin; verificar que las nuevas versiones conservan el prompt activo y que la primera configuración incluye un valor predeterminado.
- [x] 1.2 Crear el modelo y migración del conjunto de palabras clave asociado a revisión de perfil y configuración; verificar unicidad por ese par y conservar revisiones anteriores.

## 2. Generación estructurada con OmniRoute

- [x] 2.1 Implementar la solicitud y validación del JSON de términos a partir del texto extraído del CV, criterios y prompt activo; verificar salida válida, términos duplicados, respuesta malformada y reintento ante indisponibilidad.
- [x] 2.2 Reutilizar el conjunto guardado y generar uno nuevo si cambia la revisión del perfil o la configuración; verificar que una repetición del ciclo no vuelve a solicitar términos para el mismo par.

## 3. Búsquedas específicas en Elempleo

- [x] 3.1 Ampliar el contrato de conectores para recibir palabras clave y construir consultas públicas de Elempleo con rutas normalizadas; verificar con fixtures el término “procesos”, varios términos, URLs originales y respuestas sin resultados.
- [x] 3.2 Combinar y deduplicar publicaciones por URL entre términos, detener solicitudes ante bloqueos de acceso y espaciar consultas; verificar deduplicación y registro del estado de la fuente.

## 4. Integración por perfil

- [x] 4.1 Actualizar la tarea periódica para consultar cada perfil activo con su conjunto vigente y programar análisis existentes para vacantes nuevas; verificar dos perfiles con términos distintos y una vacante compartida con análisis privados separados.
- [x] 4.2 Ejecutar la validación integrada del flujo desde perfil versionado hasta URL original en el dashboard y documentar cómo activar la actualización local con Worker y Beat; verificar que una falla de OmniRoute conserva vacantes anteriores y no dispara consulta general.
