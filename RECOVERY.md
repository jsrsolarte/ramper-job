# Recuperación de Ramper Job

Preparado el 2026-11-13, America/Bogota, para reinstalar Ubuntu o migrar a Fedora. Este respaldo conserva trabajo de desarrollo; no recupera cuentas, perfiles reales, historial de vacantes, CV ni servicios desplegados. No se ejecutó la aplicación, no se consultaron bases de datos, no se accedió al servidor y no se modificaron ramas ni despliegues.

## Propósito y mapa del código

Asistente privado para familiares: obtiene vacantes públicas de El Empleo y Computrabajo Colombia, agrupa búsquedas equivalentes y analiza compatibilidad con el perfil mediante OmniRoute. No hay registro público; existe una única cuenta administradora. La carga administrativa por URL solo admite El Empleo.

| Ruta | Contenido |
| --- | --- |
| `config/` | Ajustes Django, URLs, middleware, Celery, salud y comandos de inicialización |
| `profiles/` | Perfiles, revisiones, extracción PDF/DOCX, preferencias y recorrido inicial; es código, no una carpeta de datos de usuario |
| `jobs/` | Conectores, ingesta, deduplicación, búsquedas compartidas y trabajo durable recuperable |
| `matching/` | Cliente OmniRoute, rúbrica versionada, puntuación, organización y recuperación de análisis |
| `dashboard/` | Vacantes, filtros, estrellas, seguimiento y vistas del aspirante |
| `operations/` | Administración, parámetros, observabilidad, estadísticas y programación |
| `templates/`, `static/` | Interfaz propia HTML/CSS/JS; conservar estos archivos aunque sean resultados elaborados durante el desarrollo |
| `*/migrations/`, `*/tests/`, `operations/test*.py` | Esquema y pruebas con datos sintéticos; los CV de tests se construyen en memoria o directorios temporales |
| `openspec/` | Especificaciones principales, cambios activos y archivo histórico completo |
| `.agents/skills/` | Workflows OpenSpec locales y selector `codex`; se conservan aun estando ignorados por Git |
| `deploy/`, `.github/workflows/` | Overlays staging/prod, runbook, CI y liberaciones; no aplicarlos automáticamente |
| `scripts/`, `docs/` | Desarrollo, validación de versiones, provisionadores y diagnósticos; los provisionadores son código, no secretos, y no se ejecutaron |
| `pyproject.toml`, `uv.lock`, `Dockerfile`, `compose.yaml`, `Makefile` | Dependencias y entorno reproducible |

## Estado comprobado y límites de Git

El directorio `.git` local está vacío. `git status --short --branch` devuelve «not a git repository». No se pudo determinar rama, HEAD, cambios sin commit, stash, worktrees ni diferencia respecto al remoto. No existe un bundle ni un parche contra una base conocida; el snapshot completo es la forma autónoma de preservar este árbol sin inventar historial.

Se confirmó mediante metadatos del conector GitHub que `jsrsolarte/ramper-job` existe, es público y su rama predeterminada es `main`, con URL `https://github.com/jsrsolarte/ramper-job.git`. No se descargó ni auditó el historial remoto y no se comprobó igualdad de archivos. El respaldo es independiente de GitHub para recuperar los archivos incluidos, pero no contiene historial Git recuperable.

## Contexto recuperado de chats

Se consultaron mensajes del proyecto, no se copiaron conversaciones completas ni salidas de herramientas. Estos antecedentes no sustituyen una comprobación actual ni conceden autorización operativa:

