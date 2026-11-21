# Proposal

## Why

Las personas aspirantes y la administración no pueden saber cuándo se ejecutará el siguiente ciclo automático de búsqueda. Mostrar esa referencia hace más predecible la espera por nuevas vacantes y permite a la administración comunicar el estado real del servicio.

## What Changes

- Mostrar en el dashboard de aspirantes la fecha y hora estimadas del próximo ciclo automático de búsqueda.
- Mostrar la misma información en el centro administrativo, junto con el estado de pausa del procesamiento.
- Aclarar que una actualización manual o un cambio en un perfil puede iniciar una búsqueda antes del siguiente ciclo automático.
- Cuando el procesamiento esté pausado o no haya información suficiente para calcular el horario, mostrar ese estado en lugar de una fecha engañosa.

## Capabilities

### New Capabilities

- `programacion-busquedas`: Consulta del próximo ciclo automático de búsqueda por aspirantes y administración.

### Modified Capabilities

Ninguna.

## Impact

- Afecta la información presentada en `dashboard` y en el centro administrativo de `operations`.
- Depende del intervalo global de actualización ya configurable y del estado global de pausa.
- Requiere una fuente fiable para estimar el siguiente ciclo, sin exponer información operativa privada a las cuentas aspirantes.
