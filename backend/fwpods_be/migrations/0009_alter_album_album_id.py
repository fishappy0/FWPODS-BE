# Generated by Django 4.2.14 on 2024-08-09 14:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("fwpods_be", "0008_alter_path_to_item_path"),
    ]

    operations = [
        migrations.AlterField(
            model_name="album",
            name="album_id",
            field=models.BigIntegerField(primary_key=True, serialize=False),
        ),
    ]
