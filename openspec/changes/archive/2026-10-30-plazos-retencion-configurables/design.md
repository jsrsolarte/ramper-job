# Design

## Context

El descarte de recomendaciones y el archivado de seguimientos son tareas diarias con umbrales definidos actualmente en siete y 30 días. El centro administrativo expone parámetros operativos y conserva auditoría de cambios.

## Goals / Non-Goals

**Goals:**
- Exponer dos parámetros globales en días, separados por finalidad.
- Hacer que cada tarea consulte el valor vigente al ejecutarse.
- Mantener los valores iniciales y la frecuencia diaria acordados.

**Non-Goals:**
- Cambiar los schedulers o ejecutar tareas inmediatamente al guardar un parámetro.
- Permitir valores por usuario o perfil.
- Cambiar qué estados se archivan o cómo se restaura una recomendación descartada.

## Decisions

### Configuración global persistida y validada

Agregar los parámetros globales de descarte de recomendaciones y archivado por inactividad a la lista permitida del centro administrativo. Mostrar ambos valores con unidades en días, validarlos como enteros entre 1 y 365, usar 7 y 30 como valores iniciales y aplicar la auditoría existente. Cada tarea leerá su propio valor vigente cuando se ejecute y lo aplicará por igual a todos los perfiles; guardar un cambio no disparará una tarea fuera de horario.

**Alternativa considerada:** almacenar los valores como variables de entorno. Se descarta porque se quieren administrar desde el portal sin reiniciar procesos y registrar quién hizo el cambio.

### Conservar tareas periódicas y alcance por perfil

La frecuencia de ejecución continúa siendo diaria. El descarte compara el tiempo en Recomendaciones del perfil con el umbral de descarte; el archivado compara la antigüedad del estado vigente por perfil con el umbral de inactividad. El cambio de estado reinicia el cómputo del archivado, y las tareas mantienen su idempotencia.

**Alternativa considerada:** hacer coincidir la frecuencia del job con el umbral en días. Se descarta porque la ejecución diaria ya permite procesar vencimientos con una demora máxima aproximada de un ciclo.

## Risks / Trade-offs

- [Umbrales pequeños archivan o descartan rápidamente tras el ciclo diario] → Presentar unidades y efecto de cada parámetro en la interfaz y validar el rango permitido.
- [Una configuración puede no estar disponible por una inconsistencia] → Aplicar los valores por defecto de 7 y 30 días si no hay valor guardado válido.
- [Un umbral cambia entre ejecuciones] → Leer el valor al inicio de cada ejecución y auditar el anterior y el nuevo.

## Migration Plan

1. Añadir ambos parámetros al centro administrativo y a la persistencia operativa con defaults de 7 y 30 días.
2. Cambiar cada tarea para leer el parámetro correspondiente al ejecutarse.
3. Verificar validaciones, auditoría, comportamiento de ambos umbrales y que guardar un valor no lance tareas inmediatamente.
