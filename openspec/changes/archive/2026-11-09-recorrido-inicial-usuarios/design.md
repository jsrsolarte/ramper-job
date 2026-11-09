# Design

## Context

La aplicación usa vistas y plantillas Django para Mi perfil, el dashboard y sus siete pestañas. Los controles del perfil y los estados de las vacantes ya tienen comportamientos especificados; el recorrido los explica sin alterar los formularios ni el seguimiento. El perfil se relaciona uno a uno con la cuenta, pero la guía también debe recordar su estado para cuentas que aún no hayan creado un perfil.

## Goals / Non-Goals

**Goals:**

- Mantener una experiencia guiada coherente al moverse entre Mi perfil y el dashboard.
- Guardar el avance en el servidor, separado de los datos y revisiones del perfil.
- Hacer que los elementos explicados sean identificables aunque cambie el texto o el estilo visual de una plantilla.
- Mantener accesibilidad de teclado y uso en móvil sin añadir una dependencia de tour.

**Non-Goals:**

- Cambiar cómo se busca, analiza, filtra, descarta o sigue una vacante.
- Editar automáticamente preferencias o completar formularios como parte del recorrido.
- Crear recorridos para administración ni un editor de recorridos configurable.

## Decisions

### Guardar progreso separado del perfil

Crear un registro de progreso uno a uno con la cuenta autenticada, con estado (sin iniciar, en curso, completado u omitido), versión de guía y paso actual estable. El modelo vive en la app `profiles`, que ya gestiona preferencias por aspirante, pero su clave es la cuenta y no la revisión del perfil. No usar `localStorage` como fuente de verdad: no comparte el estado entre dispositivos y no cubre sesiones nuevas.

No hace falta rellenar registros mediante migración. Las cuentas aspirantes existentes sin registro recibirán la oferta inicial en su siguiente visita; la pueden omitir y reabrir más tarde. Las cuentas administradoras no crean ni consultan progreso.

### Declarar pasos con identificadores estables

Mantener una secuencia de pasos identificada por claves estables y rutas de destino. En Mi perfil se explican CV, frases de búsqueda, ubicaciones y trabajo remoto, y el umbral. En el dashboard se explican compatibilidad, filtro temporal, detalles del análisis y pestañas de seguimiento. Añadir atributos `data-tour` a los controles explicados en las plantillas en vez de enlazar la lógica a clases de presentación o texto visible.

El recorrido empieza en Recomendaciones resaltando «Mi perfil» antes de explicar cualquier campo. Después de presentar todos los controles del perfil, resalta «Volver a mis vacantes» para regresar a Recomendaciones. Al activar cualquiera de esos enlaces mientras está en su paso, el recorrido guarda el paso siguiente y continúa en la página de destino. Los pasos sobre recomendaciones van después del regreso al dashboard; «Por analizar» se explica al final.

El botón de avance guarda el paso siguiente. Si el paso vive en otra página, la navegación abre esa ruta y presenta el paso al cargar. Si el usuario cierra la guía, el paso permanece guardado para reanudarlo; omitir y completar son estados distintos. Un enlace visible «Ver guía» inicia otra vez desde el primer paso y es exclusivo de aspirantes.

### Usar vistas Django autenticadas para guardar el estado

Exponer una acción autenticada para iniciar, avanzar, retroceder, completar u omitir el recorrido. Validar en el servidor que el usuario no sea administrador y que el identificador del paso pertenezca a la versión vigente. Proteger las mutaciones con CSRF y derivar las páginas de destino de la secuencia del servidor, no de una URL arbitraria enviada por el navegador.

El último cambio guardado para una cuenta es el que se reanuda en otro dispositivo. Si hay sesiones simultáneas, prevalece la última acción recibida; no se necesita sincronización en tiempo real.

### Mantener el componente pequeño y accesible

Implementar la capa visual con JavaScript y CSS del proyecto, y cargarla desde la plantilla base solo para cuentas aspirantes cuando haya un paso activo. El recorrido enfoca el diálogo, anuncia el paso y su total, mantiene visibles los controles para avanzar, retroceder y omitir, y devuelve el foco al cerrar. En pantallas estrechas, el diálogo se acomoda sin ocultar el texto ni los controles explicados; no se requiere mantener un recorte perfecto del elemento destacado.

## Risks / Trade-offs

- [Los selectores de destino pueden quedar obsoletos al editar plantillas] → Los pasos usan atributos `data-tour` explícitos y una prueba comprueba cada destino.
- [Una persona puede omitir la guía antes de guardar su perfil] → Omitir solo cambia el estado de la guía; no modifica el requisito de CV ni activa búsquedas.
- [Varias sesiones pueden avanzar el mismo recorrido a la vez] → La persistencia de cada acción mantiene el último paso recibido; la guía no promete edición colaborativa.
- [La descripción del umbral puede confundirse con el filtro temporal] → Los pasos presentan ambos controles por separado y aclaran que el filtro solo afecta las recomendaciones visibles.

## Migration Plan

1. Crear la tabla de progreso por cuenta sin cambiar ni recalcular perfiles existentes.
2. Desplegar las vistas y controles del recorrido junto con sus pasos y marcadores de destino.
3. Las cuentas aspirantes sin progreso reciben la oferta inicial; pueden cerrar, omitir o reabrir la guía.
4. Para revertir, retirar los controles y vistas del recorrido. La tabla de progreso se puede conservar sin afectar el perfil ni las vacantes.
