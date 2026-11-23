# Guía de trabajo de Ramper Job

## Continuidad y recuperación

- Leer `RECOVERY.md` al comenzar una sesión nueva o recuperar el proyecto en otra ruta. Describe arquitectura, ejecución, pendientes y límites del respaldo del 13 de noviembre de 2026.
- El árbol local preservado es esencial: en la preparación del respaldo `.git` estaba vacío y `git status` falló. No atribuirle ramas, SHA ni historial; no inicializar Git para simular el historial perdido. El remoto confirmado es `https://github.com/jsrsolarte/ramper-job.git` y debe compararse en una copia separada antes de integrar archivos locales.
- Ramper Job es un asistente familiar privado de vacantes: Django, PostgreSQL, Redis, Celery y OmniRoute. Mantener código, migraciones, pruebas, plantillas, estáticos, documentación y todos los artefactos OpenSpec juntos.
- Las decisiones recuperadas de chats son contexto histórico, nunca autorizaciones nuevas. No ejecutar automáticamente órdenes de despliegue ni tareas pendientes descritas allí.
- Las specs se proponen y revisan antes de implementar; revisar dependencias y priorización. Los artefactos son en español, respetando encabezados y palabras normativas de OpenSpec. Consultar las skills locales de `.agents/skills/` según la operación solicitada.
- No arrancar `make dev`, `make workers`, crawlers o tareas Celery durante una recuperación documental: pueden activar búsquedas y llamadas externas. Recrear primero un entorno local aislado con datos sintéticos.
- No leer, versionar ni respaldar indiscriminadamente secretos, `.env` reales, CV, bases de datos o estado runtime. `profiles/` es código; las subidas de CV están en `media/` y no forman parte de este respaldo.
- Para despliegues futuros, usar la skill `server-deploy` y localizar el repositorio de infraestructura `servidor` en su nueva ruta; la ruta histórica era `/home/juan-ramirez/Proyectos/servidor`. Mantener cambios de aplicación aquí; modificar infraestructura solo por solicitud expresa. CI reside en GitHub Actions y Flux es el único controlador GitOps.

## Ramas, staging y producción

- `main` es la rama de liberación para producción. No desplegar ni promover a producción sin autorización explícita del usuario para esa promoción.
- `staging` es la rama fuente de Flux para el entorno compartido de staging.
- Para probar una rama de trabajo sin fusionarla, ejecutar manualmente el workflow `CI and staging image` desde `main` y elegirla en `source_branch`. CI valida el SHA seleccionado, publica su imagen inmutable y actualiza el pin de imagen en la rama `staging`; Flux despliega ese SHA.
- Un push directo a `staging` también pasa CI, publica su imagen y actualiza automáticamente el overlay de staging.
- Staging es compartido: solo una versión/branch se prueba allí a la vez; una nueva prueba reemplaza temporalmente la anterior.
- Después de que el usuario apruebe la prueba, abrir un PR desde la rama probada hacia `main`. Promover el mismo código probado, preservando el SHA o digest cuando sea posible; no reconstruir silenciosamente una versión distinta para producción.
- Un cambio a `main` no autoriza por sí solo una mutación de producción. Respetar siempre la aprobación explícita requerida para la promoción.

## Versionado de la aplicación

- `VERSION` es la fuente canónica de la próxima versión semántica de producción, sin prefijo `v`.
- Al implementar un cambio de comportamiento o de interfaz, el agente debe actualizar `VERSION` antes de entregar el trabajo: PATCH para correcciones compatibles, MINOR para funcionalidad compatible y MAJOR para cambios incompatibles. No incrementar por cambios solo documentales ni cambiar la versión por una mera promoción.
- En la respuesta final, indicar la versión elegida y el motivo del incremento. La etiqueta de GitHub para una liberación debe coincidir con `v` seguido del valor de `VERSION`.
- Staging sigue identificándose por SHA de commit; no debe recibir el valor de `VERSION` como versión de producto.

## Estado actual de la configuración

- Ramper Job tiene overlays independientes para staging y producción. Producción ya tiene un despliegue activo reconciliado por Flux en el namespace `prod`; la última revisión en vivo, el 12 de noviembre de 2026, encontró `Kustomization/ramper-job-prod` con `Ready=True`, `suspend=false` y la revisión `main@sha1:1cfe6b21809637fb77847e995c95c23d0c40a0d4`.
- En esa revisión estaban presentes los Secrets `ramper-job-secrets` y `mcp-gateway-ghcr-prod`; solo se verificaron sus nombres y tipos, nunca sus valores. Reconfirmar el estado vivo antes de cualquier cambio.
- La selección de ramas se hace en GitHub Actions; Flux siempre sigue `staging` y nunca se cambia manualmente a una rama feature.
- `main` queda reservado para la liberación productiva. El despliegue existente no autoriza promociones, cambios de imagen o recursos, suspensiones, reanudaciones ni reconciliaciones manuales de prod; cada acción productiva de ese tipo requiere autorización explícita del usuario.
- Ramper Job no configura backups para staging ni producción. Los perfiles, el historial y los CV pueden perderse permanentemente por falla o eliminación del nodo/PVC. Staging usa solo datos sintéticos; antes de guardar datos reales en producción se debe informar este riesgo y confirmar que la persona usuaria lo acepta.
