# Spec Delta

## ADDED Requirements

### Requirement: Descartar recomendaciones inactivas
El sistema SHALL descartar por perfil las recomendaciones que permanezcan pendientes de decisión durante al menos siete días desde su entrada al estado Recomendaciones.

#### Scenario: Recomendación pendiente alcanza siete días
- **WHEN** una recomendación vigente de un perfil lleva siete días o más pendiente de decisión
- **THEN** el sistema la cambia a descartada, conserva pendiente como estado previo y registra la fecha de entrada a descartadas

#### Scenario: Recomendación aún no cumple el plazo
- **WHEN** una recomendación vigente lleva menos de siete días pendiente
- **THEN** el sistema la conserva en Recomendaciones

#### Scenario: La persona avanzó la vacante
- **WHEN** una vacante ya fue aplicada, descartada manualmente, finalizada o avanzó a otra etapa
- **THEN** la tarea automática no cambia su estado

#### Scenario: Dos perfiles tienen estados distintos
- **WHEN** una recomendación compartida cumple siete días para un perfil pero otro perfil tiene un estado distinto
- **THEN** el sistema descarta únicamente el seguimiento del perfil vencido

#### Scenario: La persona restaura un descarte automático
- **WHEN** la persona restaura una recomendación descartada automáticamente
- **THEN** la vacante vuelve a Recomendaciones y los siete días comienzan de nuevo desde esa restauración

#### Scenario: La tarea diaria se repite
- **WHEN** la tarea vuelve a procesar las mismas vacantes
- **THEN** no vuelve a cambiar estados ya descartados ni duplica acciones
