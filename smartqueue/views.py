import os
import requests
import uuid

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

from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

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
        # 1. ดึงค่าจากฟอร์ม
        username_form = request.POST.get('username', '').strip()
        email_form = request.POST.get('email', '').strip()
        password1_form = request.POST.get('password', '')
        password2_form = request.POST.get('password_confirm', '')
        firstname_form = request.POST.get('firstname', '').strip()
        lastname_form = request.POST.get('lastname', '').strip()
        phone_form = request.POST.get('phone', '').strip()

        # 2. เตรียมข้อมูลส่งกลับ (เผื่อมี Error)
        context = {
            'old_username': username_form,
            'old_email': email_form,
            'old_firstname': firstname_form,
            'old_lastname': lastname_form,
            'old_phone': phone_form,
        }

        # 3. Validation ต่างๆ
        try:
            if not all([username_form, email_form, password1_form, password2_form, firstname_form, lastname_form]):
                raise Exception("กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน")

            if password1_form != password2_form:
                raise Exception("รหัสผ่านทั้งสองช่องไม่ตรงกัน")
                
            if len(password1_form) < 8:
                raise Exception("รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")

            if User.objects.filter(username=username_form).exists():
                raise Exception("ชื่อผู้ใช้งานนี้ถูกใช้ไปแล้ว")
            
            if User.objects.filter(email=email_form).exists():
                raise Exception("อีเมลนี้ถูกใช้ไปแล้ว")

            # 4. เริ่มสร้าง User (ใช้ Transaction เพื่อความปลอดภัย)
            with transaction.atomic():
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
            context['error_message'] = str(e)
            return render(request, 'register_customer.html', context)


