# Design

## Context

`static/app.css` usa variables y colores verdes, tipografía Inter declarada sin provisión visible y algunos elementos Georgia; `static/admin-ramper.css` mantiene una segunda paleta. `templates/base.html`, el ingreso independiente y `templates/admin/base_site.html` muestran la marca anterior. El manifiesto actual usa nombre e iconos anteriores. Véase la propuesta para el alcance.

## Goals / Non-Goals

**Goals:**
- Incorporar la identidad de Jobs sin alterar navegación, formularios o flujos de trabajo.
- Mantener una fuente rastreable de tokens y recursos y validar su uso real.

**Non-Goals:**
- Replicar mecánicamente los ejemplos de componentes o rediseñar el logo aprobado.
- Cambiar la funcionalidad de instalación, autenticación, datos o lógica de negocio.

## Decisions

- Copiar los recursos aprobados de `assets/approved/jobs/` y tokens de `ramper-brand`, fijando un commit o etiqueta verificados y documentando origen, versión y licencia. Usar logo claro u oscuro según superficie, favicon aprobado y ningún recurso exploratorio. Evitar depender de un repositorio privado en tiempo de ejecución.
- Usar Sora para títulos e identidad e Inter para UI, con suministro estable y licencia verificada; documentar procedencia, pesos y alternativa técnica si la carga falla. Evitar asumir que las fuentes están instaladas en el dispositivo.
- Adoptar roles de marca `#348CF5`, `#67D4F4`, `#12263F` y `#2D6CDF`, con superficie compartida `#F6F7FB`. Usar `#2D6CDF` para texto de marca sobre claro y acción con texto blanco solo tras medir cada combinación real. Separar semántica de éxito, advertencia y error; conservar patrones y densidad útiles.
- Actualizar ingreso, plantilla compartida, textos visibles y administración, incluidos estilos y elementos hardcodeados; no limitarse a cambiar variables raíz. Conservar nombres internos, rutas y referencias técnicas donde renombrarlos no aporte al usuario.
- El cambio `instalar-aplicacion-chrome` controla manifiesto, iconos 192/512 y pruebas PWA. Implementar conjuntamente o coordinar archivos para evitar duplicación, conservando `id`, inicio y alcance; validar actualización de instalaciones existentes.
- Verificar contraste real: texto normal 4.5:1, texto grande y componentes funcionales 3:1 según WCAG 2.2 AA; revisar foco, teclado, estados, tamaños móviles y escritorio. Las capturas y verificaciones no sustituyen pruebas funcionales.

## Risks / Trade-offs

- [Colores semánticos o elementos verdes hardcodeados quedan inconsistentes] → Inventariar vistas y revisar estados y estilos de administración, no hacer sustitución ciega de colores.
- [Fuentes o recursos no disponibles o sin licencia verificable] → Resolver procedencia y distribución antes de integrar; documentar cualquier bloqueo y no afirmar cumplimiento si falla la carga.
- [Nombre e iconos de instalación se actualizan con demora por caché] → Mantener identidad estable y comprobar actualización real en Chrome de escritorio y Android.
- [Una adaptación visual degrada legibilidad o uso] → Revisar con datos sintéticos, teclado, tamaños de pantalla y contrastes, preservando controles y recorridos.

## Migration Plan

Integrar recursos y estilos de forma reversible en un entorno local aislado; ejecutar pruebas y revisión visual con datos sintéticos. Coordinar con instalación antes de probar en staging compartido. La promoción o mutación de producción requiere autorización explícita. Revertir el cambio de aplicación restaura la presentación anterior; una instalación existente puede conservar temporalmente recursos en caché.
