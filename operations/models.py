from django.db import models
from django.conf import settings

class Mission(models.Model):
    """
    [cite_start]ماموریت‌هایی که ادمین تعریف می‌کند [cite: 206]
    """
    title = models.CharField(max_length=200, verbose_name="عنوان ماموریت")
    description = models.TextField(verbose_name="توضیحات کامل")
    reward_amount = models.PositiveIntegerField(verbose_name="پاداش (AC)")
    deadline = models.DateTimeField(verbose_name="مهلت انجام")
    is_active = models.BooleanField(default=True, verbose_name="فعال است؟")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class MissionSubmission(models.Model):
    """
    [cite_start]گزارش کار کارمند برای یک ماموریت [cite: 213, 207]
    """
    STATUS_CHOICES = (
        ('PENDING', 'در انتظار بررسی'),
        ('APPROVED', 'تایید شده'),
        ('REJECTED', 'رد شده'),
    )

    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, verbose_name="ماموریت مربوطه")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کارمند")
    proof_link = models.URLField(blank=True, null=True, verbose_name="لینک مستندات (Drive/Notion)")
    proof_image = models.ImageField(upload_to='missions/', blank=True, null=True, verbose_name="تصویر ضمیمه")
    description = models.TextField(blank=True, verbose_name="توضیحات کارمند")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING', verbose_name="وضعیت")
    submitted_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ارسال")
    admin_feedback = models.TextField(blank=True, verbose_name="بازخورد مدیر")

    def __str__(self):
        return f"{self.user.username} - {self.mission.title}"

class Attendance(models.Model):
    """
    [cite_start]سیستم حضور و غیاب برای محاسبه تاخیر و کسر امتیاز [cite: 212, 227-229]
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کارمند")
    date = models.DateField(auto_now_add=True, verbose_name="تاریخ")
    check_in = models.TimeField(auto_now_add=True, verbose_name="ساعت ورود")
    check_out = models.TimeField(null=True, blank=True, verbose_name="ساعت خروج")
    delay_minutes = models.PositiveIntegerField(default=0, verbose_name="دقایق تاخیر")
    is_penalty_applied = models.BooleanField(default=False, verbose_name="جریمه اعمال شده؟")

    def __str__(self):
        return f"{self.user.username} - {self.date}"

class TrainingSession(models.Model):
    """
    [cite_start]کارگاه آموزشی تایمردار [cite: 148, 297]
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="کارمند")
    topic = models.CharField(max_length=200, verbose_name="موضوع آموزش")
    start_time = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    end_time = models.DateTimeField(null=True, blank=True, verbose_name="زمان پایان")
    duration_minutes = models.PositiveIntegerField(default=0, verbose_name="مدت زمان (دقیقه)")
    is_approved = models.BooleanField(default=False, verbose_name="تایید نهایی ادمین")

    def __str__(self):
        return f"{self.user.username} - {self.topic}"