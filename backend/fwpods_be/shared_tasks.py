from datetime import datetime
from celery import shared_task
from time import sleep
import os
import pickle


def get_item_frequency(items, freq_dict={}):
    for item in items:
        if item in freq_dict:
            freq_dict[item] += 1
        else:
            freq_dict[item] = 1
    return freq_dict


@shared_task
def delay_test():
    print("delay_test ran")
    # print local path
    print(os.getcwd())
    sleep(10)
    print("delay_test slept for 10 seconds")


@shared_task
def test_save_playlist():
    # Fix circular import
    from .models import Artist

    Artist(artist_name="skibidi toilet").save()


@shared_task
def construct_tree_and_mine_fwp():
    from .models import (
        FrequentlyWeightedPlaylist,
        PlaylistSongs,
        TransactionWindow,
        SongWeight,
        Runtimes,
    )
    import fwpods_py

    weights_manager = fwpods_py.weights_manager()
    swn_tree = fwpods_py.swn_tree_manager()
    song_weights = {}
    for song in SongWeight.objects.all():
        song_weights[song.song_id.song_id] = float(song.weight)

    transactions_in_window = {}
    for transaction in TransactionWindow.objects.all():
        transactions_in_window[transaction.listen_id] = PlaylistSongs.objects.filter(
            playlist_id=transaction.playlist_id
        ).values_list("song_id", flat=True)

    items_freq = {}
    stamp = datetime.now()
    weights_manager.init_db(transactions_in_window, song_weights)
    weights_manager.calculate_ttw()
    weights_manager.calculate_items_ws()

    # Save weights to cwd
    with open("./weights_manager.pkl", "wb") as f:
        pickle.dump(weights_manager, f)

    for _, t_items in transactions_in_window.items():
        items_freq = get_item_frequency(t_items, items_freq)

    tree_stamp = datetime.now()
    swn_tree.build_tree(
        transactions_in_window, weights_manager.transaction_weights, items_freq
    )
    Runtimes(
        runtime_name="tree_building",
        runtime=(datetime.now() - tree_stamp).total_seconds(),
    ).save()

    # Save tree to cwd
    with open("./swn_tree.pkl", "wb") as f:
        pickle.dump(swn_tree, f)

    fwp = fwpods_py.fwpods(
        swn_tree,
        float(os.environ.get("MIN_WS")),
        weights_manager.items_ws,
        weights_manager.ttw,
    )

    algo_stamp = datetime.now()
    fwp.run()
    Runtimes(
        runtime_name="fwp_algorithm",
        runtime=(datetime.now() - algo_stamp).total_seconds(),
    ).save()

    Runtimes(
        runtime_name="total",
        runtime=(datetime.now() - stamp).total_seconds(),
    ).save()

    FrequentlyWeightedPlaylist.objects.all().delete()
    if fwp.fwps:
        for pattern in fwp.fwps:
            res_pattern = ""
            weight = pattern[1].weight
            for item in pattern[0]:
                res_pattern += str(item) + ","
            FrequentlyWeightedPlaylist(wn_node=res_pattern, weight=weight).save()


@shared_task
def maintain_tree_and_mine_fwp():
    from .models import (
        FrequentlyWeightedPlaylist,
        PlaylistSongs,
        TransactionWindow,
        SongWeight,
        Runtimes,
    )
    import fwpods_py

    if not os.path.exists("./swn_tree.pkl"):
        print("No tree found, constructing tree and mining FWP")
        construct_tree_and_mine_fwp()
        return

    with open("./swn_tree.pkl", "rb") as f:
        swn_tree = pickle.load(f)

    with open("./weights_manager.pkl", "rb") as f:
        weights_manager = pickle.load(f)

    # delete first element in transactions_in_window
    TransactionWindow.objects.first().delete()

    added_transaction = {}
    added_transaction[TransactionWindow.objects.last().listen_id] = (
        PlaylistSongs.objects.filter(
            playlist_id=TransactionWindow.objects.last().playlist_id
        ).values_list("song_id", flat=True)
    )
    song_weights = {}
    for song in SongWeight.objects.all():
        weights_manager.update_item_weight(song.song_id.song_id, float(song.weight))

    stamp = datetime.now()
    weights_manager.add_transaction(
        TransactionWindow.objects.last().listen_id, song_weights
    )
    weights_manager.remove_head_transaction()
    weights_manager.calculate_ttw()
    weights_manager.calculate_items_ws()

    tree_stamp = datetime.now()
    for _, t_items in added_transaction.items():
        items_freq = get_item_frequency(t_items)

    swn_tree.maintain_tree(
        added_transaction, weights_manager.transaction_weights, items_freq
    )
    Runtimes(
        runtime_name="tree_maintenance",
        runtime=(datetime.now() - tree_stamp).total_seconds(),
    ).save()

    fwp = fwpods_py.fwpods(
        swn_tree,
        float(os.environ.get("MIN_WS")),
        weights_manager.items_ws,
        weights_manager.ttw,
    )
    algo_stamp = datetime.now()
    fwp.run()
    Runtimes(
        runtime_name="fwp_algorithm",
        runtime=(datetime.now() - algo_stamp).total_seconds(),
    ).save()

    Runtimes(
        runtime_name="total",
        runtime=(datetime.now() - stamp).total_seconds(),
    ).save()

    FrequentlyWeightedPlaylist.objects.all().delete()
    if fwp.fwps:
        for pattern in fwp.fwps:
            res_pattern = ""
            weight = pattern[1][0].weight
            for item in pattern[0]:
                res_pattern += str(item) + ","
            FrequentlyWeightedPlaylist(wn_node=res_pattern, weight=weight).save()
