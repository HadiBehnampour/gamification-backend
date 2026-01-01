from django.db import models
from django.conf import settings


class Transaction(models.Model):
    """
    دفتر کل تمام تراکنش‌های مالی (مثبت و منفی)
    """
    TOKEN_TYPES = [
        ('PERFORMANCE', 'عملکرد'),
        ('DISCIPLINE', 'نظم'),
        ('CULTURAL', 'فرهنگی'),
        ('IDEA', 'ایده و خلاقیت'),
        ('SPEND', 'خرید/خرج'),
        ('STAKING', 'سرمایه‌گذاری'),
        ('ADMIN', 'اصلاح مدیریتی'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    amount = models.IntegerField()  # می‌تواند منفی (خرج) یا مثبت (پاداش) باشد
    token_type = models.CharField(max_length=20, choices=TOKEN_TYPES)
    description = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.amount} ({self.token_type})"


class Product(models.Model):
    """
    محصولات موجود در فروشگاه
    """
    CATEGORY_CHOICES = [
        ('gadget', 'گجت و ابزار'),
        ('daily', 'مصارف روزانه'),
        ('digital', 'دیجیتال'),
        ('service', 'خدمات و مرخصی'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.PositiveIntegerField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='gadget')
    stock = models.IntegerField(default=-1)  # -1 به معنی موجودی نامحدود
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class StakingPlan(models.Model):
    """
    پلن‌های سرمایه‌گذاری در بانک توکن
    """
    name = models.CharField(max_length=255)
    duration_months = models.PositiveIntegerField(help_text="مدت زمان به ماه")
    profit_percent = models.PositiveIntegerField(help_text="درصد سود")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.profit_percent}%)"


# (اختیاری) مدل بج‌ها اگر بخواهید استفاده کنید
class Badge(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_name = models.CharField(max_length=50)
    criteria = models.TextField()


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)