import os
from django.core.wsgi import get_wsgi_application

# ตรงนี้สำคัญมาก ต้องเป็น 'project.settings' ครับ
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = get_wsgi_application()