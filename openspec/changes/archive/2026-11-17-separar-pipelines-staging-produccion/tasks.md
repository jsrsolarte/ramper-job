# Tasks

## 1. Preparar la separación

- [x] 1.1 Comparar en una copia Git separada las ramas y workflows remotos vigentes con el árbol local y registrar el plan de transición, evitando reemplazar archivos o cambios ajenos; identificar el workflow antiguo, sus ejecuciones y el pin actual antes de cualquier mutación.
- [x] 1.2 Separar la validación de PR en un archivo independiente del workflow antiguo, reutilizando pasos comunes cuando sea seguro; verificar que los PR ejecutan pruebas sin publicar ni alterar pines y documentar eventos y permisos.

## 2. Entregar desde staging

- [x] 2.1 Implementar el pipeline de `staging` desde el SHA del push integrado, retirar la selección manual de otra rama y verificar que los fallos de CI no publican ni actualizan el pin. El workflow `Deliver staging` pasó validación, publicación y actualización del pin en la ejecución 44187687999.
- [x] 2.2 Serializar y proteger el pin ante ejecuciones atrasadas, commits automáticos y cambios concurrentes; probar candidatos fuera de orden, commits solo de pin, avance de la rama y ausencia de bucles, preservando trazabilidad de SHA e imagen. Las 12 pruebas unitarias de `scripts.test_check_staging_candidate` pasaron; el pipeline de staging publicó la imagen del merge `e3aa84c2b69d13c118b46d6e9e7eb0cb64693180` y Flux aplicó la revisión `370fa55eeda027a512975a218a405ae7ede676ee`.
- [x] 2.3 Documentar integración en `staging`, despliegue compartido, verificación y reversión por Git; comprobar que los ejemplos corresponden a los triggers y permisos implementados. Se actualizó `docs/transicion-pipelines-staging.md` y se validó en CI.

## 3. Preparar producción sin promover

- [x] 3.1 Separar el pipeline de producción activado por cambios en `main`; probar que valida y prepara el código integrado sin cambiar el pin ni recursos productivos hasta recibir autorización explícita para desplegar. La ejecución 44189674018 validó y publicó la imagen de `main`; la tarea de promoción quedó omitida hasta la autorización manual.
- [x] 3.2 Garantizar y probar que el código integrado en `main` corresponde al candidato validado en `staging`, aunque el merge tenga otro SHA o el pipeline construya otra imagen; registrar ambos SHA y mantener el workflow de versión compatible. La promoción manual 44190207674 verificó el código entre ramas y publicó el pin autorizado de producción.

## 4. Verificación integral en staging

- [x] 4.1 Validar workflows y casos de fallo con pruebas automatizadas y revisar el plan de migración y reversión; comprobar que los overlays y límites entre entornos siguen intactos. Pasaron CI, pruebas unitarias del candidato, validación de overlays y build de ambas ramas.
- [x] 4.2 Habilitar y verificar la validación de PR independiente, desactivar el workflow anterior en GitHub Actions y esperar a que terminen sus ejecuciones activas o en cola; comprobar el estado y el pin antes de activar la entrega nueva, y documentar una reversión que no reactive escritores simultáneos. El workflow anterior aparece `disabled_manually` y sin ejecuciones activas o en cola; la validación independiente pasó en los PR #25 y #26.
- [x] 4.3 Integrar un candidato en `staging` mediante el nuevo flujo, comprobar CI, publicación, pin, reconciliación de Flux, disponibilidad y flujo principal; registrar el SHA y la ruta de reversión. Flux quedó `Ready` en `staging@sha1:370fa55eeda027a512975a218a405ae7ede676ee`, con web, worker y Beat listos; `/healthz` y `/readyz` respondieron correctamente.
- [x] 4.4 Tras aprobar la prueba en `staging`, integrar ese mismo código en `main`, comprobar el pipeline productivo y, con autorización explícita, desplegarlo por GitOps; verificar la versión activa y los criterios pendientes de `primera-version-produccion` para poder cerrar ambos cambios. El PR #26 se integró como `9cb5e4e90bc0593497f0576ae6bfa8bf0560977a`; la promoción autorizada actualizó el pin y Flux quedó `Ready` en `main@sha1:76278a9c14014cf50d3fd53b5b3923d803831f81`. Salud web validada. En `primera-version-produccion` permanece pendiente validar el flujo de login, análisis OmniRoute y descarga privada de CV.
