import getpass
import sys

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Crea una sola cuenta administradora inicial desde una terminal interactiva."

    def handle(self, *args, **options):
        user_model = get_user_model()
        if user_model.objects.filter(is_superuser=True).exists():
            raise CommandError("Ya existe una cuenta administradora; no se creó otra.")
        if not sys.stdin.isatty():
            raise CommandError("Este comando requiere una terminal interactiva para ocultar la contraseña.")

        username = input("Usuario administrador: ").strip()
        if not username:
            raise CommandError("El usuario no puede estar vacío.")
        email = input("Correo electrónico (opcional): ").strip()
        password = getpass.getpass("Contraseña (entrada oculta): ")
        password_confirmation = getpass.getpass("Confirma la contraseña: ")
        if password != password_confirmation:
            raise CommandError("Las contraseñas no coinciden.")

        user = user_model(username=username, email=email)
        try:
            validate_password(password, user=user)
        except ValidationError as exc:
            raise CommandError("La contraseña no cumple la política de seguridad.") from exc

        if user_model.objects.filter(username=username).exists():
            raise CommandError("Ya existe una cuenta con ese nombre de usuario.")

        user_model.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS("Cuenta administradora creada."))
