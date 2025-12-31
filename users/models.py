from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'مدیر'),
        ('EMPLOYEE', 'کارمند'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)

    # سیستم لول و امتیاز
    level = models.PositiveIntegerField(default=1)
    total_points = models.PositiveIntegerField(default=0)
    current_balance = models.PositiveIntegerField(default=0)

    # --- این همون چیزیه که برای تلگرام لازم داریم (فقط همین یه خط) ---
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def update_level(self):
        new_level = (self.total_points // 500) + 1
        if new_level != self.level:
            self.level = new_level
            self.save()


# مدل پیام‌ها (که قبلاً اضافه کردیم)
class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.recipient.username}"