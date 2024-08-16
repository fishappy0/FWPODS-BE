from django.apps import AppConfig
import sys

from matplotlib.artist import Artist
from .startup import *
from os import environ


class FwpodsBeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "fwpods_be"

    def ready(self) -> None:
        migration_running = False

        if (
            "makemigrations" in sys.argv
            or "migrate" in sys.argv
            or "makemigration" in sys.argv
            or "celery" in sys.argv
        ):
            migration_running = True

        # Prevent ready() from running twice in the production environment
        if environ.get("RUN_MAIN", None) != "true" and not migration_running:
            # Has to be imported here to avoid the app is not ready error
            from .models import Song
            from .models import Album
            from .models import Artist
            from .models import path_to_item

            test_startup()
            scan_songs(Song, Artist, Album, path_to_item)
