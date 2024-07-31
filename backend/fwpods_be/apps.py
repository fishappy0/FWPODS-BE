from django.apps import AppConfig
from .startup import *


class FwpodsBeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fwpods_be"

    def ready(self) -> None:
        test_startup()
