# Proposal

## Why

El formulario manual actual requiere copiar varios datos de una publicación. Permitir que la administración pegue solo la URL pública reduce ese trabajo y hace que la vacante use el mismo registro global y el mismo análisis individual por perfil.

## What Changes

- Permitir registrar una vacante administrativa pegando únicamente su URL pública.
- Para esta primera versión, reconocer y extraer fichas públicas de El Empleo.
- Validar URLs contra proveedores compatibles y reutilizar conectores para admitir otros proveedores posteriormente.
- Encolar extracción, deduplicación y análisis por perfil de forma asíncrona, con estado y errores comprensibles en el admin.

## Capabilities

### New Capabilities

### Modified Capabilities
- `ingesta-vacantes`: crear una vacante a partir de una URL pública soportada y conectarla al flujo normal de ingesta y análisis.

## Impact

- Formulario y procesamiento administrativo, resolución segura de proveedor y extracción de ficha pública.
- Reutiliza deduplicación global, elegibilidad y análisis individual por perfil de la carga manual existente.
- Depende de `carga-manual-vacantes-admin` y de los prerrequisitos de centro administrativo y análisis; debe completarse antes de stage.
