from rest_framework import serializers
from .models import Transaction, Badge, UserBadge


class TransactionSerializer(serializers.ModelSerializer):
    # این فیلد اسم فارسی نوع توکن رو برمی‌گردونه (مثلاً: توکن عملکرد)
    token_type_display = serializers.CharField(source='get_token_type_display', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'token_type', 'token_type_display', 'description', 'created_at']


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = ['name', 'description', 'icon_name', 'criteria']


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer(read_only=True)

    class Meta:
        model = UserBadge
        fields = ['badge', 'earned_at']