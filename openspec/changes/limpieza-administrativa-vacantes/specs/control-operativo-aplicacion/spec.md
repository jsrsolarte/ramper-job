# Spec Delta

## ADDED Requirements

### Requirement: Ejecutar limpieza con procesamiento controlado
El sistema SHALL coordinar la limpieza con la pausa global, esperar el fin seguro de trabajo activo e impedir que trabajos anteriores vuelvan a crear datos borrados. SHALL conservar el estado de pausa previo y recuperarse de forma segura ante interrupciones.

#### Scenario: Hay trabajo activo
- **WHEN** se confirma la limpieza con búsquedas o análisis en ejecución
- **THEN** el sistema impide trabajo nuevo y espera que terminen de forma segura antes de borrar; si no puede garantizarlo, aborta sin borrar

#### Scenario: Se entrega una tarea anterior
- **WHEN** una tarea de la generación anterior se entrega después de limpiar
- **THEN** no recrea datos de la limpieza ni causa efectos sobre registros nuevos

#### Scenario: El procesamiento ya estaba pausado
- **WHEN** se completa o interrumpe la limpieza que comenzó con pausa previa
- **THEN** el sistema conserva el procesamiento pausado

#### Scenario: El procesamiento estaba activo
- **WHEN** se completa la limpieza de manera segura y no hay una pausa posterior solicitada por administración
- **THEN** el sistema restaura el procesamiento activo e informa que búsquedas futuras pueden generar nuevas vacantes

#### Scenario: Interrupción o estado incierto
- **WHEN** se interrumpe la coordinación o no se puede verificar que el sistema está seguro
- **THEN** el procesamiento permanece pausado y el sistema informa cómo recuperar o reanudar la operación
