# Design

## Context

Ver `proposal.md` para la motivación y `specs/programacion-busquedas/spec.md` para el contrato visible. El ciclo global se configura en `DatabaseRefreshInterval`, usa el intervalo guardado en parámetros operativos y termina en `jobs.tasks.refresh_sources`. También existen actualizaciones manuales y tareas de actualización de perfil, por lo que el historial actual de consultas individuales no identifica por sí solo cuándo se lanzó el ciclo periódico. La pausa global se guarda como parámetro operativo.

## Goals / Non-Goals

**Goals:**

- Presentar la misma estimación al dashboard de aspirantes y al centro administrativo.
- Calcularla desde el intervalo vigente y un registro fiable del ciclo periódico.
- Evitar fechas que parezcan promesas mientras el sistema esté pausado o aún no tenga una referencia válida.

**Non-Goals:**

- Garantizar la hora exacta en que una fuente responderá o en que aparecerán nuevas vacantes.
- Mostrar fechas individuales para búsquedas encoladas por edición de perfil.
- Cambiar la frecuencia o el comportamiento del planificador.

## Decisions

### Guardar la última activación del ciclo periódico

Agregar un estado operativo persistente para registrar la fecha y hora en que se activa cada ciclo global automático. Actualizarlo solo para la tarea periódica, nunca para una ejecución administrativa manual ni para una actualización de perfil. La interfaz calcula la siguiente hora estimada sumando a esa referencia el intervalo automático vigente.

Esto evita inferir el ciclo a partir de `OperationalRun`, cuyos registros describen consultas individuales y pueden originarse en varios flujos. También evita depender de un archivo local de estado de Celery Beat, que no es directamente consultable por las vistas web y puede perderse al recrear el pod.

Alternativa considerada: inferir la referencia de la ejecución de ingesta más reciente. Se descarta porque una búsqueda manual o por perfil podría desplazar la hora mostrada y comunicar una programación incorrecta.

### Compartir el cálculo entre las dos vistas

Exponer un único dato de presentación reutilizable por el dashboard privado y el centro administrativo. Renderizar la fecha con la zona horaria configurada para la aplicación, incluir una etiqueta que la identifique como estimada y mantener en ambas vistas el aviso de que pueden ocurrir búsquedas antes.

Alternativa considerada: calcular la fecha por separado en cada vista. Se descarta para evitar resultados distintos y duplicar las reglas de intervalo, pausa y datos faltantes.

### Representar explícitamente los estados sin fecha

Si no existe el registro de un ciclo periódico, presentar «horario todavía no disponible». Si la pausa global está activa, mostrar «búsquedas pausadas» y ocultar la fecha estimada. Al reanudar, volver a calcular con el último ciclo periódico conocido y el intervalo que esté vigente.

## Risks / Trade-offs

- [La hora calculada es orientativa y puede diferir del inicio real por retrasos del planificador o de la cola] → Etiquetarla como estimada y actualizar el registro al activarse el ciclo periódico.
- [Un reinicio puede dejar un registro antiguo si el planificador no se ejecuta] → Conservar un vencimiento visible como estimación, no como garantía; la vista no debe afirmar que el ciclo ya comenzó.
- [Las búsquedas manuales o individuales podrían hacer que haya actividad antes] → Mostrar junto a la hora el aviso definido en la spec.

## Migration Plan

No requiere migrar datos históricos. El nuevo estado comienza vacío; hasta que ocurra el primer ciclo periódico tras el despliegue, las vistas mostrarán que el horario todavía no está disponible. La reversión consiste en retirar la presentación y el registro nuevo sin afectar parámetros existentes ni el historial de consultas.
