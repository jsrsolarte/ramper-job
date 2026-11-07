# Spec Delta

## Purpose

Obtiene y prepara vacantes de portales de empleo para analizarlas por perfil, conservando su procedencia y evitando repetir publicaciones.

## ADDED Requirements

### Requirement: Scraping de vacantes públicas
El sistema SHALL obtener vacantes mediante scraping de páginas públicas de elempleo.com Colombia, sin acceder a áreas que requieran autenticación ni evadir controles de acceso o medidas de seguridad.

#### Scenario: Página pública disponible
- **WHEN** una página pública de elempleo.com contiene vacantes
- **THEN** el sistema obtiene vacantes públicas y conserva el enlace a cada publicación original

#### Scenario: La fuente bloquea la consulta pública
- **WHEN** elempleo.com bloquea la consulta o solicita autenticación
- **THEN** el sistema detiene la extracción de esa página y deja visible que la fuente no está disponible

### Requirement: Conectores de fuentes intercambiables
El sistema SHALL integrar cada bolsa de empleo mediante un conector que implemente un contrato común de consulta y normalización, de forma que una nueva fuente pueda añadirse sin cambiar el flujo compartido de análisis y dashboard.

#### Scenario: Se agrega una nueva bolsa de empleo
- **WHEN** se habilita un conector que cumple el contrato común de fuente
- **THEN** sus vacantes normalizadas pasan al mismo flujo de deduplicación, análisis y presentación que las fuentes existentes

### Requirement: Normalización de vacantes
El sistema SHALL conservar los datos disponibles de cada vacante en una estructura común para su análisis, incluyendo su fuente y enlace original.

#### Scenario: Vacante con campos incompletos
- **WHEN** una vacante no incluye alguno de los campos esperados
- **THEN** el sistema conserva los campos disponibles y marca los datos faltantes como desconocidos

### Requirement: Detección de publicaciones repetidas
El sistema SHALL evitar presentar más de una vez la misma vacante obtenida de una fuente.

#### Scenario: La fuente devuelve una vacante ya conocida
- **WHEN** una nueva consulta encuentra una publicación previamente registrada
- **THEN** el sistema actualiza sus datos disponibles en lugar de crear una segunda vacante
