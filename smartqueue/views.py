import os
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from django.db import transaction

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
        # 1. ดึงประเภทโต๊ะของร้านนี้มาเตรียมส่งไปให้หน้าเว็บ
        tables = Table.objects.filter(shop=shop) 
        
        context = {
            'shop': shop,
            'tables': tables # ส่งตัวแปร tables เข้าไปด้วย
        }
        return render(request, 'queue_reserve.html', context)
    
    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        # ดึงมาเผื่อกรณีเกิด Error จะได้ส่งรายชื่อโต๊ะกลับไปหน้าเดิมได้ (Dropdown จะได้ไม่หาย)
        tables = Table.objects.filter(shop=shop) 
        
        queue_date_str = request.POST.get('queue_date')
        queue_time_str = request.POST.get('queue_time')
        table_id = request.POST.get('table_id') # 2. รับค่าไอดีโต๊ะที่ลูกค้าเลือก

        if not queue_date_str or not queue_time_str or not table_id:
            return render(request, 'queue_reserve.html', {
                'shop': shop,
                'tables': tables,
                'error_message': 'กรุณาเลือกวันที่ เวลา และประเภทโต๊ะให้ครบถ้วน'
            })

        try:
            customer = Customer.objects.get(auth=request.user)
            
            parsed_date = parse_date(queue_date_str)
            parsed_time = parse_time(queue_time_str)
            combined_datetime = datetime.datetime.combine(parsed_date, parsed_time)

            # --- 3. เริ่มกระบวนการล็อก Database เพื่อป้องกันคนแย่งโต๊ะกัน (Race Condition) ---
            with transaction.atomic():
                # select_for_update() จะล็อกข้อมูลโต๊ะนี้ไว้ ถ้ามีคนกดพร้อมกัน คนที่ 2 ต้องรอเสี้ยววิ
                table = Table.objects.select_for_update().get(pk=table_id, shop=shop)
                
                # นับว่า ณ วันและเวลานี้ โต๊ะประเภทนี้โดนจองไปกี่คิวแล้ว
                existing_queues_count = Queue.objects.filter(
                    shop=shop,
                    table=table,
                    queue_time=combined_datetime
                ).count()

                # ถ้าจำนวนคิวที่จองไปแล้ว >= จำนวนโต๊ะที่มีอยู่จริง = โต๊ะเต็ม!
                if existing_queues_count >= table.amount:
                    return render(request, 'queue_reserve.html', {
                        'shop': shop,
                        'tables': tables,
                        'error_message': f'ขออภัย โต๊ะประเภท "{table.name}" ในเวลาดังกล่าวถูกจองเต็มแล้ว'
                    })

                # ถ้ายังไม่เต็ม ก็สร้างคิวใหม่ได้เลย
                Queue.objects.create(
                    customer=customer,
                    shop=shop,
                    table=table, # อย่าลืมเซฟโต๊ะลงไปด้วย
                    queue_date=parsed_date,
                    queue_time=combined_datetime
                )
            # --- จบกระบวนการล็อก Database ---
            
            return redirect('home-c') 

        except Customer.DoesNotExist:
            return render(request, 'queue_reserve.html', {
                'shop': shop,
                'tables': tables,
                'error_message': 'ไม่พบข้อมูลลูกค้าในระบบ กรุณาล็อกอินใหม่'
            })
        except Table.DoesNotExist:
            return render(request, 'queue_reserve.html', {
                'shop': shop,
                'tables': tables,
                'error_message': 'ไม่พบประเภทโต๊ะที่คุณเลือก (ข้อมูลอาจถูกลบไปแล้ว)'
            })
        except Exception as e:
            return render(request, 'queue_reserve.html', {
                'shop': shop,
                'tables': tables,
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
        # 1. ค้นหาร้านค้า
        try:
            shop = Shop.objects.get(pk=shop_id)
        except Shop.DoesNotExist:
            return redirect('home-c') 
            
        # 2. ดึงข้อมูลที่เกี่ยวข้อง
        promotions = Promotion.objects.filter(shop=shop)
        menus = Menu.objects.filter(shop=shop)
        tables = Table.objects.filter(shop=shop)

        # 3. จัดการเวลาทำการ (OpenDate) แบบตารางกว้าง (Wide Table)
        open_dates_list = []
        try:
            # ใช้ shop.open_date เพราะเราตั้ง OneToOneField และ related_name='open_date' ไว้
            od = shop.open_date 
            
            days_mapping = [
                ('mon', 'จันทร์'), ('tue', 'อังคาร'), ('wed', 'พุธ'), 
                ('thu', 'พฤหัสบดี'), ('fri', 'ศุกร์'), ('sat', 'เสาร์'), ('sun', 'อาทิตย์')
            ]
            
            for key, name in days_mapping:
                open_dates_list.append({
                    'day_name': name,
                    'is_closed': getattr(od, f"{key}_is_closed"),
                    'open_time': getattr(od, f"{key}_open"),
                    'close_time': getattr(od, f"{key}_close"),
                })
        except OpenDate.DoesNotExist:
            # ถ้าร้านนี้ยังไม่เคยตั้งเวลาเลย
            open_dates_list = []

        context = {
            'shop': shop,
            'promotions': promotions,
            'menus': menus,
            'tables': tables,
            'open_dates_list': open_dates_list, # เปลี่ยนชื่อตัวแปรเป็น open_dates_list
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
        # สมมติว่าดึงร้านค้าจาก User ที่ล็อกอิน
        shop = Shop.objects.get(auth=request.user)
        
        # พยายามดึงข้อมูลเวลาเปิดปิด ถ้ายังไม่มีก็ให้เป็น None ไปก่อน
        try:
            open_date = shop.open_date
        except OpenDate.DoesNotExist:
            open_date = None
            
        # จับคู่คีย์ (ตรงกับชื่อฟิลด์ใน Model) กับ ชื่อวันภาษาไทย
        days_mapping = [
            ('mon', 'จันทร์'), ('tue', 'อังคาร'), ('wed', 'พุธ'), 
            ('thu', 'พฤหัสบดี'), ('fri', 'ศุกร์'), ('sat', 'เสาร์'), ('sun', 'อาทิตย์')
        ]
        
        days_data = []
        for key, name in days_mapping:
            # ดึงข้อมูลจากโมเดลทีละฟิลด์โดยใช้ getattr (ถ้ามี open_date ค่อยดึง ถ้าไม่มีให้เป็นค่าว่าง)
            days_data.append({
                'key': key,
                'name': name,
                'is_closed': getattr(open_date, f"{key}_is_closed") if open_date else False,
                'open_time': getattr(open_date, f"{key}_open") if open_date else None,
                'close_time': getattr(open_date, f"{key}_close") if open_date else None,
            })
            
        return render(request, 'opendate_edit.html', {'days_data': days_data})

    def post(self, request):
        shop = Shop.objects.get(auth=request.user)
        
        days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        defaults_data = {}
        
        # วนลูปรับค่าจากฟอร์มทีละวัน แล้วยัดใส่ Dictionary
        for day in days:
            is_closed = request.POST.get(f"{day}_is_closed") == 'on'
            open_time = request.POST.get(f"{day}_open")
            close_time = request.POST.get(f"{day}_close")
            
            # ถ้าติ๊กปิดร้าน หรือลืมกรอกเวลา ให้ถือว่าวันนั้นปิดร้านไปเลยเพื่อป้องกัน Error
            if is_closed or not open_time or not close_time:
                defaults_data[f"{day}_is_closed"] = True
                defaults_data[f"{day}_open"] = None
                defaults_data[f"{day}_close"] = None
            else:
                defaults_data[f"{day}_is_closed"] = False
                defaults_data[f"{day}_open"] = open_time
                defaults_data[f"{day}_close"] = close_time
                
        # ใช้ update_or_create: ถ้า 1 ร้านค้านี้เคยตั้งเวลาแล้วให้อัปเดต ถ้าไม่เคยให้สร้างใหม่
        OpenDate.objects.update_or_create(
            shop=shop,
            defaults=defaults_data
        )
        
        # เปลี่ยนชื่อ URL ตรงนี้ให้ตรงกับหน้าจัดการร้านของคุณ
        return redirect('opendate-edit')


class ViewShopProfile(View):
    def get(self, request):
        user = request.user
        try:
            shop = Shop.objects.get(auth=user)
        except Shop.DoesNotExist:
            shop = None
            
        context = {
            'user': user,
            'shop': shop,
        }
        return render(request, "shop_profile.html", context)


class EditShopProfile(View):
    def get(self, request):
        user = request.user
        # ดึงข้อมูลร้านค้าที่ผูกกับ User หรือสร้างใหม่ถ้ายังไม่มี
        shop, created = Shop.objects.get_or_create(auth=user) 
        context = {
            'user': user,
            'shop': shop,
        }
        return render(request, "edit_shop_profile.html", context)

    def post(self, request):
        user = request.user
        shop, created = Shop.objects.get_or_create(auth=user)
        
        # 1. รับค่าข้อมูลส่วนตัว (จากตาราง User)
        new_first_name = request.POST.get('first_name', '').strip()
        new_last_name = request.POST.get('last_name', '').strip()
        new_email = request.POST.get('email', '').strip()
        
        # 2. รับค่าข้อมูลร้านค้า (จากตาราง Shop)
        new_shop_name = request.POST.get('shop_name', '').strip()
        new_description = request.POST.get('description', '').strip()
        new_phone = request.POST.get('phone', '').strip()

        # เช็คว่าถ้ามีข้อมูลพิมพ์มาใหม่ ถึงจะเอาไปทับของเดิม
        if new_first_name:
            user.first_name = new_first_name
        if new_last_name:
            user.last_name = new_last_name
        if new_email:
            user.email = new_email
            
        if new_shop_name:
            shop.shop_name = new_shop_name
        if new_description:
            shop.description = new_description
        if new_phone:
            shop.phone = new_phone

        # รับไฟล์รูปร้านค้า (โลโก้ร้าน)
        profile_image = request.FILES.get('profile_image')

        # ถ้าอัปรูปใหม่เข้ามา
        if profile_image:
            # เปลี่ยนชื่อโฟลเดอร์เป็น shop
            folder_name = 'shop'
            target_folder = os.path.join(settings.BASE_DIR, 'static', 'images', 'profile_images', folder_name)
            
            os.makedirs(target_folder, exist_ok=True)
            
            fs = FileSystemStorage(location=target_folder)
            saved_filename = fs.save(profile_image.name, profile_image)
            db_image_path = f"images/profile_images/{folder_name}/{saved_filename}"

            if shop.image:
                old_file_path = os.path.join(settings.BASE_DIR, 'static', shop.image.image_path)
                
                # เช็คว่าไฟล์นี้มีอยู่จริงไหม ถ้ามีให้ลบไฟล์ทิ้ง
                if os.path.isfile(old_file_path):
                    os.remove(old_file_path)
                
                # ลบ Object รูปเดิมออกจาก Database เพื่อไม่ให้เป็นขยะ
                old_image_obj = shop.image
                shop.image = None # ตัดการผูกกับ db
                old_image_obj.delete()
                
            # สร้าง Object รูปใหม่ลงตาราง Image
            image_obj = Image.objects.create(image_path=db_image_path)
            
            # ผูกรูปใหม่เข้ากับ Shop
            shop.image = image_obj

        try:
            user.save()      
            shop.save()
            messages.success(request, 'อัปเดตข้อมูลร้านค้าสำเร็จ')
        
            # กลับไปหน้าดูโปรไฟล์ร้านค้า (อย่าลืมตั้งชื่อ url เป็น 'view-s-profile' ใน urls.py นะครับ)
            return redirect('view-s-profile') 
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
        context = {
            'user': user,
            'shop': shop,
        }
        return render(request, "edit_shop_profile.html", context)


class ViewCustomerProfile(View):
    def get(self, request):
        user = request.user
        try:
            customer = Customer.objects.get(auth=user)
        except Customer.DoesNotExist:
            customer = None
            
        context = {
            'user': user,
            'customer': customer,
        }
        return render(request, "customer_profile.html", context)


class EditCustomerProfile(View):
    def get(self, request):
        user = request.user
        customer, created = Customer.objects.get_or_create(auth=user) 
        context = {
            'user': user,
            'customer': customer,
        }
        return render(request, "edit_customer_profile.html", context)

    def post(self, request):
        user = request.user
        customer, created = Customer.objects.get_or_create(auth=user)
        
        # รับค่าจากฟอร์ม (ถ้าไม่ได้พิมพ์อะไรมา ค่าจะเป็น string ว่าง '')
        new_first_name = request.POST.get('first_name', '').strip()
        new_last_name = request.POST.get('last_name', '').strip()
        new_email = request.POST.get('email', '').strip()
        new_phone = request.POST.get('phone', '').strip()

        # เช็คว่าถ้ามีข้อมูลพิมพ์มาใหม่ ถึงจะเอาไปทับของเดิม
        if new_first_name:
            user.first_name = new_first_name
        if new_last_name:
            user.last_name = new_last_name
        if new_email:
            user.email = new_email
        if new_phone:
            customer.phone = new_phone

        profile_image = request.FILES.get('profile_image')

        # ถ้าอัปรูปใหม่เข้ามา
        if profile_image:
            folder_name = 'customer'
            target_folder = os.path.join(settings.BASE_DIR, 'static', 'images', 'profile_images', folder_name)
            
            os.makedirs(target_folder, exist_ok=True)
            
            fs = FileSystemStorage(location=target_folder)
            saved_filename = fs.save(profile_image.name, profile_image)
            db_image_path = f"images/profile_images/{folder_name}/{saved_filename}"

            if customer.image:
                old_file_path = os.path.join(settings.BASE_DIR, 'static', customer.image.image_path)
                
                # เช็คว่าไฟล์นี้มีอยู่จริงไหม ถ้ามีให้ลบไฟล์ทิ้ง
                if os.path.isfile(old_file_path):
                    os.remove(old_file_path)
                
                # ลบ Object รูปเดิมออกจาก Database เพื่อไม่ให้เป็นขยะ
                old_image_obj = customer.image
                customer.image = None # ตัดการผูกกับ db
                old_image_obj.delete()
                
            # สร้าง Object รูปใหม่ลงตาราง Image
            image_obj = Image.objects.create(image_path=db_image_path)
            
            # ผูกรูปใหม่เข้ากับ Customer
            customer.image = image_obj

        try:
            user.save()      
            customer.save()
            messages.success(request, 'อัปเดตข้อมูลลูกค้าสำเร็จ')
        
            return redirect('view-c-profile') 
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
        return render(request, "edit_customer_profile.html")