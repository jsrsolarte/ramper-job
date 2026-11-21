# Proposal

## Why

La comprobación de una reparación JSON puede modificar caracteres dentro de cadenas antes de compararlas y aceptar evidencia alterada. Se requiere corregir urgentemente esta brecha de integridad.

## What Changes

- Verificar reparaciones sin transformar claves ni valores literales, incluidos escapes y cadenas anidadas.
- Rechazar cualquier reparación cuya equivalencia no se pueda demostrar y conservar la recuperación existente.
- Cubrir el caso reproducido y casos adversos con pruebas sintéticas.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `compatibilidad-vacantes`: precisar la preservación verificable de valores durante la reparación de JSON.

## Impact

Afecta la comparación de reparaciones y sus pruebas en `matching`. No cambia la rúbrica, los datos históricos, el modelo ni el flujo de despliegue. Se prioriza staging y requiere autorización explícita para promoción a producción.
