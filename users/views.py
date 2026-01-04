from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Sum, Q

from .models import User, Message
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    MessageSerializer,
    UserCreateUpdateSerializer
)

# --- ۱. ویوی لاگین سفارشی ---
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


# --- ۲. ویوی مدیریت کاربران ---
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return UserCreateUpdateSerializer
        return UserProfileSerializer

    # دریافت اطلاعات کاربر جاری (هماهنگ با Profile.jsx)
    @action(detail=False, methods=['get'])
    def me(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        data = serializer.data

        # اطمینان از ارسال آدرس کامل عکس برای صفحه پروفایل و تنظیمات
        if user.avatar:
            data['avatar'] = request.build_absolute_uri(user.avatar.url)

        return Response(data)

    # اطلاعات داشبورد (با منطق لول‌بندی جدید و آدرس نسبی عکس)
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        user = request.user
        from gamification.models import Transaction
        points = user.total_points

        # تعیین بازه لول بر اساس سیستم: ۵۰۰، ۱۵۰۰، ۲۵۰۰ و ۴۰۰۰
        if points < 500:
            lower, upper = 0, 500
        elif points < 1500:
            lower, upper = 500, 1500
        elif points < 2500:
            lower, upper = 1500, 2500
        elif points < 4000:
            lower, upper = 2500, 4000
        else:
            lower, upper = 4000, 10000  # سقف فرضی برای لول ۵

        # محاسبه درصد پیشرفت در لول فعلی
        range_total = upper - lower
        current_progress = points - lower
        progress_percentage = (current_progress / range_total) * 100

        # محاسبات رتبه و آمار توکن‌ها
        rank = User.objects.filter(total_points__gt=points, role='EMPLOYEE').count() + 1
        total_emp = User.objects.filter(role='EMPLOYEE').count()

        stats = {}
        for t_type, key in [('PERFORMANCE', 'performance'), ('DISCIPLINE', 'discipline'),
                            ('CULTURAL', 'cultural'), ('IDEA', 'trend')]:
            val = Transaction.objects.filter(user=user, token_type=t_type).aggregate(Sum('amount'))['amount__sum'] or 0
            stats[key] = val

        return Response({
            'full_name': f"{user.first_name} {user.last_name}" if user.first_name else user.username,
            'level': user.level,
            'level_progress': round(max(0, min(100, progress_percentage)), 1),
            'xp_to_next_level': max(0, upper - points),
            'rank': rank,
            'total_employees': total_emp,
            'tokens': stats,
            # ارسال آدرس کامل (Absolute) برای هماهنگی با فرانت جدید
            'avatar_url': request.build_absolute_uri(user.avatar.url) if user.avatar else None
        })

    # لیدربرد
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        users = User.objects.filter(role='EMPLOYEE').order_by('-total_points')
        rankings = []
        for idx, u in enumerate(users):
            rankings.append({
                'id': u.id,
                'full_name': f"{u.first_name} {u.last_name}" if u.first_name else u.username,
                'avatar_url': u.avatar.url if u.avatar else None,
                'total_tokens': u.total_points,
                'level': u.level,
                'trend': 'up' if idx < 3 else 'steady'
            })
        return Response({'current_user_id': request.user.id, 'rankings': rankings})

    # آپدیت عکس پروفایل
    @action(detail=False, methods=['patch'], url_path='me/update_avatar')
    def update_avatar(self, request):
        if 'avatar' in request.FILES:
            u = request.user
            u.avatar = request.FILES['avatar']
            u.save()
            # ارسال آدرس نسبی که فرانت خودش آن را کامل کند
            return Response({
                'avatar_url': u.avatar.url
            })
        return Response({'error': 'No file'}, status=400)

    # آپدیت پروفایل (بدون تغییر)
    @action(detail=False, methods=['patch'], url_path='me/update_profile')
    def update_profile(self, request):
        u = request.user
        data = request.data
        if data.get('newPassword'):
            if u.check_password(data.get('currentPassword')):
                u.set_password(data['newPassword'])
            else:
                return Response({'detail': 'رمز فعلی اشتباه است'}, status=400)

        if data.get('username'): u.username = data['username']
        if data.get('email'): u.email = data['email']
        u.save()
        return Response({'message': 'Updated'})

    # بقیه متدها (simple_list, top_performers, retrieve) بدون تغییر باقی بمانند...
    @action(detail=False, methods=['get'], url_path='simple-list')
    def simple_list(self, request):
        users = User.objects.filter(role='EMPLOYEE')
        data = [{'id': u.id, 'full_name': f"{u.first_name} {u.last_name}" if u.first_name else u.username,
                 'department': 'Fanni'} for u in users]
        return Response(data)

    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        users = User.objects.filter(role='EMPLOYEE').order_by('-total_points')[:5]
        data = [{'name': u.username, 'role': 'پرسنل', 'tokens': u.total_points, 'level': f"Lvl {u.level}",
                 'avatar': u.avatar.url if u.avatar else None} for u in users]
        return Response(data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

# --- ۳. ویوی مدیریت پیام‌ها (بدون تغییر) ---
class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Message.objects.filter(Q(recipient=self.request.user) | Q(sender=self.request.user)).order_by('-created_at')
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)
    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        if request.user.role != 'ADMIN': return Response({'error': 'Admin only'}, status=403)
        subject, body = request.data.get('subject'), request.data.get('text')
        recipients = User.objects.filter(role='EMPLOYEE')
        msgs = [Message(sender=request.user, recipient=u, subject=subject, body=body) for u in recipients]
        Message.objects.bulk_create(msgs)
        return Response({'message': 'Sent'})