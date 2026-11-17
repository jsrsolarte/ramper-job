# Tasks

## 1. Preparar la separación

- [ ] 1.1 Comparar en una copia Git separada las ramas y workflows remotos vigentes con el árbol local y registrar el plan de transición, evitando reemplazar archivos o cambios ajenos; identificar el workflow antiguo, sus ejecuciones y el pin actual antes de cualquier mutación.
- [ ] 1.2 Separar la validación de PR en un archivo independiente del workflow antiguo, reutilizando pasos comunes cuando sea seguro; verificar que los PR ejecutan pruebas sin publicar ni alterar pines y documentar eventos y permisos.

## 2. Entregar desde staging

- [ ] 2.1 Implementar el pipeline de `staging` desde el SHA del push integrado, retirar la selección manual de otra rama y verificar que los fallos de CI no publican ni actualizan el pin.
- [ ] 2.2 Serializar y proteger el pin ante ejecuciones atrasadas, commits automáticos y cambios concurrentes; probar candidatos fuera de orden, commits solo de pin, avance de la rama y ausencia de bucles, preservando trazabilidad de SHA e imagen.
- [ ] 2.3 Documentar integración en `staging`, despliegue compartido, verificación y reversión por Git; comprobar que los ejemplos corresponden a los triggers y permisos implementados.

## 3. Preparar producción sin promover

- [ ] 3.1 Separar el pipeline de validación y preparación de `main`; probar que un push o PR no modifica el pin, recursos o reconciliación de producción y que ninguna operación productiva ocurre sin autorización explícita.
- [ ] 3.2 Garantizar y probar la vinculación entre candidato probado, código integrado, SHA y digest de la imagen, incluyendo merge con SHA distinto; actualizar la documentación y mantener el workflow de versión compatible sin reconstruir la imagen promovida.

## 4. Verificación integral en staging

- [ ] 4.1 Validar workflows y casos de fallo con pruebas automatizadas y revisar el plan de migración y reversión; comprobar que los overlays y límites entre entornos siguen intactos.
- [ ] 4.2 Habilitar y verificar la validación de PR independiente, desactivar el workflow anterior en GitHub Actions y esperar a que terminen sus ejecuciones activas o en cola; comprobar el estado y el pin antes de activar la entrega nueva, y documentar una reversión que no reactive escritores simultáneos.
- [ ] 4.3 Integrar un candidato sintético en `staging` mediante el flujo autorizado, comprobar ejecución exitosa de CI, imagen inmutable, pin, reconciliación de Flux, disponibilidad y flujo principal; registrar el SHA, el digest y la ruta de reversión, sin mutar producción.
