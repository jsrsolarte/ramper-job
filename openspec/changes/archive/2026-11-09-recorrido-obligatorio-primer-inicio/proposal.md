# Proposal

## Why

El recorrido actual es opcional, por lo que una persona nueva puede llegar a las vacantes sin conocer la configuración del perfil ni cómo usar los estados. Hacerlo obligatorio en el primer inicio facilita el comienzo, y mantener un acceso fijo permite repasar la guía después.

## What Changes

- Iniciar automáticamente el recorrido para cuentas aspirantes en su primer acceso y exigir completarlo antes de usar las funciones normales.
- Guardar y reanudar el paso si la persona termina la sesión antes de completar el recorrido.
- Mantenerlo opcional al volver a abrirlo después de haberlo completado.
- Mostrar un botón permanente en el encabezado para abrir la guía de nuevo.
- No bloquear a cuentas que ya habían usado la plataforma antes de esta regla ni a cuentas administradoras.

## Capabilities

### New Capabilities

### Modified Capabilities
- `recorrido-inicial`: exigir el recorrido en el primer acceso de una persona aspirante y mantener un botón visible para volver a abrirlo.

## Impact

- Estado de primer acceso y progreso persistente del recorrido.
- Acceso a vistas normales de aspirantes durante la primera sesión, encabezado de navegación y controles de la guía.
- No cambia el contenido informativo ni los datos del perfil que la guía explica.
