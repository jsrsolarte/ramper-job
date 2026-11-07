# Tasks

## 1. Preservar el estado al actualizar publicaciones

- [x] 1.1 Revisar deduplicación y upsert para confirmar que una publicación conocida conserva su identidad por fuente y URL canónica, y no crea una segunda vacante.
- [x] 1.2 Asegurar que la reingesta y la actualización del análisis no creen, reinicien ni restauren automáticamente el seguimiento descartado de ese perfil.

## 2. Excluir descartadas de recomendaciones

- [x] 2.1 Aplicar el estado de seguimiento del perfil como condición al consultar Recomendaciones, incluso si existe un análisis nuevo o el seguimiento está archivado.
- [x] 2.2 Alinear los conteos y la paginación con la misma exclusión para que una vacante descartada no aparezca en resultados ni cifras de Recomendaciones.
- [x] 2.3 Mantener disponible la restauración explícita y, al restaurar, devolver la vacante al estado previo al descarte.

## 3. Verificar aislamiento y regresiones

- [x] 3.1 Verificar que una vacante descartada para un perfil pueda seguir recomendada para otro perfil.
- [x] 3.2 Añadir pruebas para reingesta, reanálisis, cambio de revisión del perfil, seguimiento archivado y restauración manual.
- [x] 3.3 Confirmar que esta funcionalidad no realiza comprobaciones de cierre o disponibilidad en la bolsa de empleo.
- [x] 3.4 Ejecutar validaciones del proyecto para ingesta, seguimiento, dashboard, conteos y permisos por perfil.
