# Proposal

## Why

La administración puede consultar estadísticas globales, pero no dispone de una vista que explique la situación de cada aspirante. Una ficha individual facilita identificar vacantes pendientes y comprender la actividad y el procesamiento de su perfil.

## What Changes

- Permitir abrir una ficha de estadísticas desde cada usuario aspirante activo en gestión de usuarios.
- Mostrar estados actuales de seguimiento, análisis y actividad histórica disponible, con definiciones y cobertura explícitas.
- Restringir la consulta a administración y distinguir estas métricas de las estadísticas globales anónimas.
- Excluir edición de datos, reconstrucción de eventos no registrados y acceso a CV o contenido privado.

## Capabilities

### New Capabilities

- `estadisticas-individuales-usuarios`: consulta administrativa de métricas y actividad disponibles para un aspirante activo.

### Modified Capabilities

## Impact

- Gestión administrativa de usuarios, consultas de perfiles, seguimiento y análisis, y sus plantillas y pruebas.
- Complementa `estadisticas-plataforma` sin modificar su contrato agregado ni depender del cambio propuesto de distribución de estrellas.
