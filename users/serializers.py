from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Message

# 1. سریالایزر سفارشی برای لاگین (JWT)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # اطلاعات اضافه‌ای که فرانت بعد از لاگین نیاز دارد
        data['role'] = self.user.role
        data['user_id'] = self.user.id
        data['full_name'] = f"{self.user.first_name} {self.user.last_name}" if self.user.first_name else self.user.username
        return data

# 2. سریالایزر پروفایل کاربر
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role',
                  'current_balance', 'total_points', 'level', 'avatar', 'date_joined']

# 3. سریالایزر پیام‌ها
class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'sender_avatar', 'recipient', 'subject', 'body', 'is_read', 'created_at']
        read_only_fields = ['sender', 'created_at', 'is_read']

    def get_sender_avatar(self, obj):
        return obj.sender.avatar.url if obj.sender.avatar else None