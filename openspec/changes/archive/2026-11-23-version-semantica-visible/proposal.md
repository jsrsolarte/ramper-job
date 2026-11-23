# Proposal

## Why

En staging, el pie de página muestra el SHA completo del commit, que no comunica una versión de producto y resulta visualmente difícil de leer. El pie también necesita una composición centrada y una firma secundaria de RamPer que mantenga a Jobs como identidad principal.

## What Changes

- Mostrar en todos los entornos la versión SemVer del archivo `VERSION` incluido en el artefacto; el SHA seguirá siendo metadato técnico y no aparecerá en la interfaz.
- Centrar el pie común, integrarlo con la paleta de Jobs y asegurar una presentación adaptable y legible.
- Añadir «By» y el lockup RamPer v0.6 como firma secundaria exclusiva de este pie. Mantener el recurso identificado como exploración, sin promoverlo a logo aprobado ni reutilizarlo en otras superficies.
- Incrementar la versión de parche canónica de `1.1.0` a `1.1.1` para este cambio compatible.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `versionado-liberaciones`: usar y mostrar la versión SemVer del código en staging y producción, sin mostrar el SHA en la interfaz.
- `interfaz-usuario`: definir la composición centrada, adaptable y con firma secundaria del pie de página común.

## Impact

Afecta el contexto de versión, el workflow y la configuración de despliegue de staging, el archivo `VERSION`, las plantillas compartidas y de login, los estilos del pie y una copia versionada del lockup RamPer v0.6. Requiere pruebas de renderizado, versión ausente y adaptación móvil.
