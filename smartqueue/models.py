from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    user_id = models.AutoField(primary_key=True)
    username = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=100, null=False)
    lastname = models.CharField(max_length=100, null=False)
    phone = models.CharField(max_length=10, blank=True, null=True)
    image = models.ForeignKey('Image', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.firstname + ' ' + self.lastname

class Queue(models.Model):
    STATUS_CHOICES = [
        ('doing', 'กำลังดำเนินการ'),
        ('done', 'เสร็จสิ้น'),
        ('cancel', 'ยกเลิก'),
    ]
    queue_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=False)
    queue_date = models.DateField(null=False)
    queue_time = models.DateTimeField(null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='doing')
    def __str__(self):
        return f"Queue {self.queue_id} - {self.get_status_display()}"


class Shop(models.Model):
    shop_id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=24, null=False)
    password = models.CharField(max_length=24, null=False)
    shop_name = models.CharField(max_length=100, null=False)
    phone = models.CharField(max_length=10, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    image = models.ForeignKey('Image', on_delete=models.SET_NULL, null=True, blank=True)

class Promotion(models.Model):
    promo_id = models.AutoField(primary_key=True)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=False)
    promo_name = models.CharField(max_length=24, null=False)
    description = models.CharField(max_length=24, blank=True, null=True)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    discount_rate = models.FloatField(null=False)

class Menu(models.Model):
    menu_id = models.AutoField(primary_key=True)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=24, null=False)
    description = models.CharField(max_length=200, blank=True, null=True)
    price = models.IntegerField(null=False)
    image = models.ForeignKey('Image', on_delete=models.CASCADE, null=False)

class Table(models.Model):
    table_id = models.AutoField(primary_key=True)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=24, null=False)
    description = models.CharField(max_length=200, blank=True, null=True)
    amount = models.IntegerField(null=False)
    image = models.ForeignKey('Image', on_delete=models.CASCADE, null=False)

class OpenDate(models.Model):
    open_date_id = models.AutoField(primary_key=True)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=False)
    working_day = models.DateField(null=False)
    open_time = models.DateTimeField(null=False)
    close_time = models.DateTimeField(null=False)

class Image(models.Model):
    image_id = models.AutoField(primary_key=True)
    image_path = models.CharField(max_length=1000, null=False)
