from celery import Celery

import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
backend = Celery("backend")
backend.config_from_object("django.conf:settings", namespace="CELERY")
backend.autodiscover_tasks()


@backend.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
