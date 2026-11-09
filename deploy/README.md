# Despliegue

El único overlay previsto en este cambio es `overlays/staging`; no hay manifiestos ni
referencias para producción. Flux debe reconciliarlo en el namespace `staging` después de
que CI publique la imagen del commit aprobado.

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

## Persistencia y alcance de datos

PostgreSQL usa un volumen de 2 GiB y los CV un PVC independiente de 2 GiB. Redis no persiste:
contiene colas reconstruibles. El almacenamiento actual `microk8s-hostpath` reside en el
nodo y no es un backup. Por ahora staging solo debe contener datos sintéticos y descartables;
no cargar perfiles ni CV reales hasta acordar un destino de backup cifrado y probar una
restauración externa. Un restablecimiento completo de datos de prueba puede eliminar los dos
PVC de staging y permitir que StatefulSet/Deployment los creen de nuevo.

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

El flujo de liberación solo acepta un commit que esté en `staging` y cuya imagen SHA sea la actualmente fijada en el overlay. Resuelve el digest de esa imagen ya construida y adjunta a la versión un manifiesto con etiqueta, versión, SHA, referencia y digest. No reconstruye la imagen. La creación de la versión no despliega a producción ni crea un overlay de producción; eso requiere autorización y configuración separadas.

El init container del web ejecuta `migrate --noinput` antes de iniciar Gunicorn. Los init
containers del worker y Beat esperan hasta 15 minutos a que no haya migraciones pendientes;
así no consumen tareas contra un esquema aún incompleto. Las migraciones futuras deben seguir
el patrón expandir/migrar/contraer: primero añadir estructuras compatibles con la imagen
anterior, mover o transformar datos en una etapa reversible y retirar campos antiguos solo
cuando ninguna imagen de rollback los use. El rollback normal cambia por Git la imagen fijada
en el overlay y deja que Flux reconcilie; antes de una migración destructiva que no tolere la
imagen anterior se necesita un backup restaurable y un plan explícito de recuperación.

Hostname de staging: `ramper-job-staging.ramper.lat`. Cloudflare Tunnel debe enrutarlo a
`http://traefik.ingress.svc.cluster.local:80`. Mantener el login de la aplicación activo y
publicar únicamente los datos sintéticos autorizados para pruebas.
