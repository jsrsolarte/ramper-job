# Tasks

## 1. Esperar el conjunto funcional acordado

- [x] 1.1 Antes de los cambios nuevos de búsqueda y carga manual, confirmar que estén implementados e integrados sus prerrequisitos: `vista-vacantes-por-analizar`, `seguimiento-postulaciones`, `panel-observabilidad-operativa`, `distribucion-umbral-puntajes`, `rubrica-criterios-criticos-decimales`, `deslizadores-filtro-puntaje`, `analisis-ia-por-etapas`, `vigencia-y-actualizacion-vacantes`, `centro-administracion-plataforma`, `portal-comandos-administrativos`, `parametros-operativos-admin` y `estadisticas-globales-administracion`; verificar el estado de OpenSpec y detener el flujo si falta alguno.
- [x] 1.2 Después de sus prerrequisitos, completar e integrar `busquedas-compartidas-por-perfil`; verificar una consulta compartida con análisis y seguimiento independientes por perfil.
- [x] 1.3 Después de `centro-administracion-plataforma`, `busquedas-compartidas-por-perfil` y los prerrequisitos de análisis y seguimiento, completar e integrar `carga-manual-vacantes-admin`; verificar deduplicación y evaluación independiente para todos los perfiles elegibles.
- [x] 1.4 Después de `carga-manual-vacantes-admin`, completar e integrar `vacante-desde-url-admin`; verificar extracción de El Empleo desde una URL sola, deduplicación y evaluaciones por perfil.
- [x] 1.5 Después de `seguimiento-postulaciones`, completar e integrar `fechas-relativas-vacantes`; verificar publicación, análisis y entrada a estados con sus fechas respectivas.
- [x] 1.6 Después de `fechas-relativas-vacantes`, completar e integrar `descarte-automatico-recomendaciones`; verificar el descarte diario a los siete días por perfil.
- [x] 1.7 Después de `fechas-relativas-vacantes` y `descarte-automatico-recomendaciones`, completar e integrar `limpieza-estados-inactivos`; verificar el archivado lógico a los 30 días sin cambio de estado.
- [x] 1.8 Después de `seguimiento-postulaciones`, `rubrica-criterios-criticos-decimales`, `analisis-ia-por-etapas` y `fechas-relativas-vacantes`, completar e integrar `ordenar-vacantes-por-puntaje`; verificar Recomendaciones por puntaje descendente y demás estados por fecha de entrada descendente.
- [x] 1.9 Después de `rubrica-criterios-criticos-decimales` y `ordenar-vacantes-por-puntaje`, completar e integrar `puntaje-en-estrellas`; verificar la presentación en tarjetas, filtro temporal y mínimo persistente, manteniendo el puntaje exacto para filtrar y ordenar.
- [x] 1.10 Después de `seguimiento-postulaciones` y `deslizadores-filtro-puntaje`, completar e integrar `paginacion-numerada-vacantes`; verificar saltos directos, conservación de pestaña y filtros, accesibilidad y presentación compacta en listados extensos.
- [x] 1.11 Después de `analisis-ia-por-etapas` y `rubrica-criterios-criticos-decimales`, completar e integrar `respuestas-ia-menos-detalladas`; verificar que las salidas conservan campos y evidencias necesarios y reducen el promedio de tokens de salida en ambas etapas.
- [x] 1.12 Después de `descarte-automatico-recomendaciones`, `limpieza-estados-inactivos` y `parametros-operativos-admin`, completar e integrar `plazos-retencion-configurables`; verificar ambos defaults, cambios desde el admin, auditoría y aplicación en el siguiente ciclo diario.
- [x] 1.13 Después de `puntaje-en-estrellas`, completar e integrar `estrellas-sin-puntaje-numerico-visible`; verificar que las tarjetas muestran estrellas sin fracción visible y mantienen la nota exacta accesible.
- [x] 1.14 Antes de construir imágenes o desplegar, confirmar que las funcionalidades anteriores y los doce cambios nuevos estén completos en OpenSpec e integrados en el commit candidato; verificar el estado y detener el flujo si falta alguno.

## 2. Preparar la aplicación y CI

