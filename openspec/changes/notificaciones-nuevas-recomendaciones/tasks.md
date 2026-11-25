# Tasks

## 1. Novedades e indicador

- [x] 1.1 Registrar primera entrada elegible por perfil y vacante y establecer línea base sin reconstrucción histórica; probar perfiles, descartes, revisión, reanálisis y concurrencia.
- [x] 1.2 Mostrar indicador accesible y acción explícita de marcar revisadas con corte seguro; probar filtros, paginación, novedades concurrentes y aislamiento entre cuentas.

## 2. Suscripciones y privacidad

- [x] 2.1 Incorporar activación por dispositivo y permiso voluntario, desactivación y desvinculación al salir; probar denegación, soporte ausente, cambio de cuenta y cuentas inactivas.
- [x] 2.2 Añadir service worker solo para push y apertura autenticada sin caché; probar contenido genérico, rutas de mismo origen, ausencia de almacenamiento privado y coexistencia con instalación.
- [x] 2.3 Configurar manejo seguro de claves y suscripciones sin secretos en logs; probar eliminación de suscripciones caducadas y documentar configuración por entorno sin modificar infraestructura.

## 3. Resumen y verificación

- [x] 3.1 Programar resumen a las 9:00 de Bogotá con reserva única por dispositivo y fecha; probar duplicación, caídas, ausencia de novedades, corte, baja y avisos no repetidos.
- [x] 3.2 Verificar fallos y respuestas ambiguas sin reenvío automático, TTL y contenido silencioso cuando esté soportado; comprobar que el indicador persiste y no se afirma la entrega.
- [ ] 3.3 Probar con datos sintéticos en Chrome de escritorio y Android la activación, notificación, apertura, desactivación y cierre de sesión; registrar versiones y limitaciones sin enviar avisos a usuarios reales.
