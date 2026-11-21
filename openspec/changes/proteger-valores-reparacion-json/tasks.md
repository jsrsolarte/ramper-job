# Tasks

## 1. Integridad de la reparación

- [x] 1.1 Sustituir las transformaciones globales por comprobación consciente de cadenas y escapes, o rechazo conservador; verificar con pruebas que solo se corrige sintaxis fuera de literales.
- [x] 1.2 Añadir regresión para `texto, } y más`, aceptación del valor intacto y rechazo de modificaciones de claves, valores y tipos; ejecutar las pruebas de `matching` pertinentes.
- [x] 1.3 Cubrir comillas y barras escapadas, Unicode, arreglos y objetos anidados, claves duplicadas y entrada ambigua; verificar rechazo seguro y ausencia de datos privados en logs.

## 2. Integración

- [x] 2.1 Verificar con respuestas sintéticas que puntuación y organización nunca guardan evidencia alterada, conservan recuperación y aceptan reparaciones inequívocas; ejecutar las pruebas de integración pertinentes.
- [x] 2.2 Validar en staging con datos sintéticos el flujo completo y la normalización Markdown; registrar resultados para revisión antes de cualquier promoción autorizada a producción.
