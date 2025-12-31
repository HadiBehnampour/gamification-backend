from rest_framework import serializers
from .models import Mission, MissionSubmission, Attendance, TrainingSession

class MissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mission
        fields = '__all__'

class MissionSubmissionSerializer(serializers.ModelSerializer):
    # فیلدهای کمکی برای اینکه در فرانت اسم‌ها رو ببینیم نه فقط ID
    mission_title = serializers.ReadOnlyField(source='mission.title')
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = MissionSubmission
        fields = [
            'id', 'mission', 'mission_title', 'user', 'user_name',
            'proof_link', 'proof_image', 'description', 'status',
            'submitted_at', 'admin_feedback'
        ]
        read_only_fields = ['status', 'admin_feedback', 'user']

class AttendanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attendance
        fields = '__all__'

class TrainingSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingSession
        fields = '__all__'