# Proposal

## Why

Ramper Job ya está desplegado en producción. Falta reconciliar las tareas originales de puesta en marcha con el estado actual y comprobar una actualización real desde código probado en staging, integrado en `main` y desplegado mediante GitOps.

## What Changes

- Registrar en solo lectura la versión de código y la imagen que ya están desplegadas en producción, sin suponer que los datos históricos de planificación siguen vigentes.
- Validar una versión aprobada en staging, integrarla a `main` y desplegarla mediante el pipeline productivo con autorización explícita.
- Comprobar Flux, salud de web, worker y Beat, acceso administrativo, análisis con OmniRoute y descarga privada de CV; revisar que los datos sigan aislados de staging.
- Verificar los Secrets solo por nombre y tipo y documentar que no hay backups; no copiar credenciales ni datos de staging.

## Capabilities

### New Capabilities
- `despliegue-produccion`: configurar, promover y validar Ramper Job en el entorno productivo aislado.

### Modified Capabilities

## Impact

- Aplicación: `deploy/overlays/prod`, provisión interactiva de Secrets y documentación de liberación.
- Infraestructura: fuente y Kustomization Flux en el namespace `flux-system`, dentro del repositorio `servidor-infra`.
- Producción: namespace `prod`, PVC propios, host `jobs.ramper.lat` y acceso al servicio OmniRoute interno.
- El código de aplicación liberado debe corresponder al candidato aprobado en staging; el SHA del merge y la imagen pueden ser nuevos. No se copiarán perfiles, vacantes, CV ni contraseñas de staging.
