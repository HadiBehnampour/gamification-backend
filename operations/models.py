from django.db import models
from users.models import User


class Mission(models.Model):
    CATEGORY_CHOICES = [
        ('performance', 'عملکردی (KPI)'),  # تغییر از KPI به performance برای هماهنگی با فرانت
        ('cultural', 'فرهنگی'),
        ('discipline', 'نظمی'),
        ('creative', 'ایده و خلاقیت'),
    ]

    title = models.CharField(max_length=255, verbose_name="عنوان")

    # --- تغییر مهم اینجاست ---
    # blank=True و null=True یعنی این فیلد اختیاری است و اگر فرانت آن را نفرستاد، ارور نده
    description = models.TextField(blank=True, null=True, verbose_name="توضیحات")
    # -----------------------

    reward_ac = models.PositiveIntegerField(verbose_name="پاداش (AC)")
    category = models.CharField(max_length=50, default='KPI', verbose_name="دسته‌بندی")
    deadline = models.CharField(max_length=50, blank=True, null=True, verbose_name="مهلت")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# بقیه کلاس‌ها (MissionSubmission و ...) بدون تغییر بمانند
class MissionSubmission(models.Model):
    STATUS_CHOICES = [('PENDING', 'در انتظار'), ('APPROVED', 'تایید'), ('REJECTED', 'رد')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='submissions')
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE)
    link = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True)  # این هم اختیاری است
    image = models.ImageField(upload_to='submissions/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    admin_feedback = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    check_in = models.TimeField()
    check_out = models.TimeField(null=True, blank=True)
    delay_minutes = models.IntegerField(default=0)
    status = models.CharField(max_length=20, default='On-time')
    daily_points = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class TrainingSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.CharField(max_length=255)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    is_approved = models.BooleanField(default=False)