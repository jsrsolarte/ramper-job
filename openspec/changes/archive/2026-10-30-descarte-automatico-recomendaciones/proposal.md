# Proposal

## Why

Las recomendaciones que no se revisan quedan indefinidamente en la pestaña principal y pueden ocultar oportunidades recientes. Descartarlas automáticamente después de una semana mantiene actualizada la lista de cada perfil y deja el reloj de retención correr desde ese cambio de estado.

## What Changes

- Ejecutar diariamente una tarea que descarte recomendaciones que lleven al menos siete días en ese estado.
- Contar los siete días desde la finalización del análisis vigente que puso la vacante en Recomendaciones.
- Aplicar el descarte al seguimiento del perfil correspondiente y conservar la vacante, el análisis y la etapa previa conforme a las reglas de seguimiento.
- Excluir la vacante de Recomendaciones y reflejarla en Descartadas y sus conteos.
- Depender de `fechas-relativas-vacantes` para identificar cuándo se completó el análisis.
- Completar la tarea antes de la salida a staging.

## Capabilities

### New Capabilities

### Modified Capabilities
- `seguimiento-postulaciones`: descartar automáticamente recomendaciones que cumplan siete días sin avanzar.
- `dashboard-vacantes`: mover las recomendaciones vencidas a Descartadas por perfil y actualizar listados y conteos.

## Impact

- Tarea diaria del worker y transición de estado por perfil.
- Conteos, pestañas y fecha de entrada al estado Descartada.
- Depende de la fecha de finalización de análisis de `fechas-relativas-vacantes` y debe integrarse antes de `despliegue-staging-ramper-job`.
