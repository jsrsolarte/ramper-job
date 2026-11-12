# Tasks

## 1. Registrar y calcular el ciclo automático

- [x] 1.1 Persistir la fecha y hora de activación del ciclo global periódico, actualizarla solo desde ese flujo y verificarlo con pruebas que distingan tareas periódicas, actualizaciones manuales y búsquedas por perfil.
- [x] 1.2 Crear un cálculo compartido de la próxima hora estimada con el intervalo vigente, la pausa global y el caso sin referencia; verificar cambios de intervalo, estado pausado y ausencia de datos con pruebas unitarias.

## 2. Mostrar el horario a las personas aspirantes

- [x] 2.1 Incluir el horario estimado o su estado explicativo en el dashboard de aspirantes, junto con el aviso sobre búsquedas anticipadas; verificar los casos habilitado, pausado y horario no disponible con pruebas del dashboard.

## 3. Mostrar el horario a la administración

- [x] 3.1 Incluir en el centro administrativo la misma hora estimada y estado que ve una persona aspirante; verificar equivalencia, estado pausado y horario no disponible con pruebas administrativas.

## 4. Verificar la experiencia completa

- [ ] 4.1 Ejecutar las pruebas relevantes de dashboard y operaciones, y verificar manualmente que ambas vistas muestran el mismo horario local estimado tras un ciclo automático y tras cambiar el intervalo.
