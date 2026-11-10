# Design

## Context

La imagen validada en staging es `4e110ecca5876488227efc3a520247d86cbbaf4f`; el workflow #56 tuvo éxito y el pin de staging la referencia. No existe despliegue de Ramper Job en prod ni Secrets de la app en ese namespace. El host wildcard `*.ramper.lat` llega a Traefik. Producción es un nodo único sin backups, según la decisión del usuario.

## Goals / Non-Goals

**Goals:**
- Crear configuración prod independiente y usar el artefacto validado en staging.
- Provisionar Secrets y bootstrap administrativo sin exponer credenciales.
- Hacer explícita la pérdida irreversible de datos.

**Non-Goals:**
- Copiar datos de staging, configurar backups, modificar OmniRoute u otras aplicaciones.

## Decisions

### Overlay independiente

Crear `deploy/overlays/prod` con namespace `prod`, host `jobs.ramper.lat`, origen CSRF correspondiente y URL interna `http://omniroute.prod.svc.cluster.local:20128/v1`. Mantener DEBUG desactivado, cookies seguras y redirección HTTPS. Fijar la imagen inmutable ya construida.

### Flux suspendido durante bootstrap

Añadir la fuente de aplicación desde `main` y la Kustomization `./deploy/overlays/prod` como suspendida. Habilitarla solo cuando el overlay esté integrado y los Secrets existan en prod.

### Secrets y cuenta inicial

Crear Secrets propios para Django, PostgreSQL y OmniRoute, además de GHCR read-only cuando no haya un Secret de registry reutilizable. Usar el provisionador interactivo con entrada oculta y temporales en `/dev/shm`. Crear el administrador después de migraciones.

### Datos sin recuperación

No crear CronJobs ni backups locales o externos. PostgreSQL y CV usan PVC hostpath separados; la pérdida del nodo o un PVC puede borrar los datos irreversiblemente.

## Risks / Trade-offs

- Perder el nodo/PVC elimina perfiles, historial y CV → informar y aceptar este riesgo antes de cargar datos reales.
- Faltan Secrets → mantener Flux suspendido.
- Errores de host/CSRF/login → validar el acceso público, OmniRoute y descarga privada de CV antes de invitar usuarios.

## Migration Plan

1. Validar overlay y CI.
2. Preparar PRs de aplicación e infraestructura.
3. Provisionar Secrets interactivos.
4. Promover el mismo SHA/digest probado en staging.
5. Habilitar Flux y validar salud, login, OmniRoute y privacidad de CV.
6. Crear la cuenta inicial e invitar familiares después de validar.
