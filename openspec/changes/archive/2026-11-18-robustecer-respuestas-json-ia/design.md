# Design

## Context

El cliente interpreta `message.content` con `json.loads` y rechaza bloques Markdown. Las pruebas sintéticas de v2 y v3 con `auto` devolvieron bloques JSON completos. El resultado ya pasa por validadores de rúbrica; los errores se reintentan hasta el vencimiento. La respuesta puede contener datos privados y no se persiste completa.

## Goals / Non-Goals

**Goals:** recuperar formato sin reevaluar ni alterar el significado; acotar llamadas y mantener trazabilidad segura.

**Non-Goals:** cambiar la rúbrica, relajar la validación, fijar un modelo o reanalizar resultados históricos.

## Decisions

1. Intentar JSON directo y después retirar solo un único bloque completo con etiqueta `json` o sin etiqueta, sin texto externo; límites de tamaño y comprobación de objeto. Si el objeto interior es válido, continuar a los validadores sin llamar a la IA. No extraer con búsqueda de llaves, que podría aceptar una porción ambigua.
2. Enviar JSON Schema específico por etapa y versión solo tras verificar compatibilidad real de OmniRoute y su ruta. Un rechazo explícito por formato no soportado permite una única llamada de compatibilidad; timeout, autenticación y otros errores no activan esa alternativa. Evitar una secuencia ilimitada de fallbacks.
3. Si el contenido directo o el interior de un bloque inequívoco sigue siendo sintácticamente inválido tras la normalización local, realizar una sola llamada de reparación por respuesta original. Enviar únicamente esa respuesta y el esquema necesario, sin CV, vacante ni prompt de evaluación por separado; tratar el contenido como datos, con instrucciones de no evaluar, añadir, omitir ni cambiar valores. No reparar JSON válido que incumpla reglas de negocio.
4. Una IA no garantiza preservar significado: aceptar la reparación únicamente si una comparación determinista puede demostrar que solo cambió sintaxis y delimitadores y que conserva todos los valores; si el original no permite demostrarlo, rechazarla. Esta limitación favorece integridad frente a recuperar contenido ambiguo. Aplicar después los validadores existentes y cálculo local de puntaje.
5. El límite de una reparación es por respuesta original, no por vida del análisis; un nuevo intento de recuperación genera otra respuesta. Conservar backoff y vencimiento, y contabilizar cada llamada de reparación para detectar costos repetidos. Las métricas no guardan contenido.

## Risks / Trade-offs

- [Esquema no admitido o ignorado] → comprobar la ruta efectiva en staging y conservar compatibilidad acotada y validadores locales.
- [La reparación altera evidencia] → comparación conservadora; rechazar si no se demuestra equivalencia. La reparación puede no recuperar JSON muy dañado.
- [Reintentos durables repiten llamadas] → medir volumen, duración y tokens; respetar espera creciente y vencimiento.
- [Respuesta incluye datos privados] → solo memoria durante la llamada, sin registro ni persistencia del contenido; mismo destino autorizado de IA.

## Migration Plan

Implementar con pruebas sintéticas y verificar en staging con la ruta real, incluyendo incompatibilidad de esquema y recuperación tras fallo. Revisar métricas y cola antes de proponer promoción. Desplegar a producción únicamente con autorización explícita; revertir al artefacto anterior mediante el flujo Git/Flux si se observa regresión. No modificar ni reencolar manualmente datos históricos.
