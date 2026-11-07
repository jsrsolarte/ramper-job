# Proposal

## Why

La rúbrica actual solo asigna puntos enteros y reparte el peso entre criterios amplios. Necesitamos más precisión y una forma transparente de reflejar requisitos realmente obligatorios, sin tratar la falta de información como incapacidad ni penalizar características personales como la discapacidad.

## What Changes

- Permitir décimas en los puntos por criterio y en el puntaje final, manteniendo la escala de 0 a 10.
- Incorporar deducciones configurables para requisitos laborales explícitos y críticos cuando exista evidencia directa de contradicción.
- Dejar los requisitos sin evidencia como pendientes de verificar, sin deducción automática.
- Excluir discapacidad y otros atributos personales no relacionados con el trabajo de cualquier puntaje o penalización.
- Mantener los filtros de puntaje como enteros entre 0 y 10 y conservar la precisión decimal para el orden, la etiqueta accesible y el desglose, mostrando solo estrellas en la tarjeta.
- Versionar la rúbrica y reprocesar análisis vigentes sin mezclar puntajes de versiones distintas.

## Capabilities

### New Capabilities

### Modified Capabilities

- `compatibilidad-vacantes`: permitir precisión decimal, requisitos críticos con deducciones explicables y salvaguardas frente a atributos personales.
- `dashboard-vacantes`: presentar puntajes decimales sin cambiar los filtros enteros.

## Impact

- Modelo, validación, cálculo y presentación accesible de análisis con puntajes decimales.
- Configuración versionada de rúbrica y reprocesamiento de resultados vigentes.
- Antes de aplicar el cambio en local, limpiar vacantes y datos asociados; conservar cuentas, perfiles y configuración. No ejecutar esa limpieza en producción.
- Sin cambios al scraping ni a la ingesta de vacantes.
