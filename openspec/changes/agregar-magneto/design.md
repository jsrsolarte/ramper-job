# Design

## Context

`ComputrabajoConnector` separa listado y detalle, devuelve `JobListing` y se registra en `jobs/registry.py`. La primera muestra del usuario registra HTTP 200, `text/html` y 20 elementos `ItemList`; la segunda, `magneto-medellin.html`, contiene dos elementos y dos tarjetas de Medellín, procesos y últimos tres días. Ambas muestran anclas con título y rutas `/co/empleos/…` dentro de `article`, con empresa, contrato, salario y ubicación en las tarjetas examinadas. La muestra independiente `magneto-ficha.html` contiene un `article` de detalle y un `JobPosting` JSON-LD; los archivos HTML no incluyen cabeceras HTTP. No se pudo reproducir la solicitud desde este entorno por resolución DNS.

## Goals / Non-Goals

**Goals:** integrar la fuente en las etapas existentes y conservar resultados parciales.

**Non-Goals:** autenticación, postulación, inferencia de identidad entre portales y paginación adicional.

## Decisions

- Crear un conector `magneto_co` con `fetch_titles` y `fetch_details` y registrarlo en el flujo común. Reutilizar preselección por título y caché de fichas; no añadir un pipeline paralelo.
- Construir búsquedas desde términos y ubicaciones expandidas. Se observan `/co/trabajos/buscar/ultimos-3-dias/coordinador-de?order=desc_relevance` y `/co/trabajos/buscar/loc-medellin-antioquia/procesos/ultimos-3-dias?order=desc_relevance`; la segunda muestra contiene dos resultados con Medellín en sus tarjetas. El 23 de noviembre se confirmó mediante el buscador público Bogotá D.C. como `loc-bogota-d.c.-bogota-d.c.`. Esto evidencia Medellín y Bogotá D.C., no el mapeo de las demás ubicaciones expandidas. No asumir que tres días equivale a una ventana exacta ni cubre interrupciones prolongadas.
- El 24 de noviembre, el selector público confirmó las ubicaciones derivadas de las áreas del perfil. Los municipios de Antioquia (Bello, Envigado, Itagüí, Sabaneta, La Estrella, Caldas, Copacabana, Girardota y Barbosa) usan `/loc-{ciudad}-antioquia/procesos-ultimos-3-dias`; los de Cundinamarca (Soacha, Chía, Cajicá, Cota, Funza, Madrid, Mosquera, La Calera, Tenjo, Facatativá y Zipaquirá) usan `/loc-{ciudad}-cundinamarca/procesos-ultimos-3-dias`. Medellín y Bogotá conservan sus rutas especiales verificadas. El conector debe construir rutas para todas las ubicaciones que generan las expansiones de perfil; para ubicaciones individuales ajenas a esas áreas, como Cali, no se inventa el slug y se registra una consulta parcial.
- Analizar HTML con BeautifulSoup, usando enlaces de ficha y estructura de tarjetas, evitando depender exclusivamente de sufijos CSS generados. El `ItemList` incrustado puede servir de evidencia o apoyo, pero no sustituye la extracción de títulos y campos de tarjetas. Capturar fixtures depurados y sintéticos. No interpretar toda la respuesta como JSON.
- En la ficha observada el `article` contiene título en `p`, empresa, contrato, cupos y fecha; un resumen presenta experiencia, formación, salario y varias ubicaciones; la descripción incluye secciones de formación, experiencia, funciones, horario y salario. El JSON-LD `JobPosting` aporta fecha, vigencia, empresa, lista de ubicaciones, salario y otros campos como evidencia complementaria, no necesariamente equivalente al texto visible. Extraer secciones estructuradas cuando sea posible y preservar ubicaciones múltiples sin convertirlas en una sola ciudad inventada; aplicar elegibilidad a cada ubicación y modalidad explícita.
- La ficha solicitada como `auxiliar-administrativo-siberia-y-aledanos-1148450` presenta contenido y metadatos de «Analista de Logística de Materias Primas - Guarne/Medellin», mientras la URL canónica conserva el slug solicitado. La muestra no demuestra por qué ocurre ni si el ID identifica el contenido. No derivar título, ubicación ni ID fiable del slug; conservar la URL y detectar discrepancias entre listado y ficha antes de confirmar detalle. Ante identidad incompatible o ambigua, conservar el listado y señalar el detalle no confirmado para evitar asociar vacantes distintas.
- La ficha presenta $1.838.450 en resumen y $2.730.728 en descripción; JSON-LD indica mínimo 1.838.450 y máximo 0, y `PART_TIME` mientras el contrato visible es por obra o labor. Preservar ambos salarios con procedencia y no interpretar el cero como máximo válido ni confundir jornada con contrato. No sobrescribir silenciosamente conflictos ni inferir modalidad.
- Mantener la identidad por fuente y URL normalizada y el ID externo cuando sea fiable. Las publicaciones duplicadas en distintas bolsas pueden permanecer separadas; no fusionar por semejanza de título y empresa.
- Como en Computrabajo, validar HTTPS, hosts permitidos, DNS público y cada redirección; establecer tiempos de espera, pausas y límite de redirecciones. Ante 401, 403, 429 o autenticación detener la fuente en esa ejecución, conservar parciales e informar estado; no evadir controles. Verificar reglas aplicables y uso permitido de las rutas antes de activarlas: la respuesta 200 por sí sola no demuestra permiso. No enviar CV, credenciales ni información personal en las consultas.
- Limitar a primera página para acotar volumen como Computrabajo. La relevancia y recencia pueden omitir vacantes; no se garantiza cobertura completa. Cuando falten campos, conservarlos como desconocidos, incluso ubicación y modalidad.

