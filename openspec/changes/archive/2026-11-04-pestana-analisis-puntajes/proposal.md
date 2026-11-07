# Proposal

## Why

La distribución de puntajes y su sugerencia compiten visualmente con las vacantes cuando aparecen en el dashboard. Una pantalla «Análisis» accesible desde la navegación principal junto a Mi perfil permite consultar estas métricas sin quitar foco a las oportunidades y deja espacio para ampliar esta área más adelante.

## What Changes

- Añadir una pantalla privada «Análisis» enlazada desde la navegación principal, junto a Mi perfil.
- Mover a esa pantalla la distribución, el tamaño de muestra, la mediana y la sugerencia de puntaje.
- Quitar el panel de distribución de la página Recomendaciones.
- Mantener la acción de aplicar la sugerencia al filtro temporal y volver a Recomendaciones con el filtro aplicado, sin cambiar el mínimo guardado del perfil.
- Si la sugerencia está por debajo del mínimo del perfil, conservar el enlace para editarlo desde la configuración del perfil.

## Capabilities

### New Capabilities

### Modified Capabilities

- `dashboard-vacantes`: añadir «Análisis» a la navegación principal y ubicar allí la distribución y sugerencia de puntaje.

## Impact

- Navegación, rutas, vista y plantilla del dashboard.
- Presentación de la distribución y acciones del filtro temporal.
- Depende de `distribucion-umbral-puntajes`, que debe implementarse, probarse y sincronizarse primero.
