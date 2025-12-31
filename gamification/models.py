from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Transaction(models.Model):
    """
    دفتر کل تراکنش‌ها (Ledger).
    هر تغییری در امتیازات باید از طریق ایجاد یک رکورد در این جدول انجام شود.
    """

    class TokenTypes(models.TextChoices):
        PERFORMANCE = 'PERFORMANCE', 'توکن عملکرد'  # [cite: 140]
        DISCIPLINE = 'DISCIPLINE', 'توکن نظم'  # [cite: 154]
        CULTURAL = 'CULTURAL', 'توکن فرهنگی'  # [cite: 147]
        IDEA = 'IDEA', 'توکن ایده ترند'  # [cite: 160]
        PURCHASE = 'PURCHASE', 'خرید از فروشگاه'  # [cite: 177]
        ADMIN_ADJUSTMENT = 'ADMIN', 'اصلاح مدیریتی'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="کاربر"
    )
    amount = models.IntegerField(verbose_name="مقدار (AC)")  # منفی برای جریمه/خرید، مثبت برای پاداش
    token_type = models.CharField(max_length=20, choices=TokenTypes.choices, verbose_name="نوع توکن")
    description = models.CharField(max_length=255, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ ثبت")

    def save(self, *args, **kwargs):
        # جلوگیری از تکرار اعمال تراکنش در صورت ویرایش (فقط هنگام ایجاد کار کند)
        if not self.pk:
            # 1. آپدیت موجودی قابل خرج (Balance)
            self.user.current_balance += self.amount

            # 2. آپدیت امتیاز کل (Total Points) فقط اگر امتیاز مثبت باشد (پاداش)
            # طبق منطق: جریمه‌ها یا خریدها نباید لول (تجربه) را پایین بیاورند، فقط موجودی را کم می‌کنند.
            if self.amount > 0:
                self.user.total_points += self.amount
                # 3. بررسی ارتقای لول
                self.user.update_level()

            self.user.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.token_type})"


class Badge(models.Model):
    name = models.CharField(max_length=100, verbose_name="نام نشان")
    description = models.TextField(verbose_name="توضیحات")
    # نام آیکون از مجموعه Lucide React (مثلاً 'Award', 'Star', 'Zap')
    icon_name = models.CharField(max_length=50, verbose_name="نام آیکون (Lucide)")
    criteria = models.TextField(verbose_name="شرط دریافت")

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="تاریخ دریافت")

    class Meta:
        unique_together = ('user', 'badge')  # هر بج را فقط یک بار می‌توان گرفت