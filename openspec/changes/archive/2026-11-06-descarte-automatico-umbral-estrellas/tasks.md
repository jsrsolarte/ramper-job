# Tasks

## 1. Umbral por descubrimiento

- [x] 1.1 Añadir el umbral guardado y la fecha de evaluación a cada descubrimiento; migrar descubrimientos y análisis existentes como históricos sin activar descarte retroactivo. Verificar el plan con `python manage.py makemigrations --check` y revisar el backfill de la migración.
- [x] 1.2 Guardar el umbral actual al crear descubrimientos nuevos desde consulta de fuentes, análisis y recuperación. Verificar que todos los puntos de creación asignen el valor solo en `get_or_create`/inserción inicial.

## 2. Descarte al completar análisis

- [x] 2.1 Aplicar una sola vez el umbral guardado al finalizar un análisis válido y enviar puntajes inferiores a Descartadas, preservando estados avanzados y descartes existentes. Verificar en la ruta de finalización que el bloqueo y la marca de evaluación impiden reevaluaciones.
- [x] 2.2 Usar el umbral del descubrimiento para decidir si se encola la descripción organizada y retirar el reencolado causado únicamente por cambiar las estrellas del perfil. Verificar que no queden decisiones de elegibilidad basadas en el umbral vigente del perfil.

## 3. Perfil y dashboard

- [x] 3.1 Cambiar la etiqueta y ayuda de las estrellas para explicar el descarte automático de vacantes nuevas por debajo del puntaje, incluyendo que 0 desactiva el descarte por puntaje. Verificar el texto y las opciones accesibles de la pantalla de perfil.
- [x] 3.2 Hacer que el filtro de estrellas del dashboard sea temporal, independiente y predeterminado en «Todas», mostrando solo las recomendaciones que siguen pendientes. Verificar que las pestañas de otros estados no reciben ese filtro y que `python manage.py check` termina sin errores.
