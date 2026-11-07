# Proposal

## Why

La plataforma ya requiere herramientas exclusivas de administración para operar métricas, procesos y cuentas, pero esas tareas están repartidas y no existe un centro unificado. Se necesita una sola cuenta administradora que pueda supervisar el sistema y gestionar el acceso de usuarios sin habilitar el auto-registro.

## What Changes

- Definir una única cuenta administradora de la plataforma, con acceso protegido al centro administrativo.
- Reunir en un área administrativa la navegación a los tableros operativos existentes y las herramientas de control.
- Permitir que la persona administradora cree, consulte, desactive y reactive usuarios aspirantes.
- Permitir que el administrador inicie el restablecimiento de contraseña de una cuenta sin conocer ni ver su contraseña nueva.
- Mantener separados los datos privados de usuarios y los datos agregados de operación.

## Capabilities

### New Capabilities

- `acceso-administrativo`: identidad única de administración y acceso a un centro administrativo que integra las vistas internas existentes.
- `gestion-usuarios`: administración de cuentas aspirantes y restablecimiento seguro de acceso.

### Modified Capabilities

- `cuentas-y-perfiles`: conservar el modelo de cuentas administradas y precisar las operaciones administrativas sobre las cuentas existentes.

## Impact

- Autorización y vistas del área administrativa, navegación hacia observabilidad operativa y herramientas de control.
- Modelo/configuración de cuentas para asegurar que exista como máximo una cuenta con rol de administrador.
- Flujos de creación, activación/desactivación y restablecimiento de contraseña para usuarios aspirantes.
