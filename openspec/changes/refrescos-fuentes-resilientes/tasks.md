# Tasks

## 1. Estado durable de las unidades

- [x] 1.1 Crear el modelo y migración aditiva para unidades de refresco, identidad estable, cursor, estado, intento, lease y heartbeat; verificar con `manage.py check` y `makemigrations --check --dry-run operations` que el modelo y la migración están alineados.
- [x] 1.2 Añadir creación idempotente, reclamación con lease y transiciones de unidad; verificar la restricción única de identidad, el reclamo transaccional y la importación de tareas Celery con `django.setup()`.

## 2. Procesamiento acotado y reanudable

- [x] 2.1 Despachar las combinaciones efectivas de cada fuente como unidades persistidas, respetando fuentes equivalentes y aislamiento por perfil; verificar que los flujos automático, manual y compatible usan el nuevo dispatcher Celery.
- [x] 2.2 Procesar búsquedas por término y bloques de hasta seis ubicaciones, y fichas en grupos de hasta cinco; verificar con la configuración cargada que los límites permanecen acotados bajo el máximo global de 15 minutos.
- [x] 2.3 Confirmar resultados y cursor en la misma transacción, con deduplicación de vacantes, asociaciones y análisis por perfil/revisión; verificar el control de lease/cursor y el reintento desde el estado persistido en la ruta de tarea.

## 3. Progreso agregado y comandos administrativos

- [x] 3.1 Actualizar métricas agregadas de fuente solo al confirmar unidades y mostrar conteos y duración en el dashboard sin términos ni ubicaciones; verificar la agregación por fuente y el renderizado mediante `manage.py check`.
- [x] 3.2 Agregar el resultado del comando desde las unidades y evitar comandos equivalentes duplicados mientras existan leases; verificar que los reportes agregados respetan consultas, vacantes y fallas confirmadas.

## 4. Reconciliación de interrupciones

- [x] 4.1 Reconciliar heartbeats, unidades y leases vencidos, actualizando ejecuciones y comandos huérfanos con categorías seguras y conservando su historial; verificar que la tarea importa y mantiene trabajo durable vigente.
- [x] 4.2 Programar la reconciliación cada cinco minutos, separada de la limpieza histórica diaria; verificar en la configuración cargada de Celery Beat que el intervalo es 300 segundos.

## 5. Integración en staging

- [ ] 5.1 Desplegar la change únicamente en staging y validar un perfil de alta cardinalidad de extremo a extremo, cobertura de combinaciones, progreso visible, recuperación tras interrupción, deduplicación y cierre de comando; registrar el SHA/digest desplegado y el resultado antes de completar la validación pendiente de `agregar-computrabajo`.

## Workflow follow-up

- Archivar esta change después de revisar y aceptar la validación de staging.
- Completar luego la validación de staging pendiente de `agregar-computrabajo`.
- Implementar `pausa-busqueda-perfil-individual` después de esta change, ya que modifica el mismo flujo de refresco y leases.
