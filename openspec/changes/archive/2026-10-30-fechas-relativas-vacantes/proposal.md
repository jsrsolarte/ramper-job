# Proposal

## Why

Las fechas exactas de publicación y análisis no permiten identificar rápidamente qué tan reciente es una oportunidad. Mostrar el tiempo transcurrido desde la publicación, el análisis y la entrada al estado actual facilita priorizar vacantes y entender su historial.

## What Changes

- Mostrar «Publicada hace…» cuando la fuente provea la fecha de publicación.
- Mostrar «Analizada hace…» desde la finalización del análisis vigente para el perfil.
- Mostrar en los estados de seguimiento «Aplicada hace…», «En proceso hace…», «Entrevista hace…», «Finalizada hace…» o «Descartada hace…» según cuándo entró la vacante al estado actual.
- Mantener las fechas y su relación con la vacante y el perfil incluso cuando la vacante cambia de estado.
- Omitir la fecha relativa cuando el dato de origen no esté disponible.

## Capabilities

### New Capabilities

### Modified Capabilities
- `dashboard-vacantes`: mostrar la antigüedad de publicación, análisis y estado actual en las vacantes del perfil.

## Impact

- Tarjetas y datos de vacantes del dashboard.
- Registro de cuándo termina cada análisis por perfil y cuándo se alcanza cada estado de seguimiento.
- Cambios de persistencia compatibles con los registros existentes; sin fecha disponible, la interfaz omite la etiqueta.
