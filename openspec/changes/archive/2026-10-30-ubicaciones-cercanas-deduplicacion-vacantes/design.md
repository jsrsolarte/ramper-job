# Design

## Context

`Profile` y `ProfileRevision` ya conservan ubicaciones como listas; el análisis recibe literalmente esos valores. `ElempleoConnector` extrae un identificador de la URL, pero el guardado solo busca por `(source, original_url)`. `VacancyAnalysis` apunta a cada vacante y no tiene una unicidad declarada por análisis.

## Goals / Non-Goals

**Goals:**
- Representar ambas preferencias con filas accesibles y controles explícitos.
- Resolver equivalencias geográficas de forma determinista y reutilizable por el análisis.
- Aplicar la identidad de vacante por bolsa en el conector, guardado y base de datos.
- Reasignar análisis únicos en una migración de datos y elegir un resultado representativo cuando una vacante repetida generó análisis duplicados.

**Non-Goals:**
- Geocodificar o consultar servicios externos de mapas.
- Inferir tiempos de desplazamiento o distancias.
- Unificar vacantes entre bolsas distintas.
- Promover automáticamente una URL alternativa a enlace principal si ya existe una URL funcional.

## Decisions

### Usar el filtro de ciudad de Elempleo en la consulta

La interfaz pública de Elempleo confirma consultas de la forma `/co/ofertas-empleo/{ciudad}/trabajo-{frase}`; el filtro manual permite hasta tres ciudades e incluye «Bogotá alrededores», Soacha e Itagüí. El conector consultará una ruta por cada combinación de frase y ciudad, expandiendo grupos locales como Valle de Aburrá y entorno de Bogotá. Si el perfil admite vacantes remotas también consultará la frase sin ciudad. Las solicitudes se limitan por el retardo ya usado y sus resultados se consolidan antes de guardar. Para ubicaciones no reconocidas, se conserva la comparación literal en el análisis. El análisis recibirá las equivalencias expandidas para que las vacantes cercanas no pierdan compatibilidad.

Se descarta usar la ciudad solo como filtro posterior de IA: no recuperaría publicaciones de ciudades que Elempleo excluye en el resultado de la consulta inicial.

### Aplicar una ventana de recencia sin etiquetar mal la aproximación

Si la fuente entrega una fecha/hora exacta de publicación, el sistema la compara con las últimas 24 horas. Elempleo ofrece la categoría «Hoy y ayer», cuya ventana sigue el calendario y puede ser mayor a 24 horas; se aplica con `?PublishDate=hoy` en cada consulta y se guarda la etiqueta que entrega la fuente. No se afirmará que todas esas publicaciones son de las últimas 24 horas.

### Renderizar las preferencias como listas verticales

Cambiar la colección de chips horizontales a `ul/li`, manteniendo el campo de formulario como valor serializado para compatibilidad y procesamiento actual. Cada fila tendrá texto y botón de quitar; el campo para agregar permanece debajo. Las filas tendrán estilos responsivos y controles accesibles por teclado.

### Crear una clave determinista de identidad dentro de cada fuente

Persistir `dedupe_key` y añadir unicidad `(source, dedupe_key)`. La clave usará un identificador numérico externo cuando Elempleo lo ofrezca; en su ausencia usará una huella normalizada de cargo, empresa y ubicación. La URL seguirá siendo el enlace primario y conservará su restricción actual. Una URL alternativa se registrará en `raw_data.alternate_urls` para diagnóstico y futuras actualizaciones. La actualización de campos continuará priorizando datos no vacíos.

Una tabla de alias URL es una alternativa más extensible, pero se difiere mientras la única fuente sea Elempleo y no se requiera buscar vacantes por alias.

### Consolidar datos históricos antes de imponer unicidad

La migración agrupará filas por fuente y clave calculada, elegirá como vacante conservada la más antigua y combinará URLs alternativas. Reasignará cada análisis al registro conservado. Si dos análisis quedarían con la misma combinación perfil/revisión/configuración, conservará el análisis completado más reciente; si ninguno terminó, conservará el más reciente. La clave única de vacante se crea después de consolidar.

La huella de cargo/empresa/ubicación puede agrupar publicaciones homónimas distintas cuando la fuente no ofrece ID; esta es la alternativa de respaldo menos frágil disponible sin URL canónica o API.

## Risks / Trade-offs

- [Las vacantes sin ID pueden tener títulos, empresas y ubicaciones idénticos] → Solo aplicar huella alternativa cuando cargo y ubicación estén presentes; incluir empresa cuando exista y usar normalización conservadora.
- [La lista de municipios puede quedarse corta o incluir un municipio que el usuario no acepta] → Mantener los nombres visibles en su selección original, usar grupos pequeños definidos en código y dejar las ubicaciones editables para reducir el área.
- [Consolidar análisis repetidos descarta filas redundantes] → Preferir resultados completados, conservar el más reciente y reasignar cualquier análisis con combinación única.
- [La deduplicación en código puede coincidir con una inserción concurrente] → La restricción compuesta en la base de datos garantiza una sola clave; recuperar el registro existente si la inserción pierde la carrera.

## Migration Plan

1. Desplegar catálogo de áreas, consultas de Elempleo por ciudad, preferencia de recencia, expansión enviada al análisis y formulario de listas.
2. Añadir `dedupe_key` inicialmente nullable; poblarla para vacantes existentes y consolidar duplicados junto con sus análisis.
3. Imponer unicidad `(source, dedupe_key)` tras consolidar, manteniendo la unicidad URL vigente.
4. Calcular clave para cada nuevo listing antes de persistir y reutilizar registro al cambiar URL.

La reversión del código puede mantener las claves en la base de datos. Para revertir la deduplicación se elimina la restricción y el campo; la unión de análisis ya consolidada no se deshace automáticamente.
