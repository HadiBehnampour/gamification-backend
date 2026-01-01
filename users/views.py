from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Sum, Q
from .models import User, Message
from .serializers import CustomTokenObtainPairSerializer, UserProfileSerializer, MessageSerializer


# ویوی لاگین سفارشی
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    # دریافت اطلاعات کاربر جاری (Profile.jsx)
    @action(detail=False, methods=['get'])
    def me(self, request):
        return Response(self.get_serializer(request.user).data)

    # اطلاعات داشبورد کارمند (محاسبه رتبه و نمودارها)
    @action(detail=False, methods=['get'])
    def dashboard_stats(self, request):
        user = request.user
        # ایمپورت مدل تراکنش در داخل متد تا فعلا ارور ندهد
        from gamification.models import Transaction

        rank = User.objects.filter(total_points__gt=user.total_points, role='EMPLOYEE').count() + 1
        total_emp = User.objects.filter(role='EMPLOYEE').count()

        # تفکیک امتیازها برای نمودار
        stats = {}
        for t_type, key in [('PERFORMANCE', 'performance'), ('DISCIPLINE', 'discipline'), ('CULTURAL', 'cultural'),
                            ('IDEA', 'trend')]:
            val = Transaction.objects.filter(user=user, token_type=t_type).aggregate(Sum('amount'))['amount__sum'] or 0
            stats[key] = val

        xp_needed = 500
        current_xp = user.total_points % xp_needed

        return Response({
            'full_name': f"{user.first_name} {user.last_name}" if user.first_name else user.username,
            'level': user.level,
            'level_progress': (current_xp / xp_needed) * 100,
            'xp_to_next_level': xp_needed - current_xp,
            'rank': rank,
            'total_employees': total_emp,
            'tokens': stats,
            'avatar_url': user.avatar.url if user.avatar else None
        })

    # لیدربرد (Leaderboard.jsx)
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
                'trend': 'up' if idx < 3 else 'steady'  # منطق ساده ترند
            })
        return Response({'current_user_id': request.user.id, 'rankings': rankings})

    # لیست ساده برای دراپ‌داون‌های ادمین (Messages.jsx)
    @action(detail=False, methods=['get'], url_path='simple-list')
    def simple_list(self, request):
        users = User.objects.filter(role='EMPLOYEE')
        data = [{'id': u.id, 'full_name': f"{u.first_name} {u.last_name}" if u.first_name else u.username,
                 'department': 'Fanni'} for u in users]
        return Response(data)

    # تاپ پرفورمرها برای داشبورد ادمین (Dashboard.jsx)
    @action(detail=False, methods=['get'])
    def top_performers(self, request):
        users = User.objects.filter(role='EMPLOYEE').order_by('-total_points')[:5]
        data = [{'name': u.username, 'role': 'پرسنل', 'tokens': u.total_points, 'level': f"Lvl {u.level}",
                 'avatar': u.avatar.url if u.avatar else None} for u in users]
        return Response(data)

    # آپدیت عکس پروفایل
    @action(detail=False, methods=['patch'], url_path='update_avatar')
    def update_avatar(self, request):
        if 'avatar' in request.FILES:
            request.user.avatar = request.FILES['avatar']
            request.user.save()
            return Response({'avatar_url': request.user.avatar.url})
        return Response({'error': 'No file'}, status=400)

    # آپدیت اطلاعات متنی پروفایل
    @action(detail=False, methods=['patch'], url_path='update_profile')
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


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(Q(recipient=self.request.user) | Q(sender=self.request.user)).order_by(
            '-created_at')

    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

    # ارسال پیام گروهی (ادمین)
    @action(detail=False, methods=['post'])
    def broadcast(self, request):
        if request.user.role != 'ADMIN': return Response(status=403)
        subject = request.data.get('subject')
        body = request.data.get('text')
        recipients = User.objects.filter(role='EMPLOYEE')
        msgs = [Message(sender=request.user, recipient=u, subject=subject, body=body) for u in recipients]
        Message.objects.bulk_create(msgs)
        return Response({'message': 'Sent'})