# Proposal

## Why

Los plazos de siete días para descartar recomendaciones y 30 días para archivar seguimientos están definidos como constantes. Permitir que la administración los ajuste ayuda a controlar la vigencia de las listas sin cambiar el código.

## What Changes

- Exponer en los parámetros operativos globales de la plataforma los días hasta descartar recomendaciones pendientes y los días de inactividad hasta archivar seguimientos, compartidos por todos los perfiles.
- Usar siete y 30 días como valores iniciales, respectivamente.
- Aplicar los valores vigentes en la siguiente ejecución diaria de cada tarea, sin iniciar la tarea al guardar el parámetro.
- Validar y auditar los cambios de la misma forma que otros parámetros operativos.

## Capabilities

### New Capabilities

### Modified Capabilities
- `parametros-operativos`: permitir configurar y auditar ambos plazos en días.
- `seguimiento-postulaciones`: aplicar los plazos configurados para descartar y archivar seguimientos por perfil.

## Impact

- Configuración operativa del centro administrativo y tareas periódicas de seguimiento.
- Valores iniciales conservan el comportamiento acordado: 7 días para recomendaciones y 30 días para archivado.
- Depende de `descarte-automatico-recomendaciones`, `limpieza-estados-inactivos` y `parametros-operativos-admin`; debe completarse antes del despliegue a staging.