class RegisterShop(View):
    def get(self, request):
        return render(request, "register_shop.html")
    
    def post(self, request):
        # 1. ดึงค่าจากฟอร์ม
        shop_name_form = request.POST.get('shop_name', '').strip()
        username_form = request.POST.get('username', '').strip()
        email_form = request.POST.get('email', '').strip()
        phone_form = request.POST.get('phone', '').strip()
        password1_form = request.POST.get('password', '')
        password2_form = request.POST.get('password_confirm', '')

        # 2. เตรียมข้อมูลส่งกลับเพื่อเก็บค่าไว้ในฟอร์ม
        context = {
            'old_shop_name': shop_name_form,
            'old_username': username_form,
            'old_email': email_form,
            'old_phone': phone_form,
        }

        try:
            # 3. Validation
            if not all([shop_name_form, username_form, password1_form, password2_form]):
                raise Exception("กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน")
            
            if password1_form != password2_form:
                raise Exception("รหัสผ่านทั้งสองช่องไม่ตรงกัน")
            
            if len(password1_form) < 8:
                raise Exception("รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
            
            if User.objects.filter(username=username_form).exists():
                raise Exception("ชื่อผู้ใช้งานนี้ถูกใช้ไปแล้ว")
            
            if email_form and User.objects.filter(email=email_form).exists():
                raise Exception("อีเมลนี้ถูกใช้ไปแล้ว")

            # 4. เริ่มบันทึกข้อมูล (ใช้ transaction.atomic เพื่อป้องกันข้อมูลค้างถ้าเกิด Error กลางทาง)
            with transaction.atomic():
                # สร้าง User
                user = User.objects.create_user(
                    username=username_form,
                    email=email_form,
                    password=password1_form
                )
                # สร้างข้อมูล Shop
                Shop.objects.create(
                    auth=user,
                    shop_name=shop_name_form,
                    phone=phone_form
                )
                
                # สมัครเสร็จให้ Login ให้อัตโนมัติ (เลือกใช้ได้)
                # login(request, user) 
                
                return redirect('home-s')

        except Exception as e:
            # ส่ง Error และค่าเดิมกลับไปที่หน้าเดิม
            context['error_message'] = str(e)
            return render(request, 'register_shop.html', context)

class ResetPassword(View):
    def get(self, request):
        return render(request, "reset_password.html")
    

class LineAuthRedirect(View):
    def get(self, request):
        # 1. รับค่าว่าลูกค้ากดปุ่มมาจากหน้าไหน (เข้าสู่ระบบ หรือ ผูกบัญชี)
        action = request.GET.get('action', 'login')
        request.session['line_action'] = action # จำใส่เซสชันไว้
        
        channel_id = settings.LINE_LOGIN_CHANNEL_ID
        callback_url = settings.LINE_LOGIN_CALLBACK_URL
        state = uuid.uuid4().hex # รหัสป้องกันการแฮ็ก
        
        # 2. สร้างลิงก์ส่งลูกค้าไปหน้าเว็บล็อกอินของ LINE
        line_auth_url = (
            f"https://access.line.me/oauth2/v2.1/authorize"
            f"?response_type=code"
            f"&client_id={channel_id}"
            f"&redirect_uri={callback_url}"
            f"&state={state}"
            f"&scope=profile%20openid"
        )
        return redirect(line_auth_url) # เด้งไปหน้า LINE สีเขียวๆ ทันที!

class LineAuthCallback(View):
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            messages.error(request, 'ยกเลิกการเชื่อมต่อ LINE แล้ว')
            return redirect('login')

        try:
            # 1. เอา Code ที่ LINE ให้มา ไปแลกเป็น Access Token
            token_url = "https://api.line.me/oauth2/v2.1/token"
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': settings.LINE_LOGIN_CALLBACK_URL,
                'client_id': settings.LINE_LOGIN_CHANNEL_ID,
                'client_secret': settings.LINE_LOGIN_CHANNEL_SECRET
            }
            token_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            token_res = requests.post(token_url, data=token_data, headers=token_headers).json()
            
            access_token = token_res.get('access_token')
            if not access_token: raise Exception("ขอ Token ไม่สำเร็จ")
            
            # 2. เอา Access Token ไปดึงข้อมูลโปรไฟล์ (UID และ ชื่อ)
            profile_url = "https://api.line.me/v2/profile"
            profile_headers = {'Authorization': f'Bearer {access_token}'}
            profile_res = requests.get(profile_url, headers=profile_headers).json()
            
            line_uid = profile_res.get('userId')
            display_name = profile_res.get('displayName')
            if not line_uid: raise Exception("ไม่สามารถดึงข้อมูล UID ได้")

            # 3. เช็คว่ากำลังทำ Action อะไรอยู่ (ล็อกอิน หรือ ผูกบัญชี)
            action = request.session.get('line_action')
            
            if action == 'bind':
                # ---- กรณี 3.1: ลูกค้ากด "ผูกบัญชี" จากหน้าโปรไฟล์ ----
                existing_line = Customer.objects.filter(line_uid=line_uid).exclude(auth=request.user).first()
                if existing_line:
                    messages.error(request, 'ขออภัย บัญชี LINE นี้ถูกเชื่อมต่อกับผู้ใช้งานอื่นไปแล้ว')
                else:
                    customer, _ = Customer.objects.get_or_create(auth=request.user)
                    customer.line_uid = line_uid
                    customer.save()
                    messages.success(request, f'เชื่อมต่อกับ LINE: {display_name} สำเร็จ!')
                return redirect('view-c-profile')
                
            else:
                # ---- กรณี 3.2: ลูกค้ากด "เข้าสู่ระบบด้วย LINE" ----
                customer = Customer.objects.filter(line_uid=line_uid).first()
                if customer:
                    login(request, customer.auth) # เคยมีบัญชีแล้ว ล็อกอินเลย
                else:
                    # สร้างบัญชีใหม่ให้เนียนๆ
                    new_user = User.objects.create_user(
                        username=f"line_{line_uid[:8]}_{uuid.uuid4().hex[:5]}",
                        password=uuid.uuid4().hex,
                        first_name=display_name[:30]
                    )
                    Customer.objects.create(auth=new_user, line_uid=line_uid)
                    login(request, new_user)
                return redirect('home-c')

        except Exception as e:
            messages.error(request, f'ระบบขัดข้อง: {str(e)}')
            return redirect('view-c-profile' if request.user.is_authenticated else 'login')



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
        now = timezone.localtime()
        today = now.date()
        pax_str = request.GET.get('pax', '')
        date_str = request.GET.get('queue_date')
        if date_str:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            if selected_date < today: selected_date = today
        else:
            selected_date = today

        weekday = selected_date.weekday()
        open_info = shop.open_date
        
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

        hour_range = []
        if not is_closed and start_time and end_time:
            buffer_time = (now + datetime.timedelta(hours=1)).time()
            for h in range(start_time.hour, end_time.hour):
                slot_time = datetime.time(hour=h, minute=0)
                if selected_date == today and slot_time < buffer_time:
                    continue
                hour_range.append(h)

        context = {
            'shop': shop,
            'hour_range': hour_range,
            'is_closed': is_closed,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'today_str': today.strftime('%Y-%m-%d'),
            'pax_value': pax_str,
        }
        return render(request, 'queue_reserve.html', context)
    
    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        
        queue_date_str = request.POST.get('queue_date')
        queue_time_str = request.POST.get('queue_time')
        pax_str = request.POST.get('pax')

        now = timezone.localtime()
        today = now.date()
        date_obj = parse_date(queue_date_str) if queue_date_str else today

        if not queue_date_str or not queue_time_str or not pax_str:
            return redirect(f"{request.path}?queue_date={date_obj.strftime('%Y-%m-%d')}")

        try:
            customer = Customer.objects.get(auth=request.user)
            parsed_date = parse_date(queue_date_str)
            parsed_time = parse_time(queue_time_str)
            pax = int(pax_str)

            if pax <= 0: raise Exception("จำนวนลูกค้าต้องมากกว่า 0 ท่าน")
            if parsed_date < today: raise Exception("ไม่สามารถจองคิวย้อนหลังได้")
            if parsed_date == today:
                buffer_time = (now + datetime.timedelta(hours=1)).time()
                if parsed_time < buffer_time:
                    raise Exception("กรุณาจองคิวล่วงหน้าอย่างน้อย 1 ชั่วโมง")
            if parsed_time.minute != 0: raise Exception("รองรับการจองเฉพาะนาทีที่ :00 เท่านั้น")

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
                raise Exception("ร้านปิดทำการในวันที่คุณเลือก")
            if not (o_time <= parsed_time < c_time):
                raise Exception("กรุณาเลือกเวลาในช่วงที่ร้านเปิดทำการ")

            combined_datetime = datetime.datetime.combine(parsed_date, parsed_time)

            # --- เริ่ม Algorithm ---
            with transaction.atomic():
                suitable_tables = Table.objects.filter(shop=shop, capacity__gte=pax).order_by('capacity')
                allocated_table = None

                # 1. ลองหาโต๊ะในเวลาที่ลูกค้าต้องการก่อน
                for table in suitable_tables:
                    locked_table = Table.objects.select_for_update().get(pk=table.pk)
                    existing_queues_count = Queue.objects.filter(
                        shop=shop, table=locked_table, queue_time=combined_datetime, status='doing'
                    ).count()

                    if existing_queues_count < locked_table.amount:
                        allocated_table = locked_table
                        break 
                
                # 2. ถ้ามีโต๊ะว่าง บันทึกคิวได้เลย
                if allocated_table:
                    Queue.objects.create(
                        customer=customer, shop=shop, table=allocated_table,
                        pax=pax, queue_date=parsed_date, queue_time=combined_datetime, status='doing'
                    )
                    if customer.line_uid:
                        try:
                            line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
                            
                            # จัดฟอร์แมตข้อความ
                            receipt_msg = (
                                f"🎉 จองคิวสำเร็จแล้ว!\n\n"
                                f"🏪 ร้าน: {shop.shop_name}\n"
                                f"🪑 โต๊ะ: {allocated_table.name} ({pax} ท่าน)\n"
                                f"📅 วันที่: {parsed_date.strftime('%d/%m/%Y')}\n"
                                f"⏰ เวลา: {parsed_time.strftime('%H:%M')} น.\n\n"
                                f"🙏 กรุณามาถึงร้านก่อนเวลา 10 นาทีนะคะ"
                            )
                            
                            # สั่งยิงข้อความตรงเข้ามือถือลูกค้า
                            line_bot_api.push_message(
                                customer.line_uid, 
                                TextSendMessage(text=receipt_msg)
                            )
                        except LineBotApiError as e:
                            # ถ้าส่งไม่ผ่าน (เช่น ลูกค้าบล็อกบอท) เว็บก็จะไม่พัง ให้ปริ้นท์ Error บอกหลังบ้าน
                            print(f"เกิดข้อผิดพลาดในการส่ง LINE: {e}")
                            
                    return redirect('home-c') 

                # 3. 🔴 ถ้าโต๊ะเต็ม! เข้าสู่ "Smart Alternative Time Algorithm" 🔴
                else:
                    alternative_times = []
                    # สร้างรายการชั่วโมงทั้งหมดที่ร้านเปิด
                    valid_hours = list(range(o_time.hour, c_time.hour))
                    
                    # ตัดเวลาในอดีตทิ้ง (ถ้าเป็นวันนี้)
                    if parsed_date == today:
                        valid_hours = [h for h in valid_hours if datetime.time(hour=h, minute=0) >= buffer_time]
                    
                    # ตัดชั่วโมงที่ลูกค้าเพิ่งกดเลือกแล้วมันเต็มออก
                    if parsed_time.hour in valid_hours:
                        valid_hours.remove(parsed_time.hour)
                    
                    # 🌟 จัดเรียงชั่วโมงที่เหลือ โดยเอาเวลาที่ "ใกล้เคียงกับเวลาที่ลูกค้าอยากได้" ขึ้นก่อน
                    valid_hours.sort(key=lambda h: abs(h - parsed_time.hour))

                    # วนลูปเช็คเวลาที่ใกล้เคียง ว่ามีโต๊ะว่างไหม
                    for h in valid_hours:
                        alt_time = datetime.time(hour=h, minute=0)
                        alt_datetime = datetime.datetime.combine(parsed_date, alt_time)
                        
                        is_alt_available = False
                        for table in suitable_tables:
                            count = Queue.objects.filter(shop=shop, table=table, queue_time=alt_datetime, status='doing').count()
                            if count < table.amount:
                                is_alt_available = True
                                break # มีโต๊ะว่างในเวลานี้
                        
                        if is_alt_available:
                            alternative_times.append(f"{h:02d}:00")
                            if len(alternative_times) >= 3: # แนะนำแค่ 3 เวลาที่ใกล้ที่สุดพอ
                                break
                    
                    # คืนค่ากลับไปบอกหน้าเว็บว่าเต็ม แต่แนบเวลาแนะนำไปด้วย
                    raise ValueError({
                        'msg': f"ขออภัย โต๊ะสำหรับ {pax} ท่าน เวลา {parsed_time.strftime('%H:%M')} น. เต็มแล้ว",
                        'alts': alternative_times
                    })

        except ValueError as ve:
            # ดักจับ Error พิเศษที่มีการแนบเวลา Alternative
            error_data = ve.args[0]
            error = error_data['msg']
            alternatives = error_data['alts']
        except Customer.DoesNotExist:
            error = 'ไม่พบข้อมูลลูกค้า'
            alternatives = []
        except Exception as e:
            error = str(e)
            alternatives = []

        # ส่งค่ากลับไป Render พร้อม UI แนะนำเวลา
        hour_range = []
        if not is_closed and o_time and c_time:
            buffer_time = (now + datetime.timedelta(hours=1)).time()
            for h in range(o_time.hour, c_time.hour):
                slot_time = datetime.time(hour=h, minute=0)
                if parsed_date == today and slot_time < buffer_time: continue
                hour_range.append(h)

        return render(request, 'queue_reserve.html', {
            'shop': shop,
            'error_message': error,
            'alternative_times': alternatives, # ส่งเวลาแนะนำไปให้ HTML
            'selected_date': parsed_date.strftime('%Y-%m-%d') if parsed_date else today.strftime('%Y-%m-%d'),
            'today_str': today.strftime('%Y-%m-%d'),
            'pax_value': pax_str,
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
    