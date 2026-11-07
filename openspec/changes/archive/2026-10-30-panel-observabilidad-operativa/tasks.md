# Tasks

## 1. Historial de ejecuciones

- [x] 1.1 Crear registros de ejecución para consultas de fuentes y de intentos de análisis, con inicio, fin, resultado y duración; verificar que una ejecución exitosa y fallida guarda los datos esperados.
- [x] 1.2 Instrumentar ingesta y análisis, guardando conteos y errores saneados; verificar que reintentos se registran como intentos separados y que no se persisten prompts ni contenido privado.
- [x] 1.3 Añadir retención de al menos 90 días y limpieza periódica; verificar que se conservan los registros recientes y se eliminan solo los expirados.
- [x] 1.4 Cerrar como fallidas las ejecuciones atascadas por más de 20 minutos; verificar que se finalizan con una categoría segura y que las ejecuciones recientes permanecen en curso.

## 2. Panel administrativo

- [x] 2.1 Crear el panel con agregados para 24 horas, 7 días y 30 días; verificar conteos, proporciones y promedios contra datos de ejecución conocidos.
- [x] 2.2 Mostrar cola pendiente, antigüedad del pendiente más viejo, estado reciente por fuente y fecha inicial de cobertura; verificar periodos sin datos y pendientes históricos.
- [x] 2.3 Restringir cada consulta del panel al permiso administrativo y mostrar errores saneados; verificar denegación para cuentas de aspirante y ausencia de CV, prompts y credenciales.
- [x] 2.4 Mostrar como pendientes, y no como procesándose, las vacantes aún en cola; verificar el conteo para la revisión y ubicación actuales del perfil.
