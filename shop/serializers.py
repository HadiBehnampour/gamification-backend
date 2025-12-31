from rest_framework import serializers
from .models import ShopItem, Purchase


class ShopItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShopItem
        fields = '__all__'


class PurchaseSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source='item.name')

    class Meta:
        model = Purchase
        fields = ['id', 'item', 'item_name', 'purchased_at', 'status']
        read_only_fields = ['status', 'user']