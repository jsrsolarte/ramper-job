# Tasks

## 1. Detección e incidentes

- [x] 1.1 Crear registro durable de episodios y reconocimiento; probar agrupación, deduplicación, recuperación con dos evaluaciones, recurrencia y estado desconocido.
- [x] 1.2 Detectar fallos recurrentes y trabajo sin progreso con reloj controlado; probar umbrales, datos ausentes, ausencia de trabajo, leases vencidos y pausas globales, individuales y de horario.
- [x] 1.3 Detectar ciclo vencido reutilizando la semántica de `corregir-horario-busqueda-vencido`; probar márgenes, franja, pausa global y falta de perfiles habilitados.

## 2. Presentación y notificaciones

- [x] 2.1 Mostrar incidentes activos, reconocidos y recuperados en administración; probar autorización, datos agregados y ausencia de contenido privado.
- [x] 2.2 Integrar transporte push compartido y consentimiento independiente por dispositivo; probar permiso, desactivación, cierre de sesión y apertura protegida.
- [x] 2.3 Agrupar avisos y limitar a uno por seis horas por dispositivo; probar concurrencia, recuperación antes del envío, caducidad y respuesta ambigua sin duplicados.

## 3. Integración y límites

- [x] 3.1 Probar fallos del evaluador y ausencia de señales; comprobar que se informa estado desconocido y documentar que la caída total requiere monitor externo independiente.
- [x] 3.2 Validar con datos sintéticos y reloj simulado los escenarios operativos y la entrega en dispositivos compatibles; registrar dependencias y limitaciones sin alertar usuarios reales.
- [x] 3.3 Incrementar `VERSION` como MINOR por funcionalidad compatible y verificar las pruebas pertinentes; preparar por separado la propuesta de vigilancia externa si se solicita.

> Validación manual en staging confirmada por el usuario el 2026-11-27.