- [x] 2.1 Crear o vincular el repositorio remoto de la aplicación en GitHub y publicar el commit candidato; verificar propietario, nombre, remoto configurado, acceso de CI y que no se publique ningún secreto ni archivo `.env` real.
- [x] 2.2 Crear un `Dockerfile` de runtime seguro que instale dependencias, prepare archivos estáticos, use un usuario sin privilegios y permita iniciar web, worker y Beat por separado; verificar la construcción local y el cierre ordenado de cada proceso.
- [x] 2.3 Añadir endpoints de salud/disponibilidad y configuración de producción para `DEBUG`, hosts, CSRF, cookies y archivos privados; verificar respuestas de salud con la configuración de staging y denegación de acceso anónimo a CV.
- [x] 2.4 Añadir GitHub Actions para ejecutar las validaciones existentes y publicar en GHCR una imagen por SHA/digest solo cuando las validaciones pasen; verificar que un fallo no publica imagen y que no se usa `latest`.
- [x] 2.5 Añadir un comando de bootstrap de uso único que solicite la contraseña con entrada interactiva oculta, cree la cuenta administradora solo si no existe y no imprima credenciales; verificar que una segunda ejecución rechace crear otro administrador y que la contraseña no aparezca en argumentos ni logs.
- [ ] 2.6 Ejecutar CI en `main` y `staging`, y añadir un `workflow_dispatch` que pruebe una rama del mismo repositorio; publicar la imagen por SHA solo después de CI exitoso y actualizar el pin de staging con el SHA validado.

## 3. Crear recursos y persistencia aislados de staging

- [x] 3.1 Crear `deploy/base` y `deploy/overlays/staging` para web, worker, Beat, PostgreSQL y Redis con Services internos, probes, requests/limits y namespace explícito; verificar el render de Kustomize y ausencia de recursos de producción.
- [ ] 3.2 Configurar volúmenes separados para PostgreSQL y CV, mantener Redis reconstruible y documentar backup externo y restauración; verificar un respaldo y restauración de prueba antes de conservar datos necesarios.
- [x] 3.3 Referenciar configuración no secreta desde ConfigMaps y credenciales desde Secrets externos a Git; verificar que manifiestos, logs, historial de shell y artefactos de imagen no contienen secretos ni datos reales de producción.
- [ ] 3.4 Añadir la ejecución controlada de migraciones antes de marcar web lista y documentar compatibilidad hacia atrás; verificar migración aplicada y ruta de reversión a la imagen anterior sin pérdida de datos.

## 4. Coordinar registro de Flux staging

- [x] 4.1 Consultar al administrador del servidor el hostname disponible, capacidad/cuotas, clase y tamaño de almacenamiento, ruta de Ingress y mecanismo de secretos; verificar que los valores acordados están documentados sin exponer credenciales.
- [x] 4.2 Coordinar con el hilo `Gestiona y despliega ramper-job` la creación en el repositorio de infraestructura de la fuente Git y Kustomization que apuntan al repositorio y overlay reales de staging; verificar referencia de rama/ruta y que no se modificaron recursos ni reconciliación de producción.
- [x] 4.3 Validar el overlay renderizado, referencias de imagen inmutable, namespace, recursos, Ingress y referencias a Secrets antes de publicarlo; verificar que no se aplican cambios directamente con `kubectl`.
- [ ] 4.4 Crear la rama `staging` desde el commit de liberación actual y cambiar únicamente el `GitRepository` de Ramper Job en staging para observar esa rama; verificar que prod permanece sin overlay ni reconciliación.

## 5. Desplegar y validar staging

- [ ] 5.1 Provisionar fuera de Git los Secrets de staging antes de activar Flux; mientras no exista backup externo probado, mantener el entorno limitado a datos sintéticos y descartables. Verificar nombres y disponibilidad sin leer valores secretos.
- [ ] 5.2 Publicar la imagen del commit funcional aprobado, actualizar el overlay de staging con su SHA/digest y dejar que Flux lo reconcilie; verificar commit, imagen, namespace y estado de reconciliación.
- [ ] 5.3 Después de aplicar migraciones, ejecutar una vez el bootstrap interactivo de administración con contraseña oculta; verificar inicio de sesión, existencia de un solo administrador y ausencia de la contraseña en logs/manifiestos.
- [ ] 5.4 Verificar disponibilidad de web, worker y Beat, logs saneados, salud del Ingress y acceso al hostname acordado; registrar el resultado observable de cada proceso.
- [ ] 5.5 Recorrer con una cuenta administradora y cuentas de prueba el centro administrativo, dashboard y funciones incluidas en el conjunto funcional; verificar tareas asíncronas y que los CV no sean accesibles sin autorización.
- [ ] 5.6 Si la versión no supera las verificaciones, revertir por Git la referencia de staging a la imagen compatible anterior y dejar que Flux reconcilie; verificar recuperación de salud y que producción no tuvo cambios.
- [ ] 5.7 Ejecutar el workflow de selección con una rama candidata, verificar CI, SHA de imagen, pin en la rama `staging`, reconciliación Ready de Flux y salud del flujo; luego promover el mismo cambio a `main` solo tras aprobación.
