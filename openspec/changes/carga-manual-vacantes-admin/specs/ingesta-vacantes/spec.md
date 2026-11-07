# Spec Delta

## ADDED Requirements

### Requirement: Registrar manualmente una vacante desde administración
El centro administrativo SHALL permitir que la persona administradora registre una vacante pegando únicamente la URL pública de una publicación admitida.

#### Scenario: La persona administradora envía una URL válida
- **WHEN** la persona administradora envía la URL HTTPS de una ficha pública compatible
- **THEN** el sistema encola su extracción, deduplicación y procesamiento y muestra el estado del registro

#### Scenario: La URL no corresponde a una ficha pública compatible
- **WHEN** la URL es inválida, no segura o pertenece a un proveedor no habilitado
- **THEN** el sistema rechaza el registro antes de encolar el procesamiento

#### Scenario: Una cuenta sin privilegios intenta registrar una vacante
- **WHEN** una cuenta aspirante solicita la pantalla o la acción de alta manual
- **THEN** el sistema deniega el acceso y no modifica vacantes ni inicia trabajos

### Requirement: Compartir la vacante manual entre perfiles elegibles
Una vacante registrada manualmente SHALL ser una publicación global y SHALL generar una evaluación independiente para cada perfil activo elegible con CV y preferencias vigentes.

#### Scenario: Se registra una vacante nueva
- **WHEN** la persona administradora registra una vacante activa que no estaba guardada
- **THEN** el sistema guarda una sola publicación y encola su análisis para cada perfil elegible según sus preferencias de ubicación y modalidad

#### Scenario: Los perfiles elegibles comparten la vacante
- **WHEN** dos o más perfiles son elegibles para la misma vacante manual
- **THEN** cada perfil recibe su propio puntaje y desglose conforme a su CV, preferencias, rúbrica y umbral vigentes

#### Scenario: Ningún perfil es elegible
- **WHEN** la vacante no cumple las preferencias geográficas o de modalidad de ningún perfil vigente
- **THEN** el sistema conserva la publicación global sin crear evaluaciones incompatibles

### Requirement: Evitar duplicar una vacante ingresada manualmente
El sistema SHALL reutilizar una publicación existente que tenga la misma URL pública canónica, sin importar si se encontró por una fuente automática o por el registro manual.

#### Scenario: La URL ya está registrada
- **WHEN** la persona administradora registra una vacante cuya URL canónica ya existe
- **THEN** el sistema actualiza o reutiliza la publicación existente y no crea un segundo registro global

#### Scenario: Se vuelve a registrar una vacante sin cambios materiales
- **WHEN** una vacante existente se registra manualmente de nuevo sin cambiar contenido material
- **THEN** el sistema no duplica análisis ya completados para el mismo perfil, revisión y configuración
