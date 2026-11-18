# Tasks

## 1. Gatear la promoción por el PR aprobado

- [ ] 1.1 Actualizar el workflow para identificar el PR fusionado hacia `main` y aceptar únicamente PRs cuyo origen sea `staging`; verificar con casos de evento simulados que pushes directos y PRs de otras ramas no cambian el pin.
- [ ] 1.2 Mantener el permiso mínimo para consultar el PR fusionado y validar el SHA de evento; verificar que si la API o la validación fallan el workflow no escriba en el overlay productivo.

## 2. Promover el artefacto validado

- [ ] 2.1 Cambiar la promoción para verificar el candidato y la imagen inmutable de staging, y apuntar el overlay de producción al mismo SHA; verificar que staging y producción resuelven a la misma imagen sin construir otra.
- [ ] 2.2 Serializar promociones y volver a leer los SHA de `main` y `staging` antes de escribir el pin; probar que un candidato obsoleto aborta sin commit GitOps.
- [ ] 2.3 Evitar que el commit del pin vuelva a disparar una promoción; verificar con el evento del commit GitOps que no se inicia otro ciclo.
- [ ] 2.4 Retirar la confirmación manual `PROMOVER` como requisito de la ruta automática y actualizar el runbook; verificar que describe el merge del PR de staging como autorización y el pin anterior como rollback.

## 3. Validar el flujo por entorno

- [ ] 3.1 Ejecutar CI y las pruebas del release candidate; verificar los casos de origen de PR, equivalencia del código, imagen ausente, staging avanzado y pin productivo sin cambios ante error.
- [ ] 3.2 Integrar el workflow actualizado en staging y confirmar que no toca recursos ni pin de producción; revisar imagen, validación de CI y resultado del pipeline.
- [ ] 3.3 Tras aprobar el resultado de staging, integrar el PR a main y comprobar promoción automática, igualdad de SHA/digest de staging y producción, reconciliación Flux y salud de web, worker y programador.
