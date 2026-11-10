# Tasks

## 1. Prerrequisito de acceso

- [x] 1.1 Implementar primero `mensaje-y-control-cuenta-inactiva`; verificar que una cuenta inactiva recibe la indicación de contactar a administración y que la consola permite reactivarla.

## 2. Medición de actividad

- [x] 2.1 Añadir y poblar la fecha de última actividad autenticada para cuentas existentes; verificar el valor inicial desde último acceso disponible o creación/activación.
- [x] 2.2 Actualizar la actividad en el uso autenticado de la aplicación y excluir tráfico técnico y tareas automáticas; verificar que solo la actividad de la persona mueve la fecha.

## 3. Desactivación periódica

- [x] 3.1 Implementar la ejecución diaria que desactiva aspirantes después de siete días sin actividad y registra el motivo; verificar límites, exclusión de administración e idempotencia.
- [x] 3.2 Confirmar que una reactivación desde la consola conserva los datos y reinicia el plazo; verificar el flujo desde cuenta inactiva hasta nuevo inicio de sesión.
