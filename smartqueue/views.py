from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render

from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from .models import Customer, Shop, Table, Queue
from django.utils.dateparse import parse_date, parse_time
import datetime


class Login(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username_form = request.POST.get('username')
        password_form = request.POST.get('password')

        user = authenticate(request, username=username_form, password=password_form)

        if user is not None:
            login(request, user)
            
            if Shop.objects.filter(username=user).exists():
                return redirect('home-s')
                
            elif Customer.objects.filter(username=user).exists():
                return redirect('home-c')
                
            elif user.is_superuser or user.is_staff:
                return redirect('/admin/')
                
            else:
                logout(request)
                error_message = "บัญชีนี้ยังไม่ได้ตั้งค่าโปรไฟล์อย่างสมบูรณ์"
                return render(request, 'login.html', {'error_message': error_message})
                
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
        username_form = request.POST.get('username', '').strip()
        email_form = request.POST.get('email', '').strip()
        password1_form = request.POST.get('password', '')
        password2_form = request.POST.get('password_confirm', '')
        firstname_form = request.POST.get('firstname', '').strip()
        lastname_form = request.POST.get('lastname', '').strip()
        phone_form = request.POST.get('phone', '').strip()

        context = {
            'old_username': username_form,
            'old_email': email_form,
            'old_firstname': firstname_form,
            'old_lastname': lastname_form,
            'old_phone': phone_form,
        }

        if not all([username_form, email_form, password1_form, password2_form, firstname_form, lastname_form]):
            context['error_message'] = "กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน"
            return render(request, 'register_customer.html', context)

        if password1_form != password2_form:
            context['error_message'] = "รหัสผ่านทั้งสองช่องไม่ตรงกัน"
            return render(request, 'register_customer.html', context)
            
        if len(password1_form) < 8:
            context['error_message'] = "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร"
            return render(request, 'register_customer.html', context)

        if User.objects.filter(username=username_form).exists():
            context['error_message'] = "ชื่อผู้ใช้งานนี้ถูกใช้ไปแล้ว"
            return render(request, 'register_customer.html', context)
        
        if User.objects.filter(email=email_form).exists():
            context['error_message'] = "อีเมลนี้ถูกใช้ไปแล้ว"
            return render(request, 'register_customer.html', context)

        try:
            django_user = User.objects.create_user(
                username=username_form,
                password=password1_form,
                email=email_form,
                first_name=firstname_form,
                last_name=lastname_form,
            )
            
            Customer.objects.create(
                username=django_user, 
                firstname=firstname_form,
                lastname=lastname_form,
                phone=phone_form,
            )
            
            login(request, django_user)
            return redirect('home-c')

        except Exception as e:
            if 'django_user' in locals() and django_user.id:
                django_user.delete()
                
            context['error_message'] = f"เกิดข้อผิดพลาดในการสมัครสมาชิก: {str(e)}"
            return render(request, 'register_customer.html', context)

class RegisterShop(View):
    def get(self, request):
        return render(request, "register_shop.html")
    
    def post(self, request):
        shop_name_form = request.POST.get('shop_name', '').strip()
        username_form = request.POST.get('username', '').strip()
        email_form = request.POST.get('email', '').strip()
        phone_form = request.POST.get('phone', '').strip()
        password1_form = request.POST.get('password', '')
        password2_form = request.POST.get('password_confirm', '')

        context = {
            'old_shop_name': shop_name_form,
            'old_username': username_form,
            'old_email': email_form,
            'old_phone': phone_form,
        }

        if not all([shop_name_form, username_form, password1_form, password2_form]):
            context['error_message'] = "กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน"
            return render(request, 'register_shop.html', context)
        
        if password1_form != password2_form:
            context['error_message'] = "รหัสผ่านทั้งสองช่องไม่ตรงกัน"
            return render(request, 'register_shop.html', context)
        
        if len(password1_form) < 8:
            context['error_message'] = "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร"
            return render(request, 'register_shop.html', context)
        
        if Shop.objects.filter(username=username_form).exists():
            context['error_message'] = "ชื่อผู้ใช้งานนี้ถูกใช้ไปแล้ว"
            return render(request, 'register_shop.html', context)
        
        if email_form and Shop.objects.filter(email=email_form).exists():
            context['error_message'] = "อีเมลนี้ถูกใช้ไปแล้ว"
            return render(request, 'register_shop.html', context)
        
        try:
            Shop.objects.create(
                shop_name=shop_name_form,
                username=username_form,
                password=password1_form,
                phone=phone_form,
                email=email_form,
            )

            return redirect('home-s')

        except Exception as e:
            context['error_message'] = f"เกิดข้อผิดพลาดในการสมัครสมาชิก: {str(e)}"
            return render(request, 'register_shop.html', context)

class ResetPassword(View):
    def get(self, request):
        return render(request, "reset_password.html")
    
    
class HomeCustomer(View):
    def get(self, request):
        shops = Shop.objects.all().order_by('shop_id')
        context = {
            'shops': shops
        }
        return render(request, "home_customer.html", context)
    

# หน้าหลักผู้ใช้งาน
class HomeShop(View):
    def get(self, request):
        queues = Queue.objects.all().order_by('queue_time')
        context = {
            'queues': queues
        }
        return render(request, "home_shop.html", context)
    
    def post(self, request):
        queues = Queue.objects.filter(
            shop__username=request.user.username
        ).order_by('queue_time')

        context = {
            'queues': queues
        }
        return render(request, "home_shop.html", context)

class QueueMange(View):
    def get(self, request):
        return render(request, "queue_manage.html")
    
    def post(self, request):
        queues = Queue.objects.all().order_by('queue_id')
        context = {
            'queues': queues
        }
        return render(request, "queue_manage.html", context)

class QueueCheck(View):
    def get(self, request):
        queues = Queue.objects.all().order_by('queue_id')
        context = {
            'queues': queues
        }
        return render(request, "queue_check.html", context)
    
class QueueReserve(View):
    def get(self, request, shop_id):  
        shop = get_object_or_404(Shop, pk=shop_id)
        context = {
            'shop': shop
        }
        return render(request, 'queue_reserve.html', context)
    
    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        
        queue_date_str = request.POST.get('queue_date')
        queue_time_str = request.POST.get('queue_time')

        if not queue_date_str or not queue_time_str:
            return render(request, 'queue_reserve.html', {
                'shop': shop,
                'error_message': 'กรุณาเลือกวันที่และเวลาให้ครบถ้วน'
            })

        try:
            customer = Customer.objects.get(username=request.user)
            
            parsed_date = parse_date(queue_date_str)
            parsed_time = parse_time(queue_time_str)
            
            combined_datetime = datetime.datetime.combine(parsed_date, parsed_time)

            Queue.objects.create(
                customer=customer,
                shop=shop,
                queue_date=parsed_date,
                queue_time=combined_datetime
            )
            
            return redirect('home-c') 

        except Customer.DoesNotExist:
            return render(request, 'queue_reserve.html', {
                'shop': shop,
                'error_message': 'ไม่พบข้อมูลลูกค้าในระบบ กรุณาล็อกอินใหม่'
            })
        except Exception as e:
            return render(request, 'queue_reserve.html', {
                'shop': shop,
                'error_message': f'เกิดข้อผิดพลาดในการจองคิว: {str(e)}'
            })



#Table
class TableManage(View):
    def get(self, request):
        tables = Table.objects.all().order_by('table_id')
        context = {
            'tables': tables
        }
        return render(request, "table_manage.html", context)
    

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