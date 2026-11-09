# Proposal

## Why

La aplicación ya tiene entregas de staging identificadas por commit, pero aún no define versiones de producto para sus lanzamientos. Asignar `1.0.0` a la primera salida aprobada a producción y seguir una regla consistente permitirá reconocer y comparar cada versión publicada.

## What Changes

- Adoptar versionado semántico `MAJOR.MINOR.PATCH` para lanzamientos de producción.
- Identificar como `1.0.0` la primera versión que se promueva a producción después de validarse en staging.
- Incrementar el número según compatibilidad: corrección compatible, funcionalidad compatible o cambio incompatible.
- Asociar cada versión a una etiqueta inmutable, un commit y el digest de la imagen desplegada.
- Mantener las pruebas de staging identificadas por commit; no asignarles una versión de producción.

## Capabilities

### New Capabilities
- `versionado-liberaciones`: identifica versiones de producto y relaciona cada lanzamiento de producción con el código y la imagen exactos.

### Modified Capabilities

## Impact

- Etiquetas y proceso de liberación en GitHub Actions/GHCR.
- Registro de la versión y el artefacto usados en producción.
- No cambia la identidad por SHA de las pruebas en staging ni autoriza por sí solo una promoción a producción.
