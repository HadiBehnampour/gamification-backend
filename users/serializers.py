from rest_framework import serializers
from .models import User, Message
# اصلاح: UserBadgeSerializer (مفرد) صحیح است
from gamification.serializers import TransactionSerializer, UserBadgeSerializer

class UserProfileSerializer(serializers.ModelSerializer):
    recent_transactions = serializers.SerializerMethodField()
    badges = UserBadgeSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'role', 'avatar',
            'level', 'total_points', 'current_balance',
            'recent_transactions', 'badges'
        ]
        read_only_fields = ['level', 'total_points', 'current_balance', 'role']

    def get_recent_transactions(self, obj):
        transactions = obj.transactions.all().order_by('-created_at')[:5]
        return TransactionSerializer(transactions, many=True).data

# اصلاح: حرف S در کلمه Serializer باید بزرگ باشد
class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.ReadOnlyField(source='sender.username')
    sender_avatar = serializers.ReadOnlyField(source='sender.avatar.url')

    class Meta:
        model = Message
        fields = ['id', 'sender', 'sender_name', 'sender_avatar', 'recipient', 'subject', 'body', 'is_read', 'created_at']
        read_only_fields = ['sender', 'created_at', 'is_read']