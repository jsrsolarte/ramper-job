# Design

## Context

Las vacantes existentes se guardan como publicaciones globales y se deduplican principalmente por fuente y URL canónica. La evaluación y el seguimiento ya se modelan por relación perfil-vacante. El centro administrativo y la canalización por etapas están definidos en cambios funcionales relacionados.

## Goals / Non-Goals

**Goals:**
- Hacer que la publicación manual use el mismo modelo global y la misma cola de evaluación por perfil.
- Validar acceso, URL pública admitida, duplicados y estado de procesamiento desde la interfaz administrativa.
- Evitar que el alta manual asigne un puntaje compartido o altere seguimientos de otros perfiles.

**Non-Goals:**
- Subir archivos adjuntos o importar lotes de vacantes.
- Ejecutar llamadas a la IA dentro de la solicitud web.
- Añadir una búsqueda independiente o una nueva rúbrica para publicaciones manuales.

## Decisions

### Registrar una publicación desde su URL pública

El alta requiere únicamente la URL pública de una ficha admitida. El proveedor extrae título, fuente y demás datos disponibles en segundo plano. La URL se valida antes de encolarla y se canonicaliza antes de guardar. Si ya existe una publicación con esa referencia, se reutiliza y actualiza el mismo registro global.

Se prefiere tomar los datos de la fuente original para que las publicaciones queden consistentes y para evitar pedir que la administración copie campos. No se permite enviar URLs de proveedores que no estén habilitados.

### Usar la publicación común y la asociación de análisis por perfil

Después de guardar, se evalúa cada perfil activo con CV y preferencias vigentes, aplicando elegibilidad geográfica y de modalidad antes de crear el análisis. Cada pareja perfil-vacante sigue la rúbrica completa de ese perfil y las etapas de IA existentes. La organización de la publicación se reutiliza según las reglas de análisis por etapas.

Se descarta duplicar la publicación por perfil o ejecutar un análisis único para todas las personas: ambos enfoques mezclarían datos globales y resultados privados.

### Ejecutar y reportar el alta de forma asíncrona

La petición administrativa valida y encola la URL; la extracción, el guardado, la elegibilidad, creación de relaciones y encolado de análisis se completan en segundo plano. El resultado muestra el estado de procesamiento, sin esperar llamadas a fuentes o al modelo.

Se descarta realizar fan-out de IA de forma síncrona para evitar bloquear la interfaz mientras se procesan varios perfiles.

## Risks / Trade-offs

- [Una URL de seguimiento puede variar aunque apunte al mismo anuncio] → Canonicalizar esquema, host, ruta y parámetros no identitarios; permitir que el diseño de implementación reutilice la política existente de URLs.
- [El mismo anuncio puede enviarse con otra URL o fuente] → La deduplicación por URL canónica elimina el duplicado exacto; no se afirma resolver equivalencias semánticas con otras URLs.
- [Una vacante puede actualizarse mientras se fan-out a perfiles] → Volver a comprobar que esté activa y que cada perfil siga vigente antes de encolar su análisis.

## Migration Plan

1. Implementar después del centro administrativo, la búsqueda/relación compartida, la deduplicación vigente, el análisis por etapas y el seguimiento personal.
2. No migrar publicaciones existentes; un registro manual con URL coincidente reutiliza la publicación actual.
3. Completar la funcionalidad e integrarla antes de la compuerta de despliegue a stage.
