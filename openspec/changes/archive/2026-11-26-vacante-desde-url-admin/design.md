# Design

## Context

El centro administrativo tendrá una carga manual que guarda una publicación global y dispara el fan-out de análisis por perfil. El conector actual de El Empleo ya interpreta fichas públicas y produce datos estructurados; la carga por URL reutiliza ese conocimiento, pero necesita una entrada directa de detalle además de la búsqueda por términos.

## Goals / Non-Goals

**Goals:**
- Aceptar solo la URL como entrada administrativa y extraer los datos públicos requeridos en segundo plano.
- Reutilizar la identidad normalizada, deduplicación global y evaluación por perfil de la carga manual.
- Permitir que otros proveedores se agreguen más adelante mediante soporte explícito.
- Limitar las consultas a páginas públicas de hosts autorizados.

**Non-Goals:**
- Aceptar HTML pegado, archivos de CV, páginas que requieren autenticación o proveedores no habilitados.
- Evadir bloqueos, CAPTCHA, límites de solicitudes o controles del proveedor.
- Habilitar en esta primera entrega otros proveedores además de El Empleo.

## Decisions

### Resolver el proveedor antes de hacer la petición

La URL se valida y se resuelve contra un registro de proveedores compatibles, que identifica host y rutas de fichas públicas. La primera integración habilitada es El Empleo. Las redirecciones deben permanecer dentro del conjunto de hosts permitidos; no se realizan peticiones a direcciones locales, privadas ni a URLs arbitrarias.

Se descarta hacer una petición genérica a cualquier URL pegada por el administrador: el allowlist evita accesos no intencionales a recursos internos y respeta la restricción de fuentes públicas.

### Reutilizar la extracción estructurada del conector

El proveedor convierte la ficha pública en los mismos campos normalizados que una búsqueda: título, compañía, ubicación, descripción, URL original, fuente, identificador y datos complementarios disponibles. Se conserva el contenido original devuelto por el proveedor sin inventar campos ausentes.

Se prefiere usar el conector existente frente a crear un segundo scraper solo para el admin, para conservar una sola interpretación de la ficha y facilitar nuevos proveedores.

### Encolar extracción y procesamiento de manera idempotente

La petición web crea una ejecución administrativa y encola la extracción. Si es válida, el resultado pasa por deduplicación global, vigencia y evaluación por perfil de `carga-manual-vacantes-admin`. La vista muestra el estado y un resumen seguro; fallos de fuente no dejan trabajos de IA incompletos.

Se descarta extraer la ficha o evaluar perfiles dentro de la petición web para evitar tiempos de espera y duplicados por reintentos del navegador.

## Risks / Trade-offs

- [La estructura pública del proveedor puede cambiar] → Reutilizar la validación de esquema del conector, registrar un error de extracción saneado y no guardar una ficha parcial como válida.
- [Un redirect podría salir del host permitido] → Validar cada destino de redirección antes de solicitarlo y rechazar cambios a hosts no autorizados.
- [La extracción y el fan-out podrían repetirse por reintento] → Identificar la ejecución por URL canónica y aplicar deduplicación e idempotencia de análisis vigentes.

## Migration Plan

1. Completar primero `carga-manual-vacantes-admin` y sus dependencias funcionales.
2. Añadir el envío de URL y extracción de El Empleo con el registro común de vacantes.
3. Integrar `vacante-desde-url-admin` antes de construir el commit candidato para stage.
4. Ante fallos, retirar la entrada por URL; la carga manual de campos y la búsqueda normal siguen disponibles.
