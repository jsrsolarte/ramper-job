# Tasks

## 1. Consultas y paginación

- [x] 1.1 Añadir a la vista administrativa la consulta paginada de ejecuciones `source_query` del periodo seleccionado, ordenada de más reciente a más antigua; verificar límites de periodo, orden y tamaño máximo de 50 registros.
- [x] 1.2 Mantener la autorización administrativa y los campos del contexto limitados a metadatos operativos seguros; verificar que el historial no incluya datos de perfil, CV, prompts ni contenido de vacantes.

## 2. Presentación del historial

- [x] 2.1 Añadir al tablero una tabla cronológica con fecha, fuente, estado, vacantes encontradas, duración y error seguro; verificar que la paginación conserva el periodo y que el estado vacío explica cuando no hubo consultas.
- [ ] 2.2 Validar el flujo en la consola administrativa con consultas reales registradas y comprobar que se distinguen por fecha y fuente sin confundirlas con los conteos de disponibilidad o seguimiento.
