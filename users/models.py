from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'مدیر'),
        ('EMPLOYEE', 'کارمند'),
    )
    # اصلاح خطای سینتکسی: choices فقط یک بار نوشته شود
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')

    # سیستم لول و امتیاز
    level = models.PositiveIntegerField(default=1)
    total_points = models.PositiveIntegerField(default=0)
    current_balance = models.PositiveIntegerField(default=0)

    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # متد محاسبه لول بر اساس بازه‌های پیشنهادی جدید
    def update_level(self):
        points = self.total_points
        if points < 500:
            new_level = 1
        elif points < 1500:
            new_level = 2
        elif points < 2500:
            new_level = 3
        elif points < 4000:
            new_level = 4
        else:
            new_level = 5

        if self.level != new_level:
            self.level = new_level

    # متد save برای آپدیت خودکار لول قبل از ذخیره در دیتابیس
    def save(self, *args, **kwargs):
        self.update_level()
        super().save(*args, **kwargs)


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"از {self.sender} به {self.recipient}"