- «Prioriza nuevas specs» (`01a1c6df-a831-7ac2-8ecf-25bcf3dad7ca`): reportó Computrabajo, refrescos resilientes, historial agrupado y desglose, y luego pausa individual y próxima búsqueda implementados; último reporte de prueba en staging con imagen `8902fd2`, CI de 305 pruebas. La pérdida controlada de un worker no se había probado en vivo. Se había pedido dejar backups fuera de la cola de implementación.
- «Proponer specs para implementar» (`01a18ab6-7553-7fe2-a993-c501af52050b`): nuevas propuestas de distribución administrativa en estrellas, pausa individual y guardado durante recorrido; para este último se identificó que el middleware redirigía el POST antes de guardar. Reutilizar evidencia del CV sigue siendo un cambio amplio que requiere preservar soporte de la rúbrica.
- «Revisar errores recientes en prod» (`01a1cfd0-782a-7380-a66c-bc6d3005a9ad`): originó `estabilizar-operacion-produccion` por redirecciones de sondas HTTPS, recuperación de ingestas y límites de texto del modelo; incluyó backups externos aún pendientes.
- «Ramper Job: staging → prod» (`01a1c760-7ee0-7180-a4cc-7acf5b387b3c`): el 13 de noviembre reportó integración a main por PR #22 y misma imagen en staging/prod (`sha256:2dc016…`), con Flux y componentes listos en su verificación. Es un reporte histórico; no se volvió a consultar el clúster. La observación del 12 de noviembre conservada en AGENTS es anterior a ese reporte.

## Pendientes preservados

No se implementó, validó ni archivó ninguna spec durante este respaldo. Revisar los `tasks.md` y el código antes de retomar: hay diferencias entre casillas y reportes históricos. No marcar tareas como hechas solo por esta guía.

- `pausa-busqueda-perfil-individual`: 7/7 tareas marcadas; código y migración presentes; permanece como cambio activo.
- `mostrar-proxima-busqueda`: 4/5 marcadas; queda casilla de pruebas/validación manual de horario tras ciclo automático y cambio de intervalo.
- `desglose-vacantes-en-consultas`: 6/6 marcadas; permanece activo.
- `estabilizar-operacion-produccion`: 7/12 marcadas; pendientes explícitos de backup/restauración y cierre de validación/despliegue. No realizar esas operaciones por recuperar este proyecto.
- `guardar-perfil-durante-recorrido`, `distribucion-puntuaciones-estrellas`, `navegacion-recomendaciones-version`, `reutilizar-evidencia-cv`: tareas sin marcar; preservar como propuestas y confirmar estado antes de implementar.
- `primera-version-produccion`: 7/12 marcadas; sus pendientes de primer despliegue pueden estar desactualizados respecto a los chats. Verificar y reconciliar planificación en una tarea expresamente solicitada.
- Todo `openspec/changes/archive/` se conserva como contexto histórico; no asumir que cada snapshot allí refleja el último despliegue.

## Restauración en cualquier ruta

El paquete se llama `ramper-job-continuidad-2026-11-13.tar.gz`, acompañado por `.sha256`. Destino previsto para transferencia por el coordinador: `/mnt/media/ubuntu backup/ramper-job-2026-11-13/`. La preparación local no acredita esa transferencia.

1. Copiar ambos archivos al equipo nuevo y verificar desde su carpeta: `sha256sum -c ramper-job-continuidad-2026-11-13.tar.gz.sha256`.
2. Extraer en una carpeta nueva vacía preservando permisos: `tar -xzpf ramper-job-continuidad-2026-11-13.tar.gz -C /ruta/nueva`. La opción `p` evita que la máscara de permisos del equipo cambie los modos del inventario.
3. La raíz extraída es `ramper-job-2026-11-13/`; ejecutar allí `python3 verify_inventory.py`. El verificador compara rutas, tipos, bytes, modos y SHA256 de todo `project/` con `INVENTORY.json`. No importa la ruta original ni requiere red.
4. Abrir `project/` como proyecto en Codex y comenzar leyendo AGENTS y esta guía. Si se mueve `project/` después, conservar también el inventario y verificador junto a una copia sin modificaciones para auditoría.
5. Para recuperar historial posteriormente, clonar el remoto en OTRA carpeta y comparar por archivos con este snapshot, incluyendo ignorados útiles como `.agents/` y specs locales. No sobrescribir el snapshot ni asumir que `main` contiene todo. Revisar diferencias y secretos antes de crear commits o integrar trabajo; esto no se hizo en el respaldo.

## Dependencias y ejecución posterior

