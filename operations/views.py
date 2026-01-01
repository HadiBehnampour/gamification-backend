from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.db.models import Q, Sum, Avg
from django.utils import timezone
import datetime

from .models import Mission, MissionSubmission, Attendance, TrainingSession
from .serializers import (
    MissionSerializer,
    MissionSubmissionSerializer,
    AttendanceSerializer,
    TrainingSessionSerializer
)
from gamification.models import Transaction


# --- 1. مدیریت هوشمند ماموریت‌ها ---

class MissionViewSet(viewsets.ModelViewSet):
    """
    این ویو هم برای کارمندان است و هم ادمین.
    بر اساس نقش کاربر، رفتار متفاوتی نشان می‌دهد.
    """
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # --- اگر کاربر ادمین است ---
        if user.role == 'ADMIN':
            status_param = self.request.GET.get('status')
            qs = Mission.objects.all().order_by('-created_at')
            if status_param == 'active':
                return qs.filter(is_active=True)
            elif status_param == 'completed':
                return qs.filter(is_active=False)
            return qs

        # --- اگر کاربر کارمند است ---
        status_param = self.request.GET.get('status', 'active')
        user_subs = MissionSubmission.objects.filter(user=user)

        if status_param == 'completed':
            ids = user_subs.filter(status='APPROVED').values_list('mission_id', flat=True)
            return Mission.objects.filter(id__in=ids)

        elif status_param == 'pending':
            ids = user_subs.filter(status='PENDING').values_list('mission_id', flat=True)
            return Mission.objects.filter(id__in=ids)

        else:  # active (پیش‌فرض)
            done_ids = user_subs.filter(status__in=['PENDING', 'APPROVED']).values_list('mission_id', flat=True)
            return Mission.objects.filter(is_active=True).exclude(id__in=done_ids).order_by('-created_at')

    def create(self, request, *args, **kwargs):
        # فقط ادمین اجازه ساخت ماموریت دارد
        if request.user.role != 'ADMIN':
            return Response({'error': 'فقط مدیران می‌توانند ماموریت تعریف کنند'}, status=403)
        return super().create(request, *args, **kwargs)

    # اکشن ثبت گزارش کار (مخصوص کارمندان)
    @action(detail=True, methods=['post'], url_path='submit')
    def report_mission(self, request, pk=None):
        mission = self.get_object()

        # بررسی تکراری نبودن گزارش
        if MissionSubmission.objects.filter(user=request.user, mission=mission,
                                            status__in=['PENDING', 'APPROVED']).exists():
            return Response({'error': 'گزارش این ماموریت قبلا ثبت شده است.'}, status=400)

        serializer = MissionSubmissionSerializer(data=request.data)

        # حالا سریالایزر بدون نیاز به فیلد mission معتبر (valid) می‌شود
        if serializer.is_valid():
            serializer.save(user=request.user, mission=mission)
            return Response({'message': 'ثبت شد!'}, status=201)

        return Response(serializer.errors, status=400)


# --- این کلاس اضافه شد تا خطای urls.py رفع شود ---
class AdminMissionViewSet(MissionViewSet):
    """
    این کلاس دقیقاً همان کار MissionViewSet را می‌کند
    اما وجودش ضروری است چون در urls.py صدا زده شده است.
    """
    pass


# --- 2. مدیریت گزارش‌کارها ---

class MissionSubmissionViewSet(viewsets.ModelViewSet):
    serializer_class = MissionSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return MissionSubmission.objects.all().order_by('-submitted_at')
        return MissionSubmission.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        if request.user.role != 'ADMIN':
            return Response({'error': 'دسترسی غیرمجاز'}, status=403)

        submission = self.get_object()
        if submission.status == 'APPROVED':
            return Response({'message': 'قبلا تایید شده'}, status=400)

        with transaction.atomic():
            submission.status = 'APPROVED'
            submission.save()

            # واریز پاداش
            reward = submission.mission.reward_ac
            user = submission.user

            # نگاشت دسته‌بندی به نوع توکن
            cat_map = {
                'performance': 'PERFORMANCE', 'cultural': 'CULTURAL',
                'discipline': 'DISCIPLINE', 'creative': 'IDEA'
            }
            t_type = cat_map.get(submission.mission.category, 'PERFORMANCE')

            Transaction.objects.create(
                user=user, amount=reward, token_type=t_type,
                description=f"پاداش: {submission.mission.title}"
            )

        return Response({'message': 'تایید و واریز شد'})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        if request.user.role != 'ADMIN': return Response({'error': 'دسترسی غیرمجاز'}, status=403)
        submission = self.get_object()
        submission.status = 'REJECTED'
        submission.save()
        return Response({'message': 'رد شد'})


# --- 3. مدیریت حضور و غیاب ---

class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return Attendance.objects.all().order_by('-date')
        return Attendance.objects.filter(user=self.request.user).order_by('-date')

    @action(detail=False, methods=['post'], url_path='upload-excel')
    def upload_excel(self, request):
        return Response({'message': 'فایل پردازش شد'})

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        return Response({'chart_data': [], 'total_fines': 0, 'avg_delay': 0})

    @action(detail=False, methods=['get'])
    def logs(self, request):
        return Response([])


# --- 4. مدیریت آموزش ---

class TrainingSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    # دیکشنری دوره‌های فرضی
    COURSES = {
        1: {'id': 1, 'title': 'مدیریت زمان و بهره‌وری', 'duration_minutes': 45, 'reward_ac': 150},
        2: {'id': 2, 'title': 'اصول کار تیمی در استارتاپ', 'duration_minutes': 30, 'reward_ac': 100},
        3: {'id': 3, 'title': 'امنیت سایبری مقدماتی', 'duration_minutes': 60, 'reward_ac': 200},
    }

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return TrainingSession.objects.all()
        return TrainingSession.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def catalog(self, request):
        active = TrainingSession.objects.filter(user=request.user, end_time__isnull=True).first()
        active_data = None

        if active:
            course_id = next((k for k, v in self.COURSES.items() if v['title'] == active.topic), None)
            if course_id:
                elapsed = (timezone.now() - active.start_time).total_seconds()
                total_seconds = self.COURSES[course_id]['duration_minutes'] * 60
                remaining = total_seconds - elapsed

                active_data = {
                    'training': self.COURSES[course_id],
                    'remaining_seconds': int(remaining) if remaining > 0 else 0
                }

        return Response({'all_trainings': list(self.COURSES.values()), 'active_session': active_data})

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        try:
            course_id = int(pk)
        except:
            return Response(status=404)

        if course_id not in self.COURSES: return Response(status=404)
        if TrainingSession.objects.filter(user=request.user, end_time__isnull=True).exists():
            return Response({'error': 'آموزش نیمه‌تمام دارید'}, status=400)

        TrainingSession.objects.create(user=request.user, topic=self.COURSES[course_id]['title'])
        return Response({'message': 'شروع شد'})

    @action(detail=True, methods=['post'])
    def finish(self, request, pk=None):
        try:
            course_id = int(pk)
        except:
            return Response(status=404)

        if course_id not in self.COURSES: return Response(status=404)
        title = self.COURSES[course_id]['title']
        session = TrainingSession.objects.filter(user=request.user, topic=title, end_time__isnull=True).first()

        if not session: return Response({'error': 'یافت نشد'}, status=404)

        session.end_time = timezone.now()
        session.duration_minutes = int((session.end_time - session.start_time).total_seconds() / 60)
        session.save()
        return Response({'message': 'پایان یافت'})

    @action(detail=False, methods=['get'], url_path='pending-verifications')
    def pending_verifications(self, request):
        return Response([])