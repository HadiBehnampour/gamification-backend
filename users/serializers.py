from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Message


# ۱. سریالایزر لاگین (اصلاح شده برای هماهنگی با توکن فرانت)
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # فرانت هر دو کلید را می‌بیند تا خطایی رخ ندهد
        data['token'] = data['access']
        data['access'] = data['access']

        data['role'] = self.user.role.lower()
        data['user_id'] = self.user.id
        full_name = f"{self.user.first_name} {self.user.last_name}".strip()
        data['full_name'] = full_name if full_name else self.user.username
        return data


# ۲. سریالایزر نمایش پروفایل (بدون تغییر)
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'role',
                  'current_balance', 'total_points', 'level', 'avatar']

    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                # این خط آدرس را از /media/... به http://127.0.0.1:8000/media/... تبدیل می‌کند
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


# ۳. سریالایزر ساخت و ویرایش کاربر (حل مشکل رمز عبور)
class UserCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'last_name', 'email', 'role']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }

    def create(self, validated_data):
        # جدا کردن رمز عبور و استفاده از create_user برای هش کردن
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)  # رمز را از متن ساده به کد امن تبدیل می‌کند
        user.save()
        return user

    def update(self, instance, validated_data):
        # مدیریت تغییر رمز در هنگام ویرایش
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


# ۴. سریالایزر پیام‌ها (بدون تغییر)
class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'sender_avatar', 'recipient', 'subject', 'body', 'is_read',
                  'created_at']
        read_only_fields = ['sender', 'created_at', 'is_read']

    def get_sender_avatar(self, obj):
        return obj.sender.avatar.url if obj.sender.avatar else None