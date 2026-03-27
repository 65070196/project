from django.contrib.auth.models import User
from django.db import models


# --- โมเดลของลูกค้า ---
class Customer(models.Model):
    user_id = models.AutoField(primary_key=True)
    auth = models.OneToOneField(User, on_delete=models.CASCADE, db_column='auth_id')
    phone = models.CharField(max_length=10, blank=True, null=True)
    image = models.ForeignKey('Image', on_delete=models.CASCADE, null=True)
    def __str__(self):
        return f"{self.auth.first_name} {self.auth.last_name}"


# --- โมเดลของลูกค้า ---
class Queue(models.Model):
    STATUS_CHOICES = [
        ('doing', 'กำลังดำเนินการ'),
        ('done', 'เสร็จสิ้น'),
        ('cancel', 'ยกเลิก'),
    ]
    queue_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE, null=False)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=False)
    table = models.ForeignKey('Table', on_delete=models.SET_NULL, null=True, blank=True)
    pax = models.IntegerField(null=False, default=1)
    queue_date = models.DateField(null=False)
    queue_time = models.DateTimeField(null=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='doing')
    def __str__(self):
        return f"Queue {self.queue_id} ({self.pax} คน) - {self.get_status_display()}"


# --- โมเดลของร้านค้า ---
class Shop(models.Model):
    shop_id = models.AutoField(primary_key=True)
    auth = models.OneToOneField(User, on_delete=models.CASCADE, db_column='auth_id')
    shop_name = models.CharField(max_length=100, null=False)
    phone = models.CharField(max_length=10, blank=True, null=True)
    description = models.CharField(max_length=1200, blank=True, null=True)
    image = models.ForeignKey('Image', on_delete=models.SET_NULL, null=True, blank=True)
    def __str__(self):
        return self.shop_name


# --- โมเดลของโปรโมชั่น ---
class Promotion(models.Model):
    promo_id = models.AutoField(primary_key=True)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=False)
    promo_name = models.CharField(max_length=24, null=False)
    description = models.CharField(max_length=24, blank=True, null=True)
    start_date = models.DateField(null=False)
    end_date = models.DateField(null=False)
    discount_rate = models.FloatField(null=False)


# --- โมเดลของลูกค้า ---
class Table(models.Model):
    table_id = models.AutoField(primary_key=True)
    shop = models.ForeignKey('Shop', on_delete=models.CASCADE, null=False)
    name = models.CharField(max_length=24, null=False)
    description = models.CharField(max_length=200, blank=True, null=True)
    amount = models.IntegerField(null=False)
    capacity = models.IntegerField(null=False, default=1)
    image = models.ForeignKey('Image', on_delete=models.CASCADE, null=True)
    def __str__(self):
        return f"{self.name} (นั่งได้ {self.capacity} คน) - ว่าง {self.amount} โต๊ะ"


# --- โมเดลของลูกค้า ---
class OpenDate(models.Model):
    open_date_id = models.AutoField(primary_key=True)
    shop = models.OneToOneField(Shop, on_delete=models.CASCADE, related_name='open_date')
    
    # --- วันจันทร์ ---
    mon_is_closed = models.BooleanField(default=False)
    mon_open = models.TimeField(null=True, blank=True)
    mon_close = models.TimeField(null=True, blank=True)

    # --- วันอังคาร ---
    tue_is_closed = models.BooleanField(default=False)
    tue_open = models.TimeField(null=True, blank=True)
    tue_close = models.TimeField(null=True, blank=True)

    # --- วันพุธ ---
    wed_is_closed = models.BooleanField(default=False)
    wed_open = models.TimeField(null=True, blank=True)
    wed_close = models.TimeField(null=True, blank=True)

    # --- วันพฤหัสบดี ---
    thu_is_closed = models.BooleanField(default=False)
    thu_open = models.TimeField(null=True, blank=True)
    thu_close = models.TimeField(null=True, blank=True)

    # --- วันศุกร์ ---
    fri_is_closed = models.BooleanField(default=False)
    fri_open = models.TimeField(null=True, blank=True)
    fri_close = models.TimeField(null=True, blank=True)

    # --- วันเสาร์ ---
    sat_is_closed = models.BooleanField(default=False)
    sat_open = models.TimeField(null=True, blank=True)
    sat_close = models.TimeField(null=True, blank=True)

    # --- วันอาทิตย์ ---
    sun_is_closed = models.BooleanField(default=False)
    sun_open = models.TimeField(null=True, blank=True)
    sun_close = models.TimeField(null=True, blank=True)


# --- โมเดลของลูกค้า ---
class Image(models.Model):
    image_id = models.AutoField(primary_key=True)
    # upload_to='images/' คือการบอกให้ Cloudinary สร้างโฟลเดอร์ชื่อ images
    image_path = models.ImageField(upload_to='images/', null=False) 
    def __str__(self):
        return str(self.image_path)