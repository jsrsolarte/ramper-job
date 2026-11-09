# Tasks

## 1. Definir y validar versiones de lanzamiento

- [x] 1.1 Añadir la convención SemVer y la validación de etiquetas `vMAJOR.MINOR.PATCH`; verificar formato válido, rechazo de etiquetas inválidas y rechazo de reutilización de versiones existentes.
- [x] 1.2 Publicar la versión como metadato inmutable de la imagen junto al SHA fuente y digest; verificar que los tres valores apuntan al mismo artefacto.
- [x] 1.3 Documentar en el flujo de liberación cuándo incrementar MAJOR, MINOR o PATCH y verificar que la primera promoción aprobada usa `1.0.0`.

## 2. Vincular staging con producción

- [x] 2.1 Mantener las imágenes de staging identificadas por SHA/digest sin número de versión de producción; verificar una prueba de rama que no cree etiquetas SemVer.
- [x] 2.2 En una liberación aprobada, promover el mismo SHA/digest probado y asociarlo a la etiqueta de versión; verificar que no se construye un artefacto distinto al crear el lanzamiento.
