# Design

## Context

La plantilla común `templates/base.html` cubre inicio de sesión y pantallas autenticadas. Django y WhiteNoise sirven los recursos estáticos. El acceso depende de sesión y el CV tiene una ruta privada; no existe un manifiesto ni una estrategia de funcionamiento sin conexión. Ver la propuesta y la delta para el alcance.

## Goals / Non-Goals

**Goals:**
- Una identidad estable y reconocible en Chrome de computador y Android.
- Mantener las mismas reglas de acceso al abrir la aplicación instalada.

**Non-Goals:**
- Aplicación nativa, tienda, notificaciones o trabajo sin conexión.
- Añadir una solicitud de instalación propia intrusiva o recopilar eventos de instalación.

## Decisions

- Enlazar desde la plantilla común un manifiesto público del mismo origen con `id` y `start_url` estables, alcance de la aplicación, nombre, `display: standalone`, colores y iconos de 192 y 512 píxeles apropiados para la marca. Evitar URLs con identificadores de usuario; mantener identidades distintas por origen para staging y producción. Como alternativa, un simple acceso directo no ofrece identidad y presentación instalable coherentes.
- Usar la interfaz de instalación de Chrome; no depender de un evento de solicitud automático ni exigir un botón propio. Los criterios y la interfaz dependen de versión y plataforma, por lo que deben comprobarse en navegadores reales. Véase la [guía de instalación de Chrome](https://developer.chrome.com/docs/modern-web-guidance/guides/pwa/install-web-app) y [requisitos del manifiesto](https://developer.chrome.com/docs/lighthouse/pwa/installable-manifest/).
- No introducir un service worker ni caché de respuestas privadas para esta funcionalidad; verificar los criterios actuales de Chrome durante la implementación. La alternativa de caché sin conexión aumenta la complejidad y el riesgo de mostrar datos de otra sesión sin que el usuario haya solicitado esa función.
- La URL inicial pasa por las redirecciones y permisos normales de Django. Servir manifiesto e iconos sin autenticación, con MIME y rutas correctas tras `collectstatic`, incluso en la pantalla de ingreso y bajo HTTPS.

## Risks / Trade-offs

- [Chrome cambia sus criterios o menús entre plataformas] → Verificar instalaciones reales y registrar versión, plataforma y resultado; no interpretar solo un manifiesto válido como prueba de instalación.
- [Cambios en origen o identidad generan otra instalación] → Mantener `id` estable por origen y probar actualización sin duplicar la aplicación.
- [Las redirecciones a login o middleware impiden obtener recursos] → Probar manifiesto e iconos sin sesión y la apertura con y sin sesión.
- [Sin conexión no se podrá consultar el contenido] → Mantener la experiencia de error del navegador y no prometer sincronización ni guardar datos privados.

## Migration Plan

Agregar recursos y referencia sin migración de datos; verificar primero en entorno local seguro y staging con datos sintéticos. Revertir el enlace y recursos desactiva la oferta de instalación nueva; una instalación anterior puede conservar su acceso directo hasta que la persona la elimine. Producción requiere autorización explícita.
