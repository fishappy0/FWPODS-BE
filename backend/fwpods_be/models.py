from re import L
from typing import Any
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from .shared_tasks import *


# Create your models here.
class User(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)


class Artist(models.Model):
    artist_id = models.AutoField(primary_key=True)
    artist_name = models.CharField(max_length=100)


class Playlist(models.Model):
    playlist_id = models.AutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    playlist_name = models.CharField(max_length=100)


class Album(models.Model):
    album_id = models.CharField(primary_key=True)
    album_name = models.CharField(max_length=1000)
    artist = models.CharField(max_length=1000)
    release_date = models.DateField(null=True)
    release_year = models.IntegerField(null=True)
    genre = models.CharField(max_length=100, null=True)


class Song(models.Model):
    song_id = models.CharField(primary_key=True)
    favorites = models.IntegerField(null=True)
    artist_id = models.ForeignKey(Artist, on_delete=models.CASCADE, null=True)
    album_id = models.ForeignKey(Album, on_delete=models.CASCADE)
    song_name = models.CharField(max_length=1000)
    duration = models.DurationField(null=True)


class PlaylistSongs(models.Model):
    playlist_id = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    song_id = models.ForeignKey(Song, on_delete=models.CASCADE)


# Song weight??????, count user id for song id then use it as weight {song_id: weight}????
class LikedSongs(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    song_id = models.ForeignKey(Song, on_delete=models.CASCADE)


class path_to_item(models.Model):
    path_id = models.AutoField(primary_key=True)
    album_id = models.ForeignKey(Album, on_delete=models.CASCADE, null=True)
    song_id = models.ForeignKey(Song, on_delete=models.CASCADE, null=True)
    path = models.CharField(max_length=1000)


class playlists_listens_window(models.Model):
    playlist_id = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    songs = models.JSONField()


# a sliding window of the last n playlists listened to
class TransactionWindow(models.Model):
    listen_id = models.AutoField(primary_key=True)
    playlist_id = models.ForeignKey(Playlist, on_delete=models.CASCADE)


class FrequentlyWeightedPlaylist(models.Model):
    fwp_id = models.AutoField(primary_key=True)
    wn_node = models.CharField(max_length=1000000)
    weight = models.FloatField()


class SongWeight(models.Model):
    song_id = models.ForeignKey(Song, on_delete=models.CASCADE)
    weight = models.IntegerField()


class Runtimes(models.Model):
    runtime_id = models.AutoField(primary_key=True)
    runtime_name = models.CharField(max_length=100)
    runtime = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)


# @receiver(post_save, sender=FrequentlyWeightedPlaylist)
# def update_fwp(sender, instance, created, **kwargs):
#     if created:
#         return
#     # instance.wn_node.save()
#     print("FrequentlyWeightedPlaylist updated")
#     delay_test()
#     # instance.save()


# @receiver(post_save, sender=User)
# def update_artist(sender, instance, created, **kwargs):
#     print("User created")
#     test_save_playlist.delay()
@receiver(post_save, sender=LikedSongs)
def update_song_weight(sender, instance, created, **kwargs):
    try:
        SongWeight.objects.get(song_id=instance.song_id).weight += 1
    except SongWeight.DoesNotExist:
        SongWeight(song_id=instance.song_id, weight=1).save()


@receiver(post_save, sender=TransactionWindow)
def update_transaction_window(sender, instance, created, **kwargs):
    print("TransactionWindow updated")
    if TransactionWindow.objects.count() == int(os.environ.get("WINDOW_SIZE")):
        print("Window size initially reached")
        construct_tree_and_mine_fwp.delay()

    if TransactionWindow.objects.count() > int(os.environ.get("WINDOW_SIZE")):
        print("Window size exceeded")
        maintain_tree_and_mine_fwp.delay()
        # Update the tree
