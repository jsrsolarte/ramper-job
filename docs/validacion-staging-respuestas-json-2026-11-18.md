# Validación de respuestas JSON en staging

Fecha: 2026-11-18 (UTC)

## Artefacto y despliegue

- Commit de aplicación validado y desplegado: `f4884d8d8ab788df3e57c379b73a9b73021adf3c`.
- Commit automático del pin de staging: `e8c8993152f7197d2c465b88b04af4c76f66b246`.
- [Workflow Deliver staging](https://github.com/jsrsolarte/ramper-job/actions/runs/44298797690): validación Django, tests, overlays Kustomize, build y publicación completados con éxito.
- Flux `ramper-job-staging`: `Ready=True`, `suspend=false`, última revisión `staging@sha1:e8c8993152f7197d2c465b88b04af4c76f66b246`; el overlay aplica la imagen del commit `f4884d8…`.
- Rollout: web `1/1`, worker `3/3`, Beat `1/1`. `/healthz` respondió `200`.
- La migración `matching.0015_aicallattempt_format_action_and_repair_stages` aparece aplicada.

## Pruebas con datos sintéticos

Se hicieron llamadas directas desde el contenedor web de staging a la ruta OmniRoute configurada. No se escribieron análisis ni vacantes en la base de datos.

| Flujo | Resultado | Tokens entrada/salida | Duración |
|---|---|---:|---:|
| Puntuación rúbrica v2 | Validada | 619 / 2.529 | 7.621 ms |
| Puntuación rúbrica v3 | Validada | 634 / 1.967 | 6.764 ms |
| Organización de vacante | Validada | 189 / 752 | 3.254 ms |
| Reparación sintáctica | Valores preservados y validada | 317 / 1.399 | 4.641 ms |
| Compatibilidad de salida estructurada | `json_schema` aceptado; una solicitud, sin fallback | 167 / 616 | 3.461 ms |

Uso reportado total: **1.926 tokens de entrada y 7.263 de salida**. OmniRoute no reportó costo monetario, por lo que no se estima un valor en dinero.

Un error HTTP 503 sintético, inyectado en memoria dentro del contenedor (sin solicitud externa), conservó la categoría `omniroute.http_503` y no produjo fallback ni una segunda llamada. La suite automatizada de este commit cubre también errores de proveedor, reintentos durables, vencimiento y ausencia de puntaje parcial.

La cola Celery `celery` tenía **0** mensajes antes y después de las pruebas. Las llamadas sintéticas directas no encolaron trabajos.

## Análisis sintético solicitado

Después se ejecutó un análisis completo de puntuación para validar el registro persistido. La configuración activa inicial todavía era rúbrica 2/prompt 5; el flujo normal `get_active_matching_config()` creó y activó la configuración v3. El análisis quedó ligado a configuración versión 3.

- Análisis `753`, vacante sintética `844`, usuario/perfil `synthetic-json-38ad9fe31c`.
- Estado `completed`, rúbrica v3, resultado **5,0 estrellas**. Las cinco dimensiones quedaron: competencias 2,0; alineación 1,0; educación 0,5; experiencia 1,0; perfil 0,5. El puntaje alto corresponde a que el CV y la vacante de prueba se redactaron deliberadamente para coincidir; no representa una evaluación de una persona real.
- Una llamada de puntuación terminó con `format_action=direct`, 1.446 tokens de entrada, 323 de salida y 4.136 ms.
- La pausa global ya estaba activa. El worker aplazó la entrega original; no se reanudó la cola. Para completar solamente el análisis solicitado se ejecutó su función de tarea dentro del contenedor web con una excepción en memoria de una sola ejecución. Se revocó la entrega diferida de ese mismo análisis.
- La organización quedó `deferred` por la pausa; no se procesó otra tarea. La pausa global permanece activa.
- El perfil, el CV DOCX y la vacante de prueba quedan en staging con identificadores sintéticos para poder revisar el análisis. No se usaron ni modificaron datos de perfiles reales.

## Producción y reversión

Producción no cambió: Flux continúa en `main@sha1:b8ff76f67025fbab2bfd3e5aa1f15101fd17806c`, y web conserva la imagen `ghcr.io/jsrsolarte/ramper-job:b0a37ec103aea19d23e45e46a1ed9d1f59365c90`.

Si se necesita revertir staging, volver a probar el SHA previo `b0a37ec103aea19d23e45e46a1ed9d1f59365c90` mediante el workflow de staging y esperar a que Flux reconcilie ese pin.
