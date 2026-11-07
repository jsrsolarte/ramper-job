# Spec Delta

## ADDED Requirements

### Requirement: Configurar plazos de retención de vacantes
El sistema SHALL permitir a la persona administradora configurar globalmente para toda la plataforma, en días, el plazo para descartar recomendaciones pendientes y el plazo para archivar seguimientos inactivos, con valores iniciales de 7 y 30 días respectivamente.

#### Scenario: No existen valores configurados
- **WHEN** todavía no se guardaron plazos desde el panel
- **THEN** el sistema muestra y aplica 7 días para el descarte automático y 30 días para el archivado de seguimientos

#### Scenario: Se modifica un plazo
- **WHEN** la persona administradora guarda un nuevo plazo entero válido entre 1 y 365 días
- **THEN** el sistema guarda y audita el cambio, y el proceso correspondiente lo aplica desde su siguiente ejecución diaria sin iniciar una ejecución inmediata

#### Scenario: Se intenta guardar un plazo inválido
- **WHEN** el valor no es un entero entre 1 y 365 días
- **THEN** el sistema rechaza el cambio, explica el error y conserva el plazo vigente

#### Scenario: Se consulta la configuración
- **WHEN** la persona administradora abre los parámetros operativos
- **THEN** puede distinguir el plazo de descarte de recomendaciones del plazo de archivado por inactividad

#### Scenario: Los valores son globales
- **WHEN** la persona administradora cambia cualquiera de los dos plazos
- **THEN** el nuevo valor se aplica por igual a las tareas que procesan todos los perfiles y no existe una configuración individual por perfil
