from django.contrib.auth.models import User
from django.db import models


class Customer(models.Model):
    user_id = models.AutoField(primary_key=True)
    auth = models.OneToOneField(User, on_delete=models.CASCADE, db_column='auth_id')
    phone = models.CharField(max_length=10, blank=True, null=True)
    image = models.ForeignKey('Image', on_delete=models.CASCADE, null=True)
    def __str__(self):
        return f"{self.auth.first_name} {self.auth.last_name}"

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
    auth = models.OneToOneField(User, on_delete=models.CASCADE, db_column='auth_id')
    shop_name = models.CharField(max_length=100, null=False)
    phone = models.CharField(max_length=10, blank=True, null=True)
    description = models.CharField(max_length=1200, blank=True, null=True)
    image = models.ForeignKey('Image', on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.shop_name

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
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='open_dates')
    
    working_days = models.JSONField(default=list, help_text="")
    
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)

class Image(models.Model):
    image_id = models.AutoField(primary_key=True)
    image_path = models.CharField(max_length=1000, null=False)
    def __str__(self):
        return self.image_path