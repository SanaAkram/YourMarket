import uuid
from django.db import models
from django.contrib.auth.models import User


class Product_details(models.Model):
    product_id = models.IntegerField(unique=True, primary_key=True, null=False)
    product_name = models.CharField(null=False, unique=True)
    product_wholesale_rate = models.CharField(null=False)
    total_sold = models.IntegerField(null=True)

    def __str__(self):
        return str(self.product_name)


class PaymentDetails(models.Model):
    payment_id = models.CharField(max_length=255, unique=True, primary_key=True)
    paid_on = models.DateField()
    rr_amount = models.IntegerField()
    invoice_amount = models.IntegerField()
    ibft_fee = models.IntegerField()
    net_payable = models.IntegerField()
    instrument_mode = models.CharField(max_length=255)
    instrument_number = models.CharField(max_length=255)

    def __str__(self):
        return f"PaymentDetails - {self.payment_id}"


class Customer_Details(models.Model):
    customer_id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    consignment_no = models.CharField(null=False, unique=True)
    consignee = models.CharField(max_length=255)
    consignee_address = models.TextField()
    consignee_number = models.CharField(max_length=20)
    booking_date = models.DateField()
    destination_branch = models.CharField(max_length=255)
    pieces = models.IntegerField()
    weight = models.FloatField()
    cod_amount = models.FloatField()
    status = models.CharField(max_length=255)
    delivery_date = models.DateField(null=True, blank=True)
    total_charges = models.FloatField()
    attempts = models.CharField(max_length=255)
    product_description = models.TextField()
    product_fk = models.ForeignKey(Product_details, on_delete=models.CASCADE, null=True)
    payment_fk = models.ForeignKey(PaymentDetails, on_delete=models.CASCADE, max_length=255, null=True)

    def __str__(self):
        return str(self.pk)


class Email(models.Model):
    email_id = models.AutoField(primary_key=True)
    sender = models.EmailField()
    recipient = models.EmailField()
    subject = models.CharField(max_length=255)
    body = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject} - {self.sender}"