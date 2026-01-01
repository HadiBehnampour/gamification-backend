from rest_framework import serializers
from .models import Mission, MissionSubmission, Attendance, TrainingSession

class MissionSerializer(serializers.ModelSerializer):
    # برای نمایش وضعیت کاربر نسبت به ماموریت (آیا انجام داده؟)
    user_status = serializers.SerializerMethodField()

    class Meta:
        model = Mission
        fields = '__all__'

    def get_user_status(self, obj):
        # این متد نیاز به request دارد که در context پاس داده می‌شود
        user = self.context.get('request').user
        if user and not user.is_anonymous:
            sub = MissionSubmission.objects.filter(mission=obj, user=user).first()
            if sub:
                return sub.status
        return 'NOT_STARTED'

class MissionSubmissionSerializer(serializers.ModelSerializer):
    mission_title = serializers.ReadOnlyField(source='mission.title')
    user_name = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = MissionSubmission
        fields = ['id', 'mission', 'mission_title', 'user_name', 'link', 'description', 'image', 'status', 'admin_feedback', 'submitted_at']
        read_only_fields = ['status', 'admin_feedback']

class AttendanceSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='user.username') # برای جدول ادمین
    time = serializers.SerializerMethodField() # ساعت ورود فرمت شده
    delay = serializers.SerializerMethodField() # تاخیر فرمت شده

    class Meta:
        model = Attendance
        fields = ['id', 'name', 'date', 'time', 'check_in', 'check_out', 'delay_minutes', 'delay', 'status', 'daily_points']

    def get_time(self, obj):
        return obj.check_in.strftime("%H:%M")

    def get_delay(self, obj):
        return f"{obj.delay_minutes} دقیقه"

class TrainingSessionSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.username')
    user_avatar = serializers.ReadOnlyField(source='user.avatar.url')

    class Meta:
        model = TrainingSession
        fields = '__all__'