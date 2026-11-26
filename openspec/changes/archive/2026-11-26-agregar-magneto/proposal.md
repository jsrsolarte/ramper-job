# Proposal

## Why

Magneto ofrece vacantes colombianas relevantes para los perfiles familiares. Dos muestras compartidas contienen HTML con tarjetas y enlaces de vacantes, incluida una búsqueda combinada de procesos en Medellín y últimos tres días, lo que permite plantear un conector público como el de Computrabajo.

## What Changes

- Añadir Magneto Colombia al flujo compartido de búsquedas por perfil, mediante extracción de HTML de listados y fichas públicas.
- Normalizar datos disponibles, conservar fuente y enlace, y reutilizar preselección, identidad, elegibilidad, análisis y observabilidad existentes.
- Limitar inicialmente cada búsqueda a la primera página; detener la fuente ante bloqueos y conservar resultados parciales.
- Mantener fuera del alcance postulaciones, cuentas, acceso autenticado, carga administrativa por URL y deduplicación entre portales.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `ingesta-vacantes`: obtener y enriquecer publicaciones públicas de Magneto.
- `busqueda-por-perfil`: consultar Magneto con términos y ubicaciones efectivos de cada grupo.

## Impact

Conectores, registro de fuentes, configuración, documentación y pruebas. El cambio reutiliza Django, requests y BeautifulSoup; requiere incremento MINOR de VERSION al implementarse. Staging y producción requieren las autorizaciones y flujos establecidos.
