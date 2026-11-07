# Design

## Context

Mi perfil guarda `min_score` como entero de 0 a 10. El dashboard ofrece otro umbral temporal en la URL y ya limita su mínimo efectivo al valor persistente del perfil.

## Goals / Non-Goals

**Goals:**

- Usar controles nativos de rango enteros en ambos lugares.
- Hacer visible el valor actual y que el mínimo incluye todos los puntajes superiores.
- Mantener separados el valor guardado y el filtro temporal.
- Aplicar el filtro temporal al cambiar el control, sin botón de confirmación.

**Non-Goals:**

- Cambiar los límites o la lógica del puntaje.

## Decisions

- En Mi perfil, reemplazar la lista por un rango de 0 a 10 con paso 1; el valor se persiste con el botón existente para guardar el perfil.
- En el dashboard, usar un rango de `profile.min_score` a 10 con paso 1. El valor mostrado se actualiza mientras se arrastra y el listado se actualiza al confirmar cada cambio del control. La URL conserva el estado temporal para compartirlo y paginar.
- Los controles mostrarán un `output` visible con “X/10 o más”, además de las etiquetas accesibles de mínimo, máximo y valor actual. El dashboard etiqueta el control como temporal y Mi perfil como preferencia guardada.
- Se conservarán los parámetros temporales al paginar. El control nativo de rango ofrece operación por teclado y en pantallas táctiles sin una dependencia adicional.

## Risks / Trade-offs

- **La persona puede confundir los dos umbrales** → Identificar uno como “mínimo en mi perfil” y el otro como “filtro temporal de este listado”, con textos de ayuda distintos.
- **El rango temporal empieza por encima de cero cuando el perfil tiene un mínimo** → Mostrar el mínimo del perfil como límite inferior y el valor actual; el filtro nunca lo reduce.
