# Proposal

## Why

El merge aprobado a `main` hoy valida y publica una imagen, pero deja la promoción productiva esperando un despacho manual separado. Esto hace que la expectativa de “merge y despliegue” no se cumpla y puede dejar staging y producción en versiones distintas.

## What Changes

- Promover automáticamente a producción después de integrar en `main` un candidato validado en staging.
- Mantener las validaciones de CI y la comprobación de que el código de aplicación integrado coincide con el candidato aprobado.
- Desplegar la misma imagen inmutable que se probó en staging, sin reconstruirla para producción.
- Actualizar el pin de producción mediante el pipeline de GitHub Actions y Flux; dejar de requerir `workflow_dispatch` y `PROMOVER` para esta ruta.
- No promover cambios de `main` que no correspondan al candidato publicado y validado en staging.

## Capabilities

### New Capabilities

<!-- None -->

### Modified Capabilities

- `despliegue-staging`: el merge a `main` del candidato probado activa su promoción automática, condicionada a verificaciones completas.
- `versionado-liberaciones`: la promoción usa exactamente la imagen inmutable validada en staging y conserva su relación con el código liberado.

## Impact

- `.github/workflows/production.yml` y posiblemente validaciones del flujo de liberación.
- `deploy/overlays/prod/kustomization.yaml`, actualizado por CI después de validar el candidato.
- GitHub Actions, GHCR y Flux; no cambia la fuente GitOps ni el entorno de staging.
- Artefactos OpenSpec de `despliegue-staging` y `versionado-liberaciones`.
