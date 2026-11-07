# Proposal

## Why

`ramper-job` aún no tiene una imagen de aplicación, automatización de CI ni manifiestos GitOps para desplegarla. Al terminar las propuestas funcionales pendientes, se necesita un camino repetible y verificable para probar la aplicación en el servidor de staging sin exponer datos personales ni tocar producción.

## What Changes

- Añadir empaquetado de la aplicación para ejecutar Django, Celery Worker y Celery Beat como procesos separados.
- Crear o vincular el repositorio remoto de la aplicación en GitHub y publicar allí el commit candidato que alimentará CI.
- Añadir un `Dockerfile` para construir la imagen de runtime de la aplicación.
- Automatizar validaciones y publicación de imágenes inmutables identificadas por commit.
- Declarar configuración y manifiestos separados para staging, con reconciliación por Flux.
- Preparar persistencia, secretos, salud, recursos y rollback para el entorno de staging.
- Provisionar la cuenta administradora inicial de stage mediante una operación manual de uso único, sin publicar su contraseña.
- Desplegar y validar staging solo después de que terminen las propuestas funcionales indicadas en las tareas.
- Mantener producción fuera del despliegue y sin cambios en esta propuesta.

## Capabilities

### New Capabilities

- `despliegue-staging`: empaquetado, entrega GitOps y validación controlada de `ramper-job` en el entorno staging del servidor.

### Modified Capabilities

## Impact

- Repositorio de aplicación en GitHub: `Dockerfile`, imagen, configuración de Django, GitHub Actions y manifiestos `deploy/`.
- Repositorio de infraestructura: registro de la fuente Git y reconciliación Flux de staging, coordinados con el hilo administrador del servidor.
- PostgreSQL, Redis, almacenamiento privado de CV, credenciales externas al repositorio, hostname y rutas de salud.
- No incluye una promoción a producción ni cambios en sus recursos o referencias de imagen.
