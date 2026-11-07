# Proposal

## Why

Los dos controles actuales usan listas de opciones y no hacen evidente que el puntaje elegido funciona como un mínimo. Un control deslizante con el valor visible hará más rápido ajustar la preferencia del perfil y el filtro temporal del dashboard.

## What Changes

- Reemplazar el selector persistente del perfil por un control deslizante entero de 0 a 10.
- Reemplazar el filtro temporal del dashboard por un control deslizante entero cuyo mínimo sea el valor guardado en el perfil.
- Aplicar automáticamente el filtro temporal al mover el control, sin botón de confirmación.
- Mostrar junto a cada control el umbral elegido y aclarar que se incluyen vacantes con ese puntaje o uno mayor.
- Mantener clara la diferencia entre el mínimo persistente del perfil y el filtro temporal del listado.
- Permitir teclado y pantallas pequeñas, y conservar el valor temporal al paginar.

## Capabilities

### New Capabilities

### Modified Capabilities

- `preferencias-busqueda-perfil`: permitir ajustar con un control deslizante el mínimo entero persistente de 0 a 10.
- `dashboard-vacantes`: permitir ajustar con un control deslizante el mínimo temporal del listado, sin bajarlo del mínimo del perfil.

## Impact

- Formulario de perfil y control de filtro del dashboard.
- Sin cambios al cálculo de puntajes, la consulta de análisis ni la configuración guardada.
