# Spec Delta

## ADDED Requirements

### Requirement: Obtener publicaciones públicas de Magneto Colombia
El sistema SHALL obtener y normalizar vacantes públicas de Magneto a partir de HTML, conservando fuente y enlace original.

#### Scenario: Tarjeta interpretable
- **WHEN** el listado contiene una publicación con título y enlace público de ficha
- **THEN** el sistema conserva ambos y los demás datos disponibles, incluyendo empresa, ubicación, salario e identificador cuando existan

#### Scenario: Campo opcional ausente
- **WHEN** el listado omite un dato opcional
- **THEN** el sistema lo deja desconocido sin inferirlo de la consulta

### Requirement: Enriquecer fichas públicas de Magneto
El sistema SHALL consultar las fichas públicas necesarias y conservar su información disponible en el formato común.

#### Scenario: Ficha disponible
- **WHEN** la ficha contiene descripción, requisitos o condiciones interpretables
- **THEN** el sistema conserva los datos disponibles y la evidencia de detalle confirmado

#### Scenario: Ficha individual inaccesible
- **WHEN** una ficha falla sin indicar bloqueo de la fuente
- **THEN** el sistema conserva los datos del listado y continúa con las demás fichas

#### Scenario: Identidad de la ficha incompatible o ambigua
- **WHEN** el contenido de la ficha no permite asociarla con confianza a la publicación del listado
- **THEN** el sistema conserva los datos del listado, informa la discrepancia y no marca el detalle como confirmado

#### Scenario: Condiciones contradictorias
- **WHEN** la ficha presenta valores salariales diferentes en el resumen y la descripción
- **THEN** el sistema conserva los valores disponibles con su procedencia y no sustituye silenciosamente uno por otro

#### Scenario: Varias ubicaciones publicadas
- **WHEN** la ficha informa varias ubicaciones de la oferta
- **THEN** el sistema conserva las ubicaciones disponibles y las considera en la elegibilidad sin inventar una ubicación a partir de la URL

### Requirement: Detener la extracción de Magneto ante bloqueo
El sistema SHALL detener las solicitudes restantes a Magneto durante la ejecución cuando la fuente bloquee o limite el acceso, sin evadir el control.

#### Scenario: Respuesta de bloqueo
- **WHEN** una búsqueda o ficha exige autenticación o devuelve 401, 403 o 429
- **THEN** el sistema conserva los resultados parciales y registra la indisponibilidad sin impedir el procesamiento de otras fuentes

#### Scenario: Destino inseguro
- **WHEN** un enlace o redirección apunta fuera de los hosts públicos permitidos o a una dirección no pública
- **THEN** el sistema rechaza el destino sin consultarlo
