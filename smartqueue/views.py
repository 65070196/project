import os
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.shortcuts import render
from django.db import transaction
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
from django.db.models import Case, When, Value, IntegerField
from django.conf import settings
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.mixins import LoginRequiredMixin

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
    

class QueueReserve(LoginRequiredMixin, View):
    def get(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        
        # ดึงเวลาปัจจุบัน (อิงตาม TIME_ZONE ใน settings.py)
        now = timezone.localtime()
        today = now.date()
        
        # 1. รับค่าวันที่ลูกค้าเลือกจากพารามิเตอร์ (ถ้ายังไม่เลือกให้ใช้วันนี้)
        date_str = request.GET.get('queue_date')
        if date_str:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            # กันเหนียว: ถ้าลูกค้าแอบแก้ URL เป็นวันในอดีต ให้บังคับกลับมาเป็นวันนี้
            if selected_date < today:
                selected_date = today
        else:
            selected_date = today

        # 2. หาวันในสัปดาห์ (0=จันทร์, 6=อาทิตย์)
        weekday = selected_date.weekday()
        open_info = shop.open_date
        
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

        # 4. สร้างรายการชั่วโมง (เฉพาะนาที :00) และเช็คเวลาล่วงหน้า 1 ชม.
        hour_range = []
        if not is_closed and start_time and end_time:
            # คำนวณเวลาที่อนุญาตให้จองได้ (ปัจจุบัน + 1 ชั่วโมง)
            buffer_time = (now + datetime.timedelta(hours=1)).time()
            
            for h in range(start_time.hour, end_time.hour):
                slot_time = datetime.time(hour=h, minute=0)
                
                # ถ้าเลือกวันจองเป็น "วันนี้" -> เวลาต้องมากกว่าปัจจุบัน 1 ชม.
                if selected_date == today:
                    if slot_time < buffer_time:
                        continue # ข้ามเวลานี้ไป ไม่เอาใส่ลงใน Dropdown
                        
                hour_range.append(h)

        context = {
            'shop': shop,
            'hour_range': hour_range,
            'is_closed': is_closed,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'today_str': today.strftime('%Y-%m-%d'), # ส่งค่าวันนี้ไปล็อคปฏิทินใน HTML
        }
        return render(request, 'queue_reserve.html', context)
    
    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        
        queue_date_str = request.POST.get('queue_date')
        queue_time_str = request.POST.get('queue_time')
        pax_str = request.POST.get('pax')

        # 1. ตรวจสอบค่าว่าง
        if not queue_date_str or not queue_time_str or not pax_str:
            return render(request, 'queue_reserve.html', {
                'shop': shop,
                'error_message': 'กรุณาเลือกวันที่ เวลา และระบุจำนวนคนให้ครบถ้วน'
            })

        try:
            customer = Customer.objects.get(auth=request.user)
            parsed_date = parse_date(queue_date_str)
            parsed_time = parse_time(queue_time_str)
            pax = int(pax_str)
            
            now = timezone.localtime()
            today = now.date()

            if pax <= 0:
                raise Exception("จำนวนลูกค้าต้องมากกว่า 0 ท่าน")

            # ตรวจสอบการจองย้อนหลัง (ป้องกันคนส่งฟอร์มข้าม HTML มา)
            if parsed_date < today:
                raise Exception("ไม่สามารถจองคิวย้อนหลังได้")
                
            if parsed_date == today:
                buffer_time = (now + datetime.timedelta(hours=1)).time()
                if parsed_time < buffer_time:
                    raise Exception("กรุณาจองคิวล่วงหน้าอย่างน้อย 1 ชั่วโมง")

            # 2. ตรวจสอบนาที (ต้องเป็น :00 เท่านั้น)
            if parsed_time.minute != 0:
                raise Exception("ขออภัย ระบบรองรับการจองเฉพาะนาทีที่ :00 (ต้นชั่วโมง) เท่านั้น")

            # 3. ตรวจสอบเวลาเปิด-ปิดร้าน
            weekday = parsed_date.weekday()
            open_info = shop.open_date
            
            day_config = {
                0: (open_info.mon_is_closed, open_info.mon_open, open_info.mon_close),
                1: (open_info.tue_is_closed, open_info.tue_open, open_info.tue_close),
                2: (open_info.wed_is_closed, open_info.wed_open, open_info.wed_close),
                3: (open_info.thu_is_closed, open_info.thu_open, open_info.thu_close),
                4: (open_info.fri_is_closed, open_info.fri_open, open_info.fri_close),
                5: (open_info.sat_is_closed, open_info.sat_open, open_info.sat_close),
                6: (open_info.sun_is_closed, open_info.sun_open, open_info.sun_close),
            }
            
            is_closed, o_time, c_time = day_config.get(weekday)

            if is_closed or not o_time or not c_time:
                raise Exception("ขออภัย ร้านปิดทำการในวันที่คุณเลือก")
            
            if not (o_time <= parsed_time < c_time):
                raise Exception(f"กรุณาเลือกเวลาในช่วงที่ร้านเปิดทำการ ({o_time.strftime('%H:%M')} - {c_time.strftime('%H:%M')})")

            # 4. รวมวันที่และเวลา
            combined_datetime = datetime.datetime.combine(parsed_date, parsed_time)

            # 5. อัลกอริทึม Best-Fit หาโต๊ะที่พอดีที่สุด
            with transaction.atomic():
                # กรองโต๊ะที่จุพอ และเรียงจากเล็กไปใหญ่ (Best-Fit)
                suitable_tables = Table.objects.filter(shop=shop, capacity__gte=pax).order_by('capacity')
                
                if not suitable_tables.exists():
                    raise Exception(f"ขออภัย ไม่พบโต๊ะสำหรับลูกค้า {pax} ท่าน")

                allocated_table = None

                for table in suitable_tables:
                    # ล็อกแถวของโต๊ะนี้ไว้ก่อนเพื่อป้องกันคนแย่งจองพร้อมกัน (Race condition)
                    locked_table = Table.objects.select_for_update().get(pk=table.pk)
                    
                    # เช็กว่าในเวลานี้ โต๊ะประเภทนี้ถูกจองที่สถานะ 'doing' ไปกี่ตัวแล้ว
                    existing_queues_count = Queue.objects.filter(
                        shop=shop,
                        table=locked_table,
                        queue_time=combined_datetime,
                        status='doing'
                    ).count()

                    # ถ้าจำนวนที่ถูกจองยังน้อยกว่าจำนวนโต๊ะที่มี = มีโต๊ะว่าง!
                    if existing_queues_count < locked_table.amount:
                        allocated_table = locked_table
                        break # เจอโต๊ะแล้ว หยุดหาทันที
                
                # ถ้าวนหาจนจบแล้วยังไม่มีโต๊ะ (allocated_table เป็น None)
                if not allocated_table:
                    raise Exception(f"ขออภัย ไม่มีโต๊ะว่างสำหรับลูกค้า {pax} ท่าน ในเวลาดังกล่าว")

                # บันทึกข้อมูลคิว
                Queue.objects.create(
                    customer=customer,
                    shop=shop,
                    table=allocated_table, # โต๊ะที่ระบบเลือกให้
                    pax=pax,               
                    queue_date=parsed_date,
                    queue_time=combined_datetime,
                    status='doing'
                )
            
            return redirect('home-c') 

        except Customer.DoesNotExist:
            error = 'ไม่พบข้อมูลลูกค้า'
        except Exception as e:
            error = str(e)

        # หากมี Error ให้ Query hour_range กลับไปให้หน้าเว็บด้วย เพื่อให้ฟอร์มยังแสดงช่องเวลาได้ถูกต้อง
        now = timezone.localtime()
        today = now.date()
        date_str = request.POST.get('queue_date')
        selected_date = parse_date(date_str) if date_str else today
        
        # fallback เผื่อ error ส่งกลับ
        return render(request, 'queue_reserve.html', {
            'shop': shop,
            'error_message': error,
            'selected_date': selected_date.strftime('%Y-%m-%d') if selected_date else today.strftime('%Y-%m-%d'),
            'today_str': today.strftime('%Y-%m-%d')
        })
        

# หน้าหลักร้านค้า
class HomeShop(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')   
        try:
            my_shop = Shop.objects.get(auth=request.user)
            today = timezone.localdate()
            
            queues = Queue.objects.filter(shop=my_shop, queue_date=today).annotate(
                status_order=Case(
                    When(status='doing', then=Value(1)),
                    When(status='done', then=Value(2)),
                    When(status='cancel', then=Value(3)),
                    output_field=IntegerField(),
                )
            ).order_by('status_order', 'queue_time')
            
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
        
        queues = Queue.objects.filter(shop__auth=request.user, queue_date=today).annotate(
            status_order=Case(
                When(status='doing', then=Value(1)),
                When(status='done', then=Value(2)),
                When(status='cancel', then=Value(3)),
                output_field=IntegerField(),
            )
        ).order_by('status_order', 'queue_time')
    
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
            
            queues = Queue.objects.filter(shop=my_shop).annotate(
                status_order=Case(
                    When(status='doing', then=Value(1)),
                    When(status='done', then=Value(2)),
                    When(status='cancel', then=Value(3)),
                    output_field=IntegerField(),
                )
            ).order_by('status_order', 'queue_date', 'queue_time')  
            
            context = {
                'queues': queues
            }
            return render(request, "queue_all.html", context)
        except Shop.DoesNotExist:
            return redirect('login')

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        queues = Queue.objects.filter(shop__auth=request.user).annotate(
            status_order=Case(
                When(status='doing', then=Value(1)),
                When(status='done', then=Value(2)),
                When(status='cancel', then=Value(3)),
                output_field=IntegerField(),
            )
        ).order_by('status_order', 'queue_date', 'queue_time')

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
        
        next_page = request.GET.get('next')
        
        if next_page == 'all':
            messages.success(request, 'ลบรายการคิวเรียบร้อยแล้ว')
            return redirect('queue-all')
        else:
            messages.success(request, 'ลบรายการคิววันนี้เรียบร้อยแล้ว')
            return redirect('home-s')


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
        capacity = request.POST.get('capacity') # 🌟 เพิ่มการรับค่าความจุ (นั่งได้กี่คน)
        image_file = request.FILES.get('image')

        # สมมติว่าล็อกอินในฐานะเจ้าของร้านแล้ว (คุณอาจต้องใส่ LoginRequiredMixin แบบหน้าจองคิวด้วยนะถ้ายังไม่มี)
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
            capacity=capacity, 
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
        new_capacity = request.POST.get('capacity', '').strip()

        
        if new_name != '':
            table.name = new_name
        if new_desc != '':
            table.description = new_desc
        if new_amount != '':
            table.amount = new_amount
        if new_capacity != '':
            table.capacity = new_capacity
            

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