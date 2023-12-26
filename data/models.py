from django.db import models


class Customer(models.Model):
    consignment_no = models.CharField(max_length=255, primary_key=True)
    consignee = models.CharField(max_length=255)
    consignee_address = models.TextField()
    consignee_number = models.CharField(max_length=20)
    booking_date = models.DateField()
    destination_branch = models.CharField(max_length=255)
    pieces = models.IntegerField()
    weight = models.FloatField()
    COD_amount = models.FloatField()
    Status = models.CharField(max_length=255)
    Delivery_date = models.DateField(null=True, blank=True)
    Total_Charges = models.FloatField()
    Attempts = models.CharField(max_length=255)
    productDescription = models.TextField()
    Payment_ID = models.CharField(max_length=255)
