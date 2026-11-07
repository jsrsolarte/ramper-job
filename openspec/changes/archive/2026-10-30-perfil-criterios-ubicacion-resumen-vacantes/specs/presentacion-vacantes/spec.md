# Spec Delta

## Purpose

Presenta las vacantes en un formato breve y comparable, separando el propósito del cargo, sus responsabilidades, requisitos y condiciones relevantes.

## ADDED Requirements

### Requirement: Organizar la información de la vacante
El sistema SHALL mostrar una síntesis estructurada de la publicación con resumen, responsabilidades, requisitos y condiciones, omitiendo las secciones sin información respaldada.

#### Scenario: Publicación con información suficiente
- **WHEN** la IA organiza una vacante con datos sobre el cargo
- **THEN** el resultado contiene un resumen breve y listas separadas de responsabilidades, requisitos y condiciones identificables

#### Scenario: Publicación con información incompleta
- **WHEN** la publicación no especifica una de las secciones
- **THEN** el sistema omite esa sección sin completar datos por inferencia

### Requirement: Limitar la síntesis a información verificable
El sistema SHALL resumir la publicación sin añadir hechos, manteniendo su URL original para consultar los detalles directamente en la fuente.

#### Scenario: Resumen sin invenciones
- **WHEN** la IA organiza el texto de una vacante
- **THEN** la síntesis usa solo información presente en la publicación y el dashboard conserva un enlace a la publicación original
