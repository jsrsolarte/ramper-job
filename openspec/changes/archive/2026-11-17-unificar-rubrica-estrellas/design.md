# Design

## Context

Ver `proposal.md` y las specs. La rúbrica vigente suma criterios y deducciones en 0–10; la presentación redondea por separado a medias estrellas. La versión de rúbrica identifica los análisis, el mínimo del perfil es entero y los descubrimientos pueden conservar el umbral vigente al encontrarse una vacante. La activación de otra rúbrica normalmente programa reanálisis; esta conversión exige evitarlo explícitamente.

## Goals / Non-Goals

**Goals:**
- Una sola escala para cálculo, resultado guardado y presentación, con migración idempotente y trazabilidad.
- Mantener privacidad, seguimiento, muestra y límites de acceso; no generar llamadas de IA por la migración.
- Determinar filtros por estado antes de paginar, con selección exacta accesible y opción «Todas».

**Non-Goals:**
- Cambiar las decisiones de seguimiento existentes o reanalizar resultados por la conversión.
- Tratar análisis antiguos como si hubieran sido producidos con la nueva rúbrica.
- Desplegar a producción como parte del diseño; conservar la autorización explícita de promoción.

## Decisions

### Rúbrica y redondeo

Versionar la rúbrica y escalar proporcionalmente los máximos anteriores: 2, 1, 1, 0,5 y 0,5. Escalar las deducciones configuradas por la misma proporción y validar las respuestas según la versión. Sumar criterios y aplicar deducciones antes de limitar a 0–5 y redondear al múltiplo de 0,5 más cercano; un empate sube. La precisión interna de criterios y deducciones se conserva suficiente para realizar la suma sin redondeos prematuros. El resultado final es siempre uno de 0, 0,5, …, 5.

### Conversión y trazabilidad

Para cada resultado antiguo, convertir el total de 0–10 dividiéndolo entre dos y redondeando con la misma regla. Mantener versión de origen, evidencia, desglose y valores históricos recuperables; no sobrescribir un desglose histórico de modo que parezca producido bajo la nueva rúbrica. La lectura de resultados vigentes debe incluir los convertidos sin que `RUBRIC_VERSION` los oculte. Proteger la migración con identificación explícita de escala para que sea idempotente y reanudable, incluyendo límites, nulos e históricos sustituidos. Evitar el encolamiento automático por cambio de rúbrica. Una futura evaluación nueva sigue usando la versión vigente y sus reglas normales.

Convertir mínimos guardados del perfil dividiéndolos entre dos y usando el entero superior: 2,5 pasa a 3. Preservar por separado el significado de umbrales capturados al descubrir vacantes y de trabajos en curso, que no deben cambiar decisiones ya tomadas; no aplicar retroactivamente el nuevo mínimo del perfil. Conservar seguimientos y estados.

### Preparación aditiva para versiones coexistentes

La primera etapa agrega `score_stars` como columna generada a partir de `score`, sin modificar el dato anterior ni su desglose. PostgreSQL recalcula la equivalencia cuando un worker antiguo escribe el puntaje de 0–10; puntuaciones nulas o fuera de rango producen una representación no disponible. El redondeo reproduce la visualización histórica y la columna puede retirarse sin alterar el dato original. Se agrega también `min_score_stars`, derivado del mínimo anterior y redondeado hacia arriba. Al guardar un resultado de rúbrica v3, el campo heredado mantiene el doble del resultado redondeado para los procesos antiguos; el desglose conserva los valores propios de la versión 3. Las dos columnas generadas se probaron en PostgreSQL con datos sintéticos, incluidos escrituras antiguas y rollback de `score_stars`.

El despliegue SHALL ocurrir en dos liberaciones de staging. La primera conserva `RUBRIC_VERSION=2`, incorpora lectores de ambas versiones y agrega las columnas generadas; así los workers previos y los de compatibilidad siguen produciendo v2 mientras se verifica la equivalencia de cada registro real de staging. Solo cuando esa imagen y todos sus workers estén activos se despliega la segunda liberación, que fija `RUBRIC_VERSION=3`. Esa imagen de compatibilidad ya entiende prompts, respuestas y escrituras v2/v3, por lo que los workers de la primera liberación pueden terminar mientras empieza la segunda. No se modifica el campo original ni se ejecuta reanálisis. Si falla la segunda liberación, se revierte a la primera y las columnas generadas permanecen compatibles con ambas versiones.

En ambos pasos, los umbrales guardados y capturados permanecen en escala 0–10 para que workers y decisiones preexistentes no cambien. La nueva interfaz muestra y guarda valores pares 0–10 que representan 0–5 estrellas; la columna generada presenta su mínimo entero equivalente. El puntaje v3 conserva el doble del resultado final redondeado en `score` por compatibilidad, mientras `score_stars` expone la escala 0–5. Antes de evaluar un umbral capturado, se compara el total v3 sin redondear; por ejemplo, 5,9/10 se presenta como 3 estrellas, pero queda por debajo de un umbral capturado de 6/10.

### Filtros y estadísticas

