from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Mission, MissionSubmission, Attendance, TrainingSession
from .serializers import MissionSerializer, MissionSubmissionSerializer, AttendanceSerializer, TrainingSessionSerializer
from gamification.models import Transaction


class MissionViewSet(viewsets.ModelViewSet):
    queryset = Mission.objects.filter(is_active=True)
    serializer_class = MissionSerializer
    permission_classes = [permissions.IsAuthenticated]


class MissionSubmissionViewSet(viewsets.ModelViewSet):
    queryset = MissionSubmission.objects.all()
    serializer_class = MissionSubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ADMIN':
            return MissionSubmission.objects.all()
        return MissionSubmission.objects.filter(user=user)

    @action(detail=True, methods=['post'], url_path='approve')
    def approve_submission(self, request, pk=None):
        if request.user.role != 'ADMIN':
            return Response({'error': 'Admin access required'}, status=403)

        submission = self.get_object()

        if submission.status == 'APPROVED':
            return Response({'message': 'Already approved'}, status=400)

        with transaction.atomic():
            submission.status = 'APPROVED'
            submission.save()

            reward = submission.mission.reward_amount
            mission_title = submission.mission.title

            # FIX: استفاده از format برای جلوگیری از خطای ادیتور در متون فارسی
            desc_text = "پاداش ماموریت: {}".format(mission_title)

            Transaction.objects.create(
                user=submission.user,
                amount=reward,
                token_type='PERFORMANCE',
                description=desc_text
            )

        return Response({'message': 'Mission approved successfully'})


class AttendanceViewSet(viewsets.ModelViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return Attendance.objects.all()
        return Attendance.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TrainingSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TrainingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'ADMIN':
            return TrainingSession.objects.all()
        return TrainingSession.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)