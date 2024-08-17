import parser
from re import S
from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from smb.SMBConnection import SMBConnection
from io import BytesIO
from os import environ
from .models import Album, Artist, Runtimes, User
from .models import path_to_item
from .models import Song
from .models import Playlist
from .models import PlaylistSongs
from .models import TransactionWindow
from .models import LikedSongs
from .models import SongWeight
from .serializers import UserSerializer
from .shared_tasks import *
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.parsers import FormParser
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from django.db.models.aggregates import Count
from random import randint

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
    parser_classes = [JSONParser, FormParser]

    def post(self, req):
        serializer = UserSerializer(data=req.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


class LoginView(APIView):
    parser_classes = [JSONParser, FormParser]

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


class GetSongInfo(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        song_id = req.data["song_id"]
        if song_id is None:
            return JsonResponse({"error": "No song_id provided"}, status=400)
        song = Song.objects.filter(song_id=song_id).first()
        if song is None:
            return JsonResponse({"error": "Song not found"}, status=400)
        artist = (
            Artist.objects.filter(artist_id=song.artist_id.artist_id)
            .first()
            .artist_name
        )
        album = Album.objects.filter(album_id=song.album_id.album_id).first().album_name
        return JsonResponse(
            {
                "song_id": song.song_id,
                "song_name": song.song_name,
                "artist": artist,
                "album": album,
            },
            status=200,
        )


class GetSong(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        song_id = req.data["song_id"]
        if song_id is None:
            return JsonResponse({"error": "No song_id provided"}, status=400)
        song_path = path_to_item.objects.filter(song_id=song_id).first()
        if song_path is None:
            return JsonResponse({"error": "Song not found"}, status=400)
        conn = SMBConnection(
            environ["smb_username"],
            environ["smb_password"],
            environ["smb_client_machine_name"],
            environ["smb_remote_name"],
            use_ntlm_v2=True,
        )
        conn.connect(environ["smb_ip"], 139)
        file_obj = BytesIO()
        conn.retrieveFile(environ["smb_share_device"], song_path.path, file_obj)
        song = file_obj.getvalue()
        return HttpResponse(song, content_type="audio/mpeg")


class GetRandomSongs(APIView):
    [JSONParser, FormParser]

    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        num_of_songs = int(req.data["Songs_number"]) or 10
        songs_ids = []
        count = Song.objects.aggregate(count=Count("song_id"))["count"]
        for _ in range(num_of_songs):
            random_index = randint(0, count - 1)
            song = Song.objects.all()[random_index]
            songs_ids.append(song.song_id)

        return JsonResponse({"songs": songs_ids}, status=200)


class GetAllUserPlaylists(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        playlists = Playlist.objects.filter(user=user)
        return JsonResponse(
            {"playlists": [playlist.playlist_id for playlist in playlists]}, status=200
        )


class GetSongInfoMultiple(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        song_ids = req.data["song_ids"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        if song_ids is None:
            return JsonResponse({"error": "No song_ids provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)

        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)

        song_info = []
        for song_id in song_ids:
            song = Song.objects.filter(song_id=song_id).first()
            if song is None:
                return JsonResponse({"error": "Song not found"}, status=400)
            artist = (
                Artist.objects.filter(artist_id=song.artist_id.artist_id)
                .first()
                .artist_name
            )
            album = (
                Album.objects.filter(album_id=song.album_id.album_id).first().album_name
            )
            song_info.append(
                {
                    "song_id": song.song_id,
                    "song_name": song.song_name,
                    "artist": artist,
                    "album": album,
                }
            )
        return JsonResponse({"songs": song_info}, status=200)


class GetPlaylistSongs(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        playlist_id = req.data["playlist_id"]
        if playlist_id is None:
            return JsonResponse({"error": "No playlist_id provided"}, status=400)
        playlist = Playlist.objects.filter(playlist_id=playlist_id).first()
        if playlist is None:
            return JsonResponse({"error": "Playlist not found"}, status=400)
        songs = playlist.songs.all()
        return JsonResponse({"songs": [song.song_id for song in songs]}, status=200)


class GetUserPlaylists(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        playlists = Playlist.objects.filter(user_id=user)
        return JsonResponse(
            {"playlists": [playlist.playlist_id for playlist in playlists]}, status=200
        )


class CreatePlaylist(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        playlist_name = req.data["playlist_name"]
        if playlist_name is None:
            return JsonResponse({"error": "No playlist_name provided"}, status=400)
        playlist = Playlist.objects.create(user_id=user, playlist_name=playlist_name)
        return JsonResponse({"playlist_id": playlist.playlist_id}, status=201)


class UpdatePlaylist(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        playlist_id = req.data["playlist_id"]
        if playlist_id is None:
            return JsonResponse({"error": "No playlist_id provided"}, status=400)
        playlist = Playlist.objects.filter(playlist_id=playlist_id).first()
        if playlist is None:
            return JsonResponse({"error": "Playlist not found"}, status=400)
        song_id = req.data["song_id"]
        if song_id is None:
            return JsonResponse({"error": "No song_id provided"}, status=400)
        song = Song.objects.filter(song_id=song_id).first()
        if song is None:
            return JsonResponse({"error": "Song not found"}, status=400)
        PlaylistSongs(playlist_id=playlist, song_id=song).save()
        return JsonResponse({"playlist_id": playlist.playlist_id}, status=201)


class UpdatePlaylistMultiple(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)

        playlist_id = req.data["playlist_id"]
        if playlist_id is None:
            return JsonResponse({"error": "No playlist_id provided"}, status=400)
        playlist = Playlist.objects.filter(playlist_id=playlist_id).first()
        if playlist is None:
            return JsonResponse({"error": "Playlist not found"}, status=400)

        song_ids = req.data["song_ids"]
        if song_ids is None:
            return JsonResponse({"error": "No song_ids provided"}, status=400)
        for song_id in song_ids:
            song = Song.objects.filter(song_id=song_id).first()
            if song is None:
                return JsonResponse({"error": "Song not found"}, status=400)
            PlaylistSongs(playlist_id=playlist, song_id=song).save()
        return JsonResponse({"playlist_id": playlist.playlist_id}, status=201)


class DeletePlaylist(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        playlist_id = req.data["playlist_id"]
        if playlist_id is None:
            return JsonResponse({"error": "No playlist_id provided"}, status=400)
        playlist = Playlist.objects.filter(playlist_id=playlist_id).first()
        if playlist is None:
            return JsonResponse({"error": "Playlist not found"}, status=400)
        playlist.delete()
        return JsonResponse({"playlist_id": playlist_id}, status=200)


# Add playlist to the transaction window in the database
class PlayPlaylist(APIView):
    [JSONParser, FormParser]

    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        playlist_id = req.data["playlist_id"]
        if playlist_id is None:
            return JsonResponse({"error": "No playlist_id provided"}, status=400)
        playlist = Playlist.objects.filter(playlist_id=playlist_id).first()
        if playlist is None:
            return JsonResponse({"error": "Playlist not found"}, status=400)

        TransactionWindow(playlist_id=playlist).save()
        return JsonResponse({"playlist_id": playlist_id}, status=200)


class GetAllAvailableSongs(APIView):
    def get(self, req):
        songs = Song.objects.all()
        return JsonResponse({"songs": [song.song_id for song in songs]}, status=200)


class LikeSong(APIView):
    [JSONParser, FormParser]

    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        song_id = req.data["song_id"]
        if song_id is None:
            return JsonResponse({"error": "No song_id provided"}, status=400)
        song = Song.objects.filter(song_id=song_id).first()
        if song is None:
            return JsonResponse({"error": "Song not found"}, status=400)
        LikedSongs(user_id=user, song_id=song).save()
        return JsonResponse({"song_id": song_id}, status=201)


class LikeSongMultiple(APIView):
    [JSONParser, FormParser]

    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)

        song_ids = req.data["song_ids"]
        times = req.data["times"] or 1
        if song_ids is None:
            return JsonResponse({"error": "No song_ids provided"}, status=400)
        for _ in range(times):
            for song_id in song_ids:
                song = Song.objects.filter(song_id=song_id).first()
                if song is None:
                    return JsonResponse({"error": "Song not found"}, status=400)
                LikedSongs(user_id=user, song_id=song).save()
        return JsonResponse({"song_ids": song_ids}, status=201)


class RemoveLikeSong(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        song_id = req.data["song_id"]
        if song_id is None:
            return JsonResponse({"error": "No song_id provided"}, status=400)
        song = Song.objects.filter(song_id=song_id).first()
        if song is None:
            return JsonResponse({"error": "Song not found"}, status=400)
        LikedSongs.objects.filter(user_id=user, song_id=song).delete()
        return JsonResponse({"song_id": song_id}, status=200)


class RunLikesUpdate(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)

        # Clear the Song Weight table
        SongWeight.objects.all().delete()

        # Scan the LikedSongs table and update the SongWeight table
        for like in LikedSongs.objects.filter(user_id=user):
            song = like.song_id
            try:
                song_weight = SongWeight.objects.get(song_id=song)
                song_weight.weight += 1
                song_weight.save()
            except SongWeight.DoesNotExist:
                SongWeight(song_id=song, weight=1).save()
        return JsonResponse({"user_id": user_id}, status=200)


class ClearRuntimes(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)

        Runtimes.objects.all().delete()
        return JsonResponse({"message": "Runtimes cleared"}, status=200)


class GetRuntimesAndType(APIView):
    def post(self, req):
        token = req.data["Authorization"]
        if token is None:
            return JsonResponse({"error": "No token provided"}, status=400)
        try:
            payload = jwt.decode(token, "random salt here idk", algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "Token has expired"}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"error": "Invalid token"}, status=400)
        user_id = payload["user_id"]
        user = User.objects.filter(user_id=user_id).first()
        if user is None:
            return JsonResponse({"error": "User not found"}, status=400)
        runtimes = Runtimes.objects.all()
        return JsonResponse(
            {
                "Time": [runtime.runtime for runtime in runtimes],
                "Type": [runtime.runtime_name for runtime in runtimes],
            },
            status=200,
        )
