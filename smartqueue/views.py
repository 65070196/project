import os
from django.conf import settings
import requests
import uuid
import urllib.parse

from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.contrib import messages
from django.db.models import Case, When, Value, IntegerField, Count, Sum
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse

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
                login(request, user)
                
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
        action = request.GET.get('action', 'login')
        request.session['line_action'] = action
        
        channel_id = settings.LINE_LOGIN_CHANNEL_ID
        callback_url = "https://project-nu-three-88.vercel.app/line/callback/"
        state = uuid.uuid4().hex 
        
        params = {
            'response_type': 'code',
            'client_id': channel_id,
            'redirect_uri': callback_url,
            'state': state,
            'scope': 'profile openid',
            'bot_prompt': 'aggressive' 
        }
        
        query_string = urllib.parse.urlencode(params)
        line_auth_url = f"https://access.line.me/oauth2/v2.1/authorize?{query_string}"
        
        return redirect(line_auth_url)

class LineAuthCallback(View):
    def get(self, request):
        code = request.GET.get('code')
        if not code:
            messages.error(request, 'ยกเลิกการเชื่อมต่อ LINE แล้ว')
            return redirect('login')

        try:
            # 🚀 2. บังคับพิมพ์ลิงก์จริงลงไปตรงนี้ด้วย (ต้องเหมือนข้างบนเป๊ะๆ)
            callback_url = "https://project-nu-three-88.vercel.app/line/callback/"
            
            # 1. เอา Code ที่ LINE ให้มา ไปแลกเป็น Access Token
            token_url = "https://api.line.me/oauth2/v2.1/token"
            token_data = {
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': callback_url, # 👈 ส่งลิงก์จริงไปยืนยัน
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
        # ดึงคำค้นหาจาก URL (ถ้าไม่มีให้เป็นค่าว่าง)
        query = request.GET.get('q', '').strip()
        
        # ถ้ามีการพิมพ์ค้นหามา ให้ฟิลเตอร์ร้านค้า
        if query:
            # ใช้ shop_name__icontains เพื่อหาคำที่อยู่ในชื่อร้าน
            shops = Shop.objects.filter(shop_name__icontains=query).order_by('shop_id')
        else:
            # ถ้าไม่ได้ค้นหาอะไร ก็ดึงมาแสดงทั้งหมดเหมือนเดิม
            shops = Shop.objects.all().order_by('shop_id')
            
        context = {
            'shops': shops,
            'search_query': query # ส่งคำค้นหากลับไปแสดงผลด้วย
        }
        return render(request, "home_customer.html", context)


class QueueCheck(View):
    def get(self, request):
        user = request.user
        
        # ค้นหาคิวของลูกค้า และจัดเรียง
        queues = Queue.objects.filter(customer__auth=user).annotate(
            status_order=Case(
                When(status='doing', then=Value(1)),
                When(status='done', then=Value(2)),
                When(status='cancel', then=Value(3)),
                output_field=IntegerField(),
            )
        ).order_by(
            'status_order', 
            'queue_date', 
            'queue_time'    
        )
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
        date_str = request.GET.get('queue_date', '')
        
        try:
            selected_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else today
            if selected_date < today: selected_date = today
        except (ValueError, TypeError):
            selected_date = today
            
        weekday = selected_date.weekday()
        open_info = shop.open_date
        
        my_booked_hours = Queue.objects.filter(
            customer__auth=request.user, queue_date=selected_date, status='doing'
        ).values_list('queue_time__hour', flat=True)

        day_map = {
            0: (open_info.mon_is_closed, open_info.mon_open, open_info.mon_close),
            1: (open_info.tue_is_closed, open_info.tue_open, open_info.tue_close),
            2: (open_info.wed_is_closed, open_info.wed_open, open_info.wed_close),
            3: (open_info.thu_is_closed, open_info.thu_open, open_info.thu_close),
            4: (open_info.fri_is_closed, open_info.fri_open, open_info.fri_close),
            5: (open_info.sat_is_closed, open_info.sat_open, open_info.sat_close),
            6: (open_info.sun_is_closed, open_info.sun_open, open_info.sun_close),
        }

        is_closed, start_time, end_time = day_map.get(weekday, (True, None, None))
        hour_range = []
        
        if not is_closed and start_time and end_time:
            buffer_dt = now + datetime.timedelta(hours=1)
            for h in range(start_time.hour, end_time.hour + (1 if end_time.minute > 0 else 0)):
                if h in my_booked_hours: continue
                slot_time = datetime.time(h, 0)
                slot_dt = timezone.make_aware(datetime.datetime.combine(selected_date, slot_time))
                if start_time <= slot_time < end_time and slot_dt >= buffer_dt:
                    hour_range.append(h)

        return render(request, 'queue_reserve.html', {
            'shop': shop, 'hour_range': hour_range, 'is_closed': is_closed,
            'selected_date': selected_date.strftime('%Y-%m-%d'),
            'today_str': today.strftime('%Y-%m-%d'), 'pax_value': pax_str,
        })
    
    def post(self, request, shop_id):
        shop = get_object_or_404(Shop, pk=shop_id)
        queue_date_str = request.POST.get('queue_date', '').strip()
        queue_time_str = request.POST.get('queue_time', '').strip()
        pax_str = request.POST.get('pax', '0')
        confirm_split = request.POST.get('confirm_split') == 'true'

        now = timezone.localtime()
        today = now.date()
        open_info = shop.open_date

        try:
            customer = Customer.objects.get(auth=request.user)
            parsed_date = parse_date(queue_date_str) if queue_date_str else today
            if not parsed_date: parsed_date = today

            if not queue_time_str:
                raise Exception("กรุณาเลือกเวลาที่ต้องการจอง")
            
            parsed_time = parse_time(queue_time_str)
            if not parsed_time:
                raise Exception("รูปแบบเวลาไม่ถูกต้อง")

            pax = int(pax_str)
            combined_datetime = timezone.make_aware(datetime.datetime.combine(parsed_date, parsed_time))

            # 1. เช็คจองซ้อน
            if Queue.objects.filter(customer=customer, queue_time=combined_datetime, status='doing').exists():
                raise Exception("คุณมีรายการจองคิวเวลานี้อยู่แล้ว")

            if pax <= 0: raise Exception("จำนวนลูกค้าต้องมากกว่า 0 ท่าน")
            
            # 2. เช็คเวลาเปิดปิดร้าน
            weekday = parsed_date.weekday()
            day_config = {0:(open_info.mon_is_closed, open_info.mon_open, open_info.mon_close), 1:(open_info.tue_is_closed, open_info.tue_open, open_info.tue_close), 2:(open_info.wed_is_closed, open_info.wed_open, open_info.wed_close), 3:(open_info.thu_is_closed, open_info.thu_open, open_info.thu_close), 4:(open_info.fri_is_closed, open_info.fri_open, open_info.fri_close), 5:(open_info.sat_is_closed, open_info.sat_open, open_info.sat_close), 6:(open_info.sun_is_closed, open_info.sun_open, open_info.sun_close)}
            is_closed, o_t, c_t = day_config.get(weekday, (True, None, None))
            if is_closed or not o_t or not (o_t <= parsed_time < c_t):
                raise Exception("ร้านปิดทำการหรืออยู่นอกเวลาให้บริการ")

            # 3. Algorithm ค้นหาโต๊ะ (Best-Fit)
            with transaction.atomic():
                all_tables = Table.objects.filter(shop=shop).order_by('capacity')
                allocated_tables = []
                
                suitable_single = all_tables.filter(capacity__gte=pax).first()
                if suitable_single:
                    locked_t = Table.objects.select_for_update().get(pk=suitable_single.pk)
                    q_count = Queue.objects.filter(shop=shop, table=locked_t, queue_time=combined_datetime, status='doing').count()
                    if q_count < locked_t.amount:
                        allocated_tables.append(locked_t)

                if not allocated_tables:
                    available_pool = []
                    for t in all_tables:
                        locked_t = Table.objects.select_for_update().get(pk=t.pk)
                        q_count = Queue.objects.filter(shop=shop, table=locked_t, queue_time=combined_datetime, status='doing').count()
                        for _ in range(max(0, locked_t.amount - q_count)):
                            available_pool.append(locked_t)
                    
                    available_pool.sort(key=lambda x: x.capacity, reverse=True)
                    temp_pax, selected_pool = pax, []
                    
                    while temp_pax > 0 and available_pool:
                        best_match = None
                        for t in reversed(available_pool): 
                            if t.capacity >= temp_pax:
                                best_match = t
                                break
                        if not best_match: best_match = available_pool[0]
                        selected_pool.append(best_match)
                        temp_pax -= best_match.capacity
                        available_pool.remove(best_match)

                    if temp_pax <= 0:
                        if confirm_split:
                            allocated_tables = selected_pool
                        else:
                            t_names = " + ".join([f"{t.name}" for t in selected_pool])
                            # 🌟 ส่ง selected_time กลับไปตอนต้องการยืนยันแยกโต๊ะ 🌟
                            return self._render_reserve(request, shop, f"ไม่มีโต๊ะเดี่ยวว่างสำหรับ {pax} ท่าน แต่สามารถแยกจองเป็น [{t_names}] ได้ ต้องการจองหรือไม่?", parsed_date, pax_str, now, open_info, is_split=True, selected_time=queue_time_str)
                    else:
                        raise Exception("ขออภัย โต๊ะที่ว่างไม่เพียงพอสำหรับจำนวนท่านที่ระบุ")

                if allocated_tables:
                    for table in allocated_tables:
                        Queue.objects.create(customer=customer, shop=shop, table=table, pax=pax, queue_date=parsed_date, queue_time=combined_datetime, status='doing')
                    return redirect('home-c')

        except Exception as e:
            # 🌟 ส่ง selected_time กลับไปตอนเกิด Error ทั่วไป 🌟
            return self._render_reserve(request, shop, str(e), parsed_date if 'parsed_date' in locals() else today, pax_str, now, open_info, selected_time=queue_time_str)

    def _render_reserve(self, request, shop, error, parsed_date, pax_str, now, open_info, is_split=False, selected_time=None):
        my_booked = Queue.objects.filter(customer__auth=request.user, queue_date=parsed_date, status='doing').values_list('queue_time__hour', flat=True)
        hour_range = []
        day_config = {0:(open_info.mon_open, open_info.mon_close), 1:(open_info.tue_open, open_info.tue_close), 2:(open_info.wed_open, open_info.wed_close), 3:(open_info.thu_open, open_info.thu_close), 4:(open_info.fri_open, open_info.fri_close), 5:(open_info.sat_open, open_info.sat_close), 6:(open_info.sun_open, open_info.sun_close)}
        o_t, c_t = day_config.get(parsed_date.weekday(), (None, None))
        
        if o_t and c_t:
            buf = now + datetime.timedelta(hours=1)
            for h in range(o_t.hour, c_t.hour):
                if h in my_booked: continue
                try:
                    if timezone.make_aware(datetime.datetime.combine(parsed_date, datetime.time(h,0))) >= buf:
                        hour_range.append(h)
                except: continue

        return render(request, 'queue_reserve.html', {
            'shop': shop, 'error_message': error, 'selected_date': parsed_date.strftime('%Y-%m-%d'),
            'pax_value': pax_str, 'hour_range': hour_range, 'is_confirm_split': is_split,
            'selected_time': selected_time, # 🌟 ส่งค่าเวลากลับไปให้ HTML
            'today_str': now.date().strftime('%Y-%m-%d')
        })


# หน้าหลักร้านค้า
class HomeShop(View):
    def get_occupancy_data(self, my_shop, target_date):
        total_tables = Table.objects.filter(shop=my_shop).aggregate(total=Sum('amount'))['total'] or 0
        weekday = target_date.weekday()
        open_info = my_shop.open_date
        
        day_map = {
            0: (open_info.mon_is_closed, open_info.mon_open, open_info.mon_close),
            1: (open_info.tue_is_closed, open_info.tue_open, open_info.tue_close),
            2: (open_info.wed_is_closed, open_info.wed_open, open_info.wed_close),
            3: (open_info.thu_is_closed, open_info.thu_open, open_info.thu_close),
            4: (open_info.fri_is_closed, open_info.fri_open, open_info.fri_close),
            5: (open_info.sat_is_closed, open_info.sat_open, open_info.sat_close),
            6: (open_info.sun_is_closed, open_info.sun_open, open_info.sun_close),
        }
        
        is_closed, start_t, end_t = day_map.get(weekday, (True, None, None))
        occupancy_report = []
        
        if not is_closed and start_t and end_t:
            now = timezone.localtime()
            for hour in range(start_t.hour, end_t.hour):
                booked_count = Queue.objects.filter(
                    shop=my_shop, queue_date=target_date, queue_time__hour=hour, status='doing'
                ).count()
                
                available = total_tables - booked_count
                percent = (booked_count / total_tables * 100) if total_tables > 0 else 0
                
                occupancy_report.append({
                    'hour': f"{hour:02d}:00", 'booked': booked_count,
                    'available': max(0, available), 'percent': percent,
                    'is_now': hour == now.hour and target_date == now.date()
                })
        
        return occupancy_report, total_tables

    def get_current_realtime_check(self, my_shop):
        # ฟังก์ชันใหม่: เช็คละเอียดว่าร้านเปิดหรือปิด ณ เวลานี้จริงๆ
        now = timezone.localtime()
        today = now.date()
        current_hour = now.hour
        
        total_tables = Table.objects.filter(shop=my_shop).aggregate(total=Sum('amount'))['total'] or 0
        weekday = today.weekday()
        open_info = my_shop.open_date
        
        day_map = {
            0: (open_info.mon_is_closed, open_info.mon_open, open_info.mon_close),
            1: (open_info.tue_is_closed, open_info.tue_open, open_info.tue_close),
            2: (open_info.wed_is_closed, open_info.wed_open, open_info.wed_close),
            3: (open_info.thu_is_closed, open_info.thu_open, open_info.thu_close),
            4: (open_info.fri_is_closed, open_info.fri_open, open_info.fri_close),
            5: (open_info.sat_is_closed, open_info.sat_open, open_info.sat_close),
            6: (open_info.sun_is_closed, open_info.sun_open, open_info.sun_close),
        }
        
        is_closed, start_t, end_t = day_map.get(weekday, (True, None, None))
        
        # 1. เช็คว่าร้านปิดวันนี้ไหม หรือไม่มีข้อมูลเวลา
        if is_closed or not start_t or not end_t:
            return {'status': 'closed', 'time_str': f"{current_hour:02d}:00 น.", 'message': 'ร้านปิดทำการวันนี้'}
            
        # 2. เช็คว่าอยู่นอกเวลาทำการไหม (เช่น ร้านเปิด 10 ปิด 20 แต่ตอนนี้ 21)
        if not (start_t.hour <= current_hour < end_t.hour):
            return {'status': 'closed', 'time_str': f"{current_hour:02d}:00 น.", 'message': 'นอกเวลาทำการ'}

        # 3. ถ้าร้านเปิดปกติ ค่อยดึงข้อมูล Walk-in
        current_booked_count = Queue.objects.filter(
            shop=my_shop, queue_date=today, queue_time__hour=current_hour, status='doing'
        ).count()
        walkin_available = total_tables - current_booked_count
        
        return {
            'status': 'open',
            'time_str': f"{current_hour:02d}:00 น.",
            'booked': current_booked_count,
            'available': max(0, walkin_available)
        }

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')   
        try:
            my_shop = Shop.objects.get(auth=request.user)
            
            date_str = request.GET.get('view_date')
            today = timezone.localtime().date()
            
            if date_str:
                try:
                    view_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    view_date = today
            else:
                view_date = today
                
            is_today = (view_date == today)
            
            queues = Queue.objects.filter(shop=my_shop, queue_date=view_date).annotate(
                status_order=Case(
                    When(status='doing', then=Value(1)),
                    When(status='done', then=Value(2)),
                    When(status='cancel', then=Value(3)),
                    output_field=IntegerField(),
                )
            ).order_by('status_order', 'queue_time')

            occupancy_report, total_tables = self.get_occupancy_data(my_shop, view_date)
            realtime_check = self.get_current_realtime_check(my_shop)
            
            context = {
                'queues': queues,
                'view_date': view_date,
                'view_date_str': view_date.strftime('%Y-%m-%d'), # คืนค่าให้ input date (มั่นใจว่ามีค่าตลอด)
                'is_today': is_today,
                'occupancy_report': occupancy_report,
                'total_tables': total_tables,
                'realtime_check': realtime_check,
            }
            return render(request, "home_shop.html", context)
        except Shop.DoesNotExist:
            return redirect('login')


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

        # อัปเดตข้อมูลข้อความ
        if new_name != '':
            table.name = new_name
        if new_desc != '':
            table.description = new_desc
        if new_amount != '':
            table.amount = new_amount
        if new_capacity != '':
            table.capacity = new_capacity
            
        new_image = request.FILES.get('image')
        
        if new_image:
            image_obj = Image.objects.create(image_path=new_image)
            table.image = image_obj

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

        messages.success(request, 'บันทึกเวลาทำการสำเร็จเรียบร้อยแล้ว!')
        
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

class SearchSuggestion(View):
    def get(self, request):
        query = request.GET.get('q', '').strip()
        if query:
            # ค้นหาร้านที่ชื่อตรงกับคำที่พิมพ์ (จำกัดแค่ 5 ร้านพอ จะได้ไม่ล้นจอ)
            shops = Shop.objects.filter(shop_name__icontains=query).values('shop_id', 'shop_name')[:5]
            # ส่งข้อมูลกลับไปเป็นแบบ JSON ให้ JavaScript อ่าน
            return JsonResponse({'results': list(shops)})
        
        return JsonResponse({'results': []})


class AboutView(View):
    def get(self, request):
        return render(request, "about.html")
