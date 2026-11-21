# Tasks

## 1. Retirar v2 del flujo de análisis

- [x] 1.1 Eliminar selector, prompt, esquema y validación de puntuación v2; verificar que todas las solicitudes nuevas declaran rúbrica 3 y rechazan otras versiones.
- [x] 1.2 Actualizar la inicialización de configuraciones antiguas a una nueva versión activa con parámetros v3; verificar conversión con pruebas y conservar registros históricos.
- [x] 1.3 Mantener lectura del desglose histórico v2 en dashboard sin permitirlo en solicitudes nuevas; verificar presentación de resultados históricos y v3.

## 2. Validar y desplegar en staging

- [x] 2.1 Ajustar y ejecutar pruebas de matching, configuración y dashboard; verificar que la suite afectada pasa y no quedan ramas de scoring v2 activas.
- [x] 2.2 Publicar el cambio solo en `staging`; verificar CI, SHA desplegado por Flux, salud web/workers y pausa global preservada.
- [x] 2.3 Ejecutar un caso sintético aislado con scoring v3 y organización completa; verificar estados finales y telemetría de ambas etapas sin activar la cola global.
