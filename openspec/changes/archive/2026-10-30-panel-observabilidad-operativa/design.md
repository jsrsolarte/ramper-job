# Design

## Context

`JobSourceStatus` conserva solo el estado más reciente por fuente. Los análisis guardan creación, última actualización y el último mensaje de error, pero no una duración fiable ni el historial de intentos. El panel debe usar datos nuevos desde su despliegue y proteger información de CV y perfiles.

## Goals / Non-Goals

**Goals:**

- Registrar cada ejecución de consulta a fuente y cada intento de análisis con inicio, fin, resultado, conteo cuando aplique y error resumido.
- Calcular agregados por ventanas de 24 horas, 7 días y 30 días, además de los pendientes actuales.
- Restringir vista y datos a personal administrativo.

**Non-Goals:**

- Medir CPU, memoria, disponibilidad de host o infraestructura Kubernetes.
- Añadir un proveedor externo de observabilidad o alertas.
- Reconstruir retrospectivamente ejecuciones anteriores a la instrumentación.

## Decisions

- Guardar eventos operativos por ejecución en tablas históricas separadas del estado más reciente de la fuente y del análisis de negocio. El evento de ingesta se crea por consulta de conector; cada llamada de análisis de IA genera un intento con resultado y duración.
- Conservar al menos 90 días de historial. La vista agregará los registros al consultarlos y mostrará la fecha inicial de cobertura, en lugar de aparentar que los datos históricos existían antes de la instrumentación.
- La limpieza periódica cerrará como fallidos los registros que sigan en curso por más de 20 minutos. Ese límite supera el timeout de las llamadas externas y evita que una interrupción del worker aparezca como ejecución activa indefinida.
- Medir duración con marcas de inicio y final registradas alrededor de cada ejecución. Mantener `JobSourceStatus` para su función actual de indicar disponibilidad más reciente.
- Usar un panel interno del sitio administrativo, con autorización administrativa en cada solicitud. Mostrar conteos y errores resumidos/saneados; no consultar ni renderizar CV, prompts, credenciales, ni cuerpos completos de vacantes.
- Calcular volumen y promedio desde los eventos persistidos. Para la cola actual, contar análisis pendientes y obtener la edad del más antiguo; no asumir que los pendientes representan workers en ejecución.
- En el dashboard de aspirantes, describir esos registros como pendientes de análisis para no dar a entender que un worker los está procesando.

## Risks / Trade-offs

- **El historial crece con cada tarea ejecutada** → Retener 90 días como mínimo y limpiar registros anteriores mediante una tarea periódica.
- **Los errores de proveedores pueden incluir datos sensibles** → Guardar categorías y mensajes saneados/truncados, nunca payloads de solicitud ni respuestas.
- **La media oculta ejecuciones muy lentas** → Mostrar conteo junto al promedio para que el usuario pueda valorar el tamaño de la muestra; percentiles quedan fuera de esta primera entrega.
- **Las métricas empiezan después del despliegue** → Mostrar claramente la fecha de inicio de cobertura y no rellenar datos históricos por inferencia.

## Migration Plan

Crear las tablas de eventos sin backfill. Desplegar instrumentación de ingesta y análisis antes de habilitar el panel. Ejecutar una tarea periódica de retención que elimine eventos con más de 90 días. La reversión retira el panel y sus eventos; no cambia vacantes, perfiles ni resultados de análisis.
