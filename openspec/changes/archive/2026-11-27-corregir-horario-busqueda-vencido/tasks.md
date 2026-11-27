# Tasks

## 1. Estado y presentación

- [x] 1.1 Definir estado compartido para estimación futura, vencida, pausa y ausencia de datos; probar con reloj controlado límites y precedencia de las pausas.
- [x] 1.2 Actualizar dashboard y administración para comunicar retraso y último inicio disponible sin inventar fechas; probar ambas vistas y que las consultas no encolan trabajo.
- [x] 1.3 Manejar pantallas abiertas que cruzan el horario estimado y errores de actualización; verificar que no sigan mostrando una fecha pasada como próxima.
- [x] 1.4 Mostrar actividad confirmada y próxima estimación como estados separados; probar trabajo activo, en cola, pausado, con concesión vencida y sin hora fiable, sin revelar datos de perfiles.

## 2. Programación y validación

- [x] 2.1 Investigar con pruebas simuladas Beat, reserva del ciclo y recuperación; documentar evidencia y corregir cualquier defecto reproducido sin duplicar ciclos ni saltar pausas.
- [x] 2.4 Investigar en entorno aislado los reinicios y tiempos de respuesta de las sondas del worker observados en producción; documentar evidencia y preparar corrección cuando sea reproducible, sin realizar mutaciones productivas.
- [x] 2.2 Ejecutar pruebas de programación y vistas con fuentes simuladas, incluyendo el ejemplo 16:34 consultado a las 18:00 y un ciclo iniciado posteriormente.
- [x] 2.3 Actualizar `VERSION` según el conjunto de cambios y verificar su valor. Como el candidato incluye funcionalidades compatibles nuevas, corresponde incremento MINOR.
