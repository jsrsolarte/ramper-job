# Proposal

## Why

La administración necesita incorporar una vacante concreta sin depender de que una búsqueda automática la encuentre. Esa publicación debe entrar al flujo global existente y llegar a cada perfil para el que sea elegible, sin duplicar registros ni mezclar evaluaciones personales.

## What Changes

- Permitir que la persona administradora registre una vacante desde el centro administrativo pegando únicamente su URL pública admitida.
- Deduplicar o actualizar la publicación global usando la identidad de la fuente y la vacante.
- Encolar el análisis por separado para todos los perfiles activos con CV vigente que sean elegibles según sus preferencias.
- Mostrar la vacante y su seguimiento por perfil, conservando puntajes y estados personales independientes.

## Capabilities

### New Capabilities

### Modified Capabilities
- `ingesta-vacantes`: incorporar vacantes desde el centro administrativo y procesarlas en el flujo común global y por perfil.

## Impact

- Interfaz protegida por el centro administrativo y proceso de alta/actualización de publicaciones.
- Deduplicación global, fan-out a análisis por perfil y seguimiento individual.
- Depende del centro administrativo, de la búsqueda compartida y de los flujos vigentes de compatibilidad, rúbrica y seguimiento; debe completarse antes del despliegue a stage.
