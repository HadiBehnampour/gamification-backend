from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Message


# تنظیمات نمایش کاربر سفارشی در پنل ادمین
class CustomUserAdmin(UserAdmin):
    model = User

    # فیلدهایی که در لیست کاربران نمایش داده می‌شوند
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'level', 'current_balance', 'is_staff']

    # فیلترهای بغل صفحه
    list_filter = ['role', 'level', 'is_staff', 'is_active']

    # فیلدها در صفحه ویرایش کاربر
    # نکته: fieldsets پیش‌فرض UserAdmin را گسترش می‌دهیم تا فیلدهای ما هم باشند
    fieldsets = UserAdmin.fieldsets + (
        ('اطلاعات تکمیلی (گیمیفیکیشن)', {
            'fields': ('role', 'level', 'total_points', 'current_balance', 'avatar', 'telegram_chat_id'),
        }),
    )

    # فیلدها در صفحه افزودن کاربر جدید
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('اطلاعات تکمیلی', {
            'fields': ('role', 'email', 'first_name', 'last_name'),
        }),
    )


# تنظیمات نمایش پیام‌ها
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'recipient', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['subject', 'body', 'sender__username', 'recipient__username']


# ثبت مدل‌ها
admin.site.register(User, CustomUserAdmin)
admin.site.register(Message, MessageAdmin)