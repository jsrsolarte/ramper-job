# Tasks

## 1. Separar resultados de listado y fichas detalladas

- [x] 1.1 Separar en los conectores la lectura de títulos y URLs de la consulta de detalles; verificar con pruebas de conector que las vacantes descartadas no generan solicitudes a fichas y las conservadas sí.
- [x] 1.2 Mantener el registro directo por URL fuera del nuevo flujo por fases; verificar que la extracción manual sigue consultando y normalizando la ficha completa.

## 2. Crear la clasificación conservadora por lotes

- [x] 2.1 Implementar una llamada por lote con títulos, identificadores y términos de búsqueda compartidos, sin CV ni descripciones; verificar formato de salida y ausencia de otros datos de perfil en pruebas del cliente.
- [x] 2.2 Validar cada decisión por identificador y conservar títulos dudosos, ausentes o malformados; verificar escenarios de respuesta parcial, duplicada, inválida y caída del servicio.

## 3. Integrar el filtro en los flujos de búsqueda

- [x] 3.1 Aplicar el filtro antes de fichas detalladas en actualizaciones periódicas y manuales agrupadas, usando una decisión por solicitud equivalente; verificar distribución a todos los perfiles del grupo y separación entre grupos distintos.
- [x] 3.2 Aplicar el mismo flujo a actualizaciones activadas por cambios de perfil; verificar que perfiles individuales reciben el comportamiento y los fallbacks esperados.

## 4. Medir calidad y ahorro

- [ ] 4.1 Comparar en una muestra representativa títulos conservados y descartados, falsos descartes, consultas a fichas y tokens de análisis frente al flujo actual; verificar que el ahorro no depende de descartar vacantes ambiguas.
