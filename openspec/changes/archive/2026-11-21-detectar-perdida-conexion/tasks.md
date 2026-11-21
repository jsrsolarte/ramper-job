# Tasks

## 1. Estado de conexión

- [x] 1.1 Determinar una comprobación pública, ligera y sin caché que no active tareas externas; probar respuesta, tiempo límite y acceso sin sesión.
- [x] 1.2 Implementar aviso accesible y recuperación con comprobaciones limitadas; probar sin red, servicio inaccesible, recuperación parcial y recuperación completa.

## 2. Operaciones y validación

- [x] 2.1 Revisar operaciones JavaScript de escritura y presentar resultado incierto ante fallos de comunicación, sin reintentos automáticos; probar que no se emite confirmación falsa ni se duplica el envío.
- [x] 2.2 Verificar con formularios sintéticos que el aviso no borra campos de una pantalla abierta; documentar y probar límites en envíos que navegan fuera de la página.
- [x] 2.3 Comprobar navegación normal, accesibilidad, comportamiento con JavaScript deshabilitado y ausencia de almacenamiento privado; ejecutar pruebas pertinentes sin iniciar servicios externos.
