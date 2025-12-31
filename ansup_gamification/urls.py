from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter

# --- این دو خط جدید برای لاگین هستن ---
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from users.views import UserViewSet, MessageViewSet
from gamification.views import TransactionViewSet, BadgeViewSet
from operations.views import (
    MissionViewSet,
    MissionSubmissionViewSet,
    AttendanceViewSet,
    TrainingSessionViewSet
)
from shop.views import ShopItemViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'messages', MessageViewSet, basename='messages')  # مسیج‌ها
router.register(r'transactions', TransactionViewSet, basename='transactions')
router.register(r'badges', BadgeViewSet)
router.register(r'missions', MissionViewSet)
router.register(r'submissions', MissionSubmissionViewSet)
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'training', TrainingSessionViewSet, basename='training')
router.register(r'shop', ShopItemViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    # --- لینک‌های دریافت توکن (Login) ---
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)