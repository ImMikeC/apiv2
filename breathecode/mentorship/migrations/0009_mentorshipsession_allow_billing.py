# Generated by Django 3.2.12 on 2022-03-11 19:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mentorship', '0008_auto_20220311_0423'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentorshipsession',
            name='allow_billing',
            field=models.BooleanField(
                default=True, help_text='If false it will not be included when generating mentorship bills'),
        ),
    ]