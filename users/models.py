from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'مدیر'),
        ('EMPLOYEE', 'کارمند'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='EMPLOYEE')

    # سیستم لول و امتیاز
    level = models.PositiveIntegerField(default=1)
    total_points = models.PositiveIntegerField(default=0)  # امتیاز کل (برای لیدربرد)
    current_balance = models.PositiveIntegerField(default=0)  # موجودی قابل خرج (کیف پول)

    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    # متدی برای محاسبه و ارتقای لول (فرض: هر 500 امتیاز = 1 لول)
    def update_level(self):
        new_level = (self.total_points // 500) + 1
        if new_level != self.level:
            self.level = new_level
            self.save()


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"از {self.sender} به {self.recipient}"