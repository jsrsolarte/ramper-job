# Tasks

## 1. Persistir y validar parámetros permitidos

- [x] 1.1 Crear almacenamiento para parámetros operativos permitidos e historial de cambios con actor, fecha y valores anterior/nuevo; verificar persistencia y que no se registren secretos.
- [x] 1.2 Inicializar el intervalo desde `JOB_REFRESH_MINUTES` y usar 120 minutos cuando no haya valor de ambiente; verificar ambos casos y la precedencia del valor guardado desde administración.
- [x] 1.3 Validar rango y formato en servidor y rechazar claves no permitidas; verificar valores válidos, inválidos y solicitudes manipuladas.

## 2. Administrar el intervalo desde el panel

- [x] 2.1 Añadir al centro administrativo una pantalla protegida para consultar, cambiar y restablecer el intervalo con unidad en minutos y límites visibles; verificar acceso exclusivo de administración y registro de auditoría.
- [x] 2.2 Conectar el valor guardado con la planificación de Celery Beat para los siguientes ciclos; verificar que al guardar no se lanza una búsqueda inmediata y que una ejecución activa termina normalmente.

## 3. Verificación integrada

- [x] 3.1 Probar el cambio de intervalo en el panel y su efecto en la planificación automática; verificar cambio, restauración del valor inicial y trazabilidad de ambos eventos.
