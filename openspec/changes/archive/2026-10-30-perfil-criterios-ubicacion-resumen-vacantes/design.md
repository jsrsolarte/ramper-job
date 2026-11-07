# Design

## Context

El perfil actual guarda criterios en `Profile.search_criteria` como texto y las revisiones copian ese mismo campo. La generación de términos espera una lista JSON derivada del CV y los criterios. Los análisis guardan la descripción organizada en texto. La descarga autenticada ya existe en `/perfil/cv/`; el prefijo `/private-media/` configurado para almacenamiento no tiene una vista pública.

## Goals / Non-Goals

**Goals:**
- Guardar frases, ubicaciones y aceptación de trabajo remoto como preferencias estructuradas y versionadas.
- Incluir las frases del usuario en el conjunto de búsqueda y permitir que la IA añada términos respaldados por el CV.
- Evaluar ubicación y modalidad como parte del ajuste de la vacante.
- Guardar la descripción nueva como campos estructurados y mostrar una vista breve para datos históricos.
- Hacer que el enlace privado informado sirva solo el CV vigente del usuario autenticado propietario.

**Non-Goals:**
- Geocodificar ubicaciones, inferir disponibilidad para reubicación o modificar la vacante original.
- Cambiar el flujo de cuentas o publicar archivos de CV bajo una ruta pública.
- Volver a analizar automáticamente todos los perfiles históricos solo por migrar los campos.

## Decisions

### Modelar preferencias como listas en Profile y ProfileRevision

Cambiar los criterios de texto a listas JSON de frases y agregar ubicaciones como otra lista JSON más un booleano `remote_ok`. Las revisiones copian los tres valores al guardarse, de modo que los análisis anteriores mantengan el contexto con el que se crearon. Una migración de datos separa los criterios existentes por líneas y normaliza espacios; ubicaciones empiezan vacías y `remote_ok` en falso. Se descarta una tabla hija por frase porque no se necesitan atributos ni historial individual por elemento.

### Mantener la lista de usuario y sumar sugerencias de IA

El prompt de búsqueda recibe CV, frases y preferencias de ubicación. La validación conserva las frases del usuario y añade términos únicos sugeridos por IA, limitados a cinco sugerencias; no exige que el modelo vuelva a generar la entrada del usuario. Las ubicaciones se envían al análisis de compatibilidad, no se convierten automáticamente en términos de cargo para Elempleo.

### Persistir la salida organizada aparte del resumen anterior

Agregar un campo JSON `organized_content` con `summary`, `responsibilities`, `requirements` y `conditions`, dejando `organized_description` disponible para registros y compatibilidad históricos. La IA nueva devuelve esas claves; la tarjeta muestra el contenido estructurado cuando existe y un resumen truncado del texto legado en caso contrario. No se reconstruyen requisitos a partir de texto antiguo con heurísticas.

### Presentar listas editables con controles ligeros

El formulario renderiza controles para agregar/quitar frases y ubicaciones, respaldados por campos ocultos JSON validados en servidor. Si JavaScript no está disponible, el formulario conserva entradas de texto separadas por línea como alternativa accesible. Se evita añadir una dependencia de UI para este editor pequeño.

### Restringir la ruta private-media al archivo propio

Agregar una vista autenticada bajo el prefijo configurado que solo entrega el archivo cuando la ruta coincide exactamente con `cv_file.name` del perfil del usuario actual. La vista delega en la descarga existente; no resuelve rutas arbitrarias desde `MEDIA_ROOT` ni sirve CV de otra cuenta. El enlace de perfil seguirá usando la ruta canónica `/perfil/cv/`.

## Risks / Trade-offs

- [La conversión a listas puede perder formato de texto libre] → La migración divide por líneas, conserva cada frase normalizada y se puede editar desde el perfil.
- [El modelo puede devolver listas estructuradas inválidas] → Validar cada campo antes de guardar; conservar el análisis pendiente y error legible para reintento/manualidad.
- [No se vuelven a generar de inmediato los análisis históricos] → Mostrar el texto histórico truncado y usar el nuevo formato en análisis de nuevas revisiones/configuraciones.
- [Las ubicaciones de una vacante pueden ser ambiguas] → La IA solo las compara con el texto publicado y las preferencias; no realiza geocodificación.
- [La ruta privada puede ser solicitada por otra cuenta] → Requerir autenticación y coincidencia exacta con el archivo del perfil propietario.

## Migration Plan

1. Migrar criterios existentes a frases y agregar listas de ubicaciones y el indicador remoto en perfiles y revisiones.
2. Agregar `organized_content` sin eliminar el texto anterior.
3. Desplegar formulario, prompts, validadores, vista autenticada y tarjeta compatible con ambos formatos.
4. Las nuevas revisiones se analizarán con preferencias versionadas y la salida estructurada. Los usuarios pueden volver a guardar su perfil para iniciar una nueva revisión y recalcular resultados.

Para revertir, conservar los datos JSON nuevos y restaurar la lectura de criterios serializados como líneas; el campo de contenido estructurado no afecta a lectores antiguos mientras se mantenga `organized_description`.
