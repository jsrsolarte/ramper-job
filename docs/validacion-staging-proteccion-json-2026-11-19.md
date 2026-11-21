# Validación de staging: reparación JSON

## Candidato y CI

- Código validado: `fd1b4c8f7df821d3e1440433125ccaf70de02153`.
- Ejecución de GitHub Actions: [Deliver staging #44438131052](https://github.com/jsrsolarte/ramper-job/actions/runs/44438131052), finalizada con éxito.
- `manage.py check`: sin problemas.
- Suite Django: 363 pruebas y 25 pruebas adicionales, todas aprobadas.
- Validación de overlays Kustomize y construcción/publicación de imagen: correctas.
- Digest de imagen desplegada: `sha256:348399ef1f792ece7e1716f530a7a11981dc8669334823478ca1dabafc938235`.

La suite cubrió con respuestas sintéticas la preservación de evidencia en puntuación y organización, la recuperación de sintaxis inequívoca, la normalización de un bloque Markdown y el rechazo de contenido alterado. No se lanzó una llamada a OmniRoute ni se crearon análisis en vivo.

Después del despliegue también se ejecutaron en el pod web las pruebas `matching.tests.test_json_response` y `matching.tests.test_processing`: 44 pruebas aprobadas. Django creó y eliminó su base de pruebas temporal. Las respuestas del proveedor estaban simuladas.

## Estado vivo

- Flux reportó `Ready=True` y aplicó `staging@sha1:694ede8d579acfc4a460c0e0066378d3fb4b9383`.
- Web: 1/1; worker: 3/3; Beat: 1/1; todos ejecutando el digest indicado.
- `/healthz`: HTTP 200. `/readyz`: HTTP 200.
- Desde el despliegue no hubo intentos de análisis IA ni ejecuciones operativas nuevas en la base de staging.

Durante el rollout, Kubernetes rechazó temporalmente pods de reemplazo por la cuota del namespace y registró fallos transitorios de sondas de inicio. Flux terminó la reconciliación y los cinco pods quedaron listos; no se observan fallos activos.

## Alcance

La validación usó la base aislada y respuestas sintéticas del workflow de CI, más las comprobaciones vivas de staging. No se usaron CV, vacantes reales ni datos de producción. Esta validación no constituye una promoción a producción.
