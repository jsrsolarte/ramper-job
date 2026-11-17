# Transición de pipelines de Ramper Job

Este documento describe el flujo propuesto para el cambio `separar-pipelines-staging-produccion`. Antes de completar la transición, el workflow anterior sigue vigente y las indicaciones existentes del proyecto continúan aplicando.

## Preparación y exclusión del workflow anterior

1. Preparar una rama desde el estado remoto revisado y abrir un PR hacia `staging`. La validación independiente `pr-validation.yml` debe terminar correctamente y no tiene permisos de escritura ni publicación. El workflow antiguo `ci.yml` puede validar el mismo PR durante esta etapa.
2. Registrar el SHA, el digest y el pin actualmente desplegados en staging y la ruta de reversión. Revisar en GitHub Actions las ejecuciones de `ci.yml` y coordinar el uso de staging compartido.
3. Deshabilitar `ci.yml` en GitHub Actions, verificar que GitHub informa su estado como deshabilitado y esperar a que todas las ejecuciones previas en curso o en cola terminen. Si se actualizó el pin, volver a registrarlo. Si no se puede confirmar el estado o quedan escritores activos, detenerse sin activar el nuevo pipeline.
4. Integrar el candidato en `staging` conservando el pin y los demás manifiestos activos hasta que CI haya validado la nueva imagen. El pipeline `staging.yml` valida el SHA del push, publica la imagen por ese SHA y actualiza el pin mediante una operación serializada que descarta candidatos obsoletos. Flux sigue la rama `staging`.
5. Observar el resultado completo de CI, la imagen por SHA y su digest, el pin y la reconciliación de Flux, además de disponibilidad y el flujo principal con datos sintéticos. Un fallo de validación no autoriza mover el pin. Un rechazo por avance concurrente requiere revisar la nueva cabeza de `staging` y su propia ejecución.

## Producción y reversión

Los PR utilizan `pr-validation.yml` con permisos de lectura. `production.yml` valida pushes a `main` sin escribir pines ni recursos. `release.yml` verifica que el commit de la etiqueta en `main` contiene el código del candidato fijado en staging y resuelve el digest de la imagen existente; cualquier diferencia fuera de configuración de despliegue, documentación OpenSpec y workflows impide preparar la liberación. Etiquetar o validar no autoriza una promoción productiva.

Para revertir la transición, deshabilitar `staging.yml` y esperar a que terminen sus ejecuciones. Confirmar que ya no puede escribir el pin antes de volver a habilitar `ci.yml`; restaurar el pin inmutable anterior mediante Git si corresponde y comprobar la validación de PR. No modificar producción sin autorización específica.
