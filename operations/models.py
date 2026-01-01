from django.db import models
from users.models import User

class Mission(models.Model):
    CATEGORY_CHOICES = [
        ('performance', 'عملکردی (KPI)'),
        ('cultural', 'فرهنگی'),
        ('discipline', 'نظمی'),
        ('creative', 'خلاقیت'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    reward_ac = models.PositiveIntegerField(verbose_name="پاداش (AC)")
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='performance')
    deadline = models.CharField(max_length=50, blank=True, null=True, help_text="تاریخ شمسی مثل ۱۴۰۳/۱۰/۲۰")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class MissionSubmission(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'در انتظار بررسی'),
        ('APPROVED', 'تایید شده'),
        ('REJECTED', 'رد شده'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    link = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='submissions/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.mission}"

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField() # تاریخ میلادی ذخیره می‌شود
    check_in = models.TimeField()
    check_out = models.TimeField(null=True, blank=True)
    delay_minutes = models.IntegerField(default=0)
    # وضعیت برای نمایش در فرانت (On-time, Late, Absent)
    status = models.CharField(max_length=20, default='On-time')
    # امتیازی که بابت این روز گرفته یا از دست داده
    daily_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.date}"

class TrainingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=255)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} - {self.topic}"