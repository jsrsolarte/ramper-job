# Spec Delta

## Purpose

Protege los perfiles, el historial de trabajo y los CV de producción frente a la pérdida del nodo o de sus volúmenes, con una ruta de restauración verificada.

## ADDED Requirements

### Requirement: Respaldar los datos persistentes de producción fuera del nodo
La plataforma SHALL mantener copias recuperables de la base de datos y de los archivos CV de producción en almacenamiento independiente del nodo que ejecuta Kubernetes.

#### Scenario: Se ejecuta el respaldo programado
- **WHEN** llega el intervalo definido para el respaldo
- **THEN** se crea una copia coherente de la base de datos y los CV, protegida contra acceso no autorizado y cuya antigüedad puede verificarse

#### Scenario: Falla un respaldo
- **WHEN** no se puede completar o validar una copia
- **THEN** el fallo queda visible para administración y el último respaldo válido no se presenta como reciente

### Requirement: Restaurar y verificar los datos de producción
La plataforma SHALL documentar y comprobar una restauración que recupere PostgreSQL y los archivos CV en conjunto, preservando su relación.

#### Scenario: Se prueba la restauración
- **WHEN** se ejecuta una prueba de recuperación en un entorno aislado
- **THEN** se comprueba la integridad de la base de datos, los archivos y su asociación, sin sobrescribir producción

#### Scenario: Se pierde un volumen de producción
- **WHEN** una falla del nodo o del almacenamiento vuelve inaccesibles los datos persistentes
- **THEN** administración puede seguir el procedimiento documentado para recuperar ambos conjuntos de datos desde una copia verificada
