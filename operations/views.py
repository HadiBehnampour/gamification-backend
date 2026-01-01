from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Sum, Avg
from django.db import transaction
import datetime

from .models import Mission, MissionSubmission, Attendance, TrainingSession
from .serializers import MissionSerializer, MissionSubmissionSerializer, AttendanceSerializer, TrainingSessionSerializer
from users.models import User
from gamification.models import Transaction


# --- 1. مدیریت ماموریت‌ها ---

class MissionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    نمایش ماموریت‌ها به کاربران و دریافت گزارش کار
    """
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        status_param = self.request.query_params.get('status', 'active')

        user_subs = MissionSubmission.objects.filter(user=user)

        if status_param == 'completed':
            ids = user_subs.filter(status='APPROVED').values_list('mission_id', flat=True)
            return Mission.objects.filter(id__in=ids)
        elif status_param == 'pending':
            ids = user_subs.filter(status='PENDING').values_list('mission_id', flat=True)
            return Mission.objects.filter(id__in=ids)
        else:  # active
            # ماموریت‌هایی که کاربر هنوز انجام نداده یا در انتظار نیست
            done_ids = user_subs.filter(status__in=['PENDING', 'APPROVED']).values_list('mission_id', flat=True)
            return Mission.objects.filter(is_active=True).exclude(id__in=done_ids)

    @action(detail=True, methods=['post'], url_path='submit')
    def submit_report(self, request, pk=None):
        mission = self.get_object()

        if MissionSubmission.objects.filter(user=request.user, mission=mission,
                                            status__in=['PENDING', 'APPROVED']).exists():
            return Response({'error': 'قبلا ارسال کرده‌اید'}, status=400)

        serializer = MissionSubmissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, mission=mission, status='PENDING')
            return Response({'message': 'گزارش ارسال شد'})
        return Response(serializer.errors, status=400)


class AdminMissionViewSet(viewsets.ModelViewSet):
    """
    مدیریت ماموریت‌ها برای ادمین (CRUD کامل)
    """
    queryset = Mission.objects.all().order_by('-created_at')
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        status_param = self.request.query_params.get('status')
        if status_param == 'active':
            return qs.filter(is_active=True)
        elif status_param == 'completed':
            return qs.filter(is_active=False)
        return qs


class MissionSubmissionViewSet(viewsets.ModelViewSet):
    """
    مدیریت گزارش‌ کارهای ارسالی (تایید/رد توسط ادمین)
    """
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
            return Response({'message': 'قبلا تایید شده است'}, status=400)

        with transaction.atomic():
            submission.status = 'APPROVED'
            submission.save()

            # واریز پاداش
            reward = submission.mission.reward_ac
            user = submission.user
            user.current_balance += reward
            user.total_points += reward
            user.save()

            Transaction.objects.create(
                user=user,
                amount=reward,
                token_type='PERFORMANCE',
                description=f"پاداش انجام ماموریت: {submission.mission.title}"
            )
        return Response({'message': 'تایید شد و پاداش واریز گردید'})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request, pk=None):
        if request.user.role != 'ADMIN': return Response({'error': 'دسترسی غیرمجاز'}, status=403)
        submission = self.get_object()
        submission.status = 'REJECTED'
        submission.save()
        return Response({'message': 'گزارش رد شد'})


# --- 2. مدیریت حضور و غیاب ---

class AttendanceViewSet(viewsets.ModelViewSet):
    """
    مدیریت حضور و غیاب (ادمین و کارمند)
    """
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return Attendance.objects.all().order_by('-date')
        return Attendance.objects.filter(user=self.request.user).order_by('-date')

    @action(detail=False, methods=['post'], url_path='upload-excel')
    def upload_excel(self, request):
        if 'file' not in request.FILES:
            return Response({'error': 'فایلی ارسال نشد'}, status=400)

        # شبیه‌سازی پردازش اکسل
        users = User.objects.filter(role='EMPLOYEE')
        today = datetime.date.today()
        created_count = 0
        for u in users:
            if not Attendance.objects.filter(user=u, date=today).exists():
                Attendance.objects.create(
                    user=u, date=today, check_in=datetime.time(8, 30), check_out=datetime.time(17, 0),
                    status='On-time', daily_points=10
                )
                created_count += 1
        return Response({'message': f'فایل پردازش شد. {created_count} رکورد ثبت گردید.'})

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        data = []
        for i in range(7):
            d = datetime.date.today() - datetime.timedelta(days=i)
            avg_delay = Attendance.objects.filter(date=d).aggregate(Avg('delay_minutes'))['delay_minutes__avg'] or 0
            data.append({'day': d.strftime("%m/%d"), 'minutes': int(avg_delay)})

        total_fines = Attendance.objects.aggregate(Sum('daily_points'))['daily_points__sum'] or 0
        return Response({
            'chart_data': list(reversed(data)),
            'total_fines': abs(total_fines) if total_fines < 0 else 0,
            'avg_delay': 15
        })

    @action(detail=False, methods=['get'])
    def logs(self, request):
        logs = Attendance.objects.all().order_by('-date', '-check_in')[:10]
        return Response(AttendanceSerializer(logs, many=True).data)


# --- 3. مدیریت آموزش ---

class TrainingSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    COURSES = {
        1: {'id': 1, 'title': 'مدیریت زمان و بهره‌وری', 'duration_minutes': 45, 'reward_ac': 150},
        2: {'id': 2, 'title': 'اصول کار تیمی در استارتاپ', 'duration_minutes': 30, 'reward_ac': 100},
        3: {'id': 3, 'title': 'امنیت سایبری مقدماتی', 'duration_minutes': 60, 'reward_ac': 200},
    }

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return TrainingSession.objects.all().order_by('-start_time')
        return TrainingSession.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def catalog(self, request):
        active = TrainingSession.objects.filter(user=request.user, end_time__isnull=True).first()
        active_data = None
        if active:
            course_id = next((k for k, v in self.COURSES.items() if v['title'] == active.topic), None)
            if course_id:
                elapsed = (timezone.now() - active.start_time).total_seconds()
                remaining = (self.COURSES[course_id]['duration_minutes'] * 60) - elapsed
                active_data = {'training': self.COURSES[course_id],
                               'remaining_seconds': int(remaining) if remaining > 0 else 0}

        return Response({'all_trainings': list(self.COURSES.values()), 'active_session': active_data})

    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        course_id = int(pk)
        if course_id not in self.COURSES: return Response(status=404)
        if TrainingSession.objects.filter(user=request.user, end_time__isnull=True).exists():
            return Response({'error': 'یک آموزش نیمه‌تمام دارید'}, status=400)

        TrainingSession.objects.create(user=request.user, topic=self.COURSES[course_id]['title'])
        return Response({'message': 'Started'})

    @action(detail=True, methods=['post'])
    def finish(self, request, pk=None):
        course_id = int(pk)
        title = self.COURSES[course_id]['title']
        session = TrainingSession.objects.filter(user=request.user, topic=title, end_time__isnull=True).first()
        if not session: return Response(status=404)

        session.end_time = timezone.now()
        session.duration_minutes = int((session.end_time - session.start_time).total_seconds() / 60)
        session.save()
        return Response({'message': 'Finished'})

    @action(detail=False, methods=['get'], url_path='pending-verifications')
    def pending_verifications(self, request):
        sessions = TrainingSession.objects.filter(is_approved=False, end_time__isnull=False)
        data = []
        for s in sessions:
            data.append({
                'id': s.id,
                'user_name': s.user.username,
                'user_avatar': s.user.avatar.url if s.user.avatar else None,
                'training_title': s.topic,
                'duration_spent': s.duration_minutes,
                'reward_ac': s.duration_minutes * 10
            })
        return Response(data)