# Design

## Context

Ver propuesta en `proposal.md`. El checkout actual solo define PostgreSQL y Redis para desarrollo local en `compose.yaml`; no incluye todavía un `Dockerfile`, GitHub Actions ni directorio `deploy/`. La aplicación ejecuta Django, Celery Worker y Beat, guarda perfiles y archivos CV, y lee secretos desde variables de entorno. El servidor usa Flux como único mecanismo normal de despliegue, con namespaces separados y acceso web por Ingress.

## Goals / Non-Goals

**Goals:**
- Ejecutar los tres procesos de aplicación desde una imagen inmutable común.
- Crear una configuración aislada de staging que Flux pueda reconciliar.
- Proteger los CV y los datos persistentes con credenciales fuera de Git y una ruta de respaldo/restauración.
- Validar el entorno antes de dar el despliegue por terminado y poder volver a una imagen anterior.

**Non-Goals:**
- Crear o habilitar un despliegue de producción.
- Copiar cuentas, perfiles, CV, vacantes privadas o secretos de producción a staging.
- Cambiar el repositorio de infraestructura desde este cambio de aplicación; el administrador del servidor atenderá allí el registro de Flux solicitado.

## Decisions

### Empaquetar una sola imagen con comandos de proceso separados

Crear una imagen de runtime con dependencias instaladas, archivos estáticos preparados y usuario sin privilegios. Los manifiestos ejecutarán el proceso web, el worker y Beat por separado desde la misma etiqueta de commit. Esto permite escalar y reiniciar cada proceso según su salud sin duplicar versiones de la aplicación.

**Alternativa considerada:** ejecutar el script local `scripts/dev.sh` en el contenedor. Se descarta porque inicia servicios de desarrollo, carga `.env` local y usa el servidor de desarrollo de Django.

### Publicar el proyecto en un repositorio de aplicación de GitHub

Crear o vincular el repositorio remoto de `ramper-job` antes de configurar CI, confirmar su propietario y URL, y publicar el commit candidato sin secretos ni archivos `.env` reales. GitHub Actions construye desde este repositorio y publica la imagen en GHCR; el overlay de staging fija el SHA/digest de esa imagen.

**Alternativa considerada:** construir la imagen solo desde el checkout local. Se descarta porque no permite la publicación repetible de CI ni la reconciliación de cambios de aplicación y despliegue desde Git.

### Publicar imágenes en GHCR y desplegar referencias inmutables

GitHub Actions ejecutará las validaciones del repositorio y publicará una imagen con etiqueta por SHA o digest del commit. El overlay de staging fija esa referencia en Git y Flux reconcilia solo el manifiesto aprobado. No se desplegará `latest` ni se mutará Kubernetes manualmente para un rollout persistente.

El repositorio de aplicación en GitHub contiene `deploy/base` y `deploy/overlays/staging`; el administrador del servidor añade en el repositorio de infraestructura la fuente y Kustomization de Flux que apuntan al overlay real. Elegir el hostname de staging y registrar el Ingress se coordina con ese administrador, usando el camino aprobado Cloudflare Tunnel → Traefik → Service.

### Separar la rama de staging y probar ramas de trabajo

La rama `staging` es la fuente estable de la Kustomization de staging; `main` queda reservada para liberaciones de producción. El workflow de GitHub corre en pushes a `main` y `staging`. Un `workflow_dispatch` iniciado desde `main` recibe `source_branch`, ejecuta las mismas validaciones sobre el SHA de esa rama y publica su imagen por SHA. Solo después del éxito, escribe el SHA probado en el overlay de la rama `staging`; Flux siempre sigue `staging`, incluso cuando la imagen probada se construyó desde una rama feature. Un push directo a `staging` también construye, publica y fija su propio SHA.

El entorno es compartido, por lo que las selecciones de ramas se serializan y cada prueba reemplaza la imagen anterior de staging. La promoción se realiza con un PR desde la rama probada a `main`, después de la aprobación del usuario. La promoción de producción requerirá una configuración y autorización separadas; esta capacidad no crea un overlay ni reconcilia recursos prod.

### Separar servicios y configuración de staging

El overlay define web, worker, Beat, PostgreSQL y Redis en el namespace `staging`, con Services internos para dependencias y recursos dentro de las cuotas vigentes. Django y Celery reciben variables desde ConfigMaps no secretas y referencias a Secrets creados fuera del repositorio. La base de datos y el almacenamiento privado de CV usan volúmenes separados de producción; la media no se publica en el Ingress.

