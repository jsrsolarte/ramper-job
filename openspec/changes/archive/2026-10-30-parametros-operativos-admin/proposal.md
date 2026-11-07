# Proposal

## Why

La frecuencia de actualización automática de vacantes tiene un valor predeterminado operativo de 120 minutos, pero no existe una forma para que administración lo ajuste sin cambiar la configuración del despliegue. Un panel de parámetros permitirá adaptar la operación y mantener trazabilidad de los cambios.

## What Changes

- Añadir una sección administrativa para editar parámetros operativos explícitamente habilitados.
- Incluir como primer parámetro la frecuencia de actualización de fuentes, expresada en minutos y con 120 como valor inicial.
- Validar el valor antes de guardarlo y aplicar el nuevo intervalo al calendario automático sin iniciar una actualización manual.
- Registrar quién cambió el valor, cuándo y cuál fue el resultado, sin exponer secretos.
- Mantener la configuración de infraestructura y secretos fuera de la interfaz.

## Capabilities

### New Capabilities

- `parametros-operativos`: configuración administrativa y trazable de parámetros operativos permitidos.

### Modified Capabilities

## Impact

- Centro administrativo y autorización de parámetros.
- Persistencia y aplicación del intervalo de actualización de fuentes que hoy se controla con `JOB_REFRESH_MINUTES`.
- Programación de Celery Beat y registro histórico de cambios administrativos.
