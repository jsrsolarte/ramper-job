# Tasks

## 1. Confirmar dependencias

- [x] 1.1 Antes de implementar, confirmar que `seguimiento-postulaciones`, `rubrica-criterios-criticos-decimales`, `analisis-ia-por-etapas` y `fechas-relativas-vacantes` estén implementados e integrados; verificar que existan las pestañas, puntajes decimales y fechas de entrada al estado.

## 2. Ordenar las listas evaluadas

- [x] 2.1 Ordenar Recomendaciones por puntaje numérico descendente completo y conservar su filtro mínimo; verificar puntajes decimales cercanos y que el mínimo no se aplique a otras pestañas.
- [x] 2.2 Ordenar Aplicadas, En proceso, Entrevista, Finalizadas y Descartadas por fecha de entrada al estado descendente; verificar que cada vacante use la fecha del estado actual.
- [x] 2.3 Mantener «Por analizar» fuera de estos órdenes y preservar filtros, paginación y conteos; verificar vacantes sin puntaje y el orden visible en cada pestaña.

## 3. Integrar antes de stage

- [x] 3.1 Verificar conjuntamente puntajes y orden cronológico en cada pestaña, junto con seguimiento por perfil y fechas de estado.
- [ ] 3.2 Antes de cualquier despliegue a stage, confirmar que `ordenar-vacantes-por-puntaje` esté completo e integrado en el commit candidato; verificar que la compuerta de despliegue lo incluya.
