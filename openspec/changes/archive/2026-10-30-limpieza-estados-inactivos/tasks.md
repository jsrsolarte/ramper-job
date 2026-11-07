# Tasks

## 1. Preparar el archivado lógico

- [x] 1.1 Después de `fechas-relativas-vacantes` y `descarte-automatico-recomendaciones`, añadir el marcador de archivado al seguimiento por perfil; verificar que la migración preserve todos los estados existentes y no elimine vacantes ni análisis.
- [x] 1.2 Excluir seguimientos archivados de consultas y conteos del dashboard; verificar que otro perfil mantenga su seguimiento activo para la misma vacante.

## 2. Ejecutar la limpieza periódica

- [x] 2.1 Añadir una tarea idempotente diaria que archive todos los estados con al menos 30 días sin cambios; verificar límite temporal, recomendaciones pendientes y cada estado de seguimiento.
- [x] 2.2 Integrar la tarea al scheduler diario y verificar en una ejecución controlada que los registros archivados desaparezcan de pestañas y conteos sin borrar datos compartidos.
