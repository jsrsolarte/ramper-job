# Proposal

## Why

Ramper Job necesita conexión para consultar y guardar información. Una interrupción puede dejar a la persona sin saber si sus cambios llegaron al servidor.

## What Changes

- Detectar cuando el navegador pierde conexión o no puede alcanzar el servicio e informar el estado sin interrumpir la pantalla.
- Informar cuándo se recupera el acceso y permitir reintentar, sin asegurar que se guardó una operación de resultado incierto.
- Conservar lo que sea posible de formularios abiertos y evitar envíos automáticos duplicados.
- No implementar funcionamiento sin conexión, almacenamiento de datos privados ni sincronización posterior.

## Capabilities

### New Capabilities

- `estado-conexion`: comunicación de la pérdida y recuperación de acceso al servicio y del resultado incierto de operaciones.

### Modified Capabilities

## Impact

- Plantilla común, cliente web y un mecanismo de comprobación ligero; pruebas de navegación y formularios.
- Independiente de `instalar-aplicacion-chrome`; aplica también al sitio abierto en una pestaña.
