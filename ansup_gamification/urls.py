from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# --- ویوهای مربوط به احراز هویت (JWT) ---
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import CustomTokenObtainPairView

# --- وارد کردن ویوهای اپلیکیشن‌ها ---
from users.views import UserViewSet, MessageViewSet
from gamification.views import (
    TransactionViewSet,
    ProductViewSet,
    AdminProductViewSet,
    WalletViewSet,
    AdminWalletViewSet,
    BadgeViewSet
)
from operations.views import (
    MissionViewSet,
    AdminMissionViewSet,
    MissionSubmissionViewSet,
    AttendanceViewSet,
    TrainingSessionViewSet
)

# --- تنظیم روتر (Router) ---
router = DefaultRouter()

# 1. کاربران و پیام‌ها
router.register(r'users', UserViewSet, basename='users')
router.register(r'messages', MessageViewSet, basename='messages')

# 2. گیمیفیکیشن (فروشگاه، کیف پول، تراکنش)
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(r'badges', BadgeViewSet, basename='badges')

# >> بخش فروشگاه
router.register(r'shop', ProductViewSet, basename='shop')  # فروشگاه کاربر (خرید)
router.register(r'admin/shop/items', AdminProductViewSet, basename='admin-shop')  # مدیریت کالا (ادمین)

# >> بخش کیف پول و بانک
router.register(r'wallet', WalletViewSet, basename='wallet')  # کیف پول کاربر
router.register(r'admin/wallet', AdminWalletViewSet, basename='admin-wallet')  # بانک مرکزی (ادمین)

# 3. عملیات (ماموریت، حضور و غیاب، آموزش)
# >> بخش ماموریت‌ها
router.register(r'missions', MissionViewSet, basename='missions')  # لیست ماموریت کاربر
router.register(r'admin/missions', AdminMissionViewSet, basename='admin-missions')  # مدیریت ماموریت (ادمین)
router.register(r'submissions', MissionSubmissionViewSet, basename='submissions')  # بررسی گزارش کارها

# >> بخش حضور و غیاب
router.register(r'attendance', AttendanceViewSet, basename='attendance')

# >> بخش آموزش
router.register(r'training', TrainingSessionViewSet, basename='training')

# --- لیست نهایی URLها ---
urlpatterns = [
    path('admin/', admin.site.urls),

    # مسیرهای API که توسط روتر ساخته شدند
    path('api/', include(router.urls)),

    # مسیرهای لاگین و رفرش توکن
    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# تنظیمات برای نمایش فایل‌های آپلودی (تصاویر پروفایل و...) در حالت Debug
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)