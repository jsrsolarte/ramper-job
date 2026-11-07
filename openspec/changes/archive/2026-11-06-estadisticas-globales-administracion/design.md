# Design

## Context

Ver `proposal.md` y `specs/estadisticas-plataforma/spec.md`. Ya existen dos vistas de alcance distinto: observabilidad registra ejecuciones, duración, cola y fallos; la distribución de puntajes del dashboard muestra datos del perfil actual y ayuda a ajustar su filtro. Las nuevas estadísticas cubren la población de toda la plataforma y los estados de seguimiento definidos por `seguimiento-postulaciones`.

## Goals / Non-Goals

**Goals:**
- Mostrar conteos globales de negocio con denominadores y fecha de corte claros.
- Evitar que puntajes de versiones distintas de la rúbrica se mezclen.
- Respetar la precisión decimal de la rúbrica nueva y usar resultados vigentes, no resultados históricos reemplazados.
- Mantener los resultados agregados separados de registros personales.

**Non-Goals:**
- Reemplazar las métricas de tiempo, volumen de cola y fallas del panel de observabilidad.
- Reemplazar la distribución individual ni la recomendación de umbral para aspirantes.
- Permitir abrir un usuario, CV o vacante individual desde un gráfico global.
- Presentar tendencias históricas de cambios de estado si aún no se registran esos eventos; la distribución de estados inicial es un corte actual.

## Decisions

### Separar métricas de negocio de métricas técnicas

La nueva vista consulta estados y puntajes de negocio; el panel operativo conserva ejecuciones, resultados técnicos, tiempos y antigüedad de cola. Ambos se enlazan desde el centro administrativo sin copiar cálculos.

**Alternativa considerada:** añadir conteos de negocio al historial de ejecución de workers. Se descarta porque esos conteos reflejan estado actual de registros, no resultado de una ejecución.

### Contar por relación de seguimiento y por publicación

Los estados pendiente, descartada, aplicada, en proceso, entrevista y finalizada cuentan relaciones perfil-vacante, porque cada perfil sigue su misma publicación por separado. La disponibilidad activa, cerrada o desconocida cuenta publicaciones únicas por fuente/identificador, de forma independiente. La vista deja explícitos ambos denominadores y fecha/hora de corte.

**Alternativa considerada:** usar un único conteo de vacantes para ambos gráficos. Se descarta porque una publicación puede tener estados de seguimiento distintos entre perfiles.

### Comparar puntajes dentro de su rúbrica

Para cada combinación perfil-vacante, considerar solo el resultado vigente y no reemplazado. Agrupar o filtrar la distribución por versión de rúbrica y no combinar puntajes de escalas distintas. Mostrar conteos en intervalos de un punto, la mediana con precisión decimal, el tamaño de muestra y periodos de 24 horas, 7 días y 30 días.

**Alternativa considerada:** combinar todos los puntajes históricos en un solo histograma. Se descarta porque reprocesamientos y cambios de escala inflarían la muestra y harían las comparaciones engañosas.

### Usar agregados sin navegación a registros

Los endpoints devuelven únicamente conteos y estadísticas sin identificadores de perfil, textos de CV, prompts ni contenido de vacantes. Los periodos anteriores al inicio de instrumentación se señalan como fuera de cobertura en vez de mostrarlos como cero.

**Alternativa considerada:** habilitar filtros o enlaces por cuenta. Se descarta porque el objetivo es entender la distribución de la plataforma sin exponer a personas en la vista estadística.

## Risks / Trade-offs

- [Los estados actuales no explican cómo ni cuándo cambiaron] → Presentarlos como corte actual; una historia de transiciones requerirá una futura especificación de eventos.
- [La rúbrica nueva no tiene cobertura histórica completa] → Mostrar cobertura y versión, y no atribuir datos de antes de la instrumentación.
- [Una distribución de puntajes puede inducir conclusiones con pocas observaciones] → Mostrar siempre cantidad de resultados y no ocultar una muestra pequeña tras promedios.
- [Consultas agregadas pueden crecer con muchos análisis] → Agregar por periodo y versión y usar índices apropiados sin almacenar copias de datos personales.

## Migration Plan

1. Confirmar en la implementación los modelos vigentes de seguimiento, disponibilidad, análisis y versión de rúbrica.
2. Añadir consultas agregadas que respeten relación perfil-vacante, publicación única y resultado vigente.
3. Integrar gráficos separados para estados y puntuaciones en el centro administrativo.
4. Verificar privacidad, denominadores, cortes, versiones de rúbrica y periodos de puntaje en datos sintéticos.
5. Habilitar las estadísticas en staging y comparar conteos visibles con los registros vigentes sin exponer datos individuales.

## Open Questions

Ninguna. Los estados de seguimiento son un corte actual; si después se necesitan tendencias históricas de esos estados, se podrá definir un registro de transiciones aparte.
