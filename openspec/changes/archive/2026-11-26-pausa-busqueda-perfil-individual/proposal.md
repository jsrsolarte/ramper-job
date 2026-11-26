# Proposal

## Why

Hoy las búsquedas automáticas incluyen todos los perfiles con cuenta activa y CV, sin un control para pausar solo uno. La persona administradora cargó su propio CV para probar la plataforma y necesita detener las búsquedas de ese perfil sin desactivar su cuenta ni perder acceso al perfil y sus resultados.

## What Changes

- Añadir en «Mi perfil» un control independiente para habilitar o pausar la búsqueda automática de ese perfil.
- Mantener habilitada la búsqueda por defecto en perfiles actuales y nuevos.
- Excluir perfiles pausados de consultas automáticas propias y de la asociación de resultados obtenidos por búsquedas compartidas.
- Al reanudar, volver a incluir el perfil en el siguiente ciclo normal sin lanzar una búsqueda inmediata.
- Mantener la cuenta, el CV, las preferencias, los resultados existentes y el análisis de vacantes existentes o ingresadas manualmente.
- Mantener el control operativo global como mecanismo separado para pausar toda la plataforma.

## Capabilities

### New Capabilities

### Modified Capabilities
- `preferencias-busqueda-perfil`: permitir que cada persona pause la búsqueda automática de su propio perfil.
- `busqueda-por-perfil`: respetar la pausa individual al programar y compartir resultados de búsquedas.

## Impact

- Formulario de Mi perfil y estado persistente de búsqueda por perfil.
- Ciclos periódicos, actualizaciones de perfil y agrupación de búsquedas equivalentes.
- Procesamiento de vacantes existentes y registro manual de vacantes, que se mantienen habilitados para el perfil pausado.
