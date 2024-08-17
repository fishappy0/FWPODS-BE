"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path

import fwpods_be.views

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("", fwpods_be.views.index),
    path("test_image", fwpods_be.views.test_image),
    path("test_song", fwpods_be.views.test_song),
    path("test_playlist", fwpods_be.views.test_playlist),
    path("register", fwpods_be.views.RegisterView.as_view()),
    path("login", fwpods_be.views.LoginView.as_view()),
    path("get_random_songs", fwpods_be.views.GetRandomSongs.as_view()),
    path("get_song", fwpods_be.views.GetSong.as_view()),
    path("get_all_user_playlists", fwpods_be.views.GetAllUserPlaylists.as_view()),
    path("get_song_info", fwpods_be.views.GetSongInfo.as_view()),
    path("get_song_info_multiple", fwpods_be.views.GetSongInfoMultiple.as_view()),
    path("get_playlist_songs", fwpods_be.views.GetPlaylistSongs.as_view()),
    path("get_user_playlists", fwpods_be.views.GetUserPlaylists.as_view()),
    path("create_playlist", fwpods_be.views.CreatePlaylist.as_view()),
    path("update_playlist", fwpods_be.views.UpdatePlaylist.as_view()),
    path("update_playlist_multiple", fwpods_be.views.UpdatePlaylistMultiple.as_view()),
    path("delete_playlist", fwpods_be.views.DeletePlaylist.as_view()),
    path("play_playlist", fwpods_be.views.PlayPlaylist.as_view()),
    path("get_all_available_songs", fwpods_be.views.GetAllAvailableSongs.as_view()),
    path("like_song", fwpods_be.views.LikeSong.as_view()),
    path("like_song_multiple", fwpods_be.views.LikeSongMultiple.as_view()),
    path("run_likes_update", fwpods_be.views.RunLikesUpdate.as_view()),
    path("clear_runtimes", fwpods_be.views.ClearRuntimes.as_view()),
    path("get_runtimes_and_type", fwpods_be.views.GetRuntimesAndType.as_view()),
]
