# Despliegue

## Ramas, rutas y ambientes de Flux

La conexión de fuentes y la activación de Kustomizations se administra fuera de este
repositorio. Cuando configures Flux, usa este mapeo:

| Rama | Ruta de Kustomize | Namespace | Host |
| --- | --- | --- | --- |
| `staging` | `./deploy/overlays/staging` | `staging` | `ramper-job-staging.ramper.lat` |
| `main` | `./deploy/overlays/prod` | `prod` | `jobs.ramper.lat` |

Cada overlay incluye `../../base` y declara sus ajustes de ambiente: namespace,
hostname, probes, ConfigMap y referencias a secretos. No apuntes ambas fuentes a
`deploy/base` ni a la raíz del repositorio.

El workflow de GitHub Actions valida los cambios. Al integrar un candidato en `staging`,
publica una imagen identificada por su SHA completo y no usa `latest`. Los pull requests
solo validan y construyen localmente; no publican imágenes.

Al integrar un candidato en `staging`, CI actualiza el pin SHA de
`deploy/overlays/staging/kustomization.yaml` en esa misma rama. Cuando el candidato
aprobado se integra desde `staging` a `main` mediante PR, CI valida el merge,
verifica que el código corresponda al candidato y que su imagen exista, y actualiza
automáticamente el pin de producción al mismo SHA de imagen probado. Un push directo,
un PR de otro origen, una falla de validación o una discrepancia no cambia el pin.
El pipeline serializa promociones y evita repetir el ciclo por su propio commit GitOps.
Flux reconcilia el pin desde `main`. Este repositorio no crea ni activa fuentes o
Kustomizations de Flux.

## Secretos requeridos

Flux no necesita un Secret de autenticación Git mientras este repositorio siga siendo
público. GitHub Actions usa su `GITHUB_TOKEN` efímero para publicar en GHCR; no se
requiere configurar una credencial adicional para el workflow.

En **cada namespace** debe existir un Secret de runtime llamado
`ramper-job-secrets`, con valores independientes por ambiente y estas claves:

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `OMNIROUTE_API_KEY`

La imagen requiere además un Secret `kubernetes.io/dockerconfigjson` con permiso
GHCR `read:packages`. Los nombres referenciados son distintos por ambiente:

- Staging, namespace `staging`: `ramper-job-registry`.
- Producción, namespace `prod`: `mcp-gateway-ghcr-prod` (Secret de solo lectura
  ya compartido en ese namespace).

Los Secrets no se guardan en Git. Para preparar los de runtime usa los provisionadores
interactivos del repositorio desde el servidor:

- Staging: `python3 scripts/provision_staging_secrets.py`
- Producción: `python3 scripts/provision_prod_secrets.py`

El provisionador de staging crea la clave Django y la contraseña PostgreSQL, solicita
OmniRoute sin eco y solo pide credenciales GHCR si no existe el Secret
`ramper-job-registry` con el tipo esperado. El de producción genera la clave Django
y la contraseña PostgreSQL, solicita OmniRoute sin eco y comprueba la existencia y el
tipo de `mcp-gateway-ghcr-prod`; no lee ni copia su credencial.

Los workloads de Ramper Job y los Secrets de runtime están separados por namespace.

El ConfigMap `ramper-job-config` contiene solo configuración no sensible. No se
versionan manifiestos de Secret, archivos `.env` ni credenciales.

## Persistencia y alcance de datos

PostgreSQL usa un volumen de 2 GiB y los CV un PVC independiente de 2 GiB. Redis no persiste:
contiene colas reconstruibles. Ramper Job no configura copias de seguridad locales ni externas
para PostgreSQL o CV, en staging ni en producción. `microk8s-hostpath` reside en el nodo; si se
pierde el nodo o un volumen, los datos pueden desaparecer sin posibilidad de restauración.
Staging solo debe contener datos sintéticos y descartables. No cargar perfiles ni CV reales ni
datos que deban conservarse. Si se configura producción, sus datos también serán descartables
mientras esta decisión siga vigente. Un restablecimiento completo puede eliminar los dos PVC de
staging y permitir que StatefulSet/Deployment los creen de nuevo.

## Recursos y comprobaciones

Requests agregados de la aplicación: 500m CPU y 1152 MiB; limits: 2.15 CPU y 2112 MiB,
dentro de la cuota observada al preparar estos manifiestos. La disponibilidad debe volver a
comprobarse antes de reconciliar, pues el uso del namespace puede cambiar.

- `/healthz` comprueba que el proceso web está vivo.
- `/readyz` comprueba PostgreSQL y Redis.
- El worker verifica su respuesta a un ping Celery; Beat verifica sus dependencias y proceso.

Las sondas HTTP de Kubernetes reciben directamente el estado de `/healthz` y `/readyz`,
sin seguir redirecciones HTTPS. Las demás rutas conservan la redirección segura cuando está
habilitada. Si falla PostgreSQL o Redis, `/readyz` responde 503 genérico sin exponer el error
interno.

La reconciliación de ingestas corre cada cinco minutos. Una unidad en ejecución se recupera
cuando lleva más de 20 minutos sin heartbeat y su lease expiró o falta. Se reencola hasta
agotar cuatro intentos totales; al agotarlos, la unidad y sus ejecuciones asociadas se cierran
con la categoría segura `execution_interrupted`, se libera el lease del perfil y se conserva
el historial. Un heartbeat reciente con lease vigente conserva la unidad en ejecución.

## Versiones y liberaciones

Las pruebas de staging siguen identificándose por el SHA de la imagen y no reciben una versión de producto. Las liberaciones aprobadas usan etiquetas Git anotadas `vMAJOR.MINOR.PATCH`; la primera versión de producción es `v1.0.0`. La validación rechaza formatos inválidos, ceros iniciales, versiones ya existentes y actualizaciones de una etiqueta publicada.

Incrementa PATCH para correcciones compatibles, MINOR para funcionalidades compatibles y MAJOR para cambios incompatibles que requieren adaptación. El asunto de la etiqueta anotada debe explicar el tipo de incremento y su motivo.

El flujo de liberación solo acepta un commit que esté en `staging` y cuya imagen SHA sea la actualmente fijada en el overlay. Resuelve el digest de esa imagen ya construida y adjunta a la versión un manifiesto con etiqueta, versión, SHA, referencia y digest. No reconstruye la imagen. El merge aprobado de `staging` a `main` promueve automáticamente el artefacto; crear una etiqueta de versión no cambia por sí sola el pin. Flux productivo obtiene `deploy/overlays/prod` desde `main`; este repositorio no activa su Kustomization.

El init container del web ejecuta `migrate --noinput` antes de iniciar Gunicorn. Los init
containers del worker y Beat esperan hasta 15 minutos a que no haya migraciones pendientes;
así no consumen tareas contra un esquema aún incompleto. Las migraciones futuras deben seguir
el patrón expandir/migrar/contraer: primero añadir estructuras compatibles con la imagen
anterior, mover o transformar datos en una etapa reversible y retirar campos antiguos solo
cuando ninguna imagen de rollback los use. El rollback normal cambia por Git la imagen fijada en el overlay y deja que Flux reconcilie. No
hay backups ni ruta de restauración: una migración destructiva o un fallo de almacenamiento
puede hacer perder los datos, que se consideran descartables.

Hostname de staging: `ramper-job-staging.ramper.lat`. Cloudflare Tunnel debe enrutarlo a
`http://traefik.ingress.svc.cluster.local:80`.

Hostname de producción: `jobs.ramper.lat`, por la misma ruta del túnel a Traefik.
Mantener el login de la aplicación activo; cargar solo datos que se acepta perder, ya que
no existe una ruta de recuperación.
