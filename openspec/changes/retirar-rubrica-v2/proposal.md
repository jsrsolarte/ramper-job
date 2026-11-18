# Proposal

## Why

La rúbrica v2 aún puede seleccionarse en código y genera una escala incompatible con las estrellas actuales. El sistema debe usar una única rúbrica vigente para evitar resultados nuevos con reglas antiguas.

## What Changes

- **BREAKING**: eliminar la selección, el prompt y la validación de puntuación nuevos con rúbrica v2; los nuevos análisis usan exclusivamente rúbrica v3 (0–5, medios puntos).
- Migrar automáticamente configuraciones activas antiguas a la configuración vigente al inicializarla, sin cambiar análisis históricos ni borrar datos.
- Conservar la lectura y presentación de resultados históricos ya almacenados.
- Desplegar el cambio solo a staging y ejecutar un análisis sintético completo, incluida la organización de la vacante.

## Capabilities

### New Capabilities

### Modified Capabilities
- `compatibilidad-vacantes`: los análisis nuevos usan solo rúbrica v3; registros antiguos siguen siendo consultables.

## Impact

Afecta la selección de configuración, prompts y esquemas JSON de `matching`, la presentación del desglose en `dashboard`, pruebas y la especificación de compatibilidad. No requiere migración de datos ni elimina análisis. La validación final se hará en staging con datos sintéticos; no se promoverá a producción.
