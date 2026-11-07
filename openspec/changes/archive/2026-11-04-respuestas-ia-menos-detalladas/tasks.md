# Tasks

## 1. Reducir detalle redundante de las respuestas

- [x] 1.1 Crear nuevas versiones del prompt de puntuación que pidan evidencia principal y eviten explicaciones secundarias; verificar que las respuestas conservan los campos de rúbrica requeridos y pasan la validación.
- [x] 1.2 Crear nuevas versiones del prompt de organización que consoliden repeticiones y prioricen información útil para comparar vacantes; verificar que las categorías actuales permanecen y el contenido sigue respaldado por la publicación.
- [x] 1.3 Comparar ambas versiones con muestras representativas usando la misma configuración y verificar una reducción del promedio de tokens de salida por etapa sin pérdida de campos o evidencias necesarios.
- [x] 1.4 Verificar que los resultados nuevos conservan la versión exacta del prompt y que los resultados históricos no se alteran.

Comparación con tres casos sintéticos y `gpt-6-luna`: puntuación anterior 643 tokens de salida de promedio, nueva 576,7; organización anterior 141, nueva 124,7. Las respuestas pasaron los validadores y conservaron los requisitos y categorías de los casos. La muestra es pequeña y el modelo puede variar entre ejecuciones.
