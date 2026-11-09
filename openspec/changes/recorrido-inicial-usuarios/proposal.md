# Proposal

## Why

Las personas aspirantes necesitan orientación dentro de la aplicación para completar su perfil de búsqueda y entender cómo interpretar y organizar sus resultados. Un recorrido inicial, guardado por cuenta y disponible nuevamente cuando lo necesiten, reduce esa curva de aprendizaje y mantiene la guía al cambiar de dispositivo.

## What Changes

- Añadir un recorrido guiado para cuentas aspirantes, excluyendo las cuentas administradoras.
- Explicar la carga del CV, las frases de búsqueda, las ubicaciones, la preferencia de trabajo remoto y el umbral de descarte automático.
- Guiar a la persona al dashboard y explicar las pestañas de vacantes, las estrellas de compatibilidad, los detalles del análisis y el seguimiento de postulaciones.
- Guardar el paso y el estado del recorrido asociados a la cuenta para continuarlo en otro dispositivo; permitir omitirlo y volver a abrirlo.
- Mantener el recorrido informativo: no modificar el CV, las preferencias, el umbral ni los estados de vacantes por avanzar en la guía.

## Capabilities

### New Capabilities

- `recorrido-inicial`: guía persistente para que las personas aspirantes configuren su perfil y entiendan los resultados y herramientas principales.

### Modified Capabilities

Ninguna. La guía explica comportamientos ya especificados en las capacidades de perfil y dashboard, sin cambiar esos comportamientos.

## Impact

- Interfaz Django de Mi perfil y del dashboard, con pasos anclados a los controles y navegación existentes.
- Persistencia por cuenta para el estado, la versión y el paso actual del recorrido.
- JavaScript y estilos accesibles para mostrar, avanzar, omitir, reanudar y volver a iniciar la guía.
- Vistas y pruebas para asegurar el acceso por rol y el aislamiento del progreso entre cuentas.
