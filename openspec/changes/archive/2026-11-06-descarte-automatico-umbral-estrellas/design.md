# Design

## Context

Ver `proposal.md` para la motivación y `specs/` para el comportamiento requerido. Hoy `Profile.min_score` se consulta durante la presentación del dashboard y encolado de la descripción organizada. `ProfileVacancyDiscovery` registra la primera fecha de hallazgo, pero no conserva el umbral usado entonces. El seguimiento individual ya permite estados pendientes, descartados y etapas posteriores.

## Goals / Non-Goals

**Goals:**
- Asociar el umbral efectivo al primer descubrimiento perfil-vacante.
- Aplicarlo una sola vez cuando termina un análisis válido.
- Evitar que la migración o cambios del perfil reescriban seguimientos existentes.
- Separar el filtro visual del dashboard del umbral de descarte.

**Non-Goals:**
- Cambiar el descarte por antigüedad configurado operativamente.
- Cambiar la rúbrica, los puntajes generados o las etapas del proceso.
- Aplicar el umbral a vacantes anteriores a la activación de esta función.

## Decisions

1. **Guardar el umbral y su evaluación en `ProfileVacancyDiscovery`.** Añadir un entero `auto_discard_threshold` y una fecha nullable `auto_discard_evaluated_at`. Los caminos que crean un descubrimiento nuevo guardarán el `Profile.min_score` vigente. Se elige el descubrimiento porque representa la primera vez que esa vacante entra al ámbito del perfil; guardar el valor en el análisis permitiría que reanálisis posteriores cambien la regla aplicada.

2. **Tratar los registros anteriores como ya evaluados.** La migración conservará los descubrimientos existentes, copiará el umbral actual como dato histórico y marcará su evaluación como realizada. También materializará como descubrimientos históricos las parejas perfil-vacante que solo aparecen en análisis existentes. Así ningún análisis pendiente o seguimiento anterior queda sujeto retroactivamente a la regla.

3. **Evaluar al guardar un análisis completo, de forma idempotente.** Después de validar y guardar el resultado, una operación transaccional bloqueará el descubrimiento; si aún no fue evaluado, comparará el puntaje con su umbral y registrará la fecha de evaluación. Un valor menor que un umbral mayor a cero llevará a Descartadas solo si no existe seguimiento o si sigue pendiente. Estados avanzados y descartes existentes se conservan. El resultado se marca evaluado incluso cuando alcanza el umbral para que reanálisis futuros no cambien la decisión.

4. **Usar el umbral del descubrimiento para decidir la descripción organizada.** Se reemplazarán comparaciones de `Profile.min_score` en la cola de organización por el umbral capturado. De este modo una nueva vacante descartada automáticamente no genera otra llamada de IA y un cambio de perfil no reencola vacantes antiguas.

5. **Hacer que el filtro del dashboard sea independiente y temporal.** La pantalla seguirá filtrando recomendaciones por un puntaje mínimo elegido entre 0 y 10, pero su valor inicial será 0 («Todas»). No se modificará el perfil ni el estado de seguimiento. Los estados fuera de Recomendaciones no reciben este filtro.

6. **No reencolar por cambios exclusivos al umbral.** Guardar un perfil con distinto valor de estrellas no programa análisis ni reorganiza resultados existentes. Cambios de CV, frases, ubicaciones o modalidad mantienen su flujo actual de nueva revisión del perfil.

## Risks / Trade-offs

- [Los descubrimientos creados por un camino no actualizado podrían quedar sin el umbral del perfil] → Centralizar la asignación en los puntos de creación existentes y revisar todos los usos de `ProfileVacancyDiscovery`.
- [Una carrera entre análisis duplicados podría intentar aplicar dos veces el descarte] → Bloquear el descubrimiento durante la primera evaluación y hacer idempotente la transición.
- [El filtro temporal puede mostrar menos resultados que la regla de descarte] → Su mínimo solo oculta recomendaciones de menor puntaje; no altera estados y 0 muestra todas las recomendaciones vigentes.

## Migration Plan

1. Añadir los campos del umbral y de evaluación al descubrimiento.
2. En la migración de datos, completar el umbral de las filas existentes, marcarlas evaluadas y crear filas históricas para análisis previos que no tengan descubrimiento.
3. Desplegar el código que guarda el umbral solo para descubrimientos nuevos y evalúa resultados nuevos.
4. Si se revierte la aplicación, los campos nuevos quedan sin uso; no se ejecutará una migración inversa destructiva ni se cambiarán los estados ya guardados.
