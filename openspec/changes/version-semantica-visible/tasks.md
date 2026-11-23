# Tasks

## 1. Version SemVer en staging

- [ ] 1.1 Incrementar `VERSION` de `1.1.0` a `1.1.1` y ajustar el pin de staging para obtener `APP_VERSION` del `VERSION` del SHA candidato, manteniendo el tag de imagen como SHA; verificar ambas variables en la configuración y la ejecución de CI.

## 2. Pie centrado con firma RamPer

- [x] 2.1 Incorporar a los estáticos el lockup claro RamPer v0.6 desde la revisión documentada, registrar su procedencia y limitar su uso al pie; verificar que no se declare como logo aprobado ni se reutilice en otra superficie.
- [ ] 2.2 Componer el pie común con la versión y «By RamPer», centrarlo con la paleta Jobs y asegurar texto alternativo; verificar login y páginas autenticadas a escritorio y móvil, sin recortes ni desbordamiento horizontal.

## 3. Validación de staging

- [ ] 3.1 Desplegar el candidato en staging y comprobar que el pie muestra `1.1.1`, el lockup secundario completo y colores legibles, y que no aparece el SHA en la interfaz.

## Workflow follow-up

- Sincronizar los deltas y archivar el cambio después de la revisión de staging.
- No promover a producción sin autorización explícita.
