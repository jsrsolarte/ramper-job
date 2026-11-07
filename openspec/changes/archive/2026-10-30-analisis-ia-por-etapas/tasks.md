# Tasks

## 1. Persistir puntajes, organizaciones e intentos

- [x] 1.1 Separar en `VacancyAnalysis` el estado del enriquecimiento del estado del puntaje y crear el almacenamiento reutilizable por vacante/configuración sin backfill de análisis anteriores; verificar unicidad y el flujo sobre vacantes nuevas después de la limpieza local.
- [x] 1.2 Crear registros por intento de IA con etapa, duración, resultado y tokens opcionales; verificar captura de uso presente/ausente y que no se guardan prompts, CV ni respuestas completas.
- [x] 1.3 Añadir pruebas de modelo y migración para organizaciones diferentes cuando cambie la configuración y para análisis nuevos sin contenido organizado inicial.

## 2. Separar cliente y validación de las llamadas

- [x] 2.1 Separar las respuestas válidas de puntuación y organización, manteniendo las reglas actuales de la rúbrica; verificar rechazo de respuestas incompletas o mal formadas en cada etapa.
- [x] 2.2 Hacer que la llamada de organización reciba únicamente datos de la publicación y configuración; verificar con pruebas que nunca se envían CV, preferencias ni datos del perfil.
- [x] 2.3 Capturar duración, tokens del proveedor y resultado de cada llamada, incluidos errores y reintentos; verificar valores nulos cuando no exista uso informado.

## 3. Implementar la orquestación por umbral

- [x] 3.1 Actualizar las tareas para persistir el puntaje antes de organizar y encolar organización solo al alcanzar `Profile.min_score`; verificar que el puntaje queda disponible si la segunda etapa está pendiente o falla.
- [x] 3.2 Hacer idempotente y concurrentemente segura la organización compartida por vacante/configuración, y permitir su reintento sin repetir ni invalidar puntajes; verificar una sola llamada ante perfiles concurrentes.
- [x] 3.3 Al reducir el mínimo persistido del perfil, encolar resultados puntuados que pasan a ser elegibles y no tienen organización; verificar que subir el mínimo y mover el filtro temporal del dashboard no encolan tareas.
- [x] 3.4 Invalidar o generar una clave nueva de organización cuando cambie el contenido relevante de una vacante; verificar que no se entrega contenido organizado obsoleto.

## 4. Mostrar estados y verificar el flujo completo

- [x] 4.1 Ajustar el dashboard para mostrar puntajes elegibles mientras la organización está pendiente, completa o agotó reintentos; verificar que cada estado se comunica y que el filtro vigente sigue aplicándose.
- [x] 4.2 Verificar el flujo integrado de validación de ubicación, puntuación, decisión por mínimo, organización compartida y reducción posterior del mínimo, sin bloquear la disponibilidad del puntaje.
- [x] 4.3 Documentar las etapas y el significado de la telemetría para su agregación en observabilidad operativa; verificar que las métricas de ambas etapas se pueden distinguir sin leer datos personales.
- [x] 4.4 Limitar el reintento automático de organizaciones fallidas a la configuración vigente; verificar que no se repiten llamadas con un prompt reemplazado.
