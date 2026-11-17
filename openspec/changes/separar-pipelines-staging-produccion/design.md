# Design

## Context

El workflow actual combina PR, pushes a `main` y `staging`, y ejecución manual con `source_branch`. CI publica una imagen por SHA y una ejecución de staging actualiza su overlay; Flux sigue `staging`. El workflow de versión exige que el commit sea ancestro de `staging` y coincida con el pin. Ver `proposal.md` y la spec para las nuevas reglas.

## Goals / Non-Goals

**Goals:**

- Hacer observable qué ejecución valida, entrega a staging o prepara producción.
- Mantener correspondencia comprobable entre commit, imagen publicada, pin y versión revisada.
- Proteger el pin frente a ejecuciones obsoletas y preservar las diferencias entre staging y prod.

**Non-Goals:**

- Cambiar fuentes Flux, infraestructura compartida, secretos o datos.
- Desplegar, reconciliar o modificar recursos productivos como parte de esta implementación.
- Garantizar que el commit de merge a `main` conserve el mismo SHA que el de staging; la promoción debe usar explícitamente el digest de la imagen ensayada aunque el merge genere otro commit.

## Decisions

### Eventos y responsabilidades separadas

Usar una validación de PR en un archivo de workflow independiente del workflow anterior, una entrega activada por pushes a `staging` y una ejecución separada para `main` y metadatos de liberación. La entrega toma como fuente el SHA del evento de `staging`, no una entrada que seleccione otra rama. La validación puede compartirse mediante un workflow reutilizable cuando ello no cambie su referencia ni permisos. Se retira `workflow_dispatch` con `source_branch` como mecanismo de despliegue. GitHub exige que un workflow manual exista en la rama predeterminada para poder ejecutarlo; la entrega normal aquí no depende de ese evento.

Alternativa: conservar la selección manual de una rama: permite pruebas aisladas, pero contradice la decisión de integrar el candidato en `staging` antes de desplegarlo.

### Pin trazable y concurrencia

La ejecución valida y publica una imagen identificada por el SHA del código del evento. Serializar las escrituras al pin y, tras obtener el turno, consultar la cabeza actual de `staging`. Solo actualizar si no existe un candidato de código posterior; distinguir commits automáticos que solo actualizan el pin de cambios de código y rechazar cualquier situación ambigua. No reconstruir otra versión ni publicar un pin antes de que la validación termine. Evitar bucles por commits automáticos de pin y conservar una ejecución verificable para cada candidato.

### Exclusión del workflow anterior durante la transición

La definición antigua en `main` sigue permitiendo despachos manuales mientras exista y esté habilitada, incluso después de que `staging` adopte una definición nueva. La concurrencia compartida solo serializa escrituras: no impide que una ejecución antigua actualice el pin más tarde. Antes de activar la entrega nueva, deshabilitar el workflow antiguo en GitHub Actions, comprobar su estado remoto y esperar a que todas sus ejecuciones en curso o en cola terminen; si alguna termina actualizando staging, volver a verificar el pin. No reactivar ese workflow durante la transición. Usar archivos de workflow distintos para la validación de PR y la entrega nueva, de manera que la deshabilitación del antiguo no las deshabilite también. La validación independiente debe estar disponible y comprobada antes de desactivar el workflow anterior.

Si no es posible consultar el estado, deshabilitar el workflow o confirmar que no quedan ejecuciones capaces de mover el pin, detener la transición antes de activar la entrega nueva. El cambio de estado de GitHub Actions no modifica por sí mismo prod ni autoriza su promoción. Registrar quién ejecutó la transición, el pin anterior y los resultados; para revertir, desactivar la entrega nueva, esperar sus ejecuciones y solo entonces restablecer el workflow anterior y el pin por Git.

### Promoción separada

El pipeline de `main` valida y prepara información de liberación sin actualizar recursos ni pines productivos. Verificar la relación entre el commit candidato en `staging`, su imagen y digest, y el código integrado en `main`; registrar diferencias de commit originadas por merges sin confundirlas con una imagen nueva. La promoción real requiere autorización explícita y un cambio GitOps revisado que use el digest aprobado. El workflow de versión existente y su requisito de ancestro se mantienen compatibles o se ajustan sin debilitar esas comprobaciones.

## Risks / Trade-offs

- [Un commit posterior llega mientras una ejecución anterior publica] → comprobar la vigencia tras entrar en la sección serializada y no mover el pin si hay un candidato posterior.
- [El commit automático del pin provoca otra ejecución o se confunde con código nuevo] → identificarlo de forma verificable y probar eventos, árbol y comportamiento de token de GitHub Actions.
- [Un merge cambia el SHA aunque conserve el contenido probado] → registrar y validar separadamente commit candidato, código integrado y digest de imagen antes de cualquier promoción.
- [En la transición coexisten workflows nuevos y antiguos] → definir orden de instalación y desactivación, comprobar eventos y evitar que dos pipelines actualicen staging.
- [La suite local no acredita permisos o comportamiento real de GitHub y Flux] → validar una ejecución de prueba controlada en staging después de implementar y observar su SHA, CI, imagen y reconciliación.

## Migration Plan

1. Comparar los workflows y las ramas remotas actuales en una copia Git separada; preparar los workflows nuevos, pruebas y documentación en una rama de trabajo.
2. Habilitar y comprobar una validación de PR independiente; deshabilitar el workflow anterior en GitHub Actions y esperar sus ejecuciones activas o en cola antes de habilitar la entrega nueva. Verificar el estado remoto y el pin en cada frontera; no alterar el flujo productivo ni la infraestructura durante la preparación.
3. Integrar el código candidato en `staging` y observar el pipeline correspondiente, la publicación de imagen y la reconciliación de Flux con datos sintéticos. Si staging compartido se usa para otra prueba, coordinar su sustitución.
4. Si la validación falla, conservar o restaurar mediante Git el pin inmutable anterior. Para volver al workflow anterior, deshabilitar primero la entrega nueva, esperar sus ejecuciones y confirmar que ya no puede escribir el pin; después restaurar el workflow anterior y comprobar la validación de PR. La reversión no autoriza cambios de producción.
5. Tras aprobarse staging, preparar PR a `main`; cualquier promoción productiva es una acción posterior que requiere autorización explícita.
