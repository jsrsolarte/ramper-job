# Tasks

## 1. Interpretación y esquema

- [x] 1.1 Implementar interpretación de JSON directo y bloque completo inequívoco con límites; verificar con pruebas de v2/v3 que un bloque válido no provoca otra llamada, y cubrir etiquetas, texto externo, múltiples bloques y objetos inválidos.
- [x] 1.2 Definir esquemas versionados de puntuación y organización y solicitar salida estructurada con alternativa acotada ante incompatibilidad explícita; verificar solicitudes, rechazos y ausencia de fallback ante timeout o autenticación.

## 2. Reparación y recuperación

- [x] 2.1 Implementar una única llamada de reparación cuando el contenido siga siendo sintácticamente inválido tras la normalización local, sin contexto adicional de evaluación y con comparación conservadora de valores; verificar preservación, alteración, ambigüedad y límite de llamadas con datos sintéticos.
- [x] 2.2 Integrar validadores y recuperación durable existentes para puntuación y organización; verificar que errores semánticos no disparan reparación, que no se guarda puntaje parcial y que se conserva el vencimiento.

## 3. Observabilidad y privacidad

- [x] 3.1 Registrar normalización y llamadas de reparación por etapa, resultado, duración y tokens disponibles; verificar agregados, migraciones y compatibilidad con historial.
- [x] 3.2 Documentar categorías y límites de privacidad; verificar con datos centinela que logs, errores y métricas no contienen respuestas, CV, prompts ni vacantes.

## 4. Integración

- [ ] 4.1 Verificar en staging con datos sintéticos los flujos v2 y v3, organización, compatibilidad de esquema, errores de proveedor y recuperación; registrar evidencia, costo y comportamiento de la cola antes de solicitar promoción.
