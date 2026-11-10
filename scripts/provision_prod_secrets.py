#!/usr/bin/env python3
"""Interactively provision production Kubernetes Secrets without echoing values."""

from __future__ import annotations

import getpass
import os
import secrets
import subprocess
import sys
import tempfile
from pathlib import Path


NAMESPACE = "prod"
APP_SECRET = "ramper-job-secrets"
REGISTRY_SECRET = "mcp-gateway-ghcr-prod"
KUBECTL = ["microk8s", "kubectl"]


class ProvisionError(Exception):
    """A safe-to-display error that never contains secret values."""


def kubectl(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            [*KUBECTL, *args],
            input=input_text,
            capture_output=True,
            check=False,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ProvisionError("No se pudo ejecutar kubectl en este servidor.") from exc


def ensure_namespace() -> None:
    result = kubectl(["get", "namespace", NAMESPACE, "-o", "name"])
    if result.returncode:
        raise ProvisionError("No existe el namespace prod o no hay acceso al clúster.")


def get_secret_type(name: str) -> str | None:
    result = kubectl(["-n", NAMESPACE, "get", "secret", name, "-o", "jsonpath={.type}"])
    if result.returncode == 0:
        return result.stdout.strip()
    if "NotFound" not in result.stderr:
        raise ProvisionError(f"No se pudo comprobar el Secret {name}; no se modificó ninguno.")
    return None


def require_single_line(label: str, value: str) -> str:
    if not value or "\n" in value or "\r" in value:
        raise ProvisionError(f"{label} debe tener un valor de una sola línea.")
    return value


def create_manifest(args: list[str]) -> str:
    result = kubectl(["create", "secret", "generic", *args, "--dry-run=client", "-o", "yaml"])
    if result.returncode:
        raise ProvisionError("kubectl no pudo preparar los Secrets; no se aplicaron.")
    return result.stdout


def main() -> int:
    if not sys.stdin.isatty():
        print("Error: ejecuta este provisionador desde una terminal interactiva.", file=sys.stderr)
        return 1
    if not Path("/dev/shm").is_dir() or not os.path.ismount("/dev/shm"):
        print("Error: /dev/shm no es un sistema temporal montado; no se guardaron valores.", file=sys.stderr)
        return 1

    try:
        ensure_namespace()
        if get_secret_type(APP_SECRET) is not None:
            raise ProvisionError(f"El Secret {APP_SECRET} ya existe; no se modificó ninguno.")
        registry_type = get_secret_type(REGISTRY_SECRET)
        if registry_type != "kubernetes.io/dockerconfigjson":
            raise ProvisionError(
                f"No existe el Secret Docker config esperado {REGISTRY_SECRET}; "
                "no se creó ningún Secret."
            )

        print("Se crearán Secrets solo en el namespace prod.")
        print("La clave Django y la contraseña PostgreSQL se generarán aquí.")
        print("OmniRoute se solicitará sin mostrar lo que escribas.")
        print(f"Se referenciará {REGISTRY_SECRET} sin leer ni copiar sus datos.")
        if input("Continuar? [s/N] ").strip().lower() not in {"s", "si", "sí"}:
            print("Cancelado; no se modificó ningún Secret.")
            return 0

        django_key = secrets.token_urlsafe(64)
        postgres_password = secrets.token_urlsafe(48)
        omniroute_key = require_single_line(
            "OMNIROUTE_API_KEY", getpass.getpass("OMNIROUTE_API_KEY (entrada oculta): ")
        )
        with tempfile.TemporaryDirectory(prefix="ramper-prod-", dir="/dev/shm") as temp_dir:
            temp_path = Path(temp_dir)
            app_env = temp_path / "app-secrets.env"
            app_env.write_text(
                f"DJANGO_SECRET_KEY={django_key}\n"
                f"POSTGRES_PASSWORD={postgres_password}\n"
                f"OMNIROUTE_API_KEY={omniroute_key}\n",
                encoding="utf-8",
            )
            app_env.chmod(0o600)

            manifests = create_manifest(
                ["-n", NAMESPACE, APP_SECRET, f"--from-env-file={app_env}"]
            )
            created = kubectl(["create", "-f", "-"], input_text=manifests)
            if created.returncode:
                raise ProvisionError(
                    "kubectl no pudo aplicar el Secret de la aplicación. Revisa su nombre y tipo antes de "
                    "volver a ejecutar; no se imprimieron valores."
                )

        print(f"Secret creado en {NAMESPACE}: {APP_SECRET}.")
        print(f"GHCR se referencia desde {REGISTRY_SECRET}; no se copió su contenido.")
        print("Los valores no se mostraron y los archivos temporales se eliminaron.")
        return 0
    except ProvisionError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (EOFError, KeyboardInterrupt):
        print("Cancelado; no se imprimieron valores.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
