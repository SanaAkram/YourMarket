# Generated by Django 5.0 on 2023-12-27 08:03

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='customer_details',
            old_name='id',
            new_name='customer_id',
        ),
    ]
