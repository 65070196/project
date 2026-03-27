from django.urls import path
from django.shortcuts import redirect
from smartqueue.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("login/", Login.as_view(), name="login"), 
    path("logout/", Logout.as_view(), name="logout"),
    path("register/c/", RegisterCustomer.as_view(), name="register-c"), 
    path("register/s/", RegisterShop.as_view(), name="register-s"), 
    path("reset-password/", ResetPassword.as_view(), name="reset-password"),
    path("line-bind/", LineBindVerify.as_view(), name="line-bind"),

    path('', lambda request: redirect('home-c')), 
    path("home/c/", HomeCustomer.as_view(), name="home-c"), 
    path("home/s/", HomeShop.as_view(), name="home-s"),

    path("shop-detail/<int:shop_id>/", ShopDetail.as_view(), name="shop-detail"),
    
    path("queue-reserve/<int:shop_id>/", QueueReserve.as_view(), name="queue-reserve"),
    path("queue-check/", QueueCheck.as_view(), name="queue-check"),
    path("queue-all/", AllQueueShop.as_view(), name="queue-all"),
    path("queue-edit/<int:queue_id>/", QueueEdit.as_view(), name="queue-edit"),
    path('queue/delete/<int:queue_id>/', QueueDelete.as_view(), name='queue-delete'),

    path("table/", TableManage.as_view(), name="table-manage"),
    path('table/add/', TableAdd.as_view(), name='table-add'),
    path('table/edit/<int:table_id>/', TableEdit.as_view(), name='table-edit'),

    path('table/delete/<int:table_id>/', TableDelete.as_view(), name='table-delete'),

    path("promo/", PromoManage.as_view(), name="promo-manage"),
    path("promo-add/", PromoAdd.as_view(), name="promo-add"),
    path("promo-edit/<int:promo_id>/", PromoEdit.as_view(), name="promo-edit"),
    path("promo/delete/<int:promo_id>/", PromoDelete.as_view(), name="promo-delete"),

    path("opendate-edit/", EditOpendate.as_view(), name="opendate-edit"),

    path("c-profile/", ViewCustomerProfile.as_view(), name="view-c-profile"),
    path("edit-c-profile/", EditCustomerProfile.as_view(), name="edit-c-profile"),

    path("s-profile/", ViewShopProfile.as_view(), name="view-s-profile"),
    path("edit-s-profile/", EditShopProfile.as_view(), name="edit-s-profile"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)