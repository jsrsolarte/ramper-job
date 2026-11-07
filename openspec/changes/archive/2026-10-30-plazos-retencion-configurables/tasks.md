# Tasks

## 1. Configurar los dos plazos desde el admin

- [x] 1.1 Añadir al admin los parámetros globales de descarte de recomendaciones y archivado por inactividad con defaults de 7 y 30 días; verificar que se muestran por separado, aplican a todos los perfiles y conservan auditoría.
- [x] 1.2 Validar valores enteros entre 1 y 365 días y rechazar entradas fuera del rango; verificar que un valor inválido no cambia la configuración vigente.

## 2. Aplicar valores vigentes a las tareas

- [x] 2.1 Actualizar la tarea de descarte para consultar el umbral vigente al empezar cada ejecución; verificar defaults, un plazo cambiado y que guardar el parámetro no dispara el job.
- [x] 2.2 Actualizar la tarea de archivado para consultar el umbral vigente al empezar cada ejecución; verificar defaults, un plazo cambiado, reinicio del reloj al cambiar estado e idempotencia.
- [x] 2.3 Verificar la integración de ambos ciclos diarios para que el descarte actualice el estado antes de que se evalúe el plazo de archivado y sin afectar seguimientos de otros perfiles.
