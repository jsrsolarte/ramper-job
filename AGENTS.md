# Guía de trabajo de Ramper Job

## Ramas, staging y producción

- `main` es la rama de liberación para producción. No desplegar ni promover a producción sin autorización explícita del usuario para esa promoción.
- `staging` es la rama de integración y la fuente normal del entorno compartido de staging.
- Se pueden probar ramas de trabajo en staging mediante un despliegue explícito que seleccione una rama o SHA. Staging es compartido: solo una versión/branch se prueba allí a la vez; una nueva prueba reemplaza temporalmente la anterior.
- CI debe validar el código y publicar imágenes inmutables identificadas por SHA o digest. Flux debe aplicar a staging únicamente la referencia seleccionada y conservar el cambio de despliegue auditable en Git.
- Después de que el usuario apruebe la prueba en staging, promover a `main` el mismo código probado. Preferir preservar el SHA o promover el mismo digest; no reconstruir silenciosamente una versión distinta para producción.
- Un cambio a `main` no autoriza por sí solo una mutación de producción. Respetar siempre la aprobación explícita requerida para la promoción.

## Estado actual de la configuración

- Ramper Job tiene configurado el overlay de staging; todavía no tiene un overlay de producción.
- La Kustomization de staging actualmente sigue `main`. Cambiarla para que siga `staging` y habilitar selección explícita de ramas requiere actualizar la configuración de Flux y los workflows; esta guía documenta la política objetivo, no afirma que esos cambios técnicos ya estén aplicados.
- Los datos de staging son sintéticos y descartables. No cargar CV reales hasta contar con backups cifrados externos y una restauración probada.
