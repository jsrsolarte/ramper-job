# Design

## Context

Ramper Job ya está desplegado en producción y Flux lo reconcilia desde `main`. Las referencias históricas de SHA, workflow e imagen de este documento pueden estar obsoletas: capturar el estado actual en solo lectura antes de la nueva liberación. Esta tarea valida una actualización de código ya probada en staging, integrada a `main` y desplegada con autorización. La decisión vigente es no respaldar datos de Ramper Job.

## Goals / Non-Goals

**Goals:**
- Identificar la versión ya activa antes de actualizarla.
- Validar el recorrido desde staging hasta la versión integrada en main y su despliegue aprobado en producción.
- Comprobar los servicios productivos y las condiciones de seguridad sin exponer credenciales.
- Dejar comprobable el costo de perder permanentemente todos los datos.

**Non-Goals:**
- Copiar datos desde staging, añadir backups o modificar OmniRoute.
- Cambiar recursos de otras aplicaciones o políticas compartidas del clúster.

## Decisions

### Overlay productivo independiente

`deploy/overlays/prod` ya separa namespace, host, CSRF, OmniRoute y valores de seguridad de staging. La actualización conserva esas diferencias y modifica solo la referencia de imagen mediante Git cuando el workflow de producción recibe una autorización explícita. La versión de código se rastrea por su SHA de `main`; puede construirse una imagen nueva después del merge.

**Alternativa considerada:** reutilizar el overlay de staging o cambiar su namespace. Se descarta porque mezclaría host, credenciales y parámetros y podría interrumpir el entorno que se está usando para validar.

### Flux productivo reconciliado desde main

La aplicación ya tiene una Kustomization activa que reconcilia el overlay desde `main`. El pipeline no modifica el pin al recibir un push normal a `main`: valida y publica primero. Una ejecución manual de promoción compara el código de aplicación de `main` con el candidato fijado en staging; solo con la confirmación explícita escribe el pin en `main` y deja que Flux aplique el cambio.

**Alternativa considerada:** activar Flux al agregar el manifiesto. Se descarta porque Flux intentaría crear recursos antes de que estén las credenciales y podría publicar una aplicación incompleta.

### Verificación de Secrets y acceso existentes

Antes de promover, comprobar únicamente que existan los Secrets esperados por nombre y tipo. Nunca leer, copiar ni versionar sus valores. La cuenta administradora también existe; se valida su acceso sin volver a ejecutar el bootstrap ni crear cuentas adicionales.

**Alternativa considerada:** copiar los Secrets de staging o versionar manifiestos cifrados. Se descarta para mantener aislamiento y no introducir credenciales en Git.

### Datos sin recuperación

No se crean CronJobs ni copias locales o externas. PostgreSQL y CV usan PVC hostpath separados; una pérdida o borrado del nodo/PVC puede eliminar los datos de forma irreversible. El despliegue y la documentación no prometen restauración.

**Alternativa considerada:** esperar un destino de backup. Se descarta porque el usuario decidió operar sin backups.

## Risks / Trade-offs

- [La pérdida del único nodo o de un PVC elimina todos los datos y CV de producción] → Confirmar el riesgo en el runbook; no sugerir que los datos son recuperables.
- [El merge genera otro SHA o el pipeline construye otra imagen] → Verificar la igualdad del código de aplicación entre el candidato de staging y el commit integrado en main, registrando ambos SHA.
- [Un Secret productivo falta o está mal referenciado] → Verificar solo nombres y tipos antes de promover; no leer valores.
- [El acceso público puede exponer errores de configuración de host/CSRF] → Validar host, HTTPS, login, webhooks/OmniRoute y archivos privados antes de invitar cuentas.

## Migration Plan

1. Registrar por lectura la imagen y la revisión de Flux actualmente activas en prod, además del pin de staging.
2. Integrar por PR a `main` el código aprobado en staging y comprobar el pipeline de producción.
3. Tras la autorización explícita, ejecutar la promoción manual; actualizar el pin productivo mediante Git y esperar la reconciliación de Flux.
4. Validar migraciones, salud de web/worker/Beat, login, OmniRoute, aislamiento y privacidad de CV.
5. Verificar nombres/tipos de Secrets y documentar que no hay backups; cerrar el cambio solo si todos los criterios tienen evidencia.

