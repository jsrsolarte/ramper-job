# Tasks

## 1. Preferencias versionadas de perfil

- [x] 1.1 Convertir criterios existentes a frases y agregar ubicaciones y modalidad remota en Profile y ProfileRevision; verificar que la migración conserve perfiles previos y cree snapshots completos.
- [x] 1.2 Actualizar el formulario para agregar/quitar frases y ubicaciones, editar aceptación remota y validar las listas en servidor; verificar que guardar cree una nueva revisión con los valores esperados.
- [x] 1.3 Ajustar la generación de búsquedas para combinar todas las frases del aspirante con hasta cinco sugerencias de IA respaldadas por el CV; verificar que no se pierdan frases manuales ni se dupliquen términos.
- [x] 1.4 Incluir ubicaciones y modalidad remota en la solicitud de análisis y en sus criterios de compatibilidad; verificar que el modelo reciba ambas preferencias.

## 2. Vacantes estructuradas y CV privado

- [x] 2.1 Validar y persistir resumen, responsabilidades, requisitos y condiciones estructuradas; verificar rechazo de campos inválidos y omisión de secciones no sustentadas.
- [x] 2.2 Actualizar las tarjetas para mostrar la salida estructurada de forma concisa y truncar descripciones históricas; verificar que el enlace original continúe disponible.
- [x] 2.3 Servir `/private-media/<ruta>` solo cuando coincide con el CV del perfil del usuario autenticado; verificar descarga propia y rechazo de acceso ajeno/anónimo.

## 3. Integración local

- [x] 3.1 Ejecutar migraciones y comprobaciones de Django, y recorrer el formulario, descarga y dashboard con el usuario local de demostración; confirmar que las preferencias guardadas se usan en nuevos análisis.
