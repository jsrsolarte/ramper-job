# Tasks

## 1. Configuración de la aplicación

- [x] 1.1 Crear `deploy/overlays/prod` con host, CSRF, HTTPS, OmniRoute interno, probes y pin SHA inmutable; validar el render de Kustomize.
- [x] 1.2 Extender CI para validar los overlays de staging y prod; ejecutar el CI del PR y confirmar que la imagen de producción mantiene el SHA validado.
- [x] 1.3 Crear un provisionador interactivo exclusivo de `prod` para Django, PostgreSQL y OmniRoute; comprobar el Secret GHCR existente sin leer ni copiar sus datos.
- [x] 1.4 Actualizar documentación y AGENTS con el procedimiento productivo, el host elegido y la decisión de no usar backups; comprobar que no se describe una ruta de recuperación.

## 2. Registro GitOps de producción

- [x] 2.1 Añadir al repo de infraestructura la fuente de aplicación en `main` y la Kustomization de prod suspendida; validar el render de `clusters/prod` y que no cambian otras apps.
- [x] 2.2 Abrir PRs de aplicación e infraestructura con el candidato y overlay revisables; comprobar que la Kustomization sigue suspendida y prod live no cambia al preparar los PRs.

## 3. Promoción y puesta en marcha

- [x] 3.1 Confirmar el workflow exitoso del SHA probado en staging y que coincide con el pin; el CI del PR valida además el overlay prod sin cambiar la imagen de staging.
- [x] 3.2 Registrar la imagen/revisión actual de prod y el pin de staging; después de aprobar staging, integrar el mismo código a `main`, comprobar el pipeline productivo y registrar los SHA de candidato y merge. Candidato staging `370fa55eeda027a512975a218a405ae7ede676ee`; merge a `main` `9cb5e4e90bc0593497f0576ae6bfa8bf0560977a`; Flux prod aplicó `76278a9c14014cf50d3fd53b5b3923d803831f81`.
- [x] 3.3 Verificar que los Secrets requeridos de `prod` existen por nombre y tipo, sin aprovisionarlos de nuevo ni leer sus valores. Confirmados `ramper-job-secrets` (`Opaque`) y `mcp-gateway-ghcr-prod` (`kubernetes.io/dockerconfigjson`); no se leyeron valores.
- [x] 3.4 Tras la autorización explícita y el cambio GitOps del pin, esperar la reconciliación de Flux y comprobar migraciones, PVC, web, worker, Beat, Redis, PostgreSQL, `/healthz`, `/readyz` y el host público. Flux `Ready`; init containers de migraciones finalizaron con código 0; PVC de PostgreSQL y media enlazados; web, worker, Beat, Redis y PostgreSQL disponibles; `/healthz` y `/readyz` respondieron correctamente en `jobs.ramper.lat`.
- [x] 3.5 Validar la cuenta administradora ya existente, análisis OmniRoute, separación de datos y descarga privada de CV sin exponer información personal. Prod: una cuenta administradora activa con inicio de sesión previo; análisis de puntuación exitosos recientes; PVC distintos para PostgreSQL y media en `prod` y `staging`; el CV sin sesión redirige a login y el flujo del propietario responde 200, cerrando el archivo sin leer su contenido.
- [x] 3.6 Confirmar en el runbook que no hay backups ni recuperación de datos y que la pérdida de perfiles, seguimiento y CV es irreversible; registrar el estado final de Flux y la versión desplegada. El riesgo de pérdida permanente sigue documentado; Flux prod está `Ready` en revisión `76278a9c14014cf50d3fd53b5b3923d803831f81` con imagen de aplicación `9cb5e4e90bc0593497f0576ae6bfa8bf0560977a`.
