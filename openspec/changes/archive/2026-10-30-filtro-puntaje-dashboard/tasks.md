# Tasks

## 1. Filtro temporal en la consulta

- [x] 1.1 Leer y validar `score_min` en el dashboard, combinarlo con el mínimo del perfil usando el mayor de ambos y cubrir con pruebas los valores ausentes, válidos, inferiores al perfil y fuera de rango.
- [x] 1.2 Mantener el orden descendente por compatibilidad y verificar que la consulta excluya puntajes inferiores al umbral efectivo.

## 2. Control del listado y navegación

- [x] 2.1 Añadir junto al listado un selector temporal con la opción de todas las vacantes permitidas por el perfil y umbrales superiores; verificar que cambiarlo no guarde cambios en el perfil.
- [x] 2.2 Preservar `score_min` en los enlaces de paginación y verificar que el filtro siga aplicado al avanzar, retroceder y recargar.
- [x] 2.3 Ajustar el estado vacío y el control para que indiquen cómo quitar el filtro temporal; verificar el comportamiento con resultados y sin resultados.

## 3. Integración

- [x] 3.1 Validar el cambio con `openspec validate filtro-puntaje-dashboard --strict` y recorrer el dashboard autenticado con filtros distintos; confirmar que el mínimo configurado del perfil no cambie.
