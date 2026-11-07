# Tasks

## 0. Preparar los datos locales

- [x] 0.1 Eliminar en la base local las vacantes existentes y sus análisis y seguimientos dependientes, conservando cuentas, perfiles y configuraciones; verificar que no queden vacantes y que el perfil de prueba siga disponible.

## 1. Modelo y configuración de la rúbrica

- [x] 1.1 Migrar el puntaje final a decimal de una cifra sin conversión de datos históricos locales; verificar que la migración aplica sobre el conjunto de vacantes vacío y que se mantienen los límites 0.0–10.0.
- [x] 1.2 Versionar la configuración de deducción crítica con valor inicial 2.0; verificar que cada versión de análisis conserva los parámetros exactos utilizados.

## 2. Análisis y cálculo

- [x] 2.1 Actualizar el esquema de respuesta para puntajes decimales por criterio y evidencia de requisitos críticos; verificar aceptación de una décima y rechazo de precisión o campos inválidos.
- [x] 2.2 Calcular el total en la aplicación como suma de criterios menos deducciones, con piso 0.0 y techo 10.0; verificar varios requisitos críticos y límites.
- [x] 2.3 Ajustar instrucciones de rúbrica para diferenciar evidencia contradicha de ausencia de evidencia y excluir discapacidad y atributos personales; verificar que no se deduce por datos faltantes ni por atributos excluidos.
- [x] 2.4 Conservar en el desglose los requisitos críticos, evidencia y deducciones; verificar que el puntaje puede explicarse criterio por criterio.

## 3. Presentación y reprocesamiento

- [x] 3.1 Mostrar puntajes y deducciones con una cifra decimal, manteniendo filtros enteros; verificar orden por valor decimal y filtrado desde el umbral entero inclusivo.
- [x] 3.2 Activar la nueva versión para los análisis que se creen después de la limpieza local; verificar que el dashboard filtra por la versión activa y no mezcla resultados de distintas rúbricas.
