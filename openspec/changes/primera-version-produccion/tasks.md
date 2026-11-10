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
- [ ] 3.2 Integrar el código aprobado a `main`, registrar `v1.0.0` con su SHA/digest y comprobar que no se reconstruye ni cambia el artefacto probado.
- [ ] 3.3 Provisionar los Secrets de `prod` de forma interactiva; verificar solo nombres y tipos, sin leer valores.
- [ ] 3.4 Reanudar la Kustomization prod mediante Git y esperar migraciones, PVC, web, worker, Beat, Redis y PostgreSQL listos; comprobar `/healthz`, `/readyz` y el host público.
- [ ] 3.5 Crear la única cuenta administradora por bootstrap interactivo y validar login, análisis OmniRoute, separación de datos y descarga privada de CV antes de dar acceso a familiares.
- [ ] 3.6 Confirmar en el runbook que no hay backups ni recuperación de datos y que la pérdida de perfiles, seguimiento y CV es irreversible; validar el estado final de Flux y la versión desplegada.
