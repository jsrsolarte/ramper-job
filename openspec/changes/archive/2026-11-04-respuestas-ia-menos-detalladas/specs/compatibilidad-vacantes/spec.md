# Spec Delta

## ADDED Requirements

### Requirement: Solicitar evidencia principal en la explicación del puntaje
El sistema SHALL solicitar al modelo solo las evidencias y razones principales necesarias para sustentar cada criterio, el puntaje y las deducciones, evitando explicaciones secundarias o repetidas sin imponer un límite de longitud.

#### Scenario: Evidencia breve sustenta un criterio
- **WHEN** una evidencia concreta basta para explicar el resultado de un criterio
- **THEN** la respuesta conserva esa evidencia de forma directa sin agregar contexto redundante ni una narración extensa

#### Scenario: Un criterio requiere varios elementos de evidencia
- **WHEN** más de un elemento es necesario para justificar el puntaje o una deducción
- **THEN** la respuesta conserva todos los elementos relevantes y omite detalles que no cambian la justificación

#### Scenario: No hay evidencia suficiente
- **WHEN** el CV no permite confirmar o contradecir un requisito
- **THEN** la respuesta conserva el estado de falta de evidencia sin inventar detalles para completar la explicación

#### Scenario: Se verifica el consumo de salida
- **WHEN** se compara la nueva instrucción con la versión anterior en una muestra representativa de análisis
- **THEN** el formato requerido sigue siendo válido y el consumo medio de tokens de salida disminuye sin pérdida de evidencia necesaria para puntuar
