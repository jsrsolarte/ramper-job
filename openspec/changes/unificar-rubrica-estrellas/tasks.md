# Tasks

## 1. Reconciliar contratos y transición

- [x] 1.1 Revisar las dependencias con `distribucion-puntuaciones-estrellas`, `estadisticas-individuales-usuarios` y las specs afectadas; documentar el orden de integración y verificar que ninguna ruta convierta dos veces.
- [x] 1.2 Diseñar y probar la transición de versiones, trabajos pendientes y rollback con datos sintéticos; conservar los valores originales, el origen y la evidencia sin reclasificar seguimientos ni iniciar llamadas a IA.

## 2. Cálculo y datos históricos

- [x] 2.1 Versionar rúbrica, máximos y deducciones en escala 0–5; probar sumas, límites, estados de evidencia, deducciones y rechazo de respuestas inválidas.
- [x] 2.2 Calcular el resultado final en incrementos de 0,5, redondeando empates hacia arriba solo después de sumar y deducir; probar extremos, decimales y empates como 3,25 → 3,5.
- [x] 2.3 Implementar conversión idempotente y reanudable de análisis históricos 0–10, conservando origen, desglose y evidencia; probar duplicados, históricos, nulos y reinicios sin encolar reanálisis.
- [x] 2.4 Mantener visibles resultados históricos convertidos y procesar correctamente nuevos análisis y trabajos en cola; probar compatibilidad entre versiones de rúbrica y escalas.

## 3. Perfil y estados de vacantes

- [x] 3.1 Migrar mínimos del perfil dividiendo entre dos y redondeando hacia el entero superior; probar 0, 2,5 → 3 y 5, reintentos y preservación de estados existentes y umbrales capturados.
- [x] 3.2 Ofrecer en el perfil solo 0, 1, 2, 3, 4 y 5 estrellas; probar validación, accesibilidad y aplicación a descubrimientos futuros sin reanálisis.
- [x] 3.3 Sustituir filtros por opciones de puntuación exacta disponibles en cada estado antes de paginar, con «Todas»; probar medios, cambios de estado, filtros obsoletos, privacidad y accesibilidad.

## 4. Estadísticas y verificación integral

- [x] 4.1 Adaptar estadísticas globales y privadas, mediana y recomendaciones a la nueva escala, respetando versiones, periodos y muestras; probar históricos y nuevos resultados sin conversión duplicada.
- [x] 4.2 Ejecutar las pruebas relevantes con PostgreSQL y datos sintéticos, incluyendo migración interrumpida, trabajos pendientes y reversión; verificar que no se hacen llamadas externas ni cambian seguimientos.
- [ ] 4.3 Validar en staging con datos sintéticos el perfil, cada estado de vacantes y las estadísticas; documentar el resultado y el plan de recuperación antes de cualquier solicitud de promoción productiva.
