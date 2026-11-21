# Design

## Context

La versión activa del sistema ya es la rúbrica 3. Permanecen ramas v2 en el cliente, el validador y la construcción del prompt. Los registros históricos referencian configuraciones protegidas; no se alterarán esos registros.

## Goals / Non-Goals

**Goals:** Garantizar que todo análisis nuevo usa el contrato JSON y los límites de v3. Mantener visible el desglose histórico. Actualizar configuraciones activas antiguas al inicializar la configuración.

**Non-Goals:** Borrar análisis, configuraciones o migraciones históricas; volver a puntuar registros; cambiar la escala de cinco estrellas; promover a producción.

## Decisions

- El cliente de scoring y el validador aceptarán solo la rúbrica vigente. Se retiran la definición de criterios, el prompt y los esquemas de solicitud de v2.
- La inicialización de configuración convierte una configuración antigua en una nueva versión activa v3 con parámetros predeterminados vigentes. Las filas anteriores siguen intactas para sus análisis asociados.
- El dashboard elige el desglose de lectura según la versión almacenada: la definición histórica de v2 permanece únicamente para presentar registros previos, nunca para crear peticiones.
- No se necesita migración de base de datos: la versión está guardada por análisis y las relaciones históricas se conservan.
- Validación: pruebas focalizadas del contrato v3 y lectura histórica; CI; despliegue por staging; ejecutar un análisis sintético con puntuación y organización. La pausa global de procesamiento permanecerá activa y la ejecución del caso de prueba será aislada.

## Risks / Trade-offs

- [Una configuración activa antigua puede conservar parámetros incompatibles] → regenerar la rúbrica y deducción a partir de los valores predeterminados v3 durante la actualización.
- [Un cliente antiguo podría esperar respuestas v2] → el API de scoring es interno; las nuevas solicitudes se etiquetan exclusivamente con la versión 3.
- [La cola de staging está pausada] → ejecutar solo las etapas del registro sintético en forma aislada, sin reanudar workers globales.

## Migration Plan

1. Publicar el cambio únicamente en la rama `staging` y esperar CI y Flux.
2. Verificar salud, versión activa v3 y que la pausa se mantenga.
3. Completar un análisis sintético de scoring y organización; confirmar estado y telemetría.
4. Revertir el pin de staging al SHA anterior si falla el despliegue. No cambiar `main` ni producción.

## Open Questions

Ninguna.
