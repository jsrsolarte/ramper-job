# Design

## Context

El dashboard ya limita las recomendaciones según el mínimo de puntaje persistido en el perfil y ordena los resultados por compatibilidad. El filtro nuevo es temporal y afecta únicamente la consulta del listado. Véase `proposal.md` para la motivación y `specs/dashboard-vacantes/spec.md` para los comportamientos requeridos.

## Goals / Non-Goals

**Goals:**
- Mantener separados el umbral persistido del perfil y el filtro temporal del listado.
- Hacer que el filtrado funcione con el orden actual y con la paginación existente.

**Non-Goals:**
- Cambiar el cálculo del puntaje, la rúbrica de IA o la configuración del perfil.
- Persistir el filtro del dashboard en la base de datos o en la sesión.

## Decisions

- Leer el umbral temporal desde un parámetro GET `score_min`. La ausencia del parámetro significa mostrar todas las vacantes permitidas por el perfil.
- Validar el parámetro como número entre 0 y 10. Si está ausente o es inválido, no aplicar un umbral adicional; el mínimo del perfil sigue activo.
- Aplicar como mínimo efectivo el mayor valor entre `profile.min_score` y `score_min`. Esto mantiene la política del perfil como límite inferior y permite que el selector solo reduzca más el conjunto.
- Mostrar una opción base equivalente a “Todos los permitidos por el perfil” y opciones de puntaje que estrechen el conjunto. Los valores menores al mínimo del perfil no aportan un filtro adicional.
- Conservar `score_min` en los enlaces de paginación. El valor vive en la URL para poder recargar o compartir el estado del listado sin guardar preferencias.
- No crear migraciones: el filtro es estado temporal de la vista y no requiere cambios al modelo.

Se considera guardar el valor en la sesión, pero se elige el parámetro GET porque hace explícito el estado del listado, funciona al recargar y se puede propagar directamente en los enlaces de página.

## Risks / Trade-offs

- **El mínimo del perfil puede cambiar mientras un enlace filtrado está abierto** → recalcular el máximo efectivo en cada solicitud, usando siempre el valor actual del perfil.
- **Un enlace contiene un puntaje mal formado o fuera de rango** → ignorar el filtro temporal y mantener la barrera del perfil, sin fallar la vista.
- **Opciones menores al mínimo del perfil pueden confundir** → el selector debe rotular la opción base como todas las vacantes permitidas y no presentar esos valores como un filtro efectivo.

## Migration Plan

No hay migración de datos. Desplegar la vista y la plantilla junto con la selección temporal. Para revertir, retirar el control y el procesamiento de `score_min`; los mínimos persistidos del perfil y los análisis existentes no cambian.
