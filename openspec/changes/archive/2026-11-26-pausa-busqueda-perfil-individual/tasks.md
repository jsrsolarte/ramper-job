# Tasks

## 1. Estado de búsqueda en el perfil

- [x] 1.1 Añadir el estado persistente de búsqueda con valor habilitado para perfiles existentes y nuevos; verificar que la migración conserva la participación actual.
- [x] 1.2 Incorporar un control accesible en «Mi perfil» que muestre si la búsqueda está habilitada o pausada; verificar que guardar solo este cambio no crea una revisión ni encola trabajo inmediato.

## 2. Aplicar el estado al flujo de búsqueda

- [x] 2.1 Excluir perfiles pausados de ciclos automáticos, actualizaciones disparadas por cambios del perfil y búsquedas manuales administrativas; verificar que perfiles habilitados siguen encontrando vacantes.
- [x] 2.2 Omitir tareas pendientes de perfiles pausados y comprobar el estado antes de iniciar consultas y de asociar resultados compartidos; verificar la pausa antes y durante una búsqueda agrupada.
- [x] 2.3 Al reanudar, incluir el perfil desde el siguiente ciclo normal sin búsqueda inmediata ni recuperación de tareas omitidas; verificar el flujo de pausar, esperar el ciclo y reanudar.

## 3. Preservar el uso del perfil

- [x] 3.1 Mantener disponibles el CV, los resultados existentes, el análisis de vacantes ya guardadas y el flujo de URL manual para perfiles pausados; verificar que el interruptor no afecta esos caminos.
- [x] 3.2 Confirmar que la pausa por perfil se combina correctamente con la pausa global; verificar que la pausa global sigue deteniendo el procesamiento de todos los perfiles.
