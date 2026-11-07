# Tasks

## 1. Preparar transiciones y elegibilidad

- [x] 1.1 Después de `fechas-relativas-vacantes`, identificar por perfil las recomendaciones vigentes y su fecha de entrada al estado; excluir análisis superados y vacantes ya avanzadas.
- [x] 1.2 Implementar el descarte automático mediante la transición existente y reiniciar el reloj al restaurar.

## 2. Ejecutar y reflejar el descarte diario

- [x] 2.1 Añadir y programar una tarea diaria idempotente para recomendaciones pendientes con al menos siete días.
- [x] 2.2 Verificado con pruebas y una ejecución controlada: una vacante vencida pasó a Descartadas, las pestañas y conteos se actualizaron, y al restaurarla la tarea no volvió a descartarla.
