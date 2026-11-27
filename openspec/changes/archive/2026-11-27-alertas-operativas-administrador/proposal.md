# Proposal

## Why

Los fallos repetidos o la falta de procesamiento pueden pasar desapercibidos hasta que alguien revisa el panel. La administración necesita enterarse con contexto y sin recibir un aviso por cada error.

## What Changes

- Detectar errores recurrentes, trabajo detenido y retrasos del ciclo automático con umbrales definidos y sensibles a las pausas previstas.
- Mostrar incidentes agrupados, su estado y evidencia segura en el centro administrativo.
- Ofrecer notificaciones opcionales al dispositivo, agrupadas y limitadas para evitar interrupciones frecuentes.
- Contemplar vigilancia independiente para detectar la caída del propio planificador o worker y comunicar claramente sus límites.
- No reiniciar servicios, ejecutar búsquedas, exponer datos personales ni modificar infraestructura por esta propuesta.

## Capabilities

### New Capabilities

- `alertas-operativas`: detección y comunicación administrativa de incidentes operativos recurrentes o persistentes.

### Modified Capabilities

## Impact

- Observabilidad, seguimiento de incidentes, señales de trabajos y suscripciones de notificaciones del administrador.
- Depende de `notificaciones-nuevas-recomendaciones` para reutilizar transporte Web Push o de una base compartida equivalente; no presupone que ya esté implementada.
- Una vigilancia externa independiente y su canal requieren diseño y autorización separados en infraestructura; no se promete detección ante caída total sin ellos.
