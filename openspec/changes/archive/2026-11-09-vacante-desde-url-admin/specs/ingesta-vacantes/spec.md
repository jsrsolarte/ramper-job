# Spec Delta

## ADDED Requirements

### Requirement: Registrar una vacante administrativa usando solo su URL
El centro administrativo SHALL permitir iniciar el registro de una vacante pegando únicamente la URL pública de una publicación en un proveedor compatible.

#### Scenario: La persona administradora envía una URL pública compatible
- **WHEN** la persona administradora envía una URL válida de una ficha pública de El Empleo
- **THEN** el sistema identifica el proveedor y encola la extracción sin solicitar título, fuente ni otros datos manuales

#### Scenario: La URL no pertenece a un proveedor compatible
- **WHEN** la persona administradora envía una URL de un proveedor que no está habilitado
- **THEN** el sistema informa que el proveedor aún no es compatible y no consulta ni registra la publicación

#### Scenario: La URL no es pública o segura
- **WHEN** la URL no usa HTTPS, apunta a un host no permitido o requiere autenticación
- **THEN** el sistema la rechaza sin intentar acceder a recursos privados ni eludir controles de acceso

### Requirement: Extraer y normalizar los datos de la ficha pública
El sistema SHALL extraer de la URL compatible los datos públicos disponibles y normalizarlos al formato común de vacantes.

#### Scenario: La ficha contiene datos suficientes
- **WHEN** el proveedor devuelve una ficha pública interpretable con título y URL original
- **THEN** el sistema conserva los datos extraídos disponibles, fuente identificada y URL canónica

#### Scenario: La ficha no permite crear una vacante válida
- **WHEN** la ficha es inaccesible, está cerrada, no se puede interpretar o no contiene los datos mínimos requeridos
- **THEN** el sistema informa el resultado y no crea la vacante ni encola análisis

#### Scenario: El proveedor bloquea o limita la consulta
- **WHEN** el proveedor responde con bloqueo, límite de solicitudes o error temporal
- **THEN** el sistema detiene la extracción, informa que no fue posible completar el registro y no intenta evadir el control

### Requirement: Continuar por el flujo común de la vacante
Una vacante extraída desde una URL SHALL usar la deduplicación global y el flujo normal de evaluación independiente para cada perfil elegible.

#### Scenario: La URL ya corresponde a una publicación registrada
- **WHEN** la ficha extraída tiene una URL canónica que ya existe
- **THEN** el sistema reutiliza o actualiza la publicación existente sin crear un segundo registro global

#### Scenario: Se crea una vacante nueva desde la URL
- **WHEN** la ficha se extrae correctamente y no existe una publicación equivalente
- **THEN** el sistema guarda la publicación global y encola una evaluación individual para cada perfil activo elegible con CV y preferencias vigentes

#### Scenario: La publicación ya fue evaluada sin cambios materiales
- **WHEN** la URL corresponde a una publicación existente sin cambios materiales para el perfil, revisión y configuración vigentes
- **THEN** el sistema no duplica el análisis completado y muestra el estado del procesamiento administrativo
