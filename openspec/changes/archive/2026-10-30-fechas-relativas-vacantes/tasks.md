# Tasks

## 1. Registrar fechas para cada tipo de tiempo

- [x] 1.1 Guardar cuándo termina cada análisis por perfil y cuándo el seguimiento entra en su estado actual; verificar transiciones y que un perfil no altere las fechas de otro.
- [x] 1.2 Añadir una migración compatible para registros existentes, reutilizando solo fechas confiables y dejando sin fecha los casos que no puedan determinarse; verificar registros antiguos y nuevos.

## 2. Mostrar fechas relativas en el dashboard

- [x] 2.1 Mostrar el tiempo desde publicación, análisis y estado con etiquetas relativas en español y fecha absoluta accesible; verificar minutos, horas, días, zona horaria y datos ausentes.
- [x] 2.2 Cubrir en pruebas Recomendaciones y cada estado de seguimiento, confirmando que al cambiar de etapa se reinicia la antigüedad mostrada y no se modifica la fecha de publicación.