Calcular las puntuaciones exactas presentes para el perfil y estado actual sobre el conjunto completo, antes de filtro y paginación; presentar «Todas» y valores disponibles ordenados, incluidos medios. Cada selección filtra por igualdad; al cambiar de estado o desaparecer la puntuación elegida, volver a «Todas». Mantener filtros y conteos privados y accesibles. Las vacantes sin análisis no se representan como cero estrellas.

Actualizar las distribuciones privada y administrativa, recomendaciones de umbral y medianas para la nueva escala, evitando dividir dos veces; respetar separación por versión, muestras y periodos. Coordinar con `distribucion-puntuaciones-estrellas` y `estadisticas-individuales-usuarios`: revisar sus estados y reconciliar sus artefactos y cambios antes de integrar para evitar una conversión duplicada o sobrescritura.

## Risks / Trade-offs

- [Redondear históricos modifica su precisión] → conservar los valores y evidencias originales junto al resultado normalizado e identificar la conversión.
- [El mínimo histórico sube al entero siguiente] → documentar el cambio y aplicarlo solo a descubrimientos futuros; no modificar seguimientos.
- [Migraciones y workers de versiones distintas interpretan una escala incorrecta] → transición expandir/migrar/contraer, control de versión de datos, pruebas de compatibilidad y rollback antes de cualquier promoción.
- [No hay backups productivos] → no ejecutar migraciones de datos productivas sin autorización específica y sin resolver el riesgo y la estrategia de recuperación con la persona usuaria.

## Migration Plan

Preparar migración y pruebas con datos sintéticos, incluidos trabajos pendientes, históricos, rollback y reintentos. En staging, desplegar primero la imagen de compatibilidad y verificar con sus registros existentes que los campos originales, desgloses, evidencias y estados no cambian y que los campos generados son equivalentes. Después desplegar la activación v3 y validar perfil, estados y estadísticas. Ante falla, volver al pin de la imagen anterior; las columnas nuevas son aditivas y el rollback las conserva. Ninguna acción productiva queda autorizada por esta propuesta.

## Dependencias comprobadas antes de implementar

La rama `staging` contiene la distribución administrativa en estrellas: divide la mediana por dos y transforma los límites desde 0–10. Al adoptar puntajes finales en 0–5 esa conversión debe retirarse en el mismo cambio; la división usada para calcular una mediana de dos observaciones permanece. `estadisticas-individuales-usuarios` sigue como propuesta sin implementar y declara que no cambia la distribución global; deberá basarse en la selección vigente ya adaptada a las dos versiones de rúbrica. No integrar su implementación anterior a esta adaptación sin reconciliarla.

La revisión del código también identifica conversiones visuales en `dashboard/score_display.py`, distribuciones privadas, filtros por versión de rúbrica en vistas y tareas, y umbrales capturados en `ProfileVacancyDiscovery`. La integración debe cubrirlos como una unidad y verificar con datos mixtos que los resultados históricos no se oculten ni se conviertan dos veces.

## Validación en staging (2026-11-17)

- Flux reportó `Ready=True`, `suspend=false`; el Deployment web estaba `1/1` con la imagen `ghcr.io/jsrsolarte/ramper-job:6f00823d992ca1fcf9f43deab321e3d7ae907895`.
- `matching.0014_vacancyanalysis_score_stars` y `profiles.0008_profile_min_score_stars` figuran aplicadas. Una consulta agregada, sin leer filas individuales, encontró 751 análisis con puntajes en los once valores de 0 a 5 en medios puntos y cero fuera de rango. Los tres perfiles tenían mínimos migrados 0 (dos) y 2 (uno), sin valores fuera de rango.
- El formulario GET del perfil respondió 200 y presentó las seis opciones enteras 0–5 estrellas. Las vistas GET del dashboard respondieron 200 en Recomendaciones, Descartadas, Aplicadas, En proceso, En entrevista y Finalizadas. En el perfil sintético con datos, Recomendaciones ofreció 1, 1,5, 2, 2,5, 3, 3,5, 4 y 4,5; Descartadas ofreció 0, 0,5, 1, 1,5, 2, 2,5 y 4; los otros cuatro estados ofrecieron solo «Todas» porque no tenían puntajes disponibles.
- La consulta/render de estadísticas administrativas encontró una muestra de 280 análisis del periodo y once bandas exactas de 0 a 5 en incrementos de 0,5. El HTML renderizado produjo patrones discretos de estrellas completas, medias y vacías para las once bandas.
- Todas las consultas fueron de solo lectura y agregadas; no se dispararon tareas de búsqueda ni análisis.

### Recuperación antes de una futura promoción

Si falla la representación de estrellas, volver al pin anterior de staging `0566b63f1aec464b7af81b43b7c19219ec0cded9`. Si falla la activación v3, volver a la imagen de compatibilidad `31444e3acea140cb2b090becbb45ca277341ad27`, que conserva lectura de ambas versiones. Mantener las columnas generadas aditivas y los puntajes y mínimos originales; no ejecutar migraciones inversas como respuesta inicial. Antes de cualquier promoción futura, confirmar el pin/digest actual de producción y el rollback disponible, y solicitar autorización explícita. Esta validación no autoriza una promoción.
