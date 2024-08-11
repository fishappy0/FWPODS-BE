from os import environ, path

from smb.SMBConnection import SMBConnection
from .utils import utils
from io import BytesIO
import re


def scan_songs(Song, Artist, Album, path_to_item):
    if Song.objects.all().count() > 350:
        return
    conn = SMBConnection(
        username=environ["smb_username"],
        password=environ["smb_password"],
        my_name=environ["smb_client_machine_name"],
        remote_name=environ["smb_remote_name"],
    )
    conn.connect(environ["smb_ip"], 139)
    root_path = "Album"
    artist_folders_smb_path = conn.listPath("win-games-and-misc", f"/{root_path}/")
    artist_folder = [f.filename for f in artist_folders_smb_path][2:]
    for artist in artist_folder:
        if Song.objects.all().count() > 350:
            return
        album_folders_smb_path = conn.listPath(
            "win-games-and-misc", f"/{root_path}/{artist}"
        )
        artist_obj = Artist(artist_name=artist)
        artist_obj.save()
        for album_path_smb in album_folders_smb_path[2:]:
            album_path = album_path_smb.filename
            temp_id_and_year = re.search(r"\[[0-9]+\].*\[.*\]", album_path).group(0)
            album_id = temp_id_and_year.split(" ")[0].replace("[", "").replace("]", "")
            if Album.objects.filter(album_id=album_id).exists():
                continue
            album_year = (
                temp_id_and_year.split(" ")[1].replace("[", "").replace("]", "")
            )

            album_name = ""
            if not utils.has_weird_tags(album_path):
                album_name = album_path.split("]")[0]
            else:
                album_name = album_path.split("]")[1]
            album_name = album_name.split("[")[0]

            album = Album(
                album_id=album_id,
                album_name=album_name,
                artist=artist,
                release_year=album_year,
            )
            album.save()

            album_instance = Album.objects.get(album_id=album_id)
            path_to_album = path_to_item(
                album_id=album_instance,
                path=f"{root_path}/{artist}/{album_path}",
            )
            path_to_album.save()
            songs = conn.listPath(
                "win-games-and-misc", f"{root_path}/{artist}/{album_path}"
            )
            for song in songs[2:]:
                song_path = song.filename
                if not song_path.endswith(".flac"):
                    continue
                song_name = song_path.split("-")[2].split(".")[0]
                song_id = int(album_id + song_path.split("-")[0].replace(" ", ""))
                song = Song(
                    song_id=song_id,
                    artist_id=artist_obj,
                    album_id=album_instance,
                    song_name=song_name,
                )
                song.save()
                song_instance = Song.objects.get(song_id=song_id)
                path_to_song = path_to_item(
                    song_id=song_instance,
                    path=f"{root_path}/{artist}/{album_path}/{song_path}",
                )
                path_to_song.save()
                file_obj = BytesIO()
                conn.retrieveFile(
                    "win-games-and-misc",
                    f"{root_path}/{artist}/{album_path}/{song_path}",
                    file_obj,
                )
                duration = utils.get_flac_duration(file_obj)
                song.duration = duration
                song.save()


def test_startup():
    print("[FWPODS-BE][STARTUP] The app is ready!")
