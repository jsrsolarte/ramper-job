# Design

## Context

Ver la propuesta y la delta para el alcance. `operations.views.users` lista aspirantes; las estadísticas globales son agregadas y excluyen identidades. El dashboard calcula pendientes implícitos a partir de análisis vigentes y excluye seguimientos archivados. Los análisis y descubrimientos tienen fechas; el seguimiento conserva el estado actual y su última fecha, no una bitácora completa.

## Goals / Non-Goals

**Goals:**
- Reutilizar la semántica del dashboard y garantizar aislamiento por perfil.
- Presentar datos históricos que pueden sustentarse en registros existentes.

**Non-Goals:**
- Crear una bitácora de eventos o atribuir consultas compartidas a una persona sin evidencia.
- Cambiar el dashboard, las métricas globales ni los datos existentes.

## Decisions

- Añadir una vista de solo lectura protegida por el mismo control administrativo que gestión de usuarios. Validar la cuenta activa en cada solicitud, no solo al mostrar el enlace. La alternativa de incorporar identificadores en estadísticas globales rompería su contrato de anonimato.
- Extraer o reutilizar la selección de análisis vigentes y los conteos del dashboard sin el filtro de puntuación, para preservar pendientes implícitos y exclusión de archivados. No contar solo filas de seguimiento: omitiría pendientes sin fila. Contar archivados separadamente sobre seguimientos del perfil.
- Para procesamiento técnico seleccionar un análisis no reemplazado por vacante y perfil mediante el criterio vigente de la aplicación; si hay varios, resolver de forma determinista con el mismo criterio de selección existente. Mostrar el estado técnico independientemente del seguimiento. El total histórico cuenta registros completados, no vacantes únicas; descubrimientos cuenta relaciones únicas perfil-vacante. Usar fechas registradas, sin reconstruir transiciones.
- Informar explícitamente el alcance temporal: totales de todos los registros conservados, sin afirmar cobertura anterior a los datos disponibles. No agregar series ni filtros temporales cuya precisión dependa de eventos inexistentes.
- El diseño no requiere migración ni dependencia externa. Las consultas se filtran por perfil y se agregan en base de datos cuando sea compatible con la semántica vigente; evitar consultas por cada vacante.

## Risks / Trade-offs

- [Los datos históricos no reflejan transiciones anteriores] → Mostrar la limitación y no extrapolar.
- [Diferencias entre conteos técnicos y visibles] → Etiquetar unidad, inclusión de archivados y condiciones de vigencia en cada sección; verificar casos con revisiones y perfiles distintos.
- [Una cuenta se desactiva tras abrir el listado] → Revalidar estado al solicitar la ficha.

## Migration Plan

Publicar código y pruebas mediante el flujo habitual; no se modifican datos. Revertir el código elimina la ficha sin alterar registros. Cualquier despliegue y promoción requiere las autorizaciones correspondientes.
