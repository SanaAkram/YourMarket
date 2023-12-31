# Generated by Django 5.0 on 2023-12-27 07:56

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Customer_Details',
            fields=[
                ('consignment_no', models.IntegerField()),
                ('consignee', models.CharField(max_length=255)),
                ('consignee_address', models.TextField()),
                ('consignee_number', models.CharField(max_length=20)),
                ('booking_date', models.DateField()),
                ('destination_branch', models.CharField(max_length=255)),
                ('pieces', models.IntegerField()),
                ('weight', models.FloatField()),
                ('cod_amount', models.FloatField()),
                ('status', models.CharField(max_length=255)),
                ('delivery_date', models.DateField(blank=True, null=True)),
                ('total_charges', models.FloatField()),
                ('attempts', models.CharField(max_length=255)),
                ('product_description', models.TextField()),
                ('payment_id', models.CharField(max_length=255)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
            ],
        ),
    ]
