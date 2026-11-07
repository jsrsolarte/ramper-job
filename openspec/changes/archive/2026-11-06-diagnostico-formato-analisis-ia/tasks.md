# Tasks

## 1. Registrar causas de validación sin datos sensibles

- [x] 1.1 Asignar códigos estables y controlados a los rechazos de estructura y reglas de rúbrica; añadir pruebas que distingan sus causas y confirmen que no incorporan valores de la respuesta.
- [x] 1.2 Propagar los códigos a `AICallAttempt.error_category` y conservar el mensaje genérico del análisis; probar que errores de JSON y de validación de rúbrica quedan diferenciados.

## 2. Presentar diagnósticos en métricas administrativas

- [x] 2.1 Agregar intentos fallidos de puntuación por categoría segura dentro del periodo elegido; probar conteos, filtros por etapa/resultado y compatibilidad con intentos históricos genéricos.
- [x] 2.2 Mostrar el desglose de categorías en el panel administrativo, conservar la restricción de acceso y documentar los códigos; probar acceso denegado a aspirantes, etiquetas y estado sin datos.

## 3. Verificar el flujo completo

- [x] 3.1 Ejecutar las pruebas de validación, análisis y métricas; comprobar que el rechazo mantiene el análisis pendiente, el mensaje al aspirante es genérico y la telemetría solo expone códigos controlados.
