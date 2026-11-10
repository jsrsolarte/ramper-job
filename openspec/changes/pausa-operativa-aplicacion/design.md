# Design

## Context

Los ciclos de ingesta y análisis tienen disparadores periódicos y también pueden iniciarse desde acciones administrativas. La pausa debe cubrir todos esos caminos. El estado de pausa debe persistir ante reinicios; el portal administrativo debe seguir disponible.

## Goals / Non-Goals

**Goals:**
- Tener un único estado global de procesamiento, controlado desde administración.
- Evitar que trabajos pendientes comiencen mientras está pausado y permitir su continuidad al reanudar.
- Evitar que un trabajo en curso avance a una nueva unidad de procesamiento después de una pausa.

**Non-Goals:**
- Apagar el servidor, la interfaz web, el inicio de sesión o el centro administrativo.
- Cancelar a la fuerza una llamada externa de IA o scraping que ya esté ejecutándose.
- Eliminar o descartar trabajo pendiente por activar la pausa.

## Decisions

- Persistir el estado global en la configuración operativa de la aplicación, con valor inicial habilitado para mantener el comportamiento actual.
- Consultar la pausa tanto al iniciar un trabajo como antes de iniciar cada unidad posterior del flujo. Esto cubre tareas periódicas, trabajos en cola y ejecuciones que atraviesan varias etapas.
- Al pausar, permitir que termine la unidad indivisible actualmente en ejecución y dejar el trabajo sin avanzar a la siguiente etapa. Al reanudar, retomar desde el estado pendiente existente y proteger la reanudación contra duplicados.
- Rechazar con explicación nuevas acciones manuales que inicien búsqueda o análisis mientras la pausa esté activa; la acción podrá repetirse después de reanudar.
- Registrar en auditoría los cambios administrativos de pausa y reanudación, igual que otros parámetros operativos.

## Risks / Trade-offs

- [Una pausa puede ocurrir entre la verificación del estado y el inicio de un trabajo] → Revalidar el estado en el punto de ejecución y hacer idempotente la transición de cada etapa.
- [El trabajo externo que ya inició puede consumir recursos después de activar la pausa] → La pausa detiene la siguiente unidad y evita prometer cancelación inmediata.
- [Una integración puede omitir la verificación global] → Centralizar la regla y verificar todos los puntos de entrada automáticos y administrativos.

## Migration Plan

- La configuración ausente equivale a procesamiento habilitado; no requiere detener el servicio ni migrar trabajos existentes.
- Si se revierte el cambio, el comportamiento operativo vuelve a habilitado y los trabajos pendientes siguen disponibles.
