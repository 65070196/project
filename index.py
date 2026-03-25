import os
from django.core.wsgi import get_wsgi_application

# เปลี่ยนคำว่า 'myproject' เป็นชื่อโฟลเดอร์โปรเจกต์ของคุณ (โฟลเดอร์ที่มีไฟล์ settings.py)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# Vercel จะมองหาตัวแปรที่ชื่อว่า 'app' เพื่อใช้รันเซิร์ฟเวอร์
app = get_wsgi_application()