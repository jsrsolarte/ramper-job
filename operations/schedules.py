from datetime import timedelta

from celery.schedules import schedule
from django.conf import settings
from django.db import DatabaseError


class DatabaseRefreshInterval(schedule):
    """Allow Beat to pick up the persisted interval while it runs."""

    def __init__(self, run_every=None, relative=False, nowfun=None, app=None):
        run_every = run_every or timedelta(minutes=settings.JOB_REFRESH_MINUTES)
        super().__init__(run_every=run_every, relative=relative, nowfun=nowfun, app=app)

    def is_due(self, last_run_at):
        try:
            from .parameters import current_refresh_interval_minutes

            minutes = current_refresh_interval_minutes()
        except DatabaseError:
            minutes = settings.JOB_REFRESH_MINUTES
        self.run_every = timedelta(minutes=minutes)
        return super().is_due(last_run_at)
