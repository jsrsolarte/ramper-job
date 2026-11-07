# Tasks

## 1. Agregar estadísticas de estados

- [x] 1.1 Implementar conteos actuales por estado de seguimiento usando relaciones perfil-vacante y por disponibilidad usando publicaciones únicas; verificar que ambos conjuntos tengan denominadores y fecha de corte correctos.
- [x] 1.2 Mostrar en el panel los conteos de pendiente, descartada, aplicada, en proceso, entrevista y finalizada, además de activa, cerrada y desconocida, en vistas separadas; verificar estados vacíos y vacantes de varios perfiles.

## 2. Agregar distribución de puntuaciones

- [x] 2.1 Implementar agregación de puntajes vigentes por perfil-vacante y por versión de rúbrica, excluyendo resultados reemplazados; verificar que no se dupliquen reanálisis ni se mezclen versiones.
- [x] 2.2 Mostrar distribución por intervalos, mediana decimal, tamaño de muestra y periodos disponibles; verificar puntajes decimales, intervalos de borde y periodos sin datos.
- [x] 2.3 Indicar inicio de cobertura y no presentar como cero los datos anteriores a la instrumentación; verificar consultas sobre intervalos previos y posteriores a esa fecha.

## 3. Integrar las estadísticas y proteger privacidad

- [x] 3.1 Añadir la vista de estadísticas globales al centro administrativo sin duplicar los paneles de observabilidad ni la distribución individual; verificar navegación y separación de métricas.
- [x] 3.2 Proteger datos y consultas para que solo administración vea agregados y no haya enlaces ni identificadores individuales; verificar denegación a aspirantes y ausencia de CV, perfiles, prompts o vacantes identificables en las respuestas.

## 4. Verificación integrada

- [x] 4.1 Comparar agregaciones con conjuntos sintéticos que incluyan varios perfiles por vacante, cambios de estado, publicaciones cerradas y múltiples rúbricas; verificar conteos esperados y privacidad en el panel.
  - Verificación local: 14 pruebas cubren estados por perfil-vacante, disponibilidad activa/cerrada/desconocida, deduplicación, varias rúbricas, puntajes decimales, periodo y cobertura, ausencia de datos identificables y denegación a aspirantes.
