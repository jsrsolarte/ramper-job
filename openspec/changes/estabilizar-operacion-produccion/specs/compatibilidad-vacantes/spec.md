# Spec Delta

## ADDED Requirements

### Requirement: Ajustar la salida de requisitos críticos al formato validado
Las instrucciones de análisis SHALL exigir requisitos críticos y evidencia dentro de los límites de texto que acepta el validador, y el sistema SHALL rechazar de forma segura cualquier salida que los exceda.

#### Scenario: El modelo devuelve un requisito crítico válido
- **WHEN** el modelo describe un requisito crítico
- **THEN** el texto del requisito tiene como máximo 180 caracteres, el estado usa un valor admitido y la evidencia tiene como máximo 240 caracteres

#### Scenario: La salida supera el límite de texto
- **WHEN** el requisito crítico o su evidencia exceden el límite
- **THEN** el sistema no guarda un análisis parcial, registra solo la categoría segura de validación y mantiene genérico el mensaje visible a la persona usuaria
