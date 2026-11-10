# Spec Delta

## ADDED Requirements

### Requirement: Registrar el resultado de deduplicar una consulta
El sistema SHALL conservar por cada consulta el total de vacantes únicas devueltas, cuántas se agregaron por primera vez al catálogo y cuántas ya existían, distinguiendo entre las conocidas que cambiaron materialmente y las que no.

#### Scenario: La consulta encuentra vacantes nuevas y conocidas
- **WHEN** una búsqueda completa devuelve 148 vacantes únicas, 16 nuevas en el catálogo y 132 ya registradas
- **THEN** el historial guarda 148 encontradas, 16 nuevas y 132 conocidas, y permite desglosar las conocidas entre actualizadas y sin cambios

#### Scenario: Una consulta completa no encuentra resultados
- **WHEN** una consulta termina correctamente sin vacantes
- **THEN** el historial registra cero encontradas, nuevas y conocidas

#### Scenario: La consulta falla antes de clasificar resultados
- **WHEN** la fuente falla antes de devolver resultados utilizables
- **THEN** el historial conserva sus métricas de error y deja el desglose como no disponible, sin presentarlo como cero

#### Scenario: Una consulta encuentra una publicación existente con cambios materiales
- **WHEN** la fuente devuelve una vacante registrada y cambian sus datos materiales
- **THEN** cuenta como conocida y actualizada, no como nueva

### Requirement: Mostrar el desglose de vacantes en observabilidad
La observabilidad administrativa SHALL mostrar el desglose de resultados por ejecución y por fuente en el periodo seleccionado, preservando el significado de cada conteo.

#### Scenario: Consultar una ejecución con desglose disponible
- **WHEN** una persona administradora consulta el historial de fuentes
- **THEN** cada ejecución muestra encontradas, nuevas, conocidas, conocidas actualizadas y conocidas sin cambios

#### Scenario: Consultar los totales de un periodo
- **WHEN** una persona administradora consulta el resumen de una fuente para un periodo
- **THEN** el panel muestra la suma de resultados nuevos y conocidos entre las ejecuciones del periodo, e indica que son ocurrencias por consulta y no vacantes distintas deduplicadas entre todo el periodo

#### Scenario: Consultar historial anterior al desglose
- **WHEN** una ejecución histórica no contiene las nuevas métricas
- **THEN** el panel muestra el desglose como no disponible, sin inferir ceros ni reconstruirlo con datos incompletos

#### Scenario: Proteger la información privada
- **WHEN** el panel muestra el desglose de una ejecución
- **THEN** presenta solo conteos agregados y SHALL NOT mostrar nombres de perfil, CV, frases de búsqueda, ubicaciones preferidas ni datos personales
