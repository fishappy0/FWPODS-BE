# Generated by Django 4.2.14 on 2024-08-08 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fwpods_be", "0004_alter_path_to_item_album_id_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="song",
            name="song_id",
            field=models.BigIntegerField(primary_key=True, serialize=False),
        ),
    ]