Requiere Python >=3.12, uv, Git para futuras integraciones, Docker Engine/Compose para PostgreSQL 17 y Redis 7. `uv.lock` fija dependencias; Django 5.2, Celery 5.x, Gunicorn, psycopg, BeautifulSoup, requests, pypdf, python-docx y WhiteNoise figuran en `pyproject.toml`. El workflow de OpenSpec se puede recuperar desde las skills incluidas; reinstalar su CLI compatible antes de usarlo, sin asumir una versión global guardada.

En el nuevo equipo, `uv sync --frozen` reconstruye `.venv` con red cuando corresponda. Crear un `.env` nuevo desde `.env.example` y ajustar valores exclusivamente locales. La plantilla contiene credenciales de desarrollo de ejemplo y una URL pública de OmniRoute: sustituirlas por configuración aislada antes de iniciar procesos. Los ajustes Django leen variables de entorno; cargar el `.env` explícitamente solo cuando esté preparado.

El README describe `make setup`, `make dev`, `make workers`, `make superuser` y `make stop`. **`make dev` inicia Docker, aplica migraciones, levanta web, worker y Beat; `make workers` también puede activar búsquedas externas.** No ejecutarlos solo para verificar extracción. Tras configurar servicios locales y datos sintéticos deliberadamente, seguir README; web usa 127.0.0.1:8000 y acepta `PORT=8001`. No reutilizar conexiones a PostgreSQL/Redis de producción. Las pruebas Django necesitan una base local adecuada; no se ejecutó suite durante el respaldo.

## Conexiones y datos que no se recuperan

- Reautenticar Codex/OpenAI y conectores necesarios, GitHub para trabajo futuro y GHCR/CI según permisos. No se incluyen sesiones ni credenciales.
- Recrear la clave de Django, contraseñas locales y acceso OmniRoute por canal seguro; no usar valores reales de otro entorno. No se incluye `.env`.
- Si se solicita después desplegar, localizar el checkout `servidor`, reinstalar/configurar la skill server-deploy y reestablecer acceso SSH/Flux por canal seguro. No hay claves SSH, kubeconfig, secretos Kubernetes ni configuración privada de clientes en este paquete. Ningún despliegue queda autorizado por esta guía.
- Exclusión personal exacta: `media/profiles/3/cv/v1.docx`, 36878 bytes, modo 0644, clasificado únicamente por ruta y metadatos; no se abrió ni copió. No se puede recuperar ese CV de este paquete. Todo `media/` queda excluido por ser área de subidas.
- `.env` (459 bytes) y `celerybeat-schedule`, `celerybeat-schedule-shm`, `celerybeat-schedule-wal` quedan fuera; no se abrieron. PostgreSQL/Redis en volúmenes Docker, usuarios, perfiles, historial y CV de instalaciones locales o servidor no se respaldaron ni consultaron. No se preserva la cola ni programación runtime.
- `.venv/`, `__pycache__/`, bytecode y caches/dependencias recreables están excluidos. `.git/` vacío y los directorios privados `.aws/`, `.codex/` tampoco se incluyen. `EXCLUSIONS.json` registra todas las entradas omitidas encontradas por metadatos, sin hash ni contenido de secretos o datos personales.

No hay backup de datos de staging/prod configurado según la documentación existente: siguen expuestos a pérdida irreversible del nodo/PVC. Este snapshot de desarrollo no soluciona ese riesgo. Conservar las salvaguardas de AGENTS: staging primero, solo Git/Flux y autorización explícita para cada promoción o mutación productiva.

## Validación de este respaldo

Se verifica el inventario contra el origen seleccionado y una extracción nueva temporal, incluida igualdad exacta de rutas, permisos, bytes y hashes de archivos. Se revisan enlaces y patrones conocidos de claves en los candidatos seguros; no es una auditoría exhaustiva de secretos. No se prueba restauración Git porque no existe repositorio local válido. No se ejecutan aplicaciones, tests remotos, crawlers, comandos de usuario ni accesos a datos. Los resultados y cantidades finales están en `BACKUP_REPORT.json`, fuera de `project/`.
