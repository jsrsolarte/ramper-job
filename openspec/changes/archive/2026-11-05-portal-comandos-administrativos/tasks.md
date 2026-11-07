# Tasks

## 1. Registrar comandos y proteger el portal

- [x] 1.1 Crear el registro de solicitudes de comando o enlazarlo con los eventos operativos existentes; verificar persistencia de solicitante, hora, estado, resultado y resumen saneado.
- [x] 1.2 Implementar portal y endpoint con autorización administrativa y catálogo de identificadores permitidos; verificar denegación para aspirantes y rechazo de nombres de tareas o argumentos arbitrarios.

## 2. Encolar actualización manual

- [x] 2.1 Conectar el comando de actualización manual al flujo habitual de búsqueda e ingesta y devolver estado de cola sin esperar a que termine; verificar que la solicitud web no ejecuta el trabajo sincrónicamente y que el ciclo Beat conserva su horario.
- [x] 2.2 Añadir exclusión mutua compartida por solicitudes manuales y tareas programadas, liberada también ante fallo; verificar que solicitudes simultáneas y un ciclo Beat concurrente no duplican la actualización.
- [x] 2.3 Reutilizar deduplicación y elegibilidad de análisis en la actualización manual; verificar que vacantes nuevas se crean una vez y que una vacante con análisis completado no crea otro registro ni repite análisis sin cambio material.

## 3. Mostrar estado y auditoría

- [x] 3.1 Mostrar estado en cola, ejecución, éxito o fallo y resultado por fuente desde los eventos de ejecución; verificar actualización del estado y legibilidad de ejecuciones parciales.
- [x] 3.2 Sanear errores y registrar solicitante y duración sin secretos, CV, prompts ni respuestas completas; verificar los datos guardados y la vista ante fallas de proveedor.

## 4. Verificación integrada

- [x] 4.1 Ejecutar validaciones del portal, autorización, concurrencia, ingesta y análisis y probar un ciclo manual completo; verificar que no duplica vacantes/análisis y que el siguiente ciclo automático ocurre según el horario previsto.
