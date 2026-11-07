# Design

## Context

Ver `proposal.md` y las specs. La búsqueda periódica ya se ejecuta con Celery Beat y Celery workers consumen las tareas de forma continua; el intervalo de fuentes pasará a 120 minutos en `vigencia-y-actualizacion-vacantes`. La ingestión normal actualiza publicaciones conocidas con deduplicación por fuente y URL canónica. El cambio `panel-observabilidad-operativa` introduce historial de ejecuciones que puede mostrar resultados de tareas.

## Goals / Non-Goals

**Goals:**
- Permitir activar el mismo flujo de actualización bajo demanda y consultar su resultado posteriormente.
- Reutilizar deduplicación, análisis elegible e historial operativo existentes.
- Evitar ejecuciones solapadas y repetición de análisis completados cuando no haya cambios materiales.
- Mantener el portal acotado a comandos definidos y accesibles solo por administración.

**Non-Goals:**
- Ejecutar comandos de shell, SQL o tareas arbitrarias desde la interfaz.
- Cambiar la cadencia automática ni convertir la solicitud manual en una modificación persistente de la programación.
- Reanalizar todas las vacantes históricas con un clic.

## Decisions

### Encolar el mismo flujo de actualización

El comando solicita al backend la tarea existente de actualización de fuentes con la configuración vigente. La petición web responde con un identificador de ejecución y el estado inicial; la búsqueda, persistencia y encolado de análisis ocurren en los workers. El siguiente horario de Celery Beat permanece intacto.

**Alternativa considerada:** ejecutar la búsqueda y el análisis dentro de la petición web. Se descarta porque el tiempo de respuesta depende de fuentes externas y podría agotarse antes de completar el ciclo.

### Reutilizar deduplicación y criterios de elegibilidad

El comando no tiene un camino separado de creación de vacantes o de análisis. Reusa el flujo normal por fuente y URL canónica, ubicación/perfil elegible y estado de análisis. Vacantes ya analizadas no vuelven a encolarse solo por aparecer otra vez; los cambios materiales se rigen por las reglas existentes de reanálisis.

**Alternativa considerada:** crear una copia de vacante o forzar todas las etapas de IA al solicitar una actualización. Se descarta porque duplicaría historial y podría consumir tokens de nuevo sin cambio de contenido.

### Evitar ejecuciones equivalentes simultáneas

Antes de encolar, reclamar una exclusión mutua de actualización global o por fuente durante la ejecución, con expiración ante fallo del proceso. Si ya hay una tarea equivalente activa, devolver su referencia al portal. La exclusión debe cubrir tanto las solicitudes manuales como las programadas para no duplicar consultas.

**Alternativa considerada:** bloquear solo doble clic del mismo usuario. Se descarta porque varias sesiones o Beat podrían iniciar el mismo ciclo a la vez.

### Mantener un catálogo explícito y una auditoría segura

El servidor mapea cada identificador visible a una operación fija y valida permisos, método, argumentos y confirmación. No acepta nombres de tareas Celery o texto ejecutable del cliente. Para el primer comando, el estado visible reutiliza el historial operativo de ingesta; se registra además la solicitud de administración o se enlaza al evento de ejecución existente para identificar actor y origen. Los errores mostrados se saneaan y limitan.

**Alternativa considerada:** dar un formulario para introducir nombres de comandos y argumentos libres. Se descarta por riesgo de ejecución no autorizada y falta de trazabilidad clara.

## Risks / Trade-offs

- [La ejecución manual coincide con Beat] → Usar exclusión mutua común para ambas rutas y mostrar el trabajo ya activo.
- [El comando se acepta pero un worker no está disponible] → Mostrar la ejecución como en cola con su antigüedad y permitir revisar el resultado o el estado de cola; no reportar éxito hasta que termine.
- [Una fuente tarda o falla parcialmente] → Mantener el comportamiento parcial de la ingesta, reflejar resultado por fuente y no marcar toda la ejecución como exitosa si hubo fallas.
- [La vista de comandos crece con futuras herramientas] → Añadir comandos por catálogo explícito con permiso, argumentos, resultado y política de concurrencia definidos individualmente.

## Migration Plan

1. Confirmar que la actualización automática de 120 minutos, el centro administrativo y el historial operativo estén disponibles en el commit integrado.
2. Añadir el registro de solicitud del comando y asociarlo a la ejecución de ingesta existente.
3. Exponer el comando manual por el centro administrativo y encolarlo en workers, con exclusión respecto de Beat.
4. Verificar que la solicitud no bloquea la página, que el estado se actualiza y que fallas se muestran saneadas.
5. Recorrer en staging una búsqueda manual con vacantes nuevas y previamente analizadas; comprobar actualización única, análisis solo cuando corresponde y que Beat mantenga el siguiente ciclo programado.

## Open Questions

Ninguna para la primera operación. Comandos futuros deberán especificar explícitamente sus argumentos, autorización, concurrencia y resultado observable antes de agregarse al portal.
