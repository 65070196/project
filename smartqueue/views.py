import os
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render

from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.models import User
from .models import Customer, Shop, Table, Menu, Queue, Promotion, OpenDate, Image
from django.utils.dateparse import parse_date, parse_time
import datetime


# ระบบ Login, Logout, Register, Reset Password
class Login(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        username_form = request.POST.get('username')
        password_form = request.POST.get('password')

        # เช็คว่า username และ password ถูกต้องไหม (ถ้าถูกจะคืนค่า User object กลับมา)
        user = authenticate(request, username=username_form, password=password_form)

        if user is not None:
            login(request, user)
            
            if user.is_superuser or user.is_staff:
                return redirect('/admin/')
            elif Shop.objects.filter(auth=user).exists():
                return redirect('home-s') 
            elif Customer.objects.filter(auth=user).exists():
                return redirect('home-c')
                
            # ล็อกอินได้แต่ไม่มีข้อมูล
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
                auth=django_user,
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
        
        if User.objects.filter(username=username_form).exists():
            context['error_message'] = "ชื่อผู้ใช้งานนี้ถูกใช้ไปแล้ว"
            return render(request, 'register_shop.html', context)
        
        if email_form and User.objects.filter(email=email_form).exists():
            context['error_message'] = "อีเมลนี้ถูกใช้ไปแล้ว"
            return render(request, 'register_shop.html', context)
        
        try:
            # สร้าง User 
            user = User.objects.create_user(
                username=username_form,
                email=email_form,
                password=password1_form
            )
            # สร้างข้อมูล Shop แล้วผูกกับ User
            Shop.objects.create(
                auth=user,
                shop_name=shop_name_form,
                phone=phone_form
            )
            return redirect('home-s')

        except Exception as e:
            if 'user' in locals() and user.id:
                user.delete()
            context['error_message'] = f"เกิดข้อผิดพลาดในการสมัครสมาชิก: {str(e)}"
            return render(request, 'register_shop.html', context)

class ResetPassword(View):
    def get(self, request):
        return render(request, "reset_password.html")



# หน้าหลักผู้ใช้งาน 
class HomeCustomer(View):
    def get(self, request):
        shops = Shop.objects.all().order_by('shop_id')
        context = {
            'shops': shops
        }
        return render(request, "home_customer.html", context)


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
            customer = Customer.objects.get(auth=request.user)
            
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


# หน้าหลักร้านค้า
class HomeShop(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
            
        try:
            my_shop = Shop.objects.get(auth=request.user)
            queues = Queue.objects.filter(shop=my_shop).order_by('queue_date', 'queue_time')
            
            context = {
                'queues': queues
            }
            return render(request, "home_shop.html", context)
            
        except Shop.DoesNotExist:
            return redirect('login') 
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        queues = Queue.objects.filter(shop__auth=request.user).order_by('queue_date', 'queue_time')
        context = {
            'queues': queues
        }
        return render(request, "home_shop.html", context)
    

class ShopDetail(View):
    def get(self, request, shop_id):
        try:
            shop = Shop.objects.get(pk=shop_id)
        except Shop.DoesNotExist:
            return redirect('home-c') 
            
        promotions = Promotion.objects.filter(shop=shop)
        menus = Menu.objects.filter(shop=shop)
        tables = Table.objects.filter(shop=shop)
        open_dates = OpenDate.objects.filter(shop=shop)

        day_map = {
            0: 'จันทร์', 1: 'อังคาร', 2: 'พุธ', 
            3: 'พฤหัสบดี', 4: 'ศุกร์', 5: 'เสาร์', 6: 'อาทิตย์'
        }
        
        for od in open_dates:
            if od.working_days and isinstance(od.working_days, list):
                days_text = [day_map.get(int(day), '') for day in od.working_days if int(day) in day_map]
                
                if len(days_text) > 1:
                    od.display_days = f"{days_text[0]} - {days_text[-1]}"
                elif len(days_text) == 1:
                    # ถ้ามีวันเดียว
                    od.display_days = days_text[0]
                else:
                    od.display_days = "ไม่ระบุ"
            else:
                od.display_days = "ไม่ระบุ"

        context = {
            'shop': shop,
            'promotions': promotions,
            'menus': menus,
            'tables': tables,
            'open_dates': open_dates,
        }
        return render(request, 'shop_detail.html', context)


class QueueEdit(View):
    def get(self, request, queue_id):
        queue = get_object_or_404(Queue, queue_id=queue_id)
        
        context = {
            'queue': queue
        }
        return render(request, "queue_edit.html", context)
    
    def post(self, request, queue_id):
        queue = get_object_or_404(Queue, queue_id=queue_id)
        new_status = request.POST.get('status')
        
        if new_status:
            queue.status = new_status
            queue.save()
        return redirect('home-s')
    

class QueueDelete(View):
    def post(self, request, queue_id):
        queue = get_object_or_404(Queue, pk=queue_id)
        queue.delete()
        return redirect("home-s")

class TableManage(View):
    def get(self, request):
        my_shop = Shop.objects.get(auth=request.user)
        tables = Table.objects.all().filter(shop=my_shop).order_by('table_id')
        context = {
            'tables': tables
        }
        return render(request, "table_manage.html", context)
    

class TableAdd(View):
    def get(self, request):
        return render(request, "table_add.html")

    def post(self, request):
        name = request.POST.get('name')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        image_file = request.FILES.get('image')

        shop = Shop.objects.get(auth=request.user)

        image_obj = None # เตรียมตัวแปรเก็บ Object รูปภาพไว้ก่อน

        # จัดการรูปภาพ (ถ้ามีการแนบไฟล์มา)
        if image_file:
            # ต้องการเซฟไฟล์ไปที่โฟลเดอร์ static/images/shop_images/ ที่สร้างไว้
            target_folder = os.path.join(settings.BASE_DIR, 'static', 'images', 'shop_images')
            fs = FileSystemStorage(location=target_folder)
            
            saved_filename = fs.save(image_file.name, image_file)
            
            # สร้างข้อความ Path เพื่อเก็บลงตาราง Image
            db_image_path = f"images/shop_images/{saved_filename}"

            image_obj = Image.objects.create(image_path=db_image_path)

        Table.objects.create(
            shop=shop,                  
            name=name,
            description=description,
            amount=amount,
            image=image_obj
        )
        return redirect('table-manage')
    
class TableEdit(View):
    def get(self, request, table_id):
        table = get_object_or_404(Table, table_id=table_id)
        
        context = {
            'table': table
        }
        return render(request, "table_edit.html", context)
    
    def post(self, request, table_id):
        table = get_object_or_404(Table, table_id=table_id)
        
        new_name = request.POST.get('name', '').strip()
        new_desc = request.POST.get('description', '').strip()
        new_amount = request.POST.get('amount', '').strip()

        if new_name != '':
            table.name = new_name
        if new_desc != '':
            table.description = new_desc
        if new_amount != '':
            table.amount = new_amount
            
        table.save()
        return redirect('table-manage')
    
class TableDelete(View):
    def post(self, request, table_id):
        table = get_object_or_404(Table, table_id=table_id)
        table.delete()
        return redirect('table-manage')

    
class PromoManage(View):
    def get(self, request):
        my_shop = Shop.objects.get(auth=request.user)
        promotions = Promotion.objects.filter(shop=my_shop)
        context = {
            'promotions': promotions
        }
        return render(request, "promo_manage.html", context)
    
class PromoAdd(View):
    def get(self, request):
        return render(request, "promo_add.html")
    
    def post(self, request):
        promo_name = request.POST.get('promo_name')
        description = request.POST.get('description')
        discount_rate = request.POST.get('discount_rate')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        try:
            shop = Shop.objects.get(auth=request.user)
        except Shop.DoesNotExist:
            return redirect('home-shop')

        Promotion.objects.create(
            shop=shop,
            promo_name=promo_name,
            description=description,
            discount_rate=float(discount_rate),
            start_date=start_date,
            end_date=end_date
        )
        return redirect('promo-manage')

class PromoDelete(View):
    def post(self, request, promo_id):
        promo = get_object_or_404(Promotion, promo_id=promo_id)
        promo.delete()
        return redirect('promo-manage')

class PromoEdit(View):
    def get(self, request, promo_id):
        promo = get_object_or_404(Promotion, promo_id=promo_id)
        context = {
            'promo': promo
        }
        return render(request, "promo_edit.html", context)
    
    def post(self, request, promo_id):
        promo = get_object_or_404(Promotion, promo_id=promo_id)
        
        new_name = request.POST.get('promo_name', '')
        new_desc = request.POST.get('description', '')
        new_discount = request.POST.get('discount_rate', '')
        new_start = request.POST.get('start_date', '')
        new_end = request.POST.get('end_date', '')

        if new_name != '':
            promo.promo_name = new_name
        if new_desc != '':
            promo.description = new_desc
        if new_discount != '':
            promo.discount_rate = new_discount
        if new_start != '':
            promo.start_date = new_start
        if new_end != '':
            promo.end_date = new_end
        
        promo.save()
        return redirect('promo-manage')
    

class EditOpendate(View):
    def get(self, request):
        return render(request, "opendate_edit.html")
    
    ## def post(self, request):
        ##selected_days = request.POST.getlist('days') 

        ##days_list = [int(day) for day in selected_days]

        ##OpenDate.objects.create(
            ##shop=my_shop,
            ##working_days=days_list, # เก็บเป็น [0, 1, 2]
            ##open_time=request.POST.get('open_time'),
            ##close_time=request.POST.get('close_time')
        ##)
        ##return redirect('promo-manage')

class EditShopProfile(View):
    def get(self, request):
        context = {
            'user': request.user,
        }
        return render(request, "edit_shop_profile.html", context)

    def post(self, request):
        user = request.user
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone

        profile_image = request.FILES.get('profile_image')

        if profile_image:
            folder_name = 'shop'
            target_folder = os.path.join(settings.BASE_DIR, 'static', 'images', 'profile_images', folder_name)
            
            os.makedirs(target_folder, exist_ok=True)
            
            fs = FileSystemStorage(location=target_folder)
            saved_filename = fs.save(profile_image.name, profile_image)
            db_image_path = f"images/profile_images/{folder_name}/{saved_filename}"

            user.profile_image = db_image_path

        try:
            user.save()
            messages.success(request, 'อัปเดตข้อมูลร้านค้าสำเร็จ')
            return redirect('shop-profile-edit') 
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
        context = {
            'user': user,
        }
        return render(request, "edit_shop_profile.html", context)


class EditCustomerProfile(View):
    def get(self, request):
        context = {
            'user': request.user,
        }
        return render(request, "edit_customer_profile.html", context)

    def post(self, request):
        user = request.user
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        
        user.first_name = first_name
        user.last_name = last_name
        user.email = email
        user.phone = phone

        profile_image = request.FILES.get('profile_image')

        if profile_image:
            folder_name = 'customer'
            target_folder = os.path.join(settings.BASE_DIR, 'static', 'images', 'profile_images', folder_name)
            
            os.makedirs(target_folder, exist_ok=True)
            
            fs = FileSystemStorage(location=target_folder)
            saved_filename = fs.save(profile_image.name, profile_image)
            db_image_path = f"images/profile_images/{folder_name}/{saved_filename}"

            user.profile_image = db_image_path

        try:
            user.save()
            messages.success(request, 'อัปเดตข้อมูลลูกค้าสำเร็จ')
            return redirect('customer-profile-edit') 
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
        context = {
            'user': user,
        }
        return render(request, "edit_customer_profile.html", context)