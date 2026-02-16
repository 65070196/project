from django.views import View
from django.shortcuts import render, redirect
from django.shortcuts import render

from django.contrib.auth import authenticate, logout, login
from .models import Customer


class Login(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        # ต้องแก้ เพราะเรื่องความปลอดภัย
        username_form = request.POST.get('username')
        password_form = request.POST.get('password')

        user = authenticate(request, 
            username=username_form, 
            password=password_form)

        if user is not None:
            login(request, user)
            return redirect('home-c')
        else:
            error_message = "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"
            return render(request, 'login.html', {'error_message': error_message})

class Logout(View):
    def get(self, request):
        logout(request)
        return redirect('home-c')

class RegisterCustomer(View):
    def get(self, request):
        return render(request, 'register_customer.html')

    def post(self, request):
        # ต้องแก้ เพราะเรื่องความปลอดภัย
        username_form = request.POST.get('username')
        email_form = request.POST.get('email')
        password1_form = request.POST.get('password')
        password2_form = request.POST.get('password_confirm')
        fullname_form = request.POST.get('fullname')

        context = {}

        if password1_form != password2_form:
            context['error_message'] = "รหัสผ่านทั้งสองช่องไม่ตรงกัน"
            return render(request, 'register_customer.html', context)

        if Customer.objects.filter(username=username_form).exists():
            context['error_message'] = "ชื่อผู้ใช้งานนี้ถูกใช้ไปแล้ว"
            return render(request, 'register_customer.html', context)
        
        if Customer.objects.filter(email=email_form).exists():
            context['error_message'] = "อีเมลนี้ถูกใช้ไปแล้ว"
            return render(request, 'register_customer.html', context)

        try:
            user = Customer.objects.create_user(
                username = username_form,
                password = password1_form,
                first_name = fullname_form,
                email = email_form,
                tel = request.POST.get('phone'),

            )
            
            login(request, user)
            
            return redirect('home-c')

        except Exception as e:
            return render(request, 'register_customer.html')

class RegisterShop(View):
    def get(self, request):
        return render(request, "register_shop.html")
    
class ResetPassword(View):
    def get(self, request):
        return render(request, "reset_password.html")
    


    
class HomeCustomer(View):
    def get(self, request):
        return render(request, "home_customer.html")

class HomeShop(View):
    def get(self, request):
        return render(request, "home_shop.html")

class Booking(View):
    def get(self, request):
        return render(request, "booking.html")
    
class QueueCheck(View):
    def get(self, request):
        return render(request, "queue_check.html")

class TableManage(View):
    def get(self, request):
        return render(request, "table_manage.html")

class TableAdd(View):
    def get(self, request):
        return render(request, "table_add.html")

class TableEdit(View):
    def get(self, request):
        return render(request, "table_edit.html")
    
class PromoManage(View):
    def get(self, request):
        return render(request, "promo_manage.html")
    
class PromoAdd(View):
    def get(self, request):
        return render(request, "promo_add.html")

class PromoEdit(View):
    def get(self, request):
        return render(request, "promo_edit.html")