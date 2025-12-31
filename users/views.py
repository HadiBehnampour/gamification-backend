from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import models  # برای فیلتر کردن پیام‌ها (Q objects)
from .models import User, Message
from .serializers import UserProfileSerializer, MessageSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    نمایش لیست کاربران (برای لیدربرد) و پروفایل شخصی
    """
    # مرتب‌سازی بر اساس امتیاز کل برای لیدربرد
    queryset = User.objects.all().order_by('-total_points')
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='me')
    def get_current_user(self, request):
        """
        اطلاعات کاربر جاری (کسی که لاگین کرده) را برمی‌گرداند.
        آدرس: /api/users/me/
        """
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class MessageViewSet(viewsets.ModelViewSet):
    """
    مدیریت پیام‌های داخلی (صندوق پیام)
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # کاربر فقط باید پیام‌هایی را ببیند که یا فرستنده بوده یا گیرنده
        user = self.request.user
        return Message.objects.filter(
            models.Q(recipient=user) | models.Q(sender=user)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        # هنگام ساخت پیام، فرستنده را خودکار روی کاربر جاری تنظیم می‌کنیم
        serializer.save(sender=self.request.user)

    @action(detail=True, methods=['post'], url_path='read')
    def mark_as_read(self, request, pk=None):
        """
        تغییر وضعیت پیام به 'خوانده شده'
        آدرس: /api/messages/{id}/read/
        """
        message = self.get_object()

        # امنیتی: فقط گیرنده می‌تواند پیام را خوانده شده کند
        if message.recipient != request.user:
            return Response({'error': 'شما اجازه این کار را ندارید'}, status=403)

        message.is_read = True
        message.save()
        return Response({'status': 'پیام خوانده شد'})