Las migraciones se ejecutan como trabajo controlado antes de declarar lista la versión web. Las migraciones deben mantener compatibilidad con la imagen anterior durante un rollback. Definir el tamaño y la clase de los volúmenes requiere comprobar capacidad real antes de crear recursos.

### Proteger datos persistentes

PostgreSQL y `MEDIA_ROOT` requieren persistencia y respaldos externos con procedimiento de restauración documentado y probado antes de guardar datos que deban conservarse. Redis no requiere persistencia para los resultados de negocio; una cola se puede reconstruir. Staging comienza con datos de prueba y no se inicializa importando datos reales de producción.

**Alternativa considerada:** mantener PostgreSQL y CV solo en el sistema de archivos efímero del contenedor. Se descarta porque una recreación del pod perdería perfiles y documentos.

### Provisionar manualmente la cuenta administradora inicial

La aplicación incluirá un comando de bootstrap ejecutado una sola vez en el entorno `staging` desde una terminal administrativa autorizada. El comando solicitará la contraseña con entrada oculta y creará la cuenta solo si no existe ya una cuenta administradora. La contraseña no se pasará en argumentos, variables de entorno, manifiestos ni archivos; el comando no se ejecutará automáticamente al iniciar o reiniciar pods. Después del bootstrap se validará el inicio de sesión y la unicidad del rol administrativo.

**Alternativa considerada:** guardar la contraseña inicial en un Secret montado permanentemente o crear automáticamente la cuenta en cada arranque. Se descarta porque mantiene una credencial de bootstrap activa y acopla la identidad administrativa al ciclo de despliegue.

### Condicionar el despliegue a la finalización funcional

Antes de publicar o reconciliar la primera versión de staging, verificar que estén completos los cambios funcionales indicados en la sección 1 de `tasks.md`: `vista-vacantes-por-analizar`, `seguimiento-postulaciones`, `panel-observabilidad-operativa`, `distribucion-umbral-puntajes`, `rubrica-criterios-criticos-decimales`, `deslizadores-filtro-puntaje`, `analisis-ia-por-etapas`, `vigencia-y-actualizacion-vacantes`, `centro-administracion-plataforma`, `portal-comandos-administrativos`, `parametros-operativos-admin`, `estadisticas-globales-administracion`, `busquedas-compartidas-por-perfil`, `carga-manual-vacantes-admin`, `vacante-desde-url-admin`, `fechas-relativas-vacantes`, `descarte-automatico-recomendaciones`, `limpieza-estados-inactivos`, `ordenar-vacantes-por-puntaje`, `puntaje-en-estrellas`, `paginacion-numerada-vacantes`, `respuestas-ia-menos-detalladas`, `plazos-retencion-configurables` y `estrellas-sin-puntaje-numerico-visible`. Esto deja que la primera validación del entorno pruebe el conjunto acordado y evita desplegar una versión intermedia.

## Risks / Trade-offs

- [El cluster puede no tener suficiente cuota o almacenamiento] → Consultar uso y capacidad en vivo con el administrador antes de fijar requests, limits y volúmenes.
- [Un backup local en el mismo nodo no protege ante pérdida del nodo] → Usar el destino externo aprobado y probar restauración antes de conservar datos necesarios.
- [Un secreto no existe al momento de reconciliar] → Provisionar referencias de Secret fuera de Git antes de habilitar Flux y validar nombres sin imprimir valores.
- [El hostname o ruta de Cloudflare aún no está asignado] → Confirmarlo con el administrador del servidor antes de crear el Ingress.
- [Un cambio de esquema incompatible puede impedir rollback] → Usar migraciones compatibles hacia adelante y respaldar la base antes de aplicar cambios destructivos.
- [El despliegue puede no ser accesible desde una red pública si falta una ruta de túnel] → Confirmar la ruta documentada y validar primero la salud desde el entorno autorizado.

## Migration Plan

1. Esperar a que terminen todas las funcionalidades enumeradas en la sección 1 de `tasks.md` y revisar el commit resultante.
2. Añadir imagen, CI, recursos base y overlay de staging; validar build y manifiestos sin desplegar.
3. Coordinar con el administrador el hostname, los Secrets, el respaldo y la fuente/Kustomization de Flux staging.
4. Publicar la imagen identificada por commit, actualizar el overlay y esperar reconciliación de Flux.
5. Aplicar migraciones compatibles, verificar pods, salud, logs saneados, Ingress, login, dashboard y trabajo asíncrono.
6. Si falla la validación, revertir el commit del overlay a la imagen anterior mediante Git y Flux; restaurar datos solo si una migración o carga dañó el estado.

Producción permanece sin cambios y fuera de este plan.
