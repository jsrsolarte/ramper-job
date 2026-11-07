# Tasks

## 1. Definir el acceso administrativo único

- [x] 1.1 Auditar cuentas y permisos existentes y documentar cuál cuenta conservará el acceso administrativo; verificar que el cambio no bloquee el acceso de los usuarios aspirantes.
  - Auditoría local de solo lectura: se conserva la cuenta superusuario de ID interno 1, activa y con acceso staff. Hay 1 cuenta staff, 0 cuentas staff sin superusuario y 1 aspirante activo; no se modificaron cuentas aspirantes ni credenciales.
- [x] 1.2 Aplicar la regla de una sola cuenta administradora y documentar el aprovisionamiento inicial fuera del registro público; verificar que asignaciones concurrentes o una segunda asignación sean rechazadas.
- [x] 1.3 Centralizar autorización para páginas y endpoints administrativos; verificar que la cuenta administradora acceda y que aspirantes reciban denegación sin filtrar datos.

## 2. Construir el centro de administración

- [x] 2.1 Crear la navegación administrativa con entradas a observabilidad, gestión de usuarios y herramientas administrativas; verificar que enlaces y páginas requieran autorización en servidor.
- [x] 2.2 Integrar el tablero de observabilidad existente por navegación compartida sin duplicar sus consultas o métricas; verificar acceso desde el centro y conservación de su autorización.

## 3. Gestionar cuentas y recuperación

- [x] 3.1 Implementar listado de cuentas aspirantes y acciones de crear, desactivar y reactivar preservando sus datos; verificar permisos, inicio de sesión y persistencia del historial.
- [x] 3.2 Implementar restablecimiento de contraseña de un solo uso y vencimiento por el canal seguro configurado; verificar que no se expongan contraseñas ni tokens, y que un token vencido o reutilizado falle.
- [x] 3.3 Registrar actor y fecha de las acciones administrativas sin datos sensibles; verificar trazabilidad para creación, cambios de estado y solicitudes de recuperación.

## 4. Verificación integrada

- [x] 4.1 Ejecutar validaciones de autenticación, autorización, gestión y recuperación, y recorrer el centro con cuenta admin y aspirante; verificar que solo exista un administrador y que cada flujo mantenga el aislamiento de datos.
  - Verificación local: 35 pruebas de autenticación, autorización operativa, gestión de cuentas y recuperación pasaron; la cobertura confirma un solo superusuario, acceso al centro para admin, denegación para aspirantes, conservación del perfil al desactivar/reactivar y enlace de recuperación de un solo uso con vencimiento.
