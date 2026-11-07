# Design

## Context

Las pantallas actuales usan plantillas Django y una hoja de estilos compartida. El dashboard, el perfil y el ingreso están implementados, así que el cambio puede concentrarse en presentación y estructura semántica sin introducir otro frontend ni cambiar el flujo de datos.

## Goals / Non-Goals

**Goals:**
- Establecer una identidad visual cálida, profesional y reconocible para Ramper Job.
- Hacer que las vacantes recomendadas sean fáciles de recorrer y comparar.
- Reutilizar patrones visuales en formularios, avisos, navegación y estados vacíos.
- Mantener compatibilidad con el renderizado del servidor y pantallas móviles.

**Non-Goals:**
- Cambiar autenticación, scraping, análisis de compatibilidad o administración.
- Incorporar una SPA, framework CSS o dependencia visual externa.
- Cambiar el contenido funcional acordado o agregar nuevos flujos de producto.

## Decisions

### Conservar las plantillas Django y crear tokens visuales compartidos

Se mantendrán las vistas renderizadas en servidor. La hoja de estilos definirá tokens para color, tipografía, espaciado, bordes, elevación y foco; las plantillas aplicarán componentes reutilizables a navegación, botones, avisos, campos, tarjetas y estados vacíos. Se elige esta solución porque cubre las pantallas actuales sin duplicar componentes ni añadir compilación de frontend. Se descarta introducir una SPA o una biblioteca de componentes para un conjunto pequeño de páginas.

### Mantener el verde como acento de marca y suavizar el lienzo

La interfaz usará fondos marfil/gris cálido, texto azul tinta y el verde actual como acento para marca, compatibilidad y acciones primarias. Colores secundarios se reservarán para avisos y aspectos por revisar. El contraste, el foco visible y la legibilidad prevalecen sobre el uso decorativo del color. Se conserva el reconocimiento de la paleta actual mientras se gana profundidad visual.

### Dar prioridad visual a los datos de la vacante

En el dashboard, cada tarjeta presentará primero empresa, cargo y puntaje; después mostrará ubicación y condiciones estructuradas, seguidas por palabras clave concisas. Las razones y brechas quedarán disponibles en una sección secundaria plegable. La acción hacia la publicación original quedará claramente identificada al final. Las tarjetas no dependerán solo del color para comunicar una coincidencia.

### Resolver la composición de forma responsiva

La navegación y el contenido se adaptarán a pantallas estrechas mediante CSS, con una columna para las tarjetas, formularios a ancho disponible y controles táctiles cómodos. Se usarán fuentes del sistema y recursos CSS existentes, sin solicitudes a servicios externos ni nuevas dependencias.

## Risks / Trade-offs

- [Un rediseño puede reducir el espacio visible para vacantes] → Mantener el contenido principal compacto y evitar ornamentación que compita con cargo, puntaje y descripción.
- [Los colores pueden tener contraste insuficiente en ciertos estados] → Revisar combinaciones de texto, botones, avisos y foco durante la validación visual.
- [Los textos largos de vacantes pueden deformar tarjetas en móvil] → Probar títulos y descripciones largos en anchos estrechos y permitir que el contenido fluya sin desbordamiento.

## Migration Plan

No hay migración de datos. Actualizar las plantillas y estilos de forma compatible con las rutas existentes, y revisar ingreso, dashboard con y sin resultados y edición del perfil en escritorio y móvil. El rollback consiste en revertir los cambios de presentación.
