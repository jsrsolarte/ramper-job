# Spec Delta

## Purpose

Define las comprobaciones de salud del despliegue productivo para que Kubernetes pueda validar disponibilidad sin generar redirecciones ni exponer diagnósticos internos.

## ADDED Requirements

### Requirement: Comprobar salud de producción sin redirecciones
Las sondas internas de producción SHALL recibir respuestas HTTP exitosas directas de los endpoints de salud, sin redirección a HTTPS, y esos endpoints SHALL NOT revelar detalles internos de dependencias.

#### Scenario: Kubernetes comprueba disponibilidad
- **WHEN** una sonda consulta `/healthz` o `/readyz` por HTTP dentro del pod
- **THEN** el endpoint responde directamente con un estado HTTP exitoso, sin redirección, y solo informa salud genérica

#### Scenario: Una solicitud pública usa HTTP
- **WHEN** una persona solicita la aplicación por HTTP
- **THEN** la política productiva redirige la navegación a HTTPS y la excepción de las sondas no desactiva esa protección para otras rutas

#### Scenario: Una dependencia no está lista
- **WHEN** PostgreSQL o Redis no está disponible
- **THEN** `/readyz` responde como no disponible sin exponer mensajes de conexión, credenciales ni datos operativos
