# Design

## Context

Las llamadas de puntuación y organización ya usan prompts versionados y formatos JSON distintos. La rúbrica exige evidencia para los criterios y para requisitos críticos; la etapa de organización devuelve resumen, palabras clave y categorías. El proveedor registra tokens por etapa, lo que permite comparar el efecto del cambio sin guardar respuestas completas.

## Goals / Non-Goals

**Goals:**
- Ajustar las instrucciones de ambas etapas para pedir contenido esencial y evitar repeticiones o explicaciones que no cambian la decisión.
- Mantener los campos y la estructura validados actualmente, incluida la evidencia necesaria para explicar puntajes y deducciones.
- Usar el consumo medido por etapa para evaluar la reducción de tokens de salida.

**Non-Goals:**
- Introducir un máximo global de caracteres o tokens.
- Cambiar los criterios de la rúbrica, la fórmula del puntaje o las categorías de organización.
- Guardar prompts, CV o respuestas completas como parte de la telemetría.

## Decisions

### Ajustar prompts versionados sin cambiar el contrato JSON

Revisar las instrucciones de puntuación y organización para pedir evidencia clave y datos principales, evitando contexto auxiliar, duplicados y narraciones. Mantener los campos requeridos por los validadores y los componentes que presentan la información; así se reduce detalle sin perder comparabilidad ni explicar menos de lo necesario sobre una deducción.

**Alternativa considerada:** reducir campos del resultado estructurado. Se descarta porque eliminaría información usada para interpretar los criterios y no distingue entre detalle redundante y evidencia necesaria.

### Comparar consumo con telemetría agregada

Validar los prompts nuevos con un conjunto representativo de CV y vacantes usando la misma configuración de modelo. Comparar tokens de salida por etapa y verificar que las respuestas sigan pasando los validadores y contengan los campos requeridos. Usar promedios sobre varios casos para reducir el efecto de variabilidad de una respuesta individual.

**Alternativa considerada:** fijar un límite estricto de longitud. Se descarta porque la cantidad de detalle útil depende del caso y el objetivo es pedir menos información secundaria.

## Risks / Trade-offs

- [El modelo puede seguir agregando explicaciones redundantes] → Aclarar en los prompts que solo incluya información que sustente el puntaje o ayude a comparar la vacante; revisar muestras de salida.
- [Una instrucción demasiado concisa puede ocultar evidencia crítica] → Mantener esquema, estados y evidencia requerida, y verificar casos de contradicción, falta de evidencia y deducción.
- [Los tokens varían entre ejecuciones] → Comparar promedios por etapa con entradas y parámetros iguales, no una sola llamada.

## Migration Plan

1. Crear nuevas versiones de los prompts de puntuación y organización.
2. Validar ambas versiones con casos representativos y comprobar el esquema JSON.
3. Comparar el promedio de tokens de salida por etapa con la versión anterior y ajustar las instrucciones si no se reduce el detalle redundante.
4. Activar las nuevas versiones para llamadas futuras; conservar los resultados históricos con la versión de prompt usada.
