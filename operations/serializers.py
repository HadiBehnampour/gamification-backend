from rest_framework import serializers
from .models import Mission, MissionSubmission, Attendance, TrainingSession

class MissionSerializer(serializers.ModelSerializer):
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = '__all__'
        # اضافه کردن این بخش باعث می‌شود اگر فرانت فیلدی را نفرستاد، سریالایزر خطا نگیرد
        extra_kwargs = {
            'description': {'required': False, 'allow_null': True},
            'deadline': {'required': False, 'allow_null': True},
            'category': {'required': False}
        }

    def get_user_status(self, obj):
        request = self.context.get('request')
        if request and request.user and not request.user.is_anonymous:
            sub = MissionSubmission.objects.filter(mission=obj, user=request.user).first()
            if sub:
                return sub.status
        return 'NOT_STARTED'

class MissionSubmissionSerializer(serializers.ModelSerializer):
    mission_title = serializers.ReadOnlyField(source='mission.title')
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = MissionSubmission
        fields = [
            'id', 'mission', 'mission_title', 'user', 'user_name',
            'link', 'description', 'image', 'status', 'submitted_at'
        ]
        # اضافه کردن mission و user به لیست read_only ارور را برطرف می‌کند
        read_only_fields = ['status', 'submitted_at', 'user', 'mission']

    def get_user_avatar(self, obj):
        if obj.user.avatar:
            return obj.user.avatar.url
        return None

class AttendanceSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='user.username')
    time = serializers.SerializerMethodField()
    delay = serializers.SerializerMethodField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'name', 'date', 'time', 'check_in', 'check_out',
            'delay_minutes', 'delay', 'status', 'daily_points'
        ]

    def get_time(self, obj):
        return obj.check_in.strftime("%H:%M")

    def get_delay(self, obj):
        return f"{obj.delay_minutes} دقیقه"

class TrainingSessionSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    user_avatar = serializers.SerializerMethodField()

    class Meta:
        model = TrainingSession
        fields = '__all__'

    def get_user_avatar(self, obj):
        if obj.user.avatar:
            return obj.user.avatar.url
        return None