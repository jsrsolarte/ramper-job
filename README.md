# Ramper Job

Asistente privado para reunir vacantes y organizarlas según el perfil de cada familiar.

## Inicio local

1. Ejecuta `make setup`; crea `.env` desde `.env.example` si hace falta e instala dependencias.
2. Agrega el valor local de `OMNIROUTE_API_KEY` en `.env`. No guardes secretos en Git.
3. Ejecuta `make dev`; inicia PostgreSQL y Redis, aplica migraciones y levanta Django, Celery Worker y Beat con las variables de `.env` cargadas.
4. Abre `http://127.0.0.1:8000/`. Detén los procesos con Ctrl+C y los servicios de datos con `make stop`.

Si el puerto 8000 ya está ocupado, inicia con otro, por ejemplo `make dev PORT=8001`, y abre `http://127.0.0.1:8001/`.

Si el servidor web ya está abierto y solo necesitas arrancar o reiniciar las tareas, ejecuta `make workers`. Este modo conserva el servidor web y arranca Celery Worker y Beat.

La cuenta administradora es única. Para aprovisionarla en una instalación nueva, ejecuta `make superuser`; la base rechaza un segundo superusuario. En una base ya existente se conserva la cuenta superusuario activa auditada antes de aplicar esta regla.

El centro de administración está en `/admin/operaciones/`; el acceso técnico de Django está en `/admin/`. El acceso de familiares está en `/accounts/login/`. No existe registro público.

En **Administración → Agregar desde una URL** se pega únicamente el enlace público de una vacante de El Empleo. El worker extrae los datos disponibles, guarda o actualiza la publicación global y programa evaluaciones independientes para perfiles elegibles. La página muestra el estado y resultado de los registros recientes; si permanecen en cola, revisa que Celery Worker esté activo.

Por ahora se admiten fichas HTTPS de El Empleo bajo `/co/ofertas-trabajo/`. Para incorporar otra bolsa, añade su regla explícita de host y ruta en `jobs/connectors/elempleo.py` o extrae el resolvedor a un registro de proveedores, implementa un extractor que entregue `JobListing` y agrega pruebas para redirecciones, hosts públicos y datos incompletos. La carga no sigue redirecciones a otros hosts ni consulta URLs arbitrarias.

La administración puede generar un enlace de restablecimiento para una cuenta activa y compartirlo manualmente. El enlace se muestra una sola vez, es de un solo uso y vence según `PASSWORD_RESET_TIMEOUT` (3 días por defecto); el sistema no envía correos ni guarda el token en auditoría o logs. La administración nunca consulta ni establece la contraseña nueva.

El reconciliador recupera análisis pendientes o fallidos con una espera creciente limitada a una hora, hasta que venza el plazo de descarte configurado desde el primer hallazgo por perfil. Los valores locales se ajustan con `ANALYSIS_RECOVERY_INTERVAL_SECONDS` (60), `ANALYSIS_RECOVERY_STALE_SECONDS` (300), `ANALYSIS_RECOVERY_LEASE_SECONDS` (1200) y `ANALYSIS_RECOVERY_BATCH_SIZE` (50). El dashboard administrativo registra recuperaciones y vencimientos.

Cada vez que se guarda una versión nueva del perfil se encola una actualización de vacantes. Para iniciar manualmente una búsqueda de todos los perfiles activos, con el worker y Beat en ejecución, usa:

```sh
uv run celery -A config call jobs.tasks.refresh_sources
```

El worker deriva las palabras clave del CV y los criterios del perfil con la configuración activa de OmniRoute. Cuando varios perfiles activos generan los mismos términos, ubicaciones y modalidad para una fuente, comparte una sola consulta pública y reparte las vacantes encontradas entre ellos. Cada perfil conserva su propio análisis, puntaje y seguimiento en el dashboard. El prompt de búsqueda y los demás parámetros de coincidencia se pueden versionar desde `/admin/`.

Elempleo se consulta desde páginas públicas. Después de deduplicar resultados, el conector abre una vez la ficha de cada vacante para obtener sus condiciones y datos de ubicación; si la estructura cambia, actualiza los casos de referencia en `jobs/tests/test_elempleo.py` y ejecuta `.venv/bin/python manage.py test jobs.tests.test_elempleo`.

## Puntaje y etapas de IA

La compatibilidad se califica de 0 a 10 con una rúbrica versionada: habilidades (4), experiencia (2), alineación del cargo/sector (2), educación requerida (1) y otros criterios explícitos del perfil (1). La ubicación y modalidad se validan antes del análisis y no suman puntos. La aplicación valida y suma los criterios devueltos por OmniRoute usando una cifra decimal. Cada requisito obligatorio de la vacante que contradiga evidencia explícita del CV descuenta el valor versionado de la configuración (inicialmente 2,0); la falta de evidencia no genera deducción. El detalle de criterios, evidencia y descuentos queda en la tarjeta.

El análisis ocurre en dos llamadas. La primera compara CV, criterios del perfil y publicación; guarda el puntaje antes de iniciar otra tarea. Si alcanza el mínimo persistido en el perfil, la segunda llamada organiza solo el contenido de la vacante y comparte el resultado entre perfiles que usan la misma configuración y versión del contenido. El dashboard puede mostrar el puntaje mientras esa organización está pendiente o falló. Bajar el mínimo del perfil programa la organización pendiente; subirlo o mover el filtro temporal del dashboard no genera llamadas nuevas.

Los intentos de ambas etapas registran duración, resultado y tokens cuando OmniRoute los informa. No se guardan los prompts, el CV ni las respuestas completas. La página **Administración → Observabilidad operativa** agrega estos datos por etapa; el detalle se puede consultar en `/admin/`.

El cambio de rúbrica no convierte ni recalcula resultados históricos. En la base local se limpiaron las vacantes existentes y sus datos dependientes antes de activar la nueva versión; cuentas, perfiles y configuraciones se conservaron.

## Configuración de IA

Configura `OMNIROUTE_BASE_URL`, `OMNIROUTE_API_KEY` y `OMNIROUTE_MODEL` en el entorno que ejecute Django y Celery. La aplicación usa el formato OpenAI-compatible `chat/completions` y no instala ni configura OmniRoute.
