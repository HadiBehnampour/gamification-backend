from rest_framework import serializers
from .models import Product, Transaction, StakingPlan, Badge, UserBadge


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class TransactionSerializer(serializers.ModelSerializer):
    created_at_fa = serializers.SerializerMethodField()
    # نمایش متن فارسی نوع توکن
    type_display = serializers.CharField(source='get_token_type_display', read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'amount', 'token_type', 'type_display', 'description', 'created_at', 'created_at_fa']

    def get_created_at_fa(self, obj):
        # اینجا می‌توانید از کتابخانه jdatetime برای تبدیل به شمسی استفاده کنید
        # فعلا تاریخ میلادی را به صورت رشته برمی‌گردانیم
        return obj.created_at.strftime("%Y-%m-%d %H:%M")


class StakingPlanSerializer(serializers.ModelSerializer):
    # فیلدهای محاسباتی برای نمایش در پنل ادمین
    total_stacked = serializers.SerializerMethodField()
    active_users_count = serializers.SerializerMethodField()
    is_golden = serializers.SerializerMethodField()

    class Meta:
        model = StakingPlan
        fields = ['id', 'name', 'duration_months', 'profit_percent', 'is_active', 'total_stacked', 'active_users_count',
                  'is_golden']

    def get_total_stacked(self, obj):
        return 0  # در فاز بعدی می‌توانیم محاسبه واقعی را اضافه کنیم

    def get_active_users_count(self, obj):
        return 0  # در فاز بعدی

    def get_is_golden(self, obj):
        return obj.profit_percent >= 20  # اگر سود بیشتر از ۲۰٪ بود طلایی نمایش بده


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = '__all__'


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = BadgeSerializer()

    class Meta:
        model = UserBadge
        fields = ['badge', 'earned_at']