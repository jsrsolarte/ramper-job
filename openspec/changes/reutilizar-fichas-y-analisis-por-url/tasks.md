# Tasks

## 1. Identidad y datos históricos

- [x] 1.1 Implementar identidad por fuente y URL normalizada sin parámetros ni fragmento, con validación de URL; verificar parámetros, fragmentos, rutas distintas y fuentes distintas.
- [x] 1.2 Preparar migración de claves, alias acreditados y estado de detalle confirmado con tratamiento conservador de históricos y colisiones; verificar preservación de registros, análisis y seguimientos con datos sintéticos y documentar casos ambiguos.

## 2. Reutilización de fichas

- [x] 2.1 Consultar la identidad antes de descargar ficha y reutilizar detalles confirmados en búsquedas y registro manual; probar fichas conocidas, nuevas, sin evidencia y fallidas en ambas fuentes.
- [x] 2.2 Coordinar consultas simultáneas por URL y recuperación de trabajo interrumpido; verificar con pruebas concurrentes que no se duplican descargas ni se pierden asociaciones o cursores.

## 3. Análisis y presentación

- [x] 3.1 Reutilizar resultados completados por perfil y vacante sin depender de revisión/configuración, incluso en reprocesamiento manual; probar cambios de perfil, ficha y configuración, otro perfil y entregas concurrentes.
- [x] 3.2 Recuperar pendientes sin resultado completado con la revisión vigente y conservar fecha de primer hallazgo; probar interrupciones, elegibilidad, vencimiento y ausencia de llamadas duplicadas.
- [x] 3.3 Adaptar dashboard, detalle, filtros y estadísticas para conservar visibilidad, seguimiento y trazabilidad de resultados anteriores; verificar múltiples resultados históricos y selección determinista.

## 4. Observabilidad e integración

- [x] 4.1 Registrar y mostrar fichas reutilizadas, solicitadas y recibidas y resultados de análisis reutilizados; probar conteos y cobertura histórica sin datos privados.
- [ ] 4.2 Validar en staging con datos sintéticos, ambas fuentes, perfil cambiado, concurrencia y fallo de detalle; registrar reducción de solicitudes y llamadas IA, revisar riesgo de información desactualizada y preservar evidencia antes de solicitar promoción.
