# Design

## Context

El flujo de staging identifica las imágenes por SHA/digest y GitHub Actions las construye desde una rama seleccionada. La producción todavía no está habilitada; el primer lanzamiento aprobado representa el conjunto funcional inicial.

## Goals / Non-Goals

**Goals:**
- Definir un identificador legible para cada liberación de producción.
- Relacionar la versión con el mismo SHA/digest validado en staging.
- Mantener inmutables las etiquetas ya liberadas.

**Non-Goals:**
- Asignar números de versión a cada prueba de staging.
- Autorizar o ejecutar por sí sola la promoción a producción.
- Crear un overlay de producción como parte de este cambio.

## Decisions

### Usar etiquetas Git como fuente de verdad de la versión

Cada liberación usa una etiqueta Git anotada con prefijo `v` (por ejemplo, `v1.0.0`); la versión de producto comunicada es `1.0.0`. La primera etiqueta de producción se crea solo cuando el commit probado está aprobado para su primera promoción. CI valida formato y unicidad y publica metadatos de versión junto al artefacto.

**Alternativa considerada:** mantener un número manual en un archivo separado y en GitHub Releases. Se descarta como fuente de verdad porque puede divergir del commit y del digest publicados.

### Mantener reglas de incremento SemVer

Aplicar PATCH a correcciones compatibles, MINOR a capacidades compatibles y MAJOR a cambios incompatibles. Las decisiones se anotan en el resumen de la liberación para hacer visible el motivo del incremento.

**Alternativa considerada:** incrementar el número menor en cada entrega. Se descarta porque no comunica si una versión rompe compatibilidad.

### Conservar artefacto promovido desde staging

La liberación de producción se relaciona con el SHA/digest que pasó staging; no se reconstruye silenciosamente una imagen distinta al crear la etiqueta de versión. Las pruebas sucesivas de staging continúan etiquetándose por commit y no reciben números `1.x`.

**Alternativa considerada:** reconstruir la imagen al crear cada lanzamiento. Se descarta porque podría producir un digest distinto del que se verificó.

## Risks / Trade-offs

- [Se puede escoger un incremento mayor o menor incorrecto] → Exigir que el resumen de la liberación indique si es corrección, capacidad compatible o cambio incompatible.
- [Una etiqueta puede apuntar a un commit distinto del probado] → Validar SHA/digest en CI y rechazar etiquetas ya existentes o móviles.
- [El primer `1.0.0` puede confundirse con staging] → Reservar las etiquetas SemVer para liberaciones de producción; mantener staging identificado por SHA.

## Migration Plan

1. Añadir validación de formato y unicidad de etiquetas de lanzamiento y metadatos de imagen.
2. En el primer lanzamiento de producción aprobado, crear `v1.0.0` sobre el SHA/digest probado en staging.
3. En las liberaciones posteriores, incrementar MAJOR, MINOR o PATCH según compatibilidad y conservar el artefacto exacto probado.
