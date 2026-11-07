# Tasks

## 1. Listas y ciudades cercanas

- [x] 1.1 Cambiar el editor visual de frases y ubicaciones de chips a filas de listas accesibles; verificar agregar, quitar y guardar.
- [x] 1.2 Agregar expansión normalizada para Medellín/Valle de Aburrá y Bogotá/municipios cercanos; verificar variantes de acentos y ubicaciones desconocidas.
- [x] 1.3 Pasar ubicaciones expandidas al conector y al análisis; consultar cada combinación de frase y ciudad en Elempleo; deduplicar resultados de múltiples consultas.
- [x] 1.4 Capturar la fecha/etiqueta de publicación y aplicar la ventana de últimas 24 horas cuando exista hora exacta o el filtro «Hoy y ayer» de Elempleo cuando no; mostrar la recencia sin prometer exactitud inexistente.

## 2. Identidad y consolidación de vacantes

- [x] 2.1 Crear `dedupe_key` por bolsa, calculada con ID estable o huella de datos normalizados; mantener unicidad junto a la bolsa.
- [x] 2.2 Hacer que el guardado reutilice la vacante por clave aunque cambie la URL y conserve URLs alternativas.
- [x] 2.3 Migrar vacantes duplicadas preexistentes, reasignar análisis y resolver análisis redundantes conservando el resultado completado más reciente.

## 3. Integración

- [x] 3.1 Verificar parsing de rutas por ciudad, deduplicación en página y persistencia, análisis existentes y despliegue local.
