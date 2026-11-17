# Proposal

## Why

Durante el recorrido obligatorio de primer inicio la persona puede abrir «Mi perfil» y llenar los campos, pero al guardar el formulario la solicitud se redirige antes de persistir. La guía debe permitir completar la configuración inicial sin habilitar prematuramente el resto de la plataforma.

## What Changes

- Permitir guardar el formulario de «Mi perfil» mientras el recorrido obligatorio está activo.
- Mantener a la persona en el paso actual del recorrido después de guardar, para que pueda continuar cuando esté lista.
- Mostrar errores de validación y conservar el paso del recorrido si los datos no son válidos.
- Mantener bloqueadas las demás funciones normales hasta completar el recorrido.

## Capabilities

### New Capabilities

### Modified Capabilities
- `recorrido-inicial`: permitir editar y guardar la configuración de Mi perfil como excepción acotada durante el recorrido obligatorio.

## Impact

- Middleware que restringe navegación durante el recorrido obligatorio.
- Formulario y flujo de guardado de «Mi perfil».
- Progreso del recorrido y tareas que se programan después de guardar cambios del perfil.
