# Design

## Context

`AICallAttempt.error_category` ya registra categorías técnicas de cada llamada, mientras `VacancyAnalysis.error_message` conserva un mensaje genérico. El validador conoce la regla concreta que rechaza, pero esa razón no se propaga al registro. El panel de métricas recibe los intentos y los agrega por etapa y resultado.

## Goals / Non-Goals

**Goals:**
- Propagar códigos de validación estables desde el rechazo hasta el intento de IA.
- Consultar el volumen por categoría en las métricas administrativas existentes.
- Conservar privacidad y compatibilidad con el mecanismo de reintentos.

**Non-Goals:**
- Guardar la respuesta, prompt, CV o evidencia textual enviada por el modelo.
- Cambiar criterios, puntajes, mensajes de error al aspirante o frecuencia de reintentos.
- Añadir una pantalla separada de observabilidad.

## Decisions

### Reutilizar categorías de intento con códigos controlados

Cada validación fallida asigna un código finito que distingue errores como versión de rúbrica, estructura, clave de criterio, tipo/rango de puntaje, combinación estado-puntaje o evidencia. Se reutiliza `AICallAttempt.error_category`, que ya almacena fallos por llamada y tiene longitud suficiente. Se evita guardar el texto libre de excepciones para que una respuesta maliciosa o con información del perfil nunca termine en logs.

Para contenido que no sea JSON válido se conserva una categoría separada del rechazo semántico de una estructura JSON válida. No se añade una migración ni se alteran categorías históricas.

### Agregar los códigos en el panel existente

Las métricas agrupan intentos fallidos de la etapa de puntuación por `error_category` y periodo, manteniendo acceso administrativo. Se muestran conteos y etiquetas legibles para las categorías nuevas; los intentos históricos con `analysis_invalid` aparecen como categoría genérica heredada.

Se prefiere esta vista agregada a listar errores por vacante o perfil: ayuda a localizar fallas sistemáticas sin exponer CV, nombres, prompts ni respuestas.

### Mantener el comportamiento del análisis

El análisis sigue pendiente tras una respuesta inválida y conserva el backoff y vencimiento actuales. El mensaje en la experiencia del aspirante continúa siendo genérico. El diagnóstico se usa para orientar un ajuste posterior del prompt o la serialización, no para alterar automáticamente la rúbrica.

## Risks / Trade-offs

- [Los códigos pueden quedarse cortos ante una nueva regla] → Asignar un código seguro al añadir cada validación y probar su persistencia y agregación.
- [Los registros históricos no tienen causa específica] → Mantenerlos como `analysis_invalid` y distinguirlos de los registros posteriores al cambio.
- [Una etiqueta administrativa podría revelar información] → Derivarla de códigos controlados, nunca de texto de la excepción, modelo o perfil.

## Migration Plan

No requiere migración de base de datos. Desplegar primero el registro de códigos y el agregado de métricas; una reversión puede retirar las etiquetas nuevas y conservar los intentos ya registrados.