## Risks / Trade-offs

- [Clases HTML cambiantes o respuestas parciales] → fixtures representativos, selectores robustos y estado de error observable.
- [La ficha puede presentar contenido, salario o metadatos contradictorios] → conservar procedencia, rechazar confirmación cuando la identidad sea dudosa y cubrir conflictos con fixtures.
- [No existe validación general de filtros y ubicaciones] → resolver con pruebas autorizadas durante implementación; no inventar campos.
- [Primera página y filtro de recencia pierden resultados] → documentar límite y evaluar recuperación en cambio posterior.
- [La misma vacante aparece en varias fuentes] → conservar registros separados y seguimientos existentes.

## Revisión de condiciones de acceso (23 de noviembre de 2026)

- La [página pública de vacantes](https://www.magneto365.com/co/trabajos/servicios-nutresa?paginator%5Bpage%5D=2) enlaza un documento titulado «Términos y condiciones». La ruta enlazada (`/co/politicas/terminos-condiciones-uso-plataforma-magneto`) redirige a una página cuyo contenido visible es la [Política de tratamiento de datos personales](https://www.magneto365.com/co/politicas?content=terminos-condiciones-uso-plataforma-magneto), no términos de uso del sitio.
- Esa política describe finalidades y tratamiento de datos de usuarios; no establece en el contenido consultado permiso ni prohibición específica para extraer vacantes públicas mediante consultas automatizadas.
- La web de búsqueda pública muestra vacantes en páginas indexables, pero eso por sí solo no confirma autorización de acceso automatizado. Las capturas locales tampoco incluyen cabeceras HTTP o evidencia de permiso.
- La persona usuaria indicó que conoce las políticas y pidió continuar con el uso personal y privado previsto. La implementación se limitará a páginas públicas, agente de usuario identificable, pausas, primera página, validación de host/DNS/redirecciones y parada ante bloqueos; no usará autenticación ni intentará evadir controles.
- Resultado documentado: el documento público alcanzable desde el enlace de términos es una política de datos y no confirma reglas específicas para acceso automatizado. La persona usuaria conoce ese límite y autorizó continuar con la implementación. Revaluar si se descubre una prohibición explícita; no inferir autorización comercial ni cobertura completa.

## Migration Plan

Registrar la fuente y configuración, incrementar VERSION en MINOR y ejecutar pruebas locales con datos sintéticos. Validar en staging solo mediante el flujo autorizado y con datos sintéticos; deshabilitar o retirar el conector si falla. La promoción productiva requiere autorización explícita.

## Validación local (24 de noviembre de 2026)

- Se construyó la imagen temporal con el Dockerfile; `.dockerignore` excluye `.env`, CV, bases de datos locales y datos runtime.
- Pasaron 54 pruebas relevantes (`jobs.tests.test_magneto`, `profiles.tests.test_locations`, `jobs.tests.test_refresh`, `jobs.tests.test_detail_cache` y `jobs.tests.test_search_groups`) con SQLite temporal, broker Celery en memoria y fixtures sintéticos. No se iniciaron workers ni se hicieron solicitudes a Magneto.
- `scripts/validate_release_version.py --tag v1.2.0 --existing-tags v1.0.0` aceptó `v1.2.0`; `VERSION` quedó en `1.2.0`.
- El workflow `CI and staging image` #108 pasó desde `main`, probó la rama candidata `codex/agregar-magneto-staging-20261124` (`241dbef5694bd3cbc94967b5af23e09fd267efd5`) y fijó esa imagen en staging. No se cambió producción.
- Flux reportó `Ready=True` y `Healthy=True` en `staging@sha1:ee45570f17d546589e1646d4e19af80dd0fc1d92`; web, worker y beat quedaron listos 1/1 con la imagen SHA. `/healthz` y `/readyz` respondieron HTTP 200 dentro del pod web.
- Se observaron timeouts iniciales de sondas mientras arrancaban worker y beat; se recuperaron, Flux completó reconciliación y los pods quedaron listos sin reinicios.
- CI ejecutó las pruebas completas del proyecto, incluyendo las pruebas de Magneto con fixtures sintéticos. No se disparó una búsqueda real ni se consultaron páginas de Magneto durante esta validación.
