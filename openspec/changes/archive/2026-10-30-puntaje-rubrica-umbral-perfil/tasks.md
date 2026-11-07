# Tasks

## 1. Persistencia y versionado de compatibilidad

- [x] 1.1 Agregar al perfil el puntaje mínimo entero de 0 a 10 con predeterminado 0 y crear la migración; verificar que perfiles existentes migran con 0 y que los valores inválidos no se aceptan.
- [x] 1.2 Persistir desglose de criterios, estado y evidencia junto con el identificador/versionado de rúbrica en cada análisis; verificar lectura y escritura de los cinco criterios y mantener análisis históricos sin convertir sus puntajes.
- [x] 1.3 Actualizar los esquemas y la validación de los resultados del modelo para exigir cada criterio y sus límites; verificar que respuestas incompletas o fuera de rango se rechazan sin guardar análisis parcial.

## 2. Rúbrica y cálculo del puntaje

- [x] 2.1 Versionar la rúbrica común con pesos 4, 2, 2, 1 y 1, anclas, estados de evidencia y ejemplos en la configuración enviada al modelo; verificar que el prompt/schema describen los mismos criterios y no incluyen ubicación.
- [x] 2.2 Hacer que la aplicación sume los puntos válidos de los criterios y guarde el entero resultante de 0 a 10; verificar suma mínima, máxima y casos intermedios, incluyendo criterios `no_aplica`.
- [x] 2.3 Mostrar `/10` y el desglose por criterio, con evidencia en una sección secundaria; verificar que las tarjetas no muestren el puntaje histórico como si usara la rúbrica nueva.

## 3. Umbral de perfil y dashboard

- [x] 3.1 Añadir el selector de puntaje mínimo al formulario del perfil y conservar su valor; verificar opciones de 0 a 10, valor inicial 0 y validación de límites.
- [x] 3.2 Aplicar el umbral a las vacantes del perfil antes de ordenar y paginar; verificar inclusión en el límite exacto, exclusión por debajo, mínimo 0 y aislamiento entre perfiles.
- [x] 3.3 Confirmar que guardar un umbral distinto no crea una revisión de CV ni encola un análisis; verificar el comportamiento observable y documentarlo junto al control del perfil.

## 4. Reprocesamiento e integración

- [x] 4.1 Encolar idempotentemente el análisis más reciente por combinación vigente de perfil y vacante al activar la rúbrica; verificar que reintentos no duplican trabajo y que el análisis previo se conserva.
- [x] 4.2 Mantener fuera de los puntajes `/10` los resultados históricos y pendientes hasta completar el nuevo análisis; verificar que solo resultados de la versión actual se ordenen y filtren por el umbral.
- [x] 4.3 Ejecutar las verificaciones de integración del cambio y actualizar la documentación de operación del reprocesamiento; verificar migración, solicitud/respuesta del modelo, dashboard filtrado y recuperación ante fallo de OmniRoute.
