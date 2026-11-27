# Fuente Magneto

Ramper Job consulta una sola página pública por combinación de término y ubicación, con intervalo entre peticiones, timeout y validación de host/DNS/redirecciones. No inicia sesión, no postula y no evita bloqueos. Una respuesta 401, 403 o 429 detiene las peticiones restantes a Magneto en esa ejecución; el resto de fuentes sigue su flujo común.

## Configuración

- `MAGNETO_USER_AGENT`: agente enviado tanto a búsquedas como a fichas. Valor por defecto: `RamperJob (public vacancy search)`.
- Tiempo de espera de conexión/lectura: 5/20 segundos.
- Pausa entre consultas: 0,75 segundos.
- Máximo de redirecciones: 3; se vuelve a validar host y ruta en cada salto.

## Rutas verificadas

- Sin ciudad, término «coordinador de»: `/co/trabajos/buscar/ultimos-3-dias/coordinador-de?order=desc_relevance`.
- Medellín, término «procesos»: `/co/trabajos/buscar/loc-medellin-antioquia/procesos/ultimos-3-dias?order=desc_relevance`.
- Bogotá D.C., término «procesos»: `/co/trabajos/buscar/loc-bogota-d.c.-bogota-d.c./procesos/ultimos-3-dias?order=desc_relevance`, observado tras elegir «Bogotá, D.C., Bogotá D.C., Colombia» en el buscador público.
- El selector público confirmó las ubicaciones que generan las expansiones de perfil. En Antioquia, Bello, Envigado, Itagüí, Sabaneta, La Estrella, Caldas, Copacabana, Girardota y Barbosa usan el patrón `/co/trabajos/buscar/loc-{ciudad}-antioquia/procesos-ultimos-3-dias`. En Cundinamarca, Soacha, Chía, Cajicá, Cota, Funza, Madrid, Mosquera, La Calera, Tenjo, Facatativá y Zipaquirá usan `/co/trabajos/buscar/loc-{ciudad}-cundinamarca/procesos-ultimos-3-dias`. Medellín y Bogotá D.C. mantienen las rutas especiales observadas arriba; las formas de término y recencia reflejan lo que genera el selector.
- Todas las ubicaciones de `expand_locations` para las áreas Medellín y Bogotá tienen una entrada explícita en `MAGNETO_LOCATION_ROUTES`. Otras ubicaciones elegidas directamente en el perfil, como Cali, siguen sin ruta confirmada: el conector informa la consulta parcial y la omite en vez de fabricar un slug.

Las rutas anteriores provienen del material compartido por la persona usuaria. Ver sus condiciones antes de ampliar cobertura; las respuestas HTTP no demuestran permiso.

## Datos y límites

- Se conservan los datos de la tarjeta cuando una ficha está caída o su título, empresa o URL canónica no coincide con el listado.
- Los salarios visibles y de `JobPosting` se guardan con procedencia; un máximo estructurado de cero se descarta.
- Las ubicaciones múltiples se conservan como lista. La jornada estructurada no reemplaza el tipo de contrato visible.
- El ID externo no se infiere del slug ni del `aria-label` mientras la muestra independiente contenga una discrepancia de identidad.
- La primera página y la recencia pueden dejar vacantes relevantes por fuera.
