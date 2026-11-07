# Tasks

## 1. Confirmar prerrequisitos y alcance

- [x] 1.1 Antes de implementar, confirmar que `analisis-ia-por-etapas`, `rubrica-criterios-criticos-decimales`, `seguimiento-postulaciones` y `vigencia-y-actualizacion-vacantes` estén implementados e integrados; verificar sus requisitos y detener este cambio si falta alguno.
- [x] 1.2 Confirmar que la búsqueda por perfil, las preferencias vigentes y la deduplicación global de vacantes estén disponibles; verificar una consulta y una vacante compartida sin duplicados.

## 2. Compartir consultas equivalentes

- [x] 2.1 Definir y normalizar la identidad de una solicitud por fuente, palabras clave, ubicaciones, modalidad y versiones que afecten la consulta; verificar que criterios equivalentes produzcan la misma identidad y criterios distintos no colisionen.
- [x] 2.2 Agrupar perfiles con solicitudes equivalentes durante ciclos periódicos y ejecuciones manuales; verificar que cada grupo consulte una sola vez por fuente y que grupos distintos conserven búsquedas separadas.
- [x] 2.3 Distribuir cada vacante encontrada a los perfiles que originaron la consulta compartida, revalidando la vigencia de sus perfiles; verificar que un perfil modificado durante la consulta no reciba una asociación basada en criterios obsoletos.

## 3. Mantener evaluación y estados individuales

- [x] 3.1 Encolar o reutilizar un análisis independiente por combinación de perfil y vacante con su revisión y configuración vigentes; verificar resultados distintos para dos perfiles que comparten la publicación.
- [x] 3.2 Preservar el seguimiento individual durante búsquedas compartidas y reprocesamientos; verificar que cambiar el estado de un perfil no cambie el de otro.
- [x] 3.3 Añadir cobertura automatizada para agrupación, deduplicación, cambios concurrentes de perfil y fan-out idempotente; verificar las pruebas del flujo junto con la documentación operativa afectada.

## 4. Integrar antes de stage

- [x] 4.1 Verificar el flujo completo de búsqueda compartida, deduplicación y análisis/seguimiento por perfil con los cambios prerrequisito integrados.
- [ ] 4.2 Antes de cualquier despliegue a stage, confirmar que `busquedas-compartidas-por-perfil` esté completo e integrado en el commit candidato; verificar que la compuerta de despliegue lo incluya.
