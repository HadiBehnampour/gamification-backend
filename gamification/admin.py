from django.contrib import admin
from .models import Transaction, Product, StakingPlan, Badge, UserBadge

admin.site.register(Transaction)
admin.site.register(Product)
admin.site.register(StakingPlan)
admin.site.register(Badge)
admin.site.register(UserBadge)
