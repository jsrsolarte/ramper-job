# Guía de trabajo de Ramper Job

## Ramas, staging y producción

- `main` es la rama de liberación para producción. No desplegar ni promover a producción sin autorización explícita del usuario para esa promoción.
- `staging` es la rama fuente de Flux para el entorno compartido de staging.
- Para probar una rama de trabajo sin fusionarla, ejecutar manualmente el workflow `CI and staging image` desde `main` y elegirla en `source_branch`. CI valida el SHA seleccionado, publica su imagen inmutable y actualiza el pin de imagen en la rama `staging`; Flux despliega ese SHA.
- Un push directo a `staging` también pasa CI, publica su imagen y actualiza automáticamente el overlay de staging.
- Staging es compartido: solo una versión/branch se prueba allí a la vez; una nueva prueba reemplaza temporalmente la anterior.
- Después de que el usuario apruebe la prueba, abrir un PR desde la rama probada hacia `main`. Promover el mismo código probado, preservando el SHA o digest cuando sea posible; no reconstruir silenciosamente una versión distinta para producción.
- Un cambio a `main` no autoriza por sí solo una mutación de producción. Respetar siempre la aprobación explícita requerida para la promoción.

## Estado actual de la configuración

- La selección de ramas se hace en GitHub Actions; Flux siempre sigue `staging` y nunca se cambia manualmente a una rama feature.
- Ramper Job todavía no tiene un overlay ni un despliegue de producción. `main` queda reservado para la liberación a producción cuando esa configuración exista.
- Los datos de staging son sintéticos y descartables. No cargar CV reales hasta contar con backups cifrados externos y una restauración probada.
