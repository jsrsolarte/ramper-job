# Tasks

## 1. Confirmar dependencias funcionales

- [x] 1.1 Antes de implementar, confirmar que `centro-administracion-plataforma`, `busquedas-compartidas-por-perfil`, `analisis-ia-por-etapas`, `rubrica-criterios-criticos-decimales`, `seguimiento-postulaciones` y `vigencia-y-actualizacion-vacantes` estén implementados e integrados; verificar el estado de OpenSpec y detener este cambio si falta alguno.
- [x] 1.2 Confirmar que la deduplicación global por URL canónica y la elegibilidad por ubicación/modalidad estén disponibles; verificar reutilización de una vacante existente sin duplicarla.

## 2. Registrar y deduplicar vacantes

- [x] 2.1 Añadir el formulario administrativo protegido que recibe únicamente la URL pública admitida; verificar errores de validación y denegación de acceso para cuentas aspirantes.
- [x] 2.2 Canonicalizar la URL y reutilizar o actualizar un registro global existente cuando coincida; verificar que la misma URL no cree dos publicaciones.
- [x] 2.3 Ejecutar el registro como trabajo asíncrono y mostrar si la vacante se creó, se reutilizó o no pudo guardarse; verificar que la respuesta web no espere las llamadas a IA.

## 3. Evaluar por perfil y conservar seguimiento

- [x] 3.1 Encolar una evaluación independiente por cada perfil activo elegible con CV y preferencias vigentes; verificar perfiles incluidos y excluidos por ubicación o modalidad.
- [x] 3.2 Usar las etapas, rúbrica y umbral vigentes de cada perfil y reutilizar la organización de publicación permitida por el flujo común; verificar puntajes distintos para perfiles con CV o preferencias diferentes.
- [x] 3.3 Mantener el estado de seguimiento por perfil y evitar repetir análisis completados cuando el mismo registro se ingresa sin cambios materiales; verificar que los estados de dos perfiles no se afecten entre sí.
- [x] 3.4 Añadir pruebas de autorización, validación, duplicados, fan-out, idempotencia y fallos de cola; documentar la operación administrativa y verificar el comportamiento observable.

## 4. Integrar antes de stage

- [x] 4.1 Verificar de extremo a extremo el registro manual, deduplicación, elegibilidad, análisis por perfil y estados personales con los prerrequisitos integrados.
- [ ] 4.2 Antes de cualquier despliegue a stage, confirmar que `carga-manual-vacantes-admin` esté completo e integrado en el commit candidato; verificar que la compuerta de despliegue lo incluya.
