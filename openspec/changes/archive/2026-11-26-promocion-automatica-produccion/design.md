# Design

## Context

Ver `proposal.md` y las specs delta. El workflow de producción actual separa el evento `push` a `main`, que valida y construye otra imagen, de un `workflow_dispatch` que verifica staging y modifica el pin de producción. Flux sigue reconciliando `main`; el pin productivo se actualiza como commit GitOps.

## Goals / Non-Goals

**Goals:**
- Tratar el merge aprobado desde `staging` a `main` como la autorización de esa promoción.
- Promover el tag/digest inmutable existente de staging después de validar el merge.
- Evitar que pushes directos, PR de otros orígenes, fallos, candidatos obsoletos o ejecuciones atrasadas cambien el pin productivo.

**Non-Goals:**
- Cambiar la fuente de Flux, la configuración de staging o la política de backups.
- Promover automáticamente código que no se haya publicado y aprobado en staging.
- Asignar versiones semánticas o modificar cómo se numeran lanzamientos.

## Decisions

1. **Promover solo merges de PR desde `staging`.** El evento de push a `main` dispara validación; el pipeline identifica el PR fusionado asociado al commit y requiere base `main`, origen `staging` y estado merged. Se elige esta comprobación porque los eventos push también cubren pushes directos y commits GitOps, que no deben autorizar una promoción.

2. **Usar la imagen ya probada.** Tras validar el commit de `main`, el pipeline lee el SHA del pin de staging, verifica que la imagen GHCR exista y que el código de aplicación de ese candidato coincida con el merge. El pin de producción apunta al SHA de staging para conservar el mismo artefacto y evitar reconstruir otra imagen.

3. **Serializar y rechazar ejecuciones obsoletas.** Una concurrencia de producción permite una promoción a la vez. Antes de escribir, el pipeline vuelve a comprobar que `main` sigue en el commit del evento y que `staging` aún apunta al mismo candidato. Ante divergencia, termina sin modificar producción; un nuevo merge puede iniciar una ejecución actualizada.

4. **Mantener el commit GitOps fuera del disparador.** El workflow ignora cambios aislados al pin `deploy/overlays/prod/kustomization.yaml`; el commit automatizado solo actualiza ese archivo y Flux lo reconcilia. Así, el pin no genera una segunda promoción.

5. **Retirar el despacho manual como vía normal.** La confirmación `PROMOVER` deja de ser requisito para el flujo de merge. Se elige este camino porque el merge del PR desde staging ya representa la decisión explícita de liberar esa versión.

## Risks / Trade-offs

- [La API no identifica el PR fusionado o el token carece de lectura de PR] → Dar permiso mínimo `pull-requests: read` y fallar cerrado sin cambiar el pin.
- [Staging avanza entre validación y escritura] → Releer y comparar el SHA del pin inmediatamente antes del commit GitOps; si cambió, no promover.
- [La imagen candidata fue retirada o el pin no es una referencia inmutable válida] → Verificar el tag por SHA en GHCR y abortar sin modificar producción.
- [Un error en la automatización afecta producción sin el paso manual adicional] → CI obligatorio, origen PR restringido a `staging`, comprobación de código e imagen, concurrencia y rollback cambiando el pin mediante Git.

## Migration Plan

1. Implementar y validar las comprobaciones con fixtures o respuestas simuladas de PR; mantener inactivo el pin de producción.
2. Probar en staging que el pin y la imagen candidata coinciden; revisar la PR de promoción y sus checks.
3. Tras la aprobación del usuario, integrar a `main`; el primer merge activa la nueva promoción automática para el candidato validado.
4. Confirmar el commit del pin, reconciliación de Flux, salud de web/worker/Beat y acceso al dashboard.
5. Si el despliegue falla, restaurar mediante un commit GitOps el pin de producción anterior; Flux aplica la imagen previa.

## Open Questions

Ninguna; el origen de la autorización queda definido como el merge del PR de `staging` a `main`.
