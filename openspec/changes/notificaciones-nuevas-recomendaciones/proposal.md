# Proposal

## Why

Las personas necesitan enterarse de nuevas recomendaciones sin recibir una interrupción por cada vacante. Un indicador discreto y un resumen opcional permiten consultar novedades a su propio ritmo.

## What Changes

- Mostrar en la aplicación un indicador individual de recomendaciones nuevas y una acción explícita para marcarlas como vistas.
- Ofrecer un resumen diario opcional en dispositivos compatibles, desactivado por defecto y limitado a un envío por día cuando haya novedades.
- Solicitar permiso solo al activar la opción, permitir desactivarla y no incluir información personal en el aviso del dispositivo.
- Excluir alertas por vacante, correo, sonidos deliberados, funcionamiento sin conexión y garantía de entrega del navegador.

## Capabilities

### New Capabilities

- `notificaciones-recomendaciones`: indicador individual de novedades y resumen diario opcional en dispositivos compatibles.

### Modified Capabilities

## Impact

- Dashboard, preferencias individuales, seguimiento de novedades, programación Celery y suscripciones Web Push.
- Complementa `instalar-aplicacion-chrome`: la instalación no incluye notificaciones; este cambio añade un service worker para push sin caché ni funcionamiento offline.
- Requiere configuración de claves y acceso a servicios de push; no autoriza despliegues ni cambios de infraestructura.
