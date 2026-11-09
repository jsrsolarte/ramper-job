# Tasks

## 1. Generar y compartir el enlace desde el admin

- [ ] 1.1 Cambiar la acción de gestión para generar el enlace de la cuenta elegida y mostrarlo una sola vez con opción de copiar; verificar que no se envía correo y que la respuesta está protegida para administración.
- [ ] 1.2 Conservar la auditoría de la solicitud sin registrar URL ni token; verificar eventos de éxito y fallo y revisar que los logs no contienen el enlace.

## 2. Completar el restablecimiento seguro

- [ ] 2.1 Mantener el enlace ligado a la cuenta, con vencimiento configurado y uso único tras actualizar la contraseña; verificar enlace válido, expirado, usado y cuenta inactiva.
- [ ] 2.2 Verificar que el admin nunca ve la contraseña nueva, que una cuenta aspirante no puede generar enlaces para otra persona y que se solicita una nueva generación cuando el enlace ya no sirve.
