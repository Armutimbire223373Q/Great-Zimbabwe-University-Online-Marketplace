# Generated by Django 4.2.7 on 2025-06-02 02:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketplace', '0002_alter_cartitem_options_cartitem_added_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
    ]
