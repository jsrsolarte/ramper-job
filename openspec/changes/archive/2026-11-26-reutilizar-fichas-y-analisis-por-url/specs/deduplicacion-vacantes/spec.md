# Spec Delta

## MODIFIED Requirements

### Requirement: Reconocer una vacante repetida dentro de una bolsa
El sistema SHALL identificar una vacante por bolsa mediante la URL pública de la ficha normalizada sin parámetros ni fragmento, dentro de cada bolsa.

#### Scenario: El mismo identificador aparece con otra URL
- **WHEN** una bolsa entrega nuevamente una URL de ficha que difiere solo en parámetros o fragmento
- **THEN** el sistema reconoce la misma publicación y conserva un único registro

#### Scenario: No hay identificador estable
- **WHEN** dos publicaciones de la misma bolsa tienen URL normalizadas diferentes y datos similares
- **THEN** el sistema no las fusiona solo por título, empresa, ubicación o identificador

#### Scenario: Vacantes de bolsas distintas
- **WHEN** dos bolsas ofrecen vacantes con datos coincidentes
- **THEN** cada bolsa conserva su propio registro
