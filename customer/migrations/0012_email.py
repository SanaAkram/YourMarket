# Generated by Django 5.0 on 2024-01-02 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0011_paymentdetails_remove_customer_details_payment_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Email',
            fields=[
                ('email_id', models.AutoField(primary_key=True, serialize=False)),
                ('sender', models.EmailField(max_length=254)),
                ('recipient', models.EmailField(max_length=254)),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
