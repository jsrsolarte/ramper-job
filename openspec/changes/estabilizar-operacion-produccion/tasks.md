# Tasks

## 1. Corregir las sondas de salud productivas

- [x] 1.1 Limitar la excepción de HTTPS a `/healthz` y `/readyz`; verificar que las sondas HTTP reciben 200 o 503 directo y que las demás rutas conservan la redirección a HTTPS.
- [x] 1.2 Verificar con pruebas que `/readyz` informa indisponibilidad genérica si falla PostgreSQL o Redis y no expone mensajes internos; documentar el comportamiento de las sondas.

## 2. Reconciliar ingestas antiguas

- [x] 2.1 Reproducir en pruebas locales una unidad de ingesta con heartbeat o lease vencido y confirmar que la ejecución no se mantiene activa sin trabajo durable vigente.
- [x] 2.2 Ajustar la recuperación para reencolar unidades dentro del límite de intentos y cerrar unidades agotadas; verificar idempotencia, liberación de leases y preservación de ejecuciones con progreso reciente.
- [x] 2.3 Añadir pruebas de regresión para las rutas de reconciliación y documentar el umbral de 20 minutos y las categorías seguras de interrupción.

## 3. Alinear prompt y validador de requisitos críticos

- [x] 3.1 Actualizar las instrucciones versionadas para exigir texto de requisito de hasta 180 caracteres, evidencia de hasta 240 y estados admitidos; verificar la configuración nueva sin alterar análisis históricos.
- [x] 3.2 Añadir pruebas para límites válidos y excedidos; confirmar que las salidas inválidas no guardan resultados parciales ni texto de respuesta.

## 4. Diseñar y habilitar backups externos

- [ ] 4.1 Revisar opciones aprobadas en el repositorio de infraestructura y documentar destino, frecuencia, retención, RPO y RTO; verificar que el destino sea independiente del nodo y no requiera secretos versionados.
- [ ] 4.2 Implementar generaciones coherentes de PostgreSQL y CV en el destino elegido; verificar integridad, antigüedad, permisos y notificación agregada de fallos con datos sintéticos.
- [ ] 4.3 Documentar y ejecutar una restauración en un entorno aislado; verificar consistencia de base y archivos, y actualizar la guía de operación sin tocar datos de producción.

## 5. Validar y desplegar con autorización

- [ ] 5.1 Validar cambios de aplicación en staging con datos sintéticos; verificar sondas, categorías de análisis y reconciliación de ingestas sin errores nuevos.
- [ ] 5.2 Revisar SHA y digest probados, preparar reversión y actualizar `AGENTS.md` y la documentación de backups; desplegar a prod únicamente tras autorización explícita y verificar Flux, réplicas listas, eventos de sondas y estado agregado de trabajos.
