# Tasks

## 1. Persistencia de estados

- [x] 1.1 Añadir el estado finalizada y guardar el estado previo al descarte; verificar la migración, la unicidad por perfil y vacante y la restauración segura de registros existentes.
- [x] 1.2 Validar en el servidor las transiciones permitidas y persistir el estado previo al descartar; verificar aislamiento por perfil, rechazo de saltos o retrocesos y conservación al reprocesar el análisis.

## 2. Interfaz de seguimiento

- [x] 2.1 Mostrar solo las acciones válidas para la etapa actual, incluida la opción de finalizar desde una etapa de postulación; verificar que no se ofrecen saltos ni retrocesos.
- [x] 2.2 Añadir pestañas para los estados de seguimiento con recomendaciones pendientes de decisión como vista predeterminada; verificar que cada vacante aparece en el listado de su estado.
- [x] 2.3 Permitir descartar desde cualquier estado y mostrar «Descartadas» como listado independiente; verificar que se conserva el estado previo.
- [x] 2.4 Añadir una acción de restauración que devuelva cada vacante descartada a su estado anterior; verificar el cambio de listado.
- [x] 2.5 Mostrar conteos de vacantes únicas y ordenar las pestañas como «Por analizar», «Recomendaciones», «Aplicadas», «En proceso», «Entrevista», «Finalizadas» y «Descartadas»; verificar conteos tras cambios, vacantes duplicadas y listas vacías.
