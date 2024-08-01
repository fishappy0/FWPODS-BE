from re import S
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from smb.SMBConnection import SMBConnection
from io import BytesIO
from os import environ
from .models import User
from .serializers import UserSerializer
from rest_framework.views import APIView

import cv2
import json, jwt, datetime
import numpy as np


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

    if "album_id" not in req.GET:
        return JsonResponse(
            {
                "error": "No album_id provided, please add the album_id to the request url."
            }
        )

    conn = SMBConnection(
        environ["smb_username"],
        environ["smb_password"],
        environ["smb_client_machine_name"],
        environ["smb_remote_name"],
        use_ntlm_v2=True,
    )
    conn.connect(environ["smb_ip"], 139)

    if req.GET["album_id"] == "123456":
        file_obj = BytesIO()
        conn.retrieveFile(environ["smb_share_device"], "/Cover1.jpg", file_obj)
        if "size" in req.GET:
            size = req.GET["size"]
            image = cv2.imdecode(np.frombuffer(file_obj.getvalue(), np.uint8), -1)
            image = cv2.resize(image, (int(size), int(size)))
            image = cv2.imencode(".jpg", image)[1].tobytes()
            return HttpResponse(image, content_type="image/jpeg")

        image = file_obj.getvalue()
        return HttpResponse(image, content_type="image/jpeg")

    if req.GET["album_id"] == "7891011":
        file_obj = BytesIO()
        conn.retrieveFile(environ["smb_share_device"], "/Cover2.jpg", file_obj)
        if "size" in req.GET:
            size = req.GET["size"]
            image = cv2.imdecode(np.frombuffer(file_obj.getvalue(), np.uint8), 1)
            image = cv2.resize(image, (int(size), int(size)))
            image = cv2.imencode(".jpg", image)[1].tobytes()
            return HttpResponse(image, content_type="image/jpeg")

        image = file_obj.getvalue()
        return HttpResponse(image, content_type="image/jpeg")

    return JsonResponse(
        {"error": "Invalid album_id provided, please provide a valid album_id."}
    )


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


class RegisterView(APIView):
    def post(self, req):
        serializer = UserSerializer(data=req.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


class LoginView(APIView):
    def post(self, req):
        username = req.data["username"]
        password = req.data["password"]
        user = User.objects.filter(username=username).first()
        if user is None:
            return JsonResponse({"error": "Invalid username or password"}, status=400)
        if not user.check_password(password):
            return JsonResponse({"error": "Invalid username or password"}, status=400)
        payload = {
            "user_id": user.user_id,
            "exp": datetime.datetime.now() + datetime.timedelta(days=1),
        }
        token = jwt.encode(payload, "random salt here idk", algorithm="HS256")
        return JsonResponse({"token": token}, status=200)
