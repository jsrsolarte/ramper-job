## ADDED Requirements

### Requirement: Respetar la pausa individual en las búsquedas automáticas
El sistema SHALL iniciar búsquedas automáticas y asociar sus resultados únicamente con perfiles que tengan habilitada la búsqueda.

#### Scenario: Se ejecuta un ciclo periódico
- **WHEN** comienza un ciclo automático de búsqueda con perfiles habilitados y pausados
- **THEN** el sistema consulta fuentes solo para perfiles habilitados

#### Scenario: Administración fuerza una actualización de fuentes
- **WHEN** la persona administradora inicia una búsqueda manual de fuentes mientras hay perfiles pausados
- **THEN** el sistema incluye únicamente los perfiles con búsqueda habilitada y conserva pausados los demás

#### Scenario: Hay una actualización de perfil en cola al pausarlo
- **WHEN** una tarea de búsqueda de un perfil pausado está en cola y todavía no inició
- **THEN** el sistema omite esa búsqueda sin consultar fuentes ni volver a encolarla

#### Scenario: Una búsqueda compartida coincide con un perfil pausado
- **WHEN** una consulta equivalente corresponde a perfiles habilitados y a otro perfil pausado
- **THEN** el sistema ejecuta una sola consulta para los perfiles habilitados y no asocia el resultado ni encola análisis de esa búsqueda para el perfil pausado

#### Scenario: Se pausa un perfil durante una búsqueda compartida
- **WHEN** la consulta ya comenzó para un grupo y uno de sus perfiles se pausa antes de asociar los resultados
- **THEN** el sistema puede completar la consulta para los perfiles habilitados, pero excluye al perfil pausado de nuevos resultados y análisis originados por esa búsqueda

#### Scenario: Se reanuda la búsqueda del perfil
- **WHEN** una persona habilita de nuevo la búsqueda de su perfil
- **THEN** el perfil participa desde el siguiente ciclo automático normal sin iniciar una consulta inmediata ni recuperar tareas omitidas

#### Scenario: Se procesan vacantes existentes o ingresadas manualmente
- **WHEN** un perfil tiene pausada la búsqueda automática y se analiza una vacante ya guardada o registrada manualmente por administración
- **THEN** el sistema mantiene el análisis y acceso a esa vacante según el flujo común del perfil
