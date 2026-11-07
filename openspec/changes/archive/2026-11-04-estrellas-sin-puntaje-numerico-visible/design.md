# Design

## Context

Las tarjetas ya calculan una etiqueta accesible con el puntaje exacto y muestran las estrellas con un porcentaje de relleno. El cambio se limita a la presentación de ese puntaje; véanse la propuesta y la delta de `dashboard-vacantes`.

## Goals / Non-Goals

**Goals:**
- Mantener una única calificación visible en la tarjeta: las estrellas.
- Seguir comunicando el puntaje exacto a tecnologías de asistencia.

**Non-Goals:**
- Cambiar los valores calculados, los filtros, el orden, ni el desglose de criterios.

## Decisions

### Ocultar solo el texto visual del puntaje

Eliminar el elemento que imprime la fracción numérica junto a las estrellas y conservar intactos el `aria-label` del puntaje y el cálculo del relleno visual.

**Alternativa considerada:** ocultar la fracción solo con CSS. Se descarta porque el dato seguiría formando parte del contenido visual/DOM innecesariamente y mantendría dos representaciones en la tarjeta.

## Risks / Trade-offs

- [La cifra exacta deja de leerse visualmente en la tarjeta] → La equivalencia por estrellas se conserva visualmente y el puntaje exacto sigue disponible con lector de pantalla y en el desglose.

## Migration Plan

No requiere migración de datos. El cambio de plantilla puede revertirse para restaurar la fracción, sin tocar los análisis guardados.
