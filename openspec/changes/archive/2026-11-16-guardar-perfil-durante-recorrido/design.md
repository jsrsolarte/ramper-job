# Design

## Context

El middleware del recorrido deja pasar la vista de «Mi perfil» cuando esa es la ruta del paso actual, pero permite únicamente solicitudes `GET`. El formulario envía `POST`; por eso el middleware redirige antes de que la vista pueda validar o guardar los datos. La página ya tiene un guardado normal con redirección de vuelta a «Mi perfil».

## Goals / Non-Goals

**Goals:**
- Permitir la operación de guardado de «Mi perfil» durante el recorrido obligatorio.
- Conservar la validación, persistencia y redirección del formulario existente.
- Mantener el paso obligatorio y la restricción de las demás rutas.

**Non-Goals:**
- Habilitar Recomendaciones u otras funciones antes de completar el recorrido.
- Avanzar o completar automáticamente la guía al guardar el perfil.
- Cambiar los datos que el formulario acepta o el comportamiento normal del guardado fuera del recorrido.

## Decisions

- Ampliar la excepción del middleware para aceptar `GET` y `POST` de la ruta de edición del propio perfil mientras el paso obligatorio actual sea una sección de perfil. Mantener la redirección para cualquier otra ruta o método no permitido.
- Dejar que la vista procese el formulario sin un camino alterno: los datos válidos se guardan y redirigen a «Mi perfil»; los inválidos vuelven a mostrar el formulario con sus errores.
- No modificar el progreso del recorrido al guardar. Después de una redirección exitosa, la interfaz vuelve a consultar el progreso guardado y presenta el mismo paso hasta que la persona elija avanzar.
- Mantener el mismo comportamiento de revisión de perfil y encolamiento de tareas que ya se aplica al guardar cambios válidos fuera del recorrido.

## Risks / Trade-offs

- [Una excepción demasiado amplia podría abrir rutas mientras la guía está obligatoria] → Limitarla a la ruta de edición del propio perfil y al método `POST` que procesa su formulario, conservando la protección para el resto.
- [Un error de validación podría parecer que cerró o reinició la guía] → Mantener el progreso sin cambios y comprobar que el formulario vuelve a renderizar el paso actual.

## Migration Plan

- No requiere migración de datos. El middleware empieza a permitir el guardado durante el recorrido.
- Si se revierte, vuelve el bloqueo actual de solicitudes `POST` durante el recorrido obligatorio.
