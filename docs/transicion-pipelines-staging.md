# Transición de pipelines de Ramper Job

Este documento describe el flujo propuesto para el cambio `separar-pipelines-staging-produccion`. Antes de completar la transición, el workflow anterior sigue vigente y las indicaciones existentes del proyecto continúan aplicando.

## Preparación y exclusión del workflow anterior

1. Preparar una rama desde el estado remoto revisado y abrir un PR hacia `staging`. La validación independiente `pr-validation.yml` debe terminar correctamente y no tiene permisos de escritura ni publicación. El workflow antiguo `ci.yml` puede validar el mismo PR durante esta etapa.
2. Registrar el SHA, el digest y el pin actualmente desplegados en staging y la ruta de reversión. Revisar en GitHub Actions las ejecuciones de `ci.yml` y coordinar el uso de staging compartido.
3. Deshabilitar `ci.yml` en GitHub Actions, verificar que GitHub informa su estado como deshabilitado y esperar a que todas las ejecuciones previas en curso o en cola terminen. Si se actualizó el pin, volver a registrarlo. Si no se puede confirmar el estado o quedan escritores activos, detenerse sin activar el nuevo pipeline.
4. Integrar el candidato en `staging` conservando el pin y los demás manifiestos activos hasta que CI haya validado la nueva imagen. El pipeline `staging.yml` valida el SHA del push, publica la imagen por ese SHA y actualiza el pin mediante una operación serializada que descarta candidatos obsoletos. Flux sigue la rama `staging`.
5. Observar el resultado completo de CI, la imagen por SHA y su digest, el pin y la reconciliación de Flux, además de disponibilidad y el flujo principal con datos sintéticos. Un fallo de validación no autoriza mover el pin. Un rechazo por avance concurrente requiere revisar la nueva cabeza de `staging` y su propia ejecución.

## Producción y reversión

Los PR utilizan `pr-validation.yml` con permisos de lectura. `production.yml` valida cada push a `main` y publica una imagen etiquetada con el SHA del commit, pero no cambia el pin productivo en ese evento. Tras aprobar el staging, la promoción se inicia manualmente desde `main`, escribiendo `PROMOVER` como confirmación. El workflow verifica que el código de aplicación de `main` coincide con el candidato fijado en staging, que la imagen del commit de `main` ya fue publicada y que el SHA ejecutado sigue siendo la cabeza de `main`; después actualiza el pin de prod en Git. Flux realiza el despliegue. La promoción puede construir una imagen distinta y tener otro SHA de merge, siempre que el código de aplicación sea el aprobado en staging.

`release.yml` sigue creando metadatos de versión cuando se publica un tag `v*`; ese registro no actualiza por sí solo el pin de producción. La confirmación manual del workflow es la autorización explícita para modificar el pin productivo.

Para revertir la transición, deshabilitar `staging.yml` y esperar a que terminen sus ejecuciones. Confirmar que ya no puede escribir el pin antes de volver a habilitar `ci.yml`; restaurar el pin inmutable anterior mediante Git si corresponde y comprobar la validación de PR. No modificar producción sin autorización específica.

## Comprobación previa del 16 de noviembre de 2026

La copia separada se comparó con `main` `33dbe661fae9154dbf8b31db9bfdf9c668db325a` y `staging` `3862bf15316a69feea198c8e6cbb9b35cec845af`. El workflow anterior es `ci.yml` (ID 409975351); el pin observado en staging fue `f6e4a15475e44a80d3f7afc79b4eaeabc062ff51`, con Flux listo y los procesos de Ramper Job disponibles. La validación de PR independiente `pr-validation.yml` (ID 420842884, ejecución 44005679342) terminó correctamente en el PR #23; la ejecución 44005679141 del workflow anterior también terminó correctamente. Una consulta de los últimos 20 runs no encontró ejecuciones pendientes o activas. Estos datos son una instantánea y deben actualizarse inmediatamente antes de desactivar el workflow o integrar el candidato.
