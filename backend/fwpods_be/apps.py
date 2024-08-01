from django.apps import AppConfig
from .startup import *
from os import environ


class FwpodsBeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fwpods_be"

    def ready(self) -> None:
        # Prevent ready() from running twice in the production environment
        if environ.get("RUN_MAIN", None) != "true":
            test_startup()
