# Generated by Django 3.1 on 2020-08-14 04:28

from django.db import migrations, models
from django.utils import timezone


class Migration(migrations.Migration):

    dependencies = [
        ('authenticate', '0004_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='expires_at',
            field=models.DateTimeField(),
        ),
    ]
