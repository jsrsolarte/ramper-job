# Tasks

## 1. Persistir evidencia trazable del CV

- [x] 1.1 Definir el esquema versionado de hechos laborales y su vínculo a `ProfileRevision`; verificar restricciones de aislamiento y trazabilidad con pruebas de modelo.
- [x] 1.2 Crear extracción estructurada y validación de datos laborales, omitiendo contacto y atributos no pertinentes; verificar con muestras PDF y DOCX que los hechos guardan fragmentos fuente y no contienen campos privados excluidos.
- [x] 1.3 Guardar y reutilizar la extracción por revisión y versión de extractor; verificar que una repetición no vuelva a invocar extracción, una revisión nueva sí lo haga y un fallo siga el flujo de reintento.

## 2. Reutilizar la evidencia para búsquedas

- [x] 2.1 Adaptar la generación de términos para recibir la representación compacta y crear evidencia junto con los términos en el primer procesamiento; verificar que una nueva configuración de búsqueda reutiliza evidencia sin reenviar el CV completo.

## 3. Recuperar evidencia para cada vacante

- [x] 3.1 Implementar selección de hechos por cargo, requisitos, responsabilidades y criterios de rúbrica, incluyendo fechas y credenciales obligatorias; verificar coincidencias exactas, términos normalizados y evidencia potencialmente contradictoria.
- [x] 3.2 Añadir ampliación de cobertura cuando algún criterio aplicable quede sin contexto suficiente; verificar que la ausencia en el conjunto inicial no se convierta por sí sola en «sin evidencia».

## 4. Integrar con puntuación y medir el resultado

- [x] 4.1 Cambiar la solicitud de puntuación para usar únicamente la evidencia seleccionada y preferencias vigentes; verificar que conserva la versión de revisión, la respuesta válida de la rúbrica y la separación de la etapa de organización.
- [x] 4.2 Comparar tokens de entrada en una muestra representativa antes y después, y revisar que se mantengan hechos necesarios para cada criterio; verificar el ahorro sin pérdida de soporte para requisitos obligatorios, fechas o contradicciones.
