# Spec Delta

## ADDED Requirements

### Requirement: Confirmar limpieza administrativa de vacantes
El sistema SHALL ofrecer solo a administración una vista previa de la limpieza de vacantes, análisis, seguimientos e historial de búsquedas y SHALL exigir confirmación explícita e inequívoca para cada ejecución.

#### Scenario: Se revisa la limpieza
- **WHEN** una persona administradora abre la operación
- **THEN** el sistema muestra cantidades, datos a borrar, datos a conservar, advertencia de irreversibilidad y ausencia de respaldo configurado cuando aplique

#### Scenario: Falta confirmación
- **WHEN** se solicita la limpieza sin la confirmación específica vigente
- **THEN** el sistema no borra datos ni inicia la operación

#### Scenario: Acceso no autorizado
- **WHEN** una cuenta sin permisos administrativos intenta ver o ejecutar la limpieza
- **THEN** el sistema deniega la operación y no expone datos privados

### Requirement: Conservar datos y configuración fuera del alcance
La limpieza SHALL borrar las vacantes y sus análisis, organizaciones, descubrimientos, seguimientos, solicitudes manuales e historial operativo de búsqueda asociado; SHALL conservar usuarios, perfiles, revisiones, CV, configuración, horarios, parámetros y auditoría administrativa.

#### Scenario: Finaliza una limpieza
- **WHEN** se confirma y completa la operación
- **THEN** los datos afectados se eliminan y los datos protegidos y archivos de CV permanecen disponibles

#### Scenario: Ocurre un fallo durante el borrado
- **WHEN** falla la transacción de eliminación
- **THEN** el sistema no presenta la limpieza como completa y conserva consistencia sin borrado parcial de los datos transaccionales

### Requirement: Auditar la limpieza
El sistema SHALL registrar quién confirmó la limpieza, fecha, resultado y conteos agregados sin guardar contenido privado, y SHALL conservar ese registro después del borrado.

#### Scenario: Operación completada o fallida
- **WHEN** termina una ejecución
- **THEN** administración puede consultar el resultado y los conteos seguros, sin CV, textos de perfil ni contenido de vacantes
