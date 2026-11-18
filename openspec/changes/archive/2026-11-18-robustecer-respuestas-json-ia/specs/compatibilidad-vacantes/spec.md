# Spec Delta

## ADDED Requirements

### Requirement: Interpretar respuestas JSON delimitadas
El sistema SHALL aceptar para puntuación y organización un objeto JSON válido directamente o contenido íntegramente en un único bloque Markdown de código sin texto externo, y SHALL aplicar la validación vigente antes de guardar resultados.

#### Scenario: JSON delimitado
- **WHEN** el modelo devuelve un único bloque completo etiquetado como JSON o sin etiqueta que contiene un objeto JSON válido
- **THEN** el sistema interpreta el objeto y ejecuta las validaciones habituales sin otra llamada de IA

#### Scenario: Contenido ambiguo
- **WHEN** hay varios bloques, texto adicional, delimitadores incompletos o contenido que no es un objeto
- **THEN** el sistema no selecciona fragmentos arbitrarios ni guarda un resultado sin validación

### Requirement: Solicitar salida estructurada compatible
El sistema SHALL solicitar el esquema JSON de la etapa cuando la ruta configurada lo admita, con una alternativa explícita para rutas incompatibles que conserve las mismas validaciones.

#### Scenario: Ruta incompatible con el esquema
- **WHEN** la ruta rechaza explícitamente el formato estructurado por incompatibilidad
- **THEN** el sistema puede solicitar el formato compatible una sola vez y conserva el control de errores y validación

### Requirement: Reparar sintaxis sin reevaluar
Si el contenido directo o el interior de un único bloque Markdown inequívoco sigue siendo sintácticamente inválido después de la normalización local, el sistema SHALL realizar una única llamada de reparación por respuesta original, con instrucciones de conservar los datos y sin volver a evaluar el perfil o la vacante. La salida SHALL superar las validaciones existentes antes de guardarse.

#### Scenario: El bloque sigue teniendo JSON inválido
- **WHEN** se retiran localmente los delimitadores de un único bloque y el contenido sigue siendo sintácticamente inválido
- **THEN** el sistema solicita una sola reparación de formato a la IA sin repetir la evaluación

#### Scenario: Reparación exitosa
- **WHEN** la reparación devuelve un objeto válido y verificablemente preserva los valores y evidencia de la respuesta original
- **THEN** el sistema valida la rúbrica o la organización y guarda el resultado solo si cumple sus reglas

#### Scenario: Reparación no verificable o fallida
- **WHEN** la reparación falla, altera o inventa contenido, o no es posible verificar que preserva la evaluación original
- **THEN** el sistema rechaza el resultado y conserva la política de recuperación y vencimiento existente

#### Scenario: JSON válido pero rúbrica inválida
- **WHEN** el JSON se interpreta correctamente pero incumple la rúbrica o el esquema de organización
- **THEN** el sistema rechaza el resultado sin invocar la reparación sintáctica

#### Scenario: Error de transporte
- **WHEN** la llamada original falla por timeout, conexión o error HTTP
- **THEN** el sistema aplica la recuperación existente sin solicitar reparación de una respuesta inexistente
