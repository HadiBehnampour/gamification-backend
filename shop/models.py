from django.db import models


class ShopItem(models.Model):
    CATEGORY_CHOICES = (
        ('گجت', 'گجت و ابزار'),
        ('روزانه', 'مصارف روزانه'),
    )

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.PositiveIntegerField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='گجت')
    image = models.ImageField(upload_to='shop/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    # فیلد stock حذف شده است

    def __str__(self):
        return f"{self.name} ({self.price} AC)"


# --- احتمالا این بخش را یادت رفته بود کپی کنی 👇 ---
class Purchase(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'در انتظار تحویل'),
        ('DELIVERED', 'تحویل داده شد'),
        ('CANCELED', 'لغو شده'),
    )

    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    item = models.ForeignKey(ShopItem, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.user.username} -> {self.item.name}"