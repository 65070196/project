from django.urls import path
from django.shortcuts import redirect
from smartqueue.views import *

urlpatterns = [
    path("login/", Login.as_view(), name="login"), # http://127.0.0.1:8000/login/
    path("register/c/", RegisterCustomer.as_view(), name="register-c"), # http://127.0.0.1:8000/register/
    path("register/s/", RegisterShop.as_view(), name="register-s"), # http://127.0.0.1:8000/registerShop/
    path("reset-password/", ResetPassword.as_view(), name="reset-password"),

    path('', lambda request: redirect('home-c')), # เข้าเว็บแล้วไป http://127.0.0.1:8000/home/c/ เลย
    path("home/c/", HomeCustomer.as_view(), name="home-c"), # http://127.0.0.1:8000/home/c/   ->  for Customer
    path("home/s/", HomeShop.as_view(), name="home-s"), # http://127.0.0.1:8000/home/s/       ->  for Shop
    
    path("booking/", Booking.as_view(), name="booking"),
    path("queue-check/", QueueCheck.as_view(), name="queue-check"),

    path("table-manage/", TableManage.as_view(), name="table-manage"),
    path("table-add/", TableAdd.as_view(), name="table-add"),
    path("table-edit/", TableEdit.as_view(), name="table-edit"),

    path("promo-manage/", PromoManage.as_view(), name="promo-manage"),
    path("promo-add/", PromoAdd.as_view(), name="promo-add"),
    path("promo-edit/", PromoEdit.as_view(), name="promo-edit"),
]