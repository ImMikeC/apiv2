# Generated by Django 3.1.2 on 2020-10-11 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0022_auto_20201009_1817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='formentry',
            name='latitude',
            field=models.DecimalField(blank=True, decimal_places=15, default=None, max_digits=30, null=True),
        ),
        migrations.AlterField(
            model_name='formentry',
            name='longitude',
            field=models.DecimalField(blank=True, decimal_places=15, default=None, max_digits=30, null=True),
        ),
    ]