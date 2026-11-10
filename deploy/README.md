# Despliegue

Los overlays `overlays/staging` y `overlays/prod` son independientes. Flux reconcilia staging
desde su fuente en la rama `staging`. La fuente de producción sigue `main` y su Kustomization
debe permanecer suspendida hasta que el overlay esté en `main` y los Secrets de `prod` estén
disponibles.

## Configuración y secretos

El ConfigMap `ramper-job-config` contiene valores no sensibles. Antes de habilitar Flux debe
existir fuera del repositorio el Secret `ramper-job-secrets`, con estas claves:

- `DJANGO_SECRET_KEY`
- `POSTGRES_PASSWORD`
- `OMNIROUTE_API_KEY`

Además, debe existir el Secret de tipo `kubernetes.io/dockerconfigjson` llamado
`ramper-job-registry`, con credencial GHCR de solo lectura (`read:packages`), para que los
pods puedan descargar el paquete. Se puede reutilizar una credencial existente; el Secret
debe estar en `staging`, porque Kubernetes no permite referenciar Secrets de otra namespace.
No se versiona ningún manifiesto de Secret ni un archivo
`.env`. Para crearlos de forma interactiva, en el servidor con acceso a MicroK8s ejecuta
`python3 scripts/provision_staging_secrets.py` desde el checkout de la app. El script genera
la clave Django y la contraseña PostgreSQL, solicita OmniRoute sin eco y solo solicita GHCR
si no existe `ramper-job-registry` con el tipo esperado. Escribe los temporales solo en
`/dev/shm` con permisos privados y se niega a sobrescribir Secrets existentes. No muestra
ni guarda los valores en el repositorio. El bootstrap de la cuenta administradora es una
operación interactiva única ejecutada dentro del pod web.

En producción, ejecuta `python3 scripts/provision_prod_secrets.py` desde el checkout de la app
en el servidor. El provisionador genera la clave Django y la contraseña PostgreSQL, solicita
OmniRoute sin eco y referencia el Secret `mcp-gateway-ghcr-prod` existente en `prod`. No lee
ni copia sus credenciales; solo comprueba el nombre y tipo del Secret.

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

## Versiones y liberaciones

Las pruebas de staging siguen identificándose por el SHA de la imagen y no reciben una versión de producto. Las liberaciones aprobadas usan etiquetas Git anotadas `vMAJOR.MINOR.PATCH`; la primera versión de producción es `v1.0.0`. La validación rechaza formatos inválidos, ceros iniciales, versiones ya existentes y actualizaciones de una etiqueta publicada.

Incrementa PATCH para correcciones compatibles, MINOR para funcionalidades compatibles y MAJOR para cambios incompatibles que requieren adaptación. El asunto de la etiqueta anotada debe explicar el tipo de incremento y su motivo.

El flujo de liberación solo acepta un commit que esté en `staging` y cuya imagen SHA sea la actualmente fijada en el overlay. Resuelve el digest de esa imagen ya construida y adjunta a la versión un manifiesto con etiqueta, versión, SHA, referencia y digest. No reconstruye la imagen. Crear la versión no despliega por sí solo: Flux productivo obtiene `deploy/overlays/prod` desde `main` y solo lo aplica después de que su Kustomization se habilite mediante Git.

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
