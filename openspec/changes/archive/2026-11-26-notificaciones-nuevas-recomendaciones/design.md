# Design

## Context

El dashboard selecciona análisis vigentes, ubicación elegible y seguimiento pendiente, incluidas recomendaciones sin fila explícita; búsqueda y análisis pueden repetirse. Existen Celery y zona `America/Bogota`, pero no una bitácora de primera entrada a recomendaciones ni infraestructura Web Push. Ver propuesta y delta para el contrato.

## Goals / Non-Goals

**Goals:**
- Desacoplar la marca de novedades del estado de seguimiento y limitar avisos por dispositivo.
- Evitar duplicados ante concurrencia y no exponer información privada en el aviso.

**Non-Goals:**
- Recuperar retroactivamente una cronología histórica que no existe, hacer seguimiento de lectura por vacante o garantizar recepción.
- Notificaciones por correo, sincronización offline o creación de cachés privadas.

## Decisions

- Registrar un evento durable único por perfil y vacante cuando esta entra por primera vez a Recomendaciones y se confirma el resultado elegible, después de aplicar descarte automático. Establecer una línea base de activación por perfil al habilitar la función; no reconstruir eventos antiguos. Una restauración, cambio de revisión o reanálisis no crea una segunda novedad para una vacante ya registrada. Verificar condiciones actuales de visibilidad al contar y al corte; desacoplar estado de revisado del seguimiento.
- Guardar una marca de revisión por perfil y avanzar solo por acción explícita; fijar un límite de eventos incluido en la solicitud o secuencia transaccional, para que novedades concurrentes posteriores no se pierdan. No marcar automáticamente al abrir una página paginada. El indicador enlaza a Recomendaciones y explica la acción de marcar todas como revisadas.
- El resumen usa eventos llegados desde el corte anterior o la activación del dispositivo, aún no revisados y elegibles al corte; no vuelve a avisar por novedades de días anteriores. Una tarea Celery programada para 09:00 `America/Bogota` reserva de forma atómica un intento por suscripción y fecha, antes de enviar. No reintentar automáticamente un envío de resultado incierto ni acumular resúmenes atrasados tras caídas; un fallo puede perder el aviso del día, pero el indicador sigue disponible. La reserva única y límites de caducidad impiden duplicados o avisos tardíos.
- Registrar suscripciones Web Push por dispositivo y cuenta solo después de una acción voluntaria y permiso del navegador; presentar opción de desactivación por dispositivo. Al salir o cambiar de cuenta revocar el vínculo anterior; si el cierre falla por pérdida de red, minimizar riesgos con contenido genérico y validar asociación y cuenta antes de cada envío. Eliminar suscripciones inválidas al recibir respuesta de expiración. Proteger endpoints y claves, no incluirlos en logs; claves VAPID se configuran mediante secretos propios del entorno sin versionarlas.
- Introducir un service worker limitado a recibir push y abrir una ruta del mismo origen, sin interceptar solicitudes ni almacenar respuestas. Esto complementa la propuesta de instalación, que excluye service worker para su propio alcance, y no añade offline. HTTPS y soporte del navegador son necesarios; ver [Push API](https://developer.mozilla.org/en-US/docs/Web/API/Push_API) y [permisos de notificación](https://developer.mozilla.org/en-US/docs/Web/API/Notifications_API/Using_the_Notifications_API).
- Al desactivar o cerrar sesión bloquear nuevos intentos; un aviso ya aceptado por un servicio externo puede llegar después y no puede revocarse con certeza. Usar TTL corto, texto genérico, bandera silenciosa cuando sea compatible y no interpretar aceptación como entrega. Antes de habilitar en un entorno comprobar configuración de red, servicio push y secretos; no mutar infraestructura en este cambio de planificación.

## Risks / Trade-offs

- [Una caída o respuesta ambigua puede perder un resumen] → Preferir no duplicar; indicador interno conserva las novedades.
- [Datos existentes carecen de fecha fiable de primera recomendación] → Iniciar desde la activación, sin etiquetar masivamente el histórico como nuevo.
- [La visibilidad cambia después de registrar el evento] → Evaluar de nuevo al mostrar y enviar; no generar otro evento por reanálisis.
- [Los dispositivos comparten navegador o permisos] → Desvincular al cerrar sesión y usar solo contenido genérico; limitar TTL y comprobar sesión/asociación en el servidor.
- [Los navegadores o sistemas ignoran silencio o no entregan] → Informar límites y validar en Chrome real de escritorio y Android.

## Migration Plan

Introducir modelos y línea base sin crear eventos históricos; dejar preferencias y suscripciones desactivadas. Configurar claves y conectividad solo en entornos autorizados, con datos sintéticos en staging. Revertir desactiva envíos y elimina el registro del service worker si es seguro; preservar o migrar otros usos si existen. No activar producción sin autorización explícita.
