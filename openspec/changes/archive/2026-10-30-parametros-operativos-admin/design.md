# Design

## Context

Ver `proposal.md` y `specs/parametros-operativos/spec.md`. La frecuencia de fuentes hoy parte de `JOB_REFRESH_MINUTES` con un valor predeterminado de 180 minutos; el cambio de vigencia la reduce a 120 minutos. Un portal de comandos permite iniciar una actualización de inmediato, por lo que guardar el intervalo no debe disparar el comando manual.

## Goals / Non-Goals

**Goals:**
- Permitir ajustar valores aprobados sin editar archivos de infraestructura.
- Dar al valor guardado desde administración precedencia operativa sobre el valor inicial de ambiente.
- Hacer visible y trazable quién cambió el intervalo.

**Non-Goals:**
- Editar secretos, variables de entorno arbitrarias o parámetros no incluidos en un catálogo permitido.
- Forzar una búsqueda en el momento de guardar el intervalo.
- Cambiar el umbral personal de puntuación; este continúa bajo las preferencias y filtros del perfil.

## Decisions

### Usar catálogo de parámetros permitidos

La vista y el servicio de guardado aceptan identificadores de parámetros registrados por la aplicación, no nombres de variables ni mapas de configuración libres. La primera entrada del catálogo es el intervalo de actualización de fuentes en minutos. Los límites válidos se muestran junto al control y se validan en servidor.

**Alternativa considerada:** permitir editar cualquier clave de configuración desde la interfaz. Se descarta porque podría alterar credenciales, seguridad o procesos fuera de este alcance.

### Persistir el valor operativo en la aplicación

Cuando no exista un valor guardado, se inicializa desde `JOB_REFRESH_MINUTES`; si tampoco está definido, se usan 120 minutos. Cuando la persona administradora guarda un valor, ese valor persistido pasa a ser el valor operativo para los ciclos siguientes. La interfaz puede ofrecer restablecer al valor inicial, con confirmación y auditoría.

**Alternativa considerada:** requerir un redeploy para cada cambio. Se descarta porque no permitiría el ajuste operativo solicitado desde el panel.

### Aplicar el cambio al siguiente ciclo

Actualizar la programación efectiva de Beat al guardar y preservar cualquier ejecución ya iniciada. La acción no encola una búsqueda manual; el portal de comandos mantiene esa función independiente.

**Alternativa considerada:** iniciar una actualización como efecto secundario del guardado. Se descarta para que un cambio de configuración no produzca consumo imprevisto de fuente o IA.

### Registrar auditoría sin secretos

Guardar actor, hora, clave permitida, valor anterior y valor nuevo. Mostrar el historial solo a administración y no incluir valores de secretos porque no forman parte del catálogo.

**Alternativa considerada:** sobrescribir el valor sin historial. Se descarta porque impide entender cambios de frecuencia y diagnosticar su efecto.

## Risks / Trade-offs

- [Beat puede estar en ejecución cuando cambie la frecuencia] → Aplicar el nuevo intervalo al siguiente ciclo, sin interrumpir el actual.
- [Un límite demasiado bajo aumenta solicitudes a fuentes] → Exponer el rango permitido en UI, validar en servidor y permitir observar el efecto en el panel operativo.
- [Un valor persistido puede sobrevivir a cambios de ambiente] → Mostrar valor vigente e inicial, permitir restablecer de forma explícita y documentar la precedencia.
- [La administración introduce cambios por error] → Confirmar el guardado y conservar auditoría con valor anterior/nuevo.

## Migration Plan

1. Crear el registro de parámetros permitidos y el historial de cambios, sin guardar secretos.
2. Inicializar el intervalo con `JOB_REFRESH_MINUTES` o 120 minutos si no existe valor de ambiente.
3. Añadir autorización administrativa, validación de límites y pantalla para consultar/modificar/restablecer.
4. Conectar el valor persistido con el calendario de Beat y verificar que el cambio no inicia una ejecución manual.
5. En staging, cambiar el valor, comprobar el próximo ciclo, restablecer al valor inicial y revisar el historial de auditoría.

## Open Questions

Ninguna. Los límites numéricos del intervalo se fijarán en la implementación a partir de los límites operativos del servicio y se mostrarán al administrador antes de guardar.
