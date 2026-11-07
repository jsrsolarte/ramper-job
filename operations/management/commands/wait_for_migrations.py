import time

from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection
from django.db.migrations.executor import MigrationExecutor


class Command(BaseCommand):
    help = "Espera hasta que todas las migraciones de la base estén aplicadas."

    def add_arguments(self, parser):
        parser.add_argument("--timeout", type=float, default=900)
        parser.add_argument("--interval", type=float, default=5)

    def handle(self, *args, **options):
        timeout = options["timeout"]
        interval = options["interval"]
        if timeout <= 0 or interval <= 0:
            raise CommandError("El timeout y el intervalo deben ser mayores que cero.")

        deadline = time.monotonic() + timeout
        while True:
            try:
                executor = MigrationExecutor(connection)
                pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
            except DatabaseError:
                connection.close()
                pending = [True]

            if not pending:
                self.stdout.write(self.style.SUCCESS("Todas las migraciones están aplicadas."))
                return

            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CommandError("La base todavía tiene migraciones pendientes; expiró la espera.")
            time.sleep(min(interval, remaining))
