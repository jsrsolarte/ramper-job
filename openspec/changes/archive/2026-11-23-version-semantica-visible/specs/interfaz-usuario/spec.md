# Spec Delta

## ADDED Requirements

### Requirement: Presentar un pie de página centrado con la firma secundaria RamPer
El pie de página común SHALL centrarse, usar la paleta visual de Jobs y mostrar la firma «By» junto al lockup RamPer v0.6 como elemento secundario, manteniendo Jobs como identidad principal. La firma RamPer SHALL aparecer solo en el pie y SHALL conservar una alternativa accesible que identifique la marca.

#### Scenario: Consultar una pantalla de Jobs
- **WHEN** una persona abre una pantalla de ingreso, perfil, vacantes, análisis o administración
- **THEN** el pie común aparece centrado, muestra la firma secundaria «By RamPer» y mantiene la identidad Jobs como protagonista

#### Scenario: Consultar el pie en un móvil
- **WHEN** el ancho disponible es reducido
- **THEN** la versión y la firma se reorganizan dentro del pie sin recortarse ni producir desbordamiento horizontal

#### Scenario: Usar tecnología de asistencia
- **WHEN** un lector de pantalla encuentra el lockup RamPer
- **THEN** anuncia un texto alternativo que identifica la marca RamPer sin repetir decoración visual
