# Design

## Context

Ver `proposal.md` y las specs para el alcance. La capacidad existente `cuentas-y-perfiles` prohíbe el auto-registro y mantiene creación/desactivación de cuentas por administración. El cambio de observabilidad ya define un tablero protegido para métricas agregadas de ingesta y análisis; el centro administrativo debe integrarlo, no copiar sus consultas o controles.

## Goals / Non-Goals

**Goals:**
- Hacer que la autorización administrativa sea consistente para páginas y endpoints.
- Evitar que una operación ordinaria cree accidentalmente una segunda cuenta administradora.
- Unificar la navegación administrativa conservando los tableros operativos como capacidades separadas.
- Asegurar que el restablecimiento nunca exponga contraseñas ni debilite el aislamiento entre usuarios.

**Non-Goals:**
- Añadir auto-registro, roles administrativos múltiples o delegación de permisos.
- Cambiar las métricas y políticas de retención del tablero de observabilidad.
- Permitir que administración lea CV, contraseñas, tokens de sesión o perfiles completos desde la gestión de usuarios.

## Decisions

### Modelar administración como un rol único

Usar la autorización existente de Django como fuente para reconocer la cuenta administrativa y añadir una restricción que permita como máximo una cuenta con ese rol. El primer administrador se provisiona por un procedimiento de instalación/configuración controlado fuera del registro público. Los formularios de gestión de usuarios crean solo cuentas aspirantes. El chequeo debe operar también bajo concurrencia para que dos solicitudes no puedan asignar el rol a la vez.

**Alternativa considerada:** permitir cualquier cuenta staff o superusuario como administrador del producto. Se descarta porque contradice el requisito de una sola persona administradora y podría abrir rutas administrativas técnicas no destinadas a la gestión diaria.

### Crear un centro de navegación que reutiliza pantallas

El centro muestra enlaces a observabilidad y gestión de usuarios, además de herramientas administrativas futuras. Los endpoints internos validan permisos por solicitud; ocultar un enlace no sustituye la autorización. Las métricas continúan bajo la capability de observabilidad y se consultan desde su implementación.

**Alternativa considerada:** copiar las métricas al panel nuevo. Se descarta para evitar cálculos divergentes y duplicación de instrumentación.

### Mantener contraseñas fuera del alcance de administración

La acción de restablecer inicia un mecanismo de recuperación de un solo uso y con vencimiento, enviado por el canal seguro configurado para la cuenta. La interfaz no acepta ni muestra la nueva contraseña. El estado de entrega debe ser visible sin mostrar el token. Si el entorno no tiene el canal configurado, no debe habilitarse un flujo que revele el secreto a administración.

**Alternativa considerada:** permitir que el administrador establezca y copie una contraseña temporal. Se descarta porque expone credenciales y fomenta su reutilización.

### Preservar cuentas y datos al desactivar

Desactivar impide nuevos accesos sin eliminar perfil, CV, análisis o seguimiento. Reactivar restituye el acceso a la misma cuenta. Registrar acciones administrativas de activación y recuperación con actor y fecha, sin secretos.

**Alternativa considerada:** borrar cuentas al retirarlas. Se descarta porque pierde el historial y puede romper referencias de análisis.

## Risks / Trade-offs

- [Una cuenta única puede bloquear operaciones si se pierde el acceso] → Provisionar un procedimiento documentado de recuperación operacional fuera del portal, con acceso controlado y sin habilitar un segundo administrador cotidiano.
- [El canal de recuperación puede no estar configurado en staging] → Verificar su entrega antes de habilitar la función y mostrar un error seguro si el servicio falla.
- [Permisos heredados de Django podrían abrir administración técnica amplia] → Revisar rutas administrativas completas y aplicar la política del producto de forma central y explícita.
- [Un centro nuevo puede duplicar enlaces existentes] → Mantener una sola navegación canónica y reutilizar pantallas operativas.

## Migration Plan

1. Auditar las cuentas existentes y confirmar cuál debe conservar el rol administrativo único antes de aplicar la restricción.
2. Añadir/validar la unicidad del rol y provisionar el administrador inicial mediante configuración controlada, sin incluir credenciales en Git.
3. Incorporar el centro de navegación y aplicar autorización a vistas y endpoints; enlazar el tablero operativo ya planificado.
4. Añadir gestión de usuarios, reactivación y restablecimiento con el canal seguro configurado.
5. Verificar acceso de administrador, denegación para aspirantes, aislamiento de datos y recuperación de cuenta antes de habilitarlo en staging.

## Open Questions

Ninguna. La entrega del restablecimiento depende de configurar un canal seguro para las cuentas, requisito operativo previo a habilitar esa acción.
