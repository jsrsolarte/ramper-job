# Proposal

## Why

La aplicación puede presentar una hora pasada como la próxima búsqueda, lo que confunde y oculta un posible retraso operativo. Es necesario comunicar el estado real sin inventar una nueva hora ni asumir que el ciclo se ejecutó.

## What Changes

- Distinguir una estimación futura de una búsqueda vencida y todavía no registrada como iniciada.
- Mostrar el retraso en dashboard y administración, preservando las pausas y el intervalo vigentes.
- Mostrar cuando hay una búsqueda en curso confirmada y, por separado, la próxima hora si existe una estimación fiable.
- Facilitar el diagnóstico administrativo del ciclo retrasado y verificar si el problema afecta solo la presentación o también la programación.
- No iniciar tareas ni modificar la programación solo por consultar el aviso.

## Capabilities

### New Capabilities

### Modified Capabilities

- `programacion-busquedas`: comunicar explícitamente las estimaciones vencidas y conservar el comportamiento de pausas.

## Impact

- Cálculo compartido y plantillas de dashboard y administración; pruebas con reloj controlado.
- Evaluación de Celery Beat, salud del worker y registro de ciclos; comprobaciones locales con fuentes simuladas.
