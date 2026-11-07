# Proposal

## Why

Con la búsqueda automática cada 120 minutos, la administración no puede solicitar una actualización inmediata cuando necesita comprobar nuevas publicaciones. Se requiere un portal controlado para lanzar ese trabajo sin esperar al siguiente ciclo y sin repetir vacantes o análisis ya existentes.

## What Changes

- Añadir un portal administrativo que exponga únicamente comandos explícitamente autorizados.
- Incorporar como primer comando una actualización inmediata de fuentes que procese vacantes nuevas y encole su análisis cuando corresponda.
- Ejecutar el trabajo de forma asíncrona, con estado visible de ejecución y resultado.
- Evitar que la ejecución manual inserte vacantes duplicadas o repita análisis ya completados; conservar las reglas de elegibilidad y deduplicación del flujo normal.
- Registrar quién solicitó el comando, cuándo, su resultado y errores saneados.

## Capabilities

### New Capabilities

- `comandos-administrativos`: portal seguro de comandos permitidos, ejecución, estado y trazabilidad.

### Modified Capabilities

- `ingesta-vacantes`: permitir solicitar manualmente una actualización antes del ciclo periódico usando el mismo flujo de ingesta y análisis.

## Impact

- Interfaz y autorización del centro administrativo.
- Celery para encolar una ejecución inmediata sin bloquear una petición web ni solapar consultas iguales.
- Flujo de deduplicación, elegibilidad de análisis y métricas operativas de ejecuciones.
- Historial administrativo de acciones y resultados saneados.
