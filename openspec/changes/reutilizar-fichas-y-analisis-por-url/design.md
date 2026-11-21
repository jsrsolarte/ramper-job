# Design

## Context

La ingesta actual preselecciona títulos y descarga fichas antes de buscar URL o clave de identidad. `save_listing` usa URL y luego ID numérico o huella; `create_analysis` filtra por revisión y configuración, y el dashboard filtra resultados por revisión vigente. El estado actual no acredita por sí solo que una ficha haya sido descargada exitosamente.

## Goals / Non-Goals

**Goals:** evitar solicitudes repetidas de ficha y llamadas de puntuación para análisis completados, preservando visibilidad, seguimiento y recuperación.

**Non-Goals:** refresco automático de fichas conocidas, equivalencia entre fuentes, fusión por similitud o reprocesamiento masivo de resultados históricos.

## Decisions

1. Normalizar antes de consultar detalle: fuente, esquema y host normalizados, ruta de ficha y barra final consistente, sin query ni fragmento; conservar diferencias significativas de ruta. Validar URL con las reglas de seguridad de cada conector. Comparar exactamente por fuente y URL normalizada, incluyendo URL alternativas solo cuando haya una asociación ya acreditada. Dos rutas distintas no se fusionan por título ni ID.
2. Persistir estado explícito de detalle confirmado. Marcar solo después de una respuesta e interpretación exitosas; fallo, bloqueo o datos de listado no bastan. Para históricos, derivar únicamente de evidencia inequívoca de éxito; si no existe, dejar desconocido y consultar cuando vuelva a encontrarse. No usar `description` como prueba universal. Evitar marcar consultas fallidas como completas.
3. Comprobar fichas conocidas tras preselección y antes de red; reutilizar datos guardados y vincular cada perfil elegible. Usar coordinación durable por URL para búsquedas simultáneas, permitir recuperación de leases y no duplicar llamadas cuando compitan. Preservar progreso por lotes y resultados parciales. Registro manual usa el mismo criterio.
4. Buscar cualquier análisis completado por perfil y vacante, independientemente de revisión/configuración; usarlo como resultado canónico y no forzar reanálisis por actualización material, cambio de perfil ni acción manual. Los pendientes sin resultado completado se recuperan con revisión vigente y manteniendo la fecha de primer hallazgo. Proteger frente a concurrencia y entregas repetidas. Para múltiples resultados históricos elegir de forma determinista el completado más reciente, conservar historial, seguimiento y fechas; no ejecutar IA ni borrar datos en migración.
5. Adaptar dashboard, detalle, filtros y estadísticas para mostrar resultados canónicos de revisiones anteriores, manteniendo su revisión original y el seguimiento. Métricas distinguen fichas reutilizadas, solicitadas y recibidas; históricos sin cobertura quedan desconocidos. Las asociaciones por consulta deben incluir reutilizaciones sin contarlas como nuevas llamadas.
6. Antes de migrar claves, detectar colisiones de URL normalizada y discrepancias entre registros previos; consolidar solo cuando la equivalencia por fuente y URL esté demostrada, preservando análisis y seguimientos. No separar o borrar automáticamente registros históricos agrupados por huella cuya identidad original no pueda reconstruirse. Documentar los conflictos para resolución; no inventar historial.

## Risks / Trade-offs

- [Fichas desactualizadas o vacantes cerradas] → no se refrescan automáticamente; comunicar la limitación. Un refresco futuro requiere otra decisión.
- [URLs distintas de la misma publicación] → se consideran distintas salvo alias ya acreditado; no inferir coincidencias.
- [Descarga duplicada bajo concurrencia o caída] → coordinación durable con expiración y pruebas de recuperación.
- [Historial sin evidencia de descarga] → tratarlo como desconocido, sin asegurar ahorro inmediato en el primer encuentro.

## Migration Plan

Preparar migración reversible de metadatos, verificar colisiones y preservar registros antes de desplegar; validar con datos sintéticos en staging, incluidas búsquedas concurrentes, fallos y visibilidad histórica. Comparar métricas de red y llamadas de IA. La promoción de producción requiere autorización explícita. La reversión de código no debe borrar nuevos datos ni reconstruir análisis; revisar compatibilidad de migración antes de aplicar.
