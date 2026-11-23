# Design

## Context

La plantilla común y la plantilla de login renderizan el pie; el contexto Django expone `APP_VERSION`. Producción recibe el valor SemVer, mientras el workflow de staging lo sustituye por el SHA del candidato. `VERSION` en `staging` declara actualmente `1.1.0`. Jobs ya tiene una paleta y logos propios. La fuente de marca RamPer no registra aún un master aprobado; la persona autorizó usar el lockup claro v0.6 solo en este pie.

## Goals / Non-Goals

**Goals:**

- Mostrar el valor SemVer incluido en la misma revisión de código que construye la imagen, también en staging.
- Mantener independiente el tag/digest de imagen usado para rastrear el artefacto.
- Presentar en todas las pantallas un pie centrado, adaptable y accesible, con Jobs como identidad principal y «By RamPer» como firma secundaria.
- Usar el lockup claro v0.6 solamente en el pie de Jobs, conservando su procedencia exploratoria.

**Non-Goals:**

- Cambiar el formato de tags inmutables o digest de contenedores.
- Declarar aprobado el logo RamPer, modificar el repositorio `ramper-brand` o usar la exploración en header, favicon, PWA u otras superficies.
- Cambiar la paleta o los logos propios de Jobs.

## Decisions

### Distinguir la versión visible del identificador de imagen

El workflow que fija el candidato de staging leerá `VERSION` del SHA validado y lo pondrá en `APP_VERSION`; el `newTag` seguirá siendo el SHA inmutable. Producción seguirá recibiendo la versión SemVer del release. La plantilla usará `APP_VERSION` y mantendrá «no disponible» si falta. Antes del despliegue de prueba, `VERSION` sube de `1.1.0` a `1.1.1` como corrección compatible.

Alternativa considerada: mostrar el SHA completo y añadirle una etiqueta «versión». Se descarta porque sigue exponiendo un identificador técnico en la interfaz. Leer `VERSION` directamente dentro de la plantilla también se descarta: el contexto común ya entrega el dato y producción lo recibe del proceso de liberación.

### Mantener la firma RamPer secundaria y localizada

Copiar `assets/explorations/ramper/usage-v0.6/lockup-light.svg` desde `jsrsolarte/ramper-brand` en la revisión `1f7545e5457fb6a49ecf616fa8bd5d1afdf6654b` a un recurso estático propio de Ramper Job, documentando origen y estado de exploración. El pie mostrará «By» como texto y este lockup pequeño con texto alternativo; no se modifica el SVG ni se registra como aprobado.

Alternativa considerada: usar el logo de Jobs como firma RamPer o reconstruir el monograma. Se descarta porque confundiría identidades o alteraría una referencia de marca sin autorización.

### Integrar el pie con la interfaz existente

Conservar el pie común compartido y su alineación central; componer versión y firma con espaciado compacto, colores de texto y acentos existentes de Jobs, contraste legible y ajuste móvil sin recorte ni desbordamiento. La marca RamPer mantiene los colores propios del lockup.

Alternativa considerada: añadir un segundo bloque de navegación o una franja de marca dominante. Se descarta para que el pie no compita con la aplicación ni cambie la jerarquía actual.

## Risks / Trade-offs

- [El valor SemVer de staging puede adelantarse a la versión de producción] → Se muestra la versión declarada por el código candidato; staging sigue identificado técnicamente por SHA y la liberación productiva por tag/digest.
- [El lockup v0.6 sigue siendo exploratorio] → Limitarlo a la firma secundaria del pie, fijar su procedencia y no presentarlo como master aprobado.
- [Un pie centrado puede ocupar más espacio en móviles] → Permitir que sus elementos se envuelvan y comprobar anchuras pequeñas con contenido completo.

## Migration Plan

No hay migración de datos. Incrementar `VERSION`, actualizar el pin de staging para pasar SemVer en `APP_VERSION`, construir y probar la imagen candidata, y verificar login, dashboard, perfil y administración en escritorio y móvil. Si la validación falla, revertir el cambio del workflow, el pie y `VERSION` en staging. No se promueve a producción sin autorización explícita.
