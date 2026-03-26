import os
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.conf import settings
from django.contrib.auth import authenticate, logout, login

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_time
import datetime

from django.contrib.auth.models import User
from .models import *


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
        user = request.user
        queues = Queue.objects.filter(customer__auth=user).order_by('-queue_date', '-queue_time')
        
        context = {
            'queues': queues
        }
        return render(request, "queue_check.html", context)
    

class QueueReserve(View):
    def get(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        tables = Table.objects.filter(shop=shop)
        
        # 1. รับค่าวันที่ลูกค้าเลือกจากพารามิเตอร์ (ถ้ายังไม่เลือกให้ใช้วันนี้)
        date_str = request.GET.get('queue_date')
        if date_str:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        else:
            selected_date = datetime.date.today()

        # 2. หาวันในสัปดาห์ (0=จันทร์, 6=อาทิตย์)
        weekday = selected_date.weekday()
        open_info = shop.open_date # ดึงข้อมูลจาก OneToOneField
        
        # 3. Logic การดึงเวลาเปิด-ปิดตามวัน
        day_map = {
            0: (open_info.mon_is_closed, open_info.mon_open, open_info.mon_close),
            1: (open_info.tue_is_closed, open_info.tue_open, open_info.tue_close),
            2: (open_info.wed_is_closed, open_info.wed_open, open_info.wed_close),
            3: (open_info.thu_is_closed, open_info.thu_open, open_info.thu_close),
            4: (open_info.fri_is_closed, open_info.fri_open, open_info.fri_close),
            5: (open_info.sat_is_closed, open_info.sat_open, open_info.sat_close),
            6: (open_info.sun_is_closed, open_info.sun_open, open_info.sun_close),
        }

        is_closed, start_time, end_time = day_map.get(weekday)

        # 4. สร้างรายการชั่วโมง (เฉพาะนาที :00)
        hour_range = []
        if not is_closed and start_time and end_time:
            # วนลูปตั้งแต่ชั่วโมงที่เปิด จนถึงชั่วโมงก่อนปิด
            for h in range(start_time.hour, end_time.hour):
                hour_range.append(h)

        context = {
            'shop': shop,
            'tables': tables,
            'hour_range': hour_range,
            'is_closed': is_closed,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
        }
        return render(request, 'queue_reserve.html', context)
    
    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        tables = Table.objects.filter(shop=shop) 
        
        queue_date_str = request.POST.get('queue_date')
        queue_time_str = request.POST.get('queue_time')
        table_id = request.POST.get('table_id')

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

            # --- เพิ่มจุดเช็คเวลาตรงนี้ ---
            if parsed_time.minute not in [0, 30]:
                return render(request, 'queue_reserve.html', {
                    'shop': shop,
                    'tables': tables,
                    'error_message': 'ขออภัย ระบบรองรับการจองเฉพาะนาทีที่ :00 และ :30 เท่านั้น'
                })
            # ---------------------------

            combined_datetime = datetime.datetime.combine(parsed_date, parsed_time)

            with transaction.atomic():
                table = Table.objects.select_for_update().get(pk=table_id, shop=shop)
                
                existing_queues_count = Queue.objects.filter(
                    shop=shop,
                    table=table,
                    queue_time=combined_datetime
                ).count()

                if existing_queues_count >= table.amount:
                    return render(request, 'queue_reserve.html', {
                        'shop': shop,
                        'tables': tables,
                        'error_message': f'ขออภัย โต๊ะประเภท "{table.name}" ในเวลาดังกล่าวถูกจองเต็มแล้ว'
                    })

                Queue.objects.create(
                    customer=customer,
                    shop=shop,
                    table=table,
                    queue_date=parsed_date,
                    queue_time=combined_datetime
                )
            
            return redirect('home-c') 

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
            today = timezone.localdate()
            
            queues = Queue.objects.filter(shop=my_shop, queue_date=today).order_by('queue_time')
            
            context = {
                'queues': queues,
                'today_date': today,
            }
            return render(request, "home_shop.html", context)
            
        except Shop.DoesNotExist:
            return redirect('login') 
    
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
            
        today = timezone.localdate()
        queues = Queue.objects.filter(shop__auth=request.user, queue_date=today).order_by('queue_time')
    
        context = {
            'queues': queues,
            'today_date': today,
        }
        return render(request, "home_shop.html", context)

class AllQueueShop(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')
        try:
            my_shop = Shop.objects.get(auth=request.user)
            queues = Queue.objects.filter(shop=my_shop).order_by('queue_date', 'queue_time')  
            context = {
                'queues': queues
            }
            return render(request, "queue_all.html", context)
        except Shop.DoesNotExist:
            return redirect('login')

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        queues = Queue.objects.filter(shop__auth=request.user).order_by('queue_date', 'queue_time')

        context = {

            'queues': queues
        }
        return render(request, "queue_all.html", context)
    

class ShopDetail(View):
    def get(self, request, shop_id):
        # 1. ค้นหาร้านค้า
        try:
            shop = Shop.objects.get(pk=shop_id)
        except Shop.DoesNotExist:
            return redirect('home-c') 
            
        # 2. ดึงข้อมูลที่เกี่ยวข้อง
        promotions = Promotion.objects.filter(shop=shop)
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
            'tables': tables,
            'open_dates_list': open_dates_list,
        }
        return render(request, 'shop_detail.html', context)


class QueueEdit(View):
    def get(self, request, queue_id):
        queue = get_object_or_404(Queue, pk=queue_id)
        # รับค่าจาก URL ว่ามาจากหน้าไหน (default เป็น 'today')
        next_page = request.GET.get('next', 'today')
        
        return render(request, "queue_edit.html", {
            'queue': queue,
            'next_page': next_page
        })

    def post(self, request, queue_id):
        queue = get_object_or_404(Queue, pk=queue_id)
        queue.status = request.POST.get('status')
        queue.save()

        # ตรวจสอบว่าหลังจากบันทึกเสร็จ ควร Redirect ไปที่ไหน
        next_page = request.GET.get('next')
        if next_page == 'all':
            return redirect('queue-all')
        else:
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
        image_obj = None

        # จัดการรูปภาพ (แบบใหม่ให้ Cloudinary จัดการ)
        if image_file:
            image_obj = Image.objects.create(image_path=image_file)

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
        
        shop = Shop.objects.filter(auth=request.user).first()
        
        context = {
            'user': request.user,
            'shop': shop,
        }
        return render(request, "shop_profile.html", context)


class EditShopProfile(View):
    def get(self, request):
        # ใช้ get_or_create ป้องกันกรณี User ไม่มี Profile Shop
        shop, created = Shop.objects.get_or_create(auth=request.user) 
        context = {
            'user': request.user,
            'shop': shop,
        }
        return render(request, "edit_shop_profile.html", context)

    def post(self, request):
        user = request.user
        shop, created = Shop.objects.get_or_create(auth=user)
        
        # รับค่าจากฟอร์ม
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        shop_name = request.POST.get('shop_name', '').strip()
        description = request.POST.get('description', '').strip()
        phone = request.POST.get('phone', '').strip()
        profile_image = request.FILES.get('profile_image')

        try:
            # ใช้ transaction.atomic เพื่อให้แน่ใจว่าต้องสำเร็จทั้ง User และ Shop
            with transaction.atomic():
                # อัปเดตข้อมูล User
                if first_name: user.first_name = first_name
                if last_name: user.last_name = last_name
                if email: user.email = email
                user.save()

                # อัปเดตข้อมูล Shop
                if shop_name: shop.shop_name = shop_name
                if description: shop.description = description
                if phone: shop.phone = phone

                # จัดการรูปภาพ (Cloudinary)
                if profile_image:
                    # ถ้ามีรูปเดิม ให้ลบ Object เดิมออก (เพื่อลบไฟล์บน Cloudinary ด้วย)
                    if shop.image:
                        old_image = shop.image
                        shop.image = None # ตัดความสัมพันธ์ก่อนลบ
                        old_image.delete()
                    
                    # สร้าง Object รูปใหม่
                    new_image = Image.objects.create(image_path=profile_image)
                    shop.image = new_image
                
                shop.save()
                
            messages.success(request, 'อัปเดตข้อมูลร้านค้าสำเร็จ')
            return redirect('view-s-profile')

        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
        # ถ้าพัง ให้กลับไปหน้าเดิมพร้อมข้อมูลที่กรอกค้างไว้
        return render(request, "edit_shop_profile.html", {
            'user': user,
            'shop': shop,
        })


class ViewCustomerProfile(View):
    def get(self, request):
        customer = Customer.objects.filter(auth=request.user).first()
        return render(request, "customer_profile.html", {
            'user': request.user,
            'customer': customer,
        })


from django.db import transaction # อย่าลืม import ตัวนี้ที่ด้านบนของไฟล์นะครับ

class EditCustomerProfile(View):
    def get(self, request):
        user = request.user
        # ดึงข้อมูล Customer หรือสร้างถ้ายังไม่มี
        customer, created = Customer.objects.get_or_create(auth=user) 
        context = {
            'user': user,
            'customer': customer,
        }
        return render(request, "edit_customer_profile.html", context)

    def post(self, request):
        user = request.user
        customer, created = Customer.objects.get_or_create(auth=user)
        
        # รับค่าจาก POST
        new_first_name = request.POST.get('first_name', '').strip()
        new_last_name = request.POST.get('last_name', '').strip()
        new_email = request.POST.get('email', '').strip()
        new_phone = request.POST.get('phone', '').strip()
        profile_image = request.FILES.get('profile_image')

        try:
            # ใช้ transaction เพื่อให้เซฟทั้งสองตารางพร้อมกันแบบสมบูรณ์
            with transaction.atomic():
                # อัปเดตข้อมูล User หลัก
                if new_first_name: user.first_name = new_first_name
                if new_last_name: user.last_name = new_last_name
                if new_email: user.email = new_email
                user.save()

                # อัปเดตข้อมูล Customer
                if new_phone: customer.phone = new_phone

                # จัดการรูปภาพโปรไฟล์
                if profile_image:
                    # ลบรูปเก่าทิ้ง (ถ้ามี) เพื่อไม่ให้ขยะเต็ม Cloudinary
                    if customer.image:
                        old_image = customer.image
                        customer.image = None # ตัดความสัมพันธ์ก่อน
                        old_image.delete() # ลบ object และไฟล์
                    
                    # สร้างรูปใหม่และผูกเข้ากับ Customer
                    image_obj = Image.objects.create(image_path=profile_image)
                    customer.image = image_obj

                customer.save()

            messages.success(request, 'อัปเดตข้อมูลส่วนตัวสำเร็จแล้ว!')
            return redirect('view-c-profile') 
            
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาด: {str(e)}')
            
        # ถ้าเกิด Error ให้ส่งกลับหน้าเดิมพร้อมข้อมูลปัจจุบัน
        context = {
            'user': user,
            'customer': customer,
        }
        return render(request, "edit_customer_profile.html", context)