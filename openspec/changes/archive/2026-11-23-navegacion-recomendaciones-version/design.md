# Design

## Context

Ver `proposal.md` para la motivación y las deltas para el contrato. `templates/base.html` centraliza la navegación autenticada, muestra «Mi perfil» y «Análisis» a aspirantes y todavía no tiene pie de página. La ruta de inicio abre el dashboard, pero no hay un enlace etiquetado como «Recomendaciones». La política de liberaciones asigna tags semánticos a producción y distingue staging mediante SHA; el flujo de publicación genera metadatos de versión, SHA y digest, pero la plantilla no recibe el identificador desplegado.

## Goals / Non-Goals

**Goals:**

- Hacer que Recomendaciones sea un destino explícito y fácil de encontrar desde las pantallas de aspirantes.
- Identificar la versión o build desplegado en todas las páginas, incluida la entrada pública.
- Mantener el identificador visible vinculado al mismo artefacto inmutable que se promovió.
- Hacer que el agente actualice una única versión canónica al implementar cambios y que el pipeline la consuma al promover.

**Non-Goals:**

- Cambiar las pestañas, filtros o contenido de Recomendaciones.
- Asignar una versión de producto a builds de staging.
- Cambiar el flujo de liberación o reconstruir una imagen al promoverla.

## Decisions

### Añadir el enlace en la plantilla común de aspirantes

Agregar «Recomendaciones» al lado de «Mi perfil» en la navegación principal de cuentas aspirantes, apuntando al dashboard con el estado de recomendaciones. Mantenerlo oculto para cuentas administrativas, que no usan el dashboard de un perfil aspirante. Marcarlo como página actual cuando se consulta Recomendaciones.

Alternativa considerada: depender del logo que lleva a inicio. Se descarta porque no comunica el destino ni deja claro dónde volver desde otras pantallas.

### Mostrar la versión en el pie de página común

Añadir un pie de página discreto a la plantilla base para que la identificación aparezca de forma consistente en login, vistas de aspirantes y vistas administrativas. Si el metadato no está configurado, mostrar el estado «versión no disponible» y no usar un literal fijado en la plantilla.

Alternativa considerada: poner la versión en la barra superior. Se elige el pie de página para no competir con la navegación principal, especialmente en pantallas estrechas.

### Inyectar el identificador del artefacto en tiempo de ejecución

La aplicación lee un metadato de despliegue inmutable, provisto al ejecutar la imagen. `VERSION` es la fuente canónica de la próxima versión semántica y el agente la incrementa según SemVer al implementar cambios de producto. Producción recibe ese valor del commit de liberación; staging recibe el SHA o identificador de commit usado para etiquetar su imagen. La etiqueta no exige reconstruir la imagen probada para añadir la versión de producción. El workflow de liberación rechaza una etiqueta `vX.Y.Z` que no coincida con `VERSION`.

Alternativa considerada: deducir la versión consultando Git desde el contenedor. Se descarta porque la imagen de ejecución no debe depender de metadatos Git presentes en tiempo de ejecución y el SHA por sí solo no expresa la versión de producción.

## Risks / Trade-offs

- [Una configuración de despliegue puede pasar una etiqueta que no corresponde a la imagen] → Generar el valor desde los metadatos que ya vinculan tag, SHA y digest, y verificar la correspondencia durante el flujo de liberación.
- [La barra superior puede quedar estrecha en móvil] → Ubicar la versión en el pie común y mantener el enlace de Recomendaciones junto a Mi perfil con diseño adaptable.
- [El enlace puede aparecer activo en vistas que no son Recomendaciones] → Asociar el estado actual solo a la ruta de recomendaciones, no a cualquier pantalla del dashboard.

## Migration Plan

No requiere migrar datos. La navegación queda disponible al desplegar la nueva plantilla. El pie mostrará el identificador cuando el entorno proporcione metadatos; los despliegues sin ese dato indicarán que la versión no está disponible hasta que su configuración se actualice. La reversión puede retirar el enlace y el pie sin cambiar rutas ni datos de usuario.
