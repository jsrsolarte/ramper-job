# Tasks

## 1. Extracción de fichas de Elempleo

- [x] 1.1 Ampliar el conector para consultar una sola vez cada ficha pública después de deduplicar resultados y extraer JSON-LD y campos visibles; verificar con una ficha representativa que obtiene salario, ciudad, dirección, modalidad, contrato, formación, experiencia, área, horario y cantidad de vacantes.
- [x] 1.2 Hacer tolerante la consulta de fichas con timeout, pausa entre solicitudes y fallback a los datos del listado; verificar que una ficha inaccesible no interrumpe el lote ni borra datos previos.
- [x] 1.3 Añadir pruebas del parser con los datos de la ficha de referencia y documentar cómo se incorporan fixtures cuando Elempleo cambie su estructura; verificar casos con campos ausentes y etiquetas distintas.

## 2. Normalización y persistencia

- [x] 2.1 Proyectar salario, ubicación y contrato de la ficha en los campos comunes, preservando rango del listado, valor salarial original y periodicidad en `raw_data.details`; verificar que el ejemplo conserva `$4 a $4,5 millones` y `$4.214.000 pagos mensuales` por separado.
- [x] 2.2 Guardar ciudad, dirección/zona, modalidad y demás condiciones en un objeto estructurado versionado, sin sobrescribir con valores vacíos; verificar persistencia y compatibilidad de vacantes que solo tengan datos de listado.
- [x] 2.3 Actualizar el análisis de vacante para recibir la descripción completa y los detalles estructurados, y reprogramarlo solo ante cambios materiales; verificar que datos sin cambios no generan llamadas repetidas a OmniRoute.

## 3. Compatibilidad geográfica por perfil

- [x] 3.1 Aplicar la elegibilidad geográfica del perfil antes de programar análisis, usando la ciudad real de la ficha y los grupos de cercanía ya configurados; verificar que Bogotá se excluye para Medellín/Envigado y que los municipios cercanos aceptados pasan.
- [x] 3.2 Respetar la preferencia de trabajo remoto y tratar como desconocidas las ubicaciones no publicadas; verificar perfiles con remoto habilitado/deshabilitado y que la ciudad de búsqueda nunca se asigne como ubicación real.
- [x] 3.3 Ocultar análisis existentes que contradigan la ubicación actualizada sin borrar vacantes compartidas; verificar que otra persona del grupo familiar todavía puede recibir la misma vacante si es compatible.

## 4. Presentación y verificación integrada

- [x] 4.1 Mostrar en el dashboard ciudad, modalidad, dirección/zona, salario y contrato, con formación, experiencia y horario en una sección compacta; verificar que se omiten los campos vacíos y que no se presenta la descripción completa en la tarjeta.
- [x] 4.2 Guardar las categorías estructuradas devueltas por IA y mostrar hasta cinco palabras clave breves de la descripción en cada tarjeta.
- [x] 4.3 Ejecutar las pruebas del conector, normalización, elegibilidad geográfica y vistas, y revisar el flujo local con la ficha de referencia; verificar que una oferta presencial de Bogotá no aparece para el perfil de Medellín/Envigado y que la oferta compatible muestra sus condiciones completas y palabras clave.
