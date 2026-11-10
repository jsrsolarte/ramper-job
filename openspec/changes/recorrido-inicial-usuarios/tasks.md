# Tasks

## 1. Persistencia y acceso por cuenta

- [x] 1.1 Crear el modelo de progreso del recorrido vinculado uno a uno con la cuenta y su migración; verificar que la migración se aplique y que el registro conserve versión, estado y paso.
- [x] 1.2 Añadir pruebas de aislamiento por cuenta y exclusión de administradores; verificar que cada aspirante solo lea o cambie su propio progreso y que una cuenta administradora no cree estado.

## 2. Ciclo de vida del recorrido

- [x] 2.1 Implementar las vistas autenticadas para iniciar, avanzar, retroceder, omitir, completar y volver a abrir el recorrido; verificar acciones válidas, protección CSRF, validación de pasos y destinos internos.
- [x] 2.2 Probar la oferta inicial, la reanudación del paso guardado, la persistencia al completar u omitir y el reinicio manual; verificar los flujos con cuentas aspirantes y administrativas.

## 3. Pasos de perfil y dashboard

- [x] 3.1 Añadir identificadores estables a los controles de Mi perfil y del dashboard, y el enlace visible para volver a abrir la guía; verificar que cada paso tenga un destino único y que el enlace no se muestre a administradores.
- [x] 3.2 Implementar la capa guiada con avance entre páginas, paso y total, omisión y cierre reanudable; verificar que la navegación entre Mi perfil y dashboard presenta el paso guardado sin alterar datos de formularios ni vacantes.
- [x] 3.3 Añadir pruebas de contenido para CV, frases, ubicaciones, modalidad remota, umbral, estrellas, filtro temporal, análisis y nombres/propósito de las pestañas; verificar que el descarte automático y el filtro temporal se describan como funciones distintas.
- [x] 3.4 Ordenar la guía para empezar en Recomendaciones, recorrer toda la configuración del perfil, volver a Recomendaciones y luego continuar con el dashboard; verificar la secuencia y los destinos con pruebas.

## 4. Accesibilidad e integración

- [x] 4.1 Añadir y ejecutar pruebas de teclado, foco, anuncios accesibles y disposición móvil del recorrido; verificar que se pueda avanzar, retroceder, omitir y cerrar desde una pantalla estrecha.
- [x] 4.2 Ejecutar la suite de Django en CI; verificar que los pasos y las rutas entre perfil y dashboard pasan las pruebas automatizadas.
- [ ] 4.3 Revisar el recorrido visual en móvil y escritorio; verificar inicio, transición al activar ambos enlaces, reanudación en una sesión nueva, omisión y reapertura.
