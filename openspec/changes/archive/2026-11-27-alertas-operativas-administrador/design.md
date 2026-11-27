# Design

## Context

`OperationalRun` conserva categorías y tiempos, y `RefreshBatch` y `RefreshWorkItem` registran trabajo durable y heartbeat. El cálculo de próximos ciclos ya contempla pausas; `corregir-horario-busqueda-vencido` propone distinguir retrasos y trabajo activo. El incidente del 26 de noviembre mostró que un worker puede reiniciarse repetidamente y que Beat puede estar activo sin ejecutar una tarea concreta.

## Goals / Non-Goals

**Goals:**
- Señales basadas en evidencia, respetando pausas y ausencia legítima de trabajo.
- Agrupar incidentes y reducir ruido manteniendo un historial útil.

**Non-Goals:**
- Reparación automática, extracción de logs privados, acceso de la aplicación al API de Kubernetes o garantía de detección durante caída total.
- Cambiar infraestructura o desplegar sin solicitud expresa.

## Decisions

- Evaluar cada cinco minutos eventos durables de ingesta y análisis y el trabajo pendiente; tres fallos distintos por componente y categoría en 30 minutos abren un incidente, y 30 minutos sin progreso abren otro. Usar timestamps confirmados, heartbeat y vigencia de leases; cola sin despacho reciente se considera pendiente, no activa. Definir de forma explícita qué eventos se cuentan y conservar IDs o una marca de corte para no duplicarlos al reevaluar.
- El ciclo global vencido usa la misma definición y precedencia de pausas de `corregir-horario-busqueda-vencido`; su plazo de 30 minutos se cuenta solo mientras puede ejecutarse. La pausa individual solo excluye trabajo de ese perfil, y la franja solo búsquedas automáticas. No alertar por ausencia de trabajo elegible o falta de perfiles habilitados. Valores iniciales quedan versionados para ajuste posterior con evidencia, sin convertir cada error transitorio en incidente.
- Guardar incidentes durables por clave estable de tipo/componente/categoría, con primera y última observación, conteo, estado y reconocimiento. La recuperación requiere dos evaluaciones consecutivas con datos suficientes; la falta de datos produce estado desconocido, no resolución. Una recurrencia tras recuperación abre un nuevo episodio. La consulta del panel no dispara búsquedas ni correcciones.
- Reutilizar el transporte y consentimiento por dispositivo de `notificaciones-nuevas-recomendaciones` cuando exista, o extraer una base compartida equivalente antes de implementar este canal. La preferencia de alertas administrativas es independiente del resumen de vacantes. Un aviso genérico se intenta al detectar un incidente y luego como máximo uno cada seis horas por dispositivo; agrupar episodios nuevos activos y descartar los recuperados antes del siguiente envío. Reservar el envío atómicamente, usar TTL corto y no reintentar resultados ambiguos. Permitir desactivar por dispositivo y desvincular al cerrar sesión.
- La evaluación interna requiere aplicación, base y ejecución del evaluador. No puede detectar ni enviar por sí sola durante una caída total de esos mismos componentes. Para cubrir ese caso se necesita un monitor independiente y canal propio externos al worker y Beat, con heartbeat y alerta por ausencia; evaluar infraestructura existente en una propuesta separada. Hasta entonces mostrar limitación y salud desconocida cuando falte evidencia; no consultar Kubernetes desde la aplicación ni asumir monitor externo operativo.
- Mostrar solo categoría controlada, componente, tiempos y conteos. No incluir perfiles, URLs de ofertas, respuestas del modelo o secretos en alertas, mensajes push ni logs. Proteger los endpoints y permisos administrativos; no afirmar entrega real a partir de aceptación por el servicio push.

## Risks / Trade-offs

- [La misma infraestructura cae junto al evaluador] → Estado desconocido al volver y dependencia explícita de vigilancia externa para aviso durante la caída.
- [Umbrales detectan lentitud normal] → Agrupar por episodio, exigir ventana y considerar pausas; revisar valores con evidencia antes de ajustarlos.
- [Demora de hasta seis horas para avisos adicionales] → Mostrar todos los incidentes en el panel inmediatamente y agrupar notificaciones.
- [Fallas del dispositivo o del servicio push] → El historial interno sigue disponible; no garantizar entrega ni reintentar resultados inciertos.
- [Cambios en horario de búsquedas y notificaciones se desarrollan en paralelo] → Coordinar contratos y orden de integración, sin asumir que las propuestas están implementadas.

## Migration Plan

Agregar registros de incidentes y preferencias desactivadas sin emitir alertas masivas del historial anterior; comenzar evaluación desde un punto de activación explícito. Probar con reloj y datos sintéticos. Configuración de push, monitor externo y despliegue requieren autorización y preparación separadas; producción solo con autorización explícita.

## Validación de implementación

- La evaluación se ejecuta cada cinco minutos en la cola `matching_v2`; el estado del evaluador se guarda por separado de los incidentes.
- Las pruebas locales usan PostgreSQL temporal con fixtures sintéticos y sender push simulado. Incluyen fallos agrupados, dos evaluaciones de recuperación, recurrencia, pausas, leases vigentes/vencidos, ciclo vencido, autorización, consentimiento independiente, concurrencia de reserva, caducidad y resultado ambiguo.
- La suite dirigida completa aprobó 98 pruebas de alertas, limpieza, horario, estadísticas y vistas; `manage.py check`, `makemigrations --check` y `openspec validate` también pasaron.
- El transporte push físico no se ha probado en un dispositivo desde staging. La preferencia sigue apagada por defecto; el primer envío real requiere activación explícita en el panel administrativo.
- No existe monitor externo de caída total. El panel informa esta limitación y evita afirmar salud general solo porque se ejecutó el evaluador.
