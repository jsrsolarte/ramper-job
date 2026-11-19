# Spec Delta

## ADDED Requirements

### Requirement: Reconciliar unidades de ingesta sin heartbeat vigente
La reconciliación SHALL evitar que una ejecución protegida por trabajo durable permanezca activa indefinidamente cuando sus unidades no tienen heartbeat o lease vigente.

#### Scenario: Una unidad pierde su heartbeat antes de agotar reintentos
- **WHEN** una unidad de ingesta permanece en ejecución más de 20 minutos sin heartbeat ni lease vigente y conserva reintentos
- **THEN** la reconciliación invalida el lease vencido y vuelve a encolar la unidad, conservando la ejecución activa solo mientras exista trabajo durable pendiente

#### Scenario: Una unidad agota sus reintentos
- **WHEN** una unidad sin progreso vigente alcanza su límite de intentos
- **THEN** el sistema marca la unidad y la ejecución asociada como fallidas o parciales, registra una categoría segura de interrupción y libera los leases del perfil

#### Scenario: Se observa una ejecución activa antigua
- **WHEN** una ejecución de ingesta supera 20 minutos
- **THEN** permanece activa únicamente si tiene una unidad durable en cola o en ejecución con despacho o heartbeat vigente; en otro caso queda cerrada y visible como interrumpida
