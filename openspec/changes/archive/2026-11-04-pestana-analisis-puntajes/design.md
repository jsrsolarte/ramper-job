# Design

## Context

El dashboard actualmente usa `state` para seleccionar listas de seguimiento y tiene una vista separada para «Por analizar». El cambio de distribución está implementado en `distribucion-umbral-puntajes`, pero ese cambio aún debe archivarse y sincronizar su delta antes de modificar la spec principal.

## Goals / Non-Goals

**Goals:**
- Separar el acceso a Análisis de las pestañas que cuentan vacantes por estado y ubicarlo en la navegación principal junto a Mi perfil.
- Mantener una pantalla independiente que permita ampliar el área de análisis en el futuro.
- Reutilizar la población y el resumen de puntajes ya calculados para el perfil y revisión vigentes.
- Permitir que la sugerencia enlace de vuelta a Recomendaciones con el filtro temporal aplicado.

**Non-Goals:**
- Cambiar la distribución, la regla de la mediana ni el mínimo de cinco análisis.
- Crear conteos de vacantes para la pestaña «Análisis».
- Cambiar automáticamente el mínimo persistido en el perfil.

## Decisions

### Usar una pantalla de primer nivel para Análisis

Agregar una ruta privada `dashboard:analysis` para la página «Análisis» y enlazarla en la navegación principal, junto a «Mi perfil». Se mantiene `state` para las pestañas de seguimiento; «Análisis» no se añade como pestaña ni se interpreta como un estado de vacante.

**Alternativa considerada:** usar `?state=analysis` en la vista de Recomendaciones. Se descarta porque mezcla una pantalla informativa con los estados de seguimiento y requeriría condicionar la vista principal en muchos puntos.

### Reutilizar el resumen y concentrar allí las métricas

La vista independiente consulta los mismos análisis vigentes del perfil que alimentan el resumen actual y reutiliza `build_score_summary`. El bloque de distribución se elimina de Recomendaciones y aparece en «Análisis» con la muestra, la mediana y la sugerencia.

**Alternativa considerada:** duplicar la consulta y el cálculo en la vista nueva. Se descarta para mantener iguales los conteos y reglas entre pantallas.

### Volver a Recomendaciones al aplicar una sugerencia

El enlace de acción abre Recomendaciones con `score_min` en la URL; el dashboard mantiene el mínimo guardado del perfil. Cuando la sugerencia está por debajo del perfil, la vista muestra el enlace de configuración existente en vez de aplicar un filtro que no podría relajar el mínimo.

## Risks / Trade-offs

- [Una ruta nueva podría no conservar la navegación principal o los estilos] → Reutilizar el encabezado y los componentes visuales actuales; verificar acceso autenticado y navegación.
- [La vista nueva y Recomendaciones podrían divergir en la muestra] → Reutilizar el resumen común y las mismas restricciones de revisión y rúbrica vigentes.
- [La delta modifica requisitos añadidos por otro cambio aún no sincronizado] → No iniciar la implementación hasta archivar y sincronizar `distribucion-umbral-puntajes`.

## Migration Plan

1. Archivar y sincronizar `distribucion-umbral-puntajes` después de validar su interfaz.
2. Añadir la vista privada, ruta y enlace «Análisis» junto a «Mi perfil» en la navegación principal; quitar de Recomendaciones el panel de distribución.
3. Mostrar en la nueva vista los datos y acciones de puntaje, conservando privacidad, conteos de vacantes y mínimo persistido.
4. Validar navegación, muestras vacías e insuficientes, aplicación de sugerencia y enlace al perfil.

## Open Questions

Ninguna. «Análisis» será un destino independiente de la navegación principal, no una pestaña de vacantes.
