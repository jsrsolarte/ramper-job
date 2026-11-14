## ADDED Requirements

### Requirement: Pausar o reanudar la búsqueda automática del perfil
«Mi perfil» SHALL permitir a la persona propietaria pausar o reanudar las búsquedas automáticas de su perfil, sin desactivar su cuenta ni modificar sus demás datos.

#### Scenario: Perfil nuevo o existente sin configuración de búsqueda
- **WHEN** el sistema crea un perfil o encuentra uno que todavía no tiene un estado de búsqueda guardado
- **THEN** considera habilitada la búsqueda automática para conservar el comportamiento vigente

#### Scenario: La persona pausa la búsqueda de su perfil
- **WHEN** la persona desactiva el control de búsqueda en «Mi perfil» y guarda el cambio
- **THEN** el sistema conserva esa preferencia, muestra que la búsqueda está pausada y mantiene disponibles la cuenta, el CV, las preferencias y los resultados guardados

#### Scenario: La persona reanuda la búsqueda de su perfil
- **WHEN** la persona activa el control de búsqueda en «Mi perfil» y guarda el cambio
- **THEN** el sistema conserva la preferencia habilitada y comunica que el perfil volverá a participar en las siguientes búsquedas automáticas

#### Scenario: Cambiar solo el estado de búsqueda
- **WHEN** la persona cambia el control de búsqueda sin modificar otros datos del perfil
- **THEN** el sistema no crea una nueva revisión del CV o de preferencias ni encola una búsqueda inmediata
