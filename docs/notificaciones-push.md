# Resumen diario por notificaciones push

El resumen push es opcional por dispositivo y permanece desactivado hasta que la persona lo activa desde **Mi perfil**. El indicador dentro de Ramper Job funciona aunque no haya configuración push.

## Configuración por entorno

Configura estas variables en el gestor de secretos de cada entorno. No guardes la clave privada en el repositorio ni reutilices la misma pareja entre entornos:

- `PUSH_VAPID_PUBLIC_KEY`: clave pública URL-safe para que el navegador solicite la suscripción.
- `PUSH_VAPID_PRIVATE_KEY`: escalar privado P-256 de 32 bytes codificado en Base64 URL-safe (sin relleno), en el formato que acepta `pywebpush`. Debe mantenerse secreto; no se admite directamente el contenido PEM.
- `PUSH_VAPID_SUBJECT`: contacto de la aplicación, por ejemplo `mailto:admin@example.com`.
- `PUSH_SUBSCRIPTION_ENCRYPTION_KEY`: clave secreta estable y exclusiva del entorno para cifrar endpoints y claves de dispositivo guardados en la base de datos. Si se omite, se deriva de `DJANGO_SECRET_KEY`; cambiar esa clave requiere conservar la antigua para recuperar las suscripciones existentes.

Con `py-vapid` instalado en un entorno controlado, genera una pareja nueva y muestra la clave pública en formato `applicationServerKey`:

```sh
python -m py_vapid.main --gen --applicationServerKey --private-key private_key.pem
```

El comando genera la clave privada en PEM y muestra la pública URL-safe. Antes de configurar `PUSH_VAPID_PRIVATE_KEY`, convierte el PEM al escalar privado P-256 de 32 bytes y codifícalo en Base64 URL-safe sin `=` final. Haz la conversión y carga directamente en el gestor de secretos, sin imprimir ni registrar el valor. Configura la clave pública impresa en `PUSH_VAPID_PUBLIC_KEY`. Conserva el PEM fuera del repositorio y limita su acceso al proceso de la aplicación.

Genera la clave de cifrado en el entorno seguro con `python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`. Guárdala en `PUSH_SUBSCRIPTION_ENCRYPTION_KEY` y no la cambies mientras existan suscripciones cifradas con ella.

En una instalación local se pueden exportar las variables desde un archivo `.env` privado. Staging y producción deben recibir valores mediante sus propios mecanismos secretos. Esta spec no cambia infraestructura ni crea Secrets.

La entrega requiere HTTPS, permiso del navegador y disponibilidad de su servicio push. El resumen no garantiza recepción; cada aviso usa contenido genérico y TTL corto.
