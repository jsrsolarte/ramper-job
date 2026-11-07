# Tasks

## 1. Añadir la pantalla Análisis a la navegación principal

- [x] 1.1 Después de sincronizar `distribucion-umbral-puntajes`, añadir una vista privada y un enlace «Análisis» junto a «Mi perfil», independiente de los estados de seguimiento.
- [x] 1.2 Mover la distribución, muestra y sugerencia a «Análisis» y quitar el panel de Recomendaciones; verificar ambas vistas y los estados vacío e insuficiente.

## 2. Conectar la sugerencia con Recomendaciones

- [x] 2.1 Permitir aplicar la sugerencia desde «Análisis» y regresar a Recomendaciones con el filtro temporal seleccionado; verificar que el mínimo guardado del perfil no cambia.
- [x] 2.2 Si la sugerencia está por debajo del mínimo del perfil, mostrar el límite y el enlace de edición; verificar que solo guardar el perfil modifica su mínimo.

## 3. Validar integración

- [x] 3.1 Ejecutar las pruebas del dashboard y las validaciones OpenSpec; verificar navegación, privacidad, conteos y conservación de estados.

## Workflow follow-up

- Archivar y sincronizar `distribucion-umbral-puntajes` antes de aplicar este cambio, para que las modificaciones partan de los requisitos ya incorporados a la spec principal.
- Archivar y sincronizar este cambio después de implementarlo y validarlo con la persona usuaria.
