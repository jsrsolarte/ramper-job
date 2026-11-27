# Proposal

## Why

Ramper Job ya funciona en staging, pero `main` y el clúster todavía no tienen la configuración de producción. Hace falta preparar una primera liberación trazable y aislada.

## What Changes

- Añadir un overlay Kustomize independiente para producción, con host `jobs.ramper.lat`, CSRF, HTTPS, OmniRoute y el artefacto probado en staging.
- Registrar la fuente y reconciliación Flux de producción, inicialmente suspendida hasta provisionar los Secrets de `prod`.
- Provisionar Secrets sin mostrarlos ni versionarlos y crear la cuenta administradora inicial.
- Mantener la base, archivos privados y cuentas separados; no importar datos de staging.
- No configurar backups en producción. Los datos pueden perderse de forma irreversible.

## Capabilities

### New Capabilities
- `despliegue-produccion`: configurar, promover y validar Ramper Job en el entorno productivo aislado.

### Modified Capabilities

## Impact

- Aplicación: `deploy/overlays/prod`, provisionador de Secrets y documentación.
- Infraestructura: fuente y Kustomization Flux dentro de `servidor-infra`.
- Producción: namespace `prod`, PVC propios, host `jobs.ramper.lat` y OmniRoute interno.
- La primera imagen debe ser el mismo SHA/digest validado en staging; no se copiarán perfiles, vacantes, CV ni credenciales.
