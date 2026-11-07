# Tasks

## 1. Confirmar prerrequisitos

- [x] 1.1 Antes de implementar, confirmar que `carga-manual-vacantes-admin`, `centro-administracion-plataforma`, `analisis-ia-por-etapas`, `rubrica-criterios-criticos-decimales` y `seguimiento-postulaciones` estén implementados e integrados; verificar estado de OpenSpec y detener el cambio si falta alguno.
- [x] 1.2 Confirmar la extracción pública y deduplicación común de El Empleo; verificar que la ficha directa puede convertirse en una vacante normalizada sin usar búsqueda por términos.

## 2. Validar URL y extraer ficha pública

- [x] 2.1 Añadir resolución de proveedor por host y patrón de ficha, habilitando El Empleo para esta entrega; verificar reconocimiento correcto de URLs admitidas y rechazo de proveedores no habilitados.
- [x] 2.2 Proteger las peticiones contra URLs privadas, hosts no permitidos y redirecciones fuera del proveedor autorizado; verificar que no se consultan direcciones internas ni páginas autenticadas.
- [x] 2.3 Extraer y normalizar los datos públicos disponibles a partir de la URL sola; verificar publicación completa, datos faltantes, ficha inaccesible, bloqueo y fallo temporal.
- [x] 2.4 Añadir pruebas de regresión del conector y documentar el contrato para añadir proveedores futuros; verificar que las reglas de acceso público siguen vigentes.

## 3. Reutilizar el flujo administrativo y por perfil

- [x] 3.1 Encolar la extracción sin bloquear el formulario y mostrar estado y errores saneados; verificar que la respuesta web termina antes del procesamiento.
- [x] 3.2 Pasar la publicación extraída por deduplicación y alta manual existentes; verificar que URL ya registrada actualiza/reutiliza una sola publicación y que contenido sin cambios no duplica análisis completados.
- [x] 3.3 Encolar evaluaciones individuales para cada perfil elegible usando el flujo vigente; verificar aislamiento de puntajes, umbrales y seguimientos personales.

## 4. Integrar antes de stage

- [x] 4.1 Verificar el recorrido completo desde URL de El Empleo hasta extracción, deduplicación y evaluaciones por perfil, junto con los prerrequisitos integrados.
- [ ] 4.2 Antes de cualquier despliegue a stage, confirmar que `vacante-desde-url-admin` esté completo e integrado después de `carga-manual-vacantes-admin`; verificar que la compuerta de despliegue lo incluya.
