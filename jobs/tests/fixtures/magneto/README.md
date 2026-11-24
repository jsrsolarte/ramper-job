# Fixtures de Magneto

Estas muestras conservan la estructura observada en las dos tarjetas del listado y la ficha compartida, con textos, empresas, identificadores, ubicaciones y valores reemplazados por datos sintéticos. No contienen HTML original, perfiles, CV ni datos personales.

## Cobertura estructural

- `listing-medellin.html`: tarjeta con fecha, título enlazado, empresa, contrato y ubicación simple.
- `listing-multiple-locations.html`: segunda tarjeta de la captura de listado, con fecha ausente y ubicación de trabajo remoto; sirve para validar campos opcionales.
- `detail.html`: ficha independiente con `JobPosting` JSON-LD, varias ubicaciones, secciones de requisitos y responsabilidades, y discrepancia sintética de salario. El máximo estructurado en cero representa un dato inválido, no un tope salarial.

## Rutas vistas en el material compartido

- Listado: `/co/trabajos/buscar/ultimos-3-dias/coordinador-de?order=desc_relevance`.
- Medellín + procesos + últimos tres días: `/co/trabajos/buscar/loc-medellin-antioquia/procesos/ultimos-3-dias?order=desc_relevance`.
- La segunda captura de listado corresponde a esta combinación y contiene dos tarjetas con ubicación Medellín. No se ha probado que la ruta respete cada filtro ni que otras ciudades sigan la misma convención.

## Observaciones y límites

- Las tarjetas observadas usan clases con sufijos generados; los sufijos pueden cambiar. Los selectores de producción deben apoyarse en prefijos/estructura y tener pruebas ante cambios.
- El `aria-label` de las tarjetas incluye un identificador compuesto por título e ID; los fixtures no guardan el valor observado. No se presupone que sea estable como ID de vacante.
- La ficha compartida tenía una URL canónica cuya ruta no coincidía con el título de la ficha. La ruta no debe prevalecer sobre el título; si la identidad no puede confirmarse, conservar únicamente los datos del listado.
- La fuente expone ubicaciones múltiples y datos estructurados que pueden contradecir el contenido visible. Se debe conservar la procedencia y evitar sobrescribir un dato fiable con un valor dudoso.
- Las capturas no incluyen cabeceras HTTP ni evidencia de autorización para consultas automatizadas. Estos fixtures permiten trabajo offline, pero no prueban rutas, recencia, ubicación ni permiso de acceso.
