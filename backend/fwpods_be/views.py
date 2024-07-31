from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from smb.SMBConnection import SMBConnection
from io import BytesIO
from os import environ
import json


def index(request):
    return HttpResponse(
        "The server works! Please use the API routes to interact with the server."
    )


def test_playlist(req):
    if "playlist_id" in req.GET:
        return JsonResponse(
            {
                "requested_playlist_id": req.GET["playlist_id"],
                "songs": ["123456", "7891011"],
            }
        )
    else:
        return JsonResponse(
            {
                "error": "No playlist_id provided, please add the playlist_id to the request url."
            }
        )


def test_image(req):
    username = environ["smb_username"]
    password = environ["smb_password"]
    client_machine_name = environ["smb_client_machine_name"]
    remote_name = environ["smb_remote_name"]
    share_device = environ["smb_share_device"]

    ip = environ["smb_ip"]
    conn = SMBConnection(
        username, password, client_machine_name, remote_name, use_ntlm_v2=True
    )
    conn.connect(ip, 139)

    file_obj = BytesIO()
    conn.retrieveFile(share_device, "/Cover.jpg", file_obj)
    image = file_obj.getvalue()
    return HttpResponse(image, content_type="image/jpeg")


def test_song(req):
    username = environ["smb_username"]
    password = environ["smb_password"]
    client_machine_name = environ["smb_client_machine_name"]
    remote_name = environ["smb_remote_name"]
    share_device = environ["smb_share_device"]

    ip = environ["smb_ip"]
    conn = SMBConnection(
        username, password, client_machine_name, remote_name, use_ntlm_v2=True
    )
    conn.connect(ip, 139)

    file_obj = BytesIO()
    if "song_id" in req.GET:
        song = req.GET["song_id"]
        if song == "123456":
            conn.retrieveFile(
                share_device,
                "/Album/Tee Lopes, GameChops/[M] Gerudo Valley (Zelda) [175609369] [2021]/01 - Tee Lopes, GameChops - Gerudo Valley (Zelda).flac",
                file_obj,
            )
            song = file_obj.getvalue()
            return HttpResponse(song, content_type="audio/mpeg")
        if song == "7891011":
            conn.retrieveFile(
                share_device,
                "/Album/AJR/[E] OK ORCHESTRA [174275317] [2021]/11 - AJR - World's Smallest Violin(Explicit).flac",
                file_obj,
            )
            song = file_obj.getvalue()
            return HttpResponse(song, content_type="audio/mpeg")

    else:
        return JsonResponse(
            {"error": "No song_id provided, please add the song_id to the request url."}
        )
