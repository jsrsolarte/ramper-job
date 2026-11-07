# Proposal

## Why

Buscar vacantes compatibles en varios portales y compararlas manualmente con cada hoja de vida consume tiempo y hace difícil encontrar oportunidades relevantes para una familia. Este cambio propone un asistente privado que reúne vacantes para cada persona y prioriza las que mejor se ajustan a su perfil.

## What Changes

- Crear cuentas familiares de forma administrada, sin registro público, y mantener separados los perfiles, CV y resultados de cada persona.
- Permitir que cada persona mantenga su CV y sus criterios de búsqueda laboral.
- Incorporar vacantes de elempleo.com Colombia como primera fuente mediante un conector de scraping independiente, preparado para agregar otras bolsas de empleo sin acoplarlas al análisis.
- Usar un modelo de IA accesible mediante la instancia privada de OmniRoute que configurará el administrador para preparar una descripción organizada y clasificar la compatibilidad de cada vacante por puntaje, razones y requisitos que no coinciden.
- Incluir una interfaz de administración para ajustar prompts y parámetros de coincidencia, conservar versiones y asociar cada análisis a la configuración utilizada.
- Mostrar en el dashboard de cada persona las vacantes más compatibles, su descripción organizada por IA y el enlace a la publicación original.
- Dejar prevista para una fase futura la generación de copias del CV adaptadas a una vacante en formato ATS, sin modificar el CV base.

## Capabilities

### New Capabilities

- `cuentas-y-perfiles`: Cuentas administradas, acceso privado y datos de búsqueda laboral aislados por persona.
- `ingesta-vacantes`: Obtención y normalización de vacantes desde fuentes de empleo, empezando por elempleo.com Colombia.
- `compatibilidad-vacantes`: Descripción organizada y evaluación explicable de compatibilidad entre una vacante y el perfil mediante un modelo de IA.
- `dashboard-vacantes`: Consulta ordenada de vacantes compatibles con descripción generada, puntaje, razones, brechas y enlace a la fuente.

### Modified Capabilities

Ninguna.

## Impact

- Proyecto greenfield sin código existente. Stack propuesto: Python con Django, PostgreSQL y Celery con Redis para trabajos asíncronos.
- Requiere almacenamiento aislado para cuentas, CV, preferencias, vacantes obtenidas, análisis y estado visible en el dashboard.
- Requiere conectores de fuentes independientes y configuración versionada de análisis para facilitar la evolución del producto.
- Requiere una integración configurable con el endpoint y modelo de OmniRoute; instalación y operación de OmniRoute quedan fuera del alcance.
- El conector inicial realizará scraping directo de páginas públicas de elempleo.com Colombia.
- La aplicación automática a vacantes, el auto-registro de usuarios y la administración de OmniRoute quedan fuera del alcance.
- La generación de CV personalizados para ATS queda prevista como fase futura y no forma parte de este cambio.
