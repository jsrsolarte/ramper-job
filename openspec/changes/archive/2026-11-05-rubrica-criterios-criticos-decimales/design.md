# Design

## Context

La rúbrica vigente tiene cinco criterios con máximos que suman 10, acepta enteros y el sistema suma el total. El filtro persistido en el perfil y el filtro temporal del dashboard aceptan enteros. Cada análisis ya conserva la configuración y versión de rúbrica usadas.

## Goals / Non-Goals

**Goals:**

- Usar decimales de una cifra para aportes por criterio, deducciones y total.
- Penalizar de manera explicable contradicciones explícitas a requisitos laborales obligatorios.
- Mantener requisitos sin evidencia como desconocidos y excluir atributos personales de la evaluación.
- Versionar el cambio y recalcular resultados vigentes.

**Non-Goals:**

- Usar atributos de salud, discapacidad u otros datos personales como barreras o deducciones.
- Convertir los filtros de usuario a valores decimales.
- Permitir que el modelo decida por sí solo el peso o el puntaje total.

## Decisions

- Los puntos positivos por criterio siguen sus máximos actuales, admiten incrementos de 0.1 y se almacenan con aritmética decimal. La aplicación calcula el total para evitar errores binarios de redondeo.
- La IA puede identificar requisitos que la publicación marque explícitamente como obligatorios y clasificar la evidencia del perfil como cumple, contradicha o desconocida. La aplicación aplica una deducción fija y versionada de 2.0 por cada requisito crítico distinto contradicho. Sin evidencia no hay deducción. El total se calcula como `máximo(0, suma de criterios − deducciones)` y nunca supera 10.0. El modelo no elige la magnitud de la deducción.
- La configuración versionada conserva la penalización crítica junto a la rúbrica. Los resultados guardan cada requisito crítico, su evidencia, la deducción aplicada y el total calculado para explicar la diferencia.
- Se excluyen del análisis de puntaje discapacidad, condición de salud y otros atributos personales no relacionados con el trabajo. Los requisitos laborales como idioma o certificación solo pueden evaluarse cuando la publicación los declara obligatorios y son relevantes a las funciones; únicamente una contradicción directa genera penalización.
- Los filtros permanecen enteros. Un mínimo de 5 incluye puntajes decimales desde 5.0. Al preparar la implementación se vacía únicamente el conjunto local de vacantes y sus análisis dependientes; no se convierte ni reprocesa un historial anterior. Las versiones de rúbrica y resultados creados después del cambio mantienen trazabilidad normal.

## Risks / Trade-offs

- **La deducción puede aplicarse de forma desigual si una publicación usa lenguaje ambiguo** → Exigir que el requisito esté marcado explícitamente como obligatorio y guardar evidencia textual para revisión.
- **La ausencia de una habilidad en el CV no demuestra que falte** → Marcarla como desconocida y no restar puntos sin contradicción directa.
- **La discapacidad puede aparecer en información del CV o de una vacante** → Excluirla del puntaje en todas las etapas; esta salvaguarda también se alinea con la Ley 1618 de Colombia, que promueve igualdad de oportunidades e inclusión laboral sin discriminación por discapacidad.
- **Los puntajes históricos y nuevos no son directamente comparables** → Versionar la rúbrica, recalcular resultados vigentes y presentar en el dashboard solo resultados de la versión activa.

## Migration Plan

1. En la base local, eliminar las vacantes existentes y los análisis y seguimientos que dependan de ellas. Conservar cuentas, perfiles, revisiones de perfil y configuraciones. Esta limpieza evita convertir puntajes históricos locales.
2. Migrar el campo de puntaje final a decimal, guardar deducciones por separado y crear una nueva versión de rúbrica con penalización crítica de 2.0. Los análisis nuevos se calculan bajo la versión activa.
3. No desplegar ni ejecutar esta limpieza en producción. Si se revierte el cambio, los datos locales eliminados no se restauran automáticamente; la aplicación puede volver a ingerir vacantes.
