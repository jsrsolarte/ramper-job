# Validación en staging: retirar rúbrica v2

Fecha: 2026-11-18

## Implementación

- Cambio OpenSpec: `retirar-rubrica-v2`.
- CI validó el commit de aplicación `096db6cce89c532615f746677288fd6d5a832b36` en [ejecución 44407116989](https://github.com/jsrsolarte/ramper-job/actions/runs/44407116989): suite Django de 359 pruebas y 25 comprobaciones adicionales aprobadas; validación de Kustomize y construcción de imagen aprobadas.
- Imagen publicada: `ghcr.io/jsrsolarte/ramper-job:096db6cce89c532615f746677288fd6d5a832b36`.
- Flux en staging: `Ready=True`, `Healthy=True`, revisión `staging@sha1:664c1b23d32ea21f1514a44eb6c7c3bf241ebd7a`, que aplica la imagen anterior.
- Web, beat y worker quedaron listos (1/1, 1/1 y 3/3). `/healthz` respondió HTTP 200.
- Configuración activa observada: versión 3, rúbrica 3, prompt 6. La pausa global permaneció activa antes, durante y después.
- Producción no se modificó: Flux conserva `main@sha1:b8ff76f67025fbab2bfd3e5aa1f15101fd17806c`.

## Análisis sintético integral

Se creó una cuenta, un perfil con CV DOCX y una vacante completamente sintéticos, sin datos de una persona real. El análisis y la organización se ejecutaron como tareas aisladas dentro del proceso web de staging. El bypass de pausa fue local a ese proceso y la llamada de encolado de la organización se sustituyó por una función vacía; luego se ejecutó directamente la tarea de organización. No se reanudó Celery ni se añadió trabajo a la cola global.

- Perfil sintético: ID 5.
- Vacante sintética: ID 845.
- Análisis: ID 754, rúbrica 3, estado `completed`, equivalente visual `5,0` estrellas.
- Organización: ID 475, estado `completed`; el análisis terminó con `organization_status=completed`.
- Scoring: succeeded, 1.480 tokens de entrada, 331 de salida, 5.257 ms.
- Organización: succeeded, 362 tokens de entrada, 141 de salida, 3.499 ms.
- La pausa global se verificó activa al terminar.

Los registros sintéticos se conservaron en staging para inspección. Las configuraciones y resultados históricos v2 no se borraron ni se recalcularon; la v2 permanece solo en la presentación de históricos.
