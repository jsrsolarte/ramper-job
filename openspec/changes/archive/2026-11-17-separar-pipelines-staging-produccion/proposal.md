# Proposal

## Why

El flujo actual mezcla la validación de ramas con los pasos de publicación de staging y producción en un mismo workflow. Ejecutar una prueba desde `main` con una rama seleccionada también hace menos evidente cuál es la fuente del entorno de prueba.

## What Changes

- Separar las ejecuciones de validación, entrega a staging y producción con nombres y condiciones claramente identificables.
- Integrar el código candidato en `staging` antes de que el pipeline de esa rama lo valide y despliegue por Git y Flux.
- **BREAKING**: retirar el mecanismo que permite seleccionar una rama de trabajo para desplegarla en staging sin integrarla antes en `staging`.
- Mantener `main` como rama de liberación; su pipeline se activa al integrar el código probado en `staging` y requiere autorización explícita antes de modificar el pin productivo.
- Validar el recorrido completo con una versión: primero staging, después merge a `main`, ejecución del pipeline productivo y despliegue autorizado para comprobar la aplicación en producción.
- Desactivar el workflow anterior y esperar a que terminen sus ejecuciones antes de activar el pipeline nuevo; mantener la validación de PR en un workflow independiente y documentar la reversión.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `despliegue-staging`: usar el código integrado en `staging` como candidato del pipeline y separar la entrega de la preparación de producción.

## Impact

Afecta workflows de GitHub Actions, documentación de despliegue y especificaciones de la aplicación. Flux continúa siguiendo las ramas y overlays existentes; no se requieren cambios en el repositorio de infraestructura ni se autoriza ninguna mutación productiva. La candidata ya preparada para staging deberá integrarse mediante el flujo vigente o el nuevo después de su implementación